"""Read-only second-AI references, never authorization or executable commands.

The caller must retain the trusted manifest and regenerate current_review from
its trusted source; neither input may come from the AI being checked. There is
no provider call, tool dispatcher, approval, network access or PMS write here.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any

from .core import InputError
from .report_contract import validate_report


class ProtocolError(ValueError):
    pass


def _utc(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ProtocolError("UTC timestamp with timezone is required")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if stamp.tzinfo is None or stamp.utcoffset() != timedelta(0):
            raise ValueError
        return stamp.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise ProtocolError("Invalid UTC timestamp") from None


def make_handoff(review: Any, issued_at: str, validity_seconds: int = 300) -> dict[str, Any]:
    """Build a minimal, expiring review manifest from a validated local report."""
    issued = _utc(issued_at)
    if type(validity_seconds) is not int or not 30 <= validity_seconds <= 600:
        raise ProtocolError("Validity must be an integer from 30..600 seconds")
    try:
        validate_report(review)
        expires = issued + timedelta(seconds=validity_seconds)
    except (InputError, OverflowError):
        raise ProtocolError("Invalid operations report or expiry") from None
    digest = sha256(json.dumps(review, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "protocol": "konaklamaflow.agent-handoff.v1",
        "mode": "NO_EXECUTION_READ_ONLY",
        "snapshot_sha256": review["snapshot_sha256"],
        "report_sha256": digest,
        "issued_at": issued.isoformat(), "expires_at": expires.isoformat(),
        # No property, room, reservation/channel reference, or free text goes to AI.
        "tasks": [{"task_id": t["task_id"], "state": t["state"], "reason_codes": list(t["reasons"]),
                   "intent": "SUGGEST_RECEPTION_REVIEW",
                   "allowed_tools": ["explain_status", "prepare_checklist"]} for t in review["tasks"]],
    }


def verify_suggestion(handoff: Any, suggestion: Any, checked_at: str, *, current_review: Any) -> bool:
    """Check a read-only reference against a fresh trusted report. Never execute.

    This deliberately requires current_review: comparing an AI-provided checksum
    only to an old manifest cannot detect a newer source/property/evaluation.
    Repeated valid explanations are allowed; there is no write idempotency store.
    """
    now = _utc(checked_at)
    if not isinstance(handoff, dict) or not {"issued_at", "expires_at"} <= set(handoff):
        raise ProtocolError("Invalid handoff")
    issued, expires = _utc(handoff["issued_at"]), _utc(handoff["expires_at"])
    lifetime = (expires - issued).total_seconds()
    if not 30 <= lifetime <= 600 or not lifetime.is_integer() or not issued <= now < expires:
        raise ProtocolError("Handoff expired, future dated or invalid lifetime")
    expected = make_handoff(current_review, handoff["issued_at"], int(lifetime))
    if handoff != expected:
        raise ProtocolError("Changed report or invalid manifest")
    if not isinstance(suggestion, dict) or set(suggestion) != {"task_id", "intent", "snapshot_sha256", "report_sha256"}:
        raise ProtocolError("Invalid suggestion shape")
    if suggestion["snapshot_sha256"] != expected["snapshot_sha256"] or suggestion["report_sha256"] != expected["report_sha256"]:
        raise ProtocolError("Stale or mismatched report")
    if not isinstance(suggestion["task_id"], str) or suggestion["task_id"] not in {t["task_id"] for t in expected["tasks"]} or suggestion["intent"] != "SUGGEST_RECEPTION_REVIEW":
        raise ProtocolError("Unsupported action")
    return True
