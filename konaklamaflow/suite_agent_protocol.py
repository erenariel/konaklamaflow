"""Minimal second-AI references over the authoritative suite evaluation.

The trusted caller owns the source snapshot, retained manifest and UTC clock.
An AI supplies only the strict suggestion object. Hashes and TTL are not
signatures or authentication. This module has no AI call, tool dispatcher,
approval, network access, persistent audit/idempotency store or write operation.
"""
from __future__ import annotations

from datetime import timedelta
from hashlib import sha256
import json
import re
from typing import Any

from .agent_protocol import ProtocolError, _utc
from .experience_engine import BLOCKER_CODES, SnapshotError, evaluate

_PROTOCOL = 'konaklamaflow.suite-handoff.v1'
_INTENT = 'SUGGEST_RECEPTION_REVIEW'
_STATES = {'blocked', 'review_ready', 'other'}
_HEX64 = re.compile(r'[a-f0-9]{64}')
_HEX24 = re.compile(r'[a-f0-9]{24}')
_REVIEW_ONLY_POLICY = {'pms_writes': False, 'payments': False, 'kbs': False,
                       'guest_messages': False, 'human_approval_required': True}


def _digest(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                             separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def make_suite_handoff(trusted_snapshot: Any, issued_at: str,
                       validity_seconds: int = 300) -> dict[str, Any]:
    """Evaluate a minimized trusted source and expose only opaque review tasks.

    Engine references and report text stay local. Every task is bound to this
    full suite report and issuance interval, rather than a weaker v0.2 projection.
    The caller must not accept a snapshot or replacement manifest from the AI.
    """
    issued = _utc(issued_at)
    if type(validity_seconds) is not int or not 30 <= validity_seconds <= 600:
        raise ProtocolError('Validity must be an integer from 30..600 seconds')
    try:
        expires = issued + timedelta(seconds=validity_seconds)
        report = evaluate(trusted_snapshot)
        if (not isinstance(report, dict) or report.get('schema_version') != '0.3'
                or report.get('mode') != 'DRY_RUN_ONLY'):
            raise ValueError
        policy = report.get('approval_policy')
        if (not isinstance(policy, dict) or set(policy) != set(_REVIEW_ONLY_POLICY)
                or any(type(policy[k]) is not bool or policy[k] != expected
                       for k, expected in _REVIEW_ONLY_POLICY.items())):
            raise ValueError
        snapshot_hash = report.get('snapshot_sha256')
        if not isinstance(snapshot_hash, str) or _HEX64.fullmatch(snapshot_hash) is None:
            raise ValueError
        report_hash = _digest(report)
        arrivals = report.get('arrivals')
        if not isinstance(arrivals, list) or len(arrivals) > 5000:
            raise ValueError
        tasks = []
        seen = set()
        for row in arrivals:
            if not isinstance(row, dict):
                raise ValueError
            engine_id, state, codes = row.get('task_id'), row.get('status'), row.get('blockers')
            if row.get('human_approval_required') is not True:
                raise ValueError
            if not isinstance(engine_id, str) or _HEX24.fullmatch(engine_id) is None:
                raise ValueError
            if not isinstance(state, str) or state not in _STATES:
                raise ValueError
            if (not isinstance(codes, list) or any(not isinstance(c, str) or c not in BLOCKER_CODES for c in codes)
                    or len(codes) != len(set(codes))):
                raise ValueError
            if (state == 'review_ready' and codes) or (state == 'blocked' and not codes):
                raise ValueError
            task_id = _digest([_PROTOCOL, report_hash, engine_id,
                               issued.isoformat(), expires.isoformat()])[:24]
            if task_id in seen:
                raise ValueError
            seen.add(task_id)
            tasks.append({'task_id': task_id, 'state': state, 'reason_codes': list(codes),
                          'intent': _INTENT,
                          'allowed_tools': ['explain_status', 'prepare_checklist']})
    except (SnapshotError, ValueError, TypeError, OverflowError, RecursionError):
        # Exceptions may contain untrusted source content; never forward them.
        raise ProtocolError('Invalid minimized suite snapshot or evaluation') from None
    return {'protocol': _PROTOCOL, 'mode': 'NO_EXECUTION_READ_ONLY',
            'snapshot_sha256': snapshot_hash, 'report_sha256': report_hash,
            'issued_at': issued.isoformat(), 'expires_at': expires.isoformat(),
            'tasks': tasks}


def verify_suite_suggestion(retained_manifest: Any, suggestion: Any,
                            checked_at: str, *, current_snapshot: Any) -> bool:
    """Reevaluate trusted current state; validate an explanation, never execute.

    The retained manifest and checked_at must come from the trusted runtime,
    not the model. Repeated valid explanations are allowed. A True result is
    not authorization, staff approval, identity proof or a completed check-in.
    """
    now = _utc(checked_at)
    if (not isinstance(retained_manifest, dict)
            or not {'issued_at', 'expires_at'} <= set(retained_manifest)):
        raise ProtocolError('Invalid suite manifest')
    issued = _utc(retained_manifest['issued_at'])
    expires = _utc(retained_manifest['expires_at'])
    lifetime = (expires - issued).total_seconds()
    if not 30 <= lifetime <= 600 or not lifetime.is_integer() or not issued <= now < expires:
        raise ProtocolError('Suite manifest expired, future dated or invalid lifetime')
    expected = make_suite_handoff(current_snapshot, retained_manifest['issued_at'], int(lifetime))
    if retained_manifest != expected:
        raise ProtocolError('Changed suite state or invalid manifest')
    if (not isinstance(suggestion, dict)
            or set(suggestion) != {'task_id', 'intent', 'snapshot_sha256', 'report_sha256'}
            or not all(isinstance(v, str) for v in suggestion.values())):
        raise ProtocolError('Invalid suite suggestion shape')
    if (suggestion['snapshot_sha256'] != expected['snapshot_sha256']
            or suggestion['report_sha256'] != expected['report_sha256']):
        raise ProtocolError('Stale or mismatched suite report')
    if (suggestion['intent'] != _INTENT
            or suggestion['task_id'] not in {task['task_id'] for task in expected['tasks']}):
        raise ProtocolError('Unsupported suite action')
    return True
