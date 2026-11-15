"""Synthetic, non-authorizing decision trace with a tamper-evident hash chain.

The chain is NOT immutable, authenticated, production-safe, or evidence that
a real staff member reviewed anything. All actions are fictional simulations.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import re

from .explainability import ExplanationError, build_explanations

SCHEMA = "konaklamaflow.synthetic-decision-trace.v1"
MODE = "DRY_RUN_ONLY"
BOUNDARY = "SIMULATED_ONLY_NO_AUTHORIZATION_OR_WRITE"
ZERO_HASH = "0" * 64
ACTIONS = frozenset({"review_queued", "evidence_viewed", "handoff_suggested"})
ROLES = frozenset({"engine", "receptionist", "manager", "auditor"})
ROLE_ACTIONS = {
    "review_queued": frozenset({"engine"}),
    "evidence_viewed": frozenset({"receptionist", "manager", "auditor"}),
    "handoff_suggested": frozenset({"receptionist", "manager"}),
}
HEADER = frozenset({
    "schema", "mode", "boundary", "source_validity",
    "snapshot_sha256", "report_sha256", "events", "head_hash",
})
EVENT = frozenset({
    "sequence", "task_id", "kind", "simulated_role", "simulated_at",
    "reason_codes", "evidence_field_paths", "snapshot_sha256",
    "report_sha256", "previous_hash", "event_hash", "boundary",
})
TASK = re.compile(r"^[a-f0-9]{24}$")
HASH = re.compile(r"^[a-f0-9]{64}$")
TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class TraceError(ValueError):
    """Unverifiable synthetic trace. Never echo unexpected source data."""


def _check(ok):
    if not ok:
        raise TraceError("Invalid synthetic decision trace")


def _hash(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def _context(snapshot, report):
    try:
        proof = build_explanations(snapshot, report)
    except (ExplanationError, ValueError, TypeError, RecursionError, OverflowError):
        raise TraceError("Unverifiable source or report") from None
    _check(proof.get("mode") == "NO_EXECUTION_READ_ONLY")
    _check(proof.get("source_validity") == "UNVERIFIED_MINIMIZED_SNAPSHOT")
    tasks = {}
    for row in proof["arrivals"]:
        _check(isinstance(row["task_id"], str) and TASK.fullmatch(row["task_id"]))
        _check(row["task_id"] not in tasks)
        codes = [r["reason_code"] for r in row["reasons"]]
        fields = sorted({p for reason in row["reasons"]
                         for p in reason["evidence_field_paths"]})
        tasks[row["task_id"]] = {"reason_codes": codes,
                                 "evidence_field_paths": fields}
    return proof, tasks


def empty_trace(snapshot, report):
    """Create an empty proof-of-concept linked to the exact rule output."""
    proof, _ = _context(snapshot, report)
    return {
        "schema": SCHEMA,
        "mode": MODE,
        "boundary": BOUNDARY,
        "source_validity": proof["source_validity"],
        "snapshot_sha256": proof["snapshot_sha256"],
        "report_sha256": proof["report_sha256"],
        "events": [],
        "head_hash": ZERO_HASH,
    }


def _at(value):
    _check(type(value) is str and TIME.fullmatch(value) is not None)
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise TraceError("Invalid synthetic timestamp") from None
    _check(stamp.tzinfo == timezone.utc)
    return stamp


def verify_trace(snapshot, report, trace, *, expected_head=None):
    """Check the entire chain against current deterministic explanations.

    This does NOT detect whole-ledger replacement without an independently
    trusted anchor. expected_head is only useful if secured elsewhere.
    """
    ideal = empty_trace(snapshot, report)
    _, tasks = _context(snapshot, report)
    _check(type(trace) is dict and set(trace) == HEADER)
    for key in HEADER - {"events", "head_hash"}:
        _check(trace[key] == ideal[key])
    events = trace["events"]
    _check(type(events) is list and len(events) <= 100)
    previous = ZERO_HASH
    prior_time = None
    seen = set()
    for index, event in enumerate(events, start=1):
        _check(type(event) is dict and set(event) == EVENT)
        _check(type(event["sequence"]) is int and event["sequence"] == index)
        task_id = event["task_id"]
        _check(type(task_id) is str and TASK.fullmatch(task_id) is not None)
        _check(task_id in tasks)
        _check(type(event["kind"]) is str and event["kind"] in ACTIONS
               and type(event["simulated_role"]) is str
               and event["simulated_role"] in ROLES)
        _check(event["simulated_role"] in ROLE_ACTIONS[event["kind"]])
        stamp = _at(event["simulated_at"])
        if prior_time is not None:
            _check(stamp >= prior_time)
        prior_time = stamp
        _check(event["reason_codes"] == tasks[task_id]["reason_codes"])
        _check(event["evidence_field_paths"] == tasks[task_id]["evidence_field_paths"])
        _check(event["snapshot_sha256"] == ideal["snapshot_sha256"])
        _check(event["report_sha256"] == ideal["report_sha256"])
        _check(event["boundary"] == BOUNDARY)
        _check(event["previous_hash"] == previous)
        _check(type(event["event_hash"]) is str and HASH.fullmatch(event["event_hash"]))
        _check(event["event_hash"] == _hash({k: v for k, v in event.items()
                                            if k != "event_hash"}))
        fingerprint = (task_id, event["kind"], event["simulated_role"],
                       event["simulated_at"])
        _check(fingerprint not in seen)
        seen.add(fingerprint)
        previous = event["event_hash"]
    _check(trace["head_hash"] == previous)
    _check(type(trace["head_hash"]) is str and HASH.fullmatch(trace["head_hash"]))
    if expected_head is not None:
        _check(type(expected_head) is str and HASH.fullmatch(expected_head))
        _check(trace["head_hash"] == expected_head)
    return True


def append_simulated(snapshot, report, trace, *, task_id, kind, role, simulated_at):
    """Append an invented demo step; never an approval or a staff attestation."""
    verify_trace(snapshot, report, trace)
    _, tasks = _context(snapshot, report)
    _check(type(task_id) is str and task_id in tasks)
    _check(type(kind) is str and kind in ACTIONS
           and type(role) is str and role in ROLES
           and role in ROLE_ACTIONS[kind])
    new_time = _at(simulated_at)
    if trace["events"]:
        _check(new_time >= _at(trace["events"][-1]["simulated_at"]))
    _check(len(trace["events"]) < 100)
    _check(not any(e["task_id"] == task_id and e["kind"] == kind
                   and e["simulated_role"] == role
                   and e["simulated_at"] == simulated_at for e in trace["events"]))
    ideal = empty_trace(snapshot, report)
    new_event = {
        "sequence": len(trace["events"]) + 1,
        "task_id": task_id,
        "kind": kind,
        "simulated_role": role,
        "simulated_at": simulated_at,
        "reason_codes": list(tasks[task_id]["reason_codes"]),
        "evidence_field_paths": list(tasks[task_id]["evidence_field_paths"]),
        "snapshot_sha256": ideal["snapshot_sha256"],
        "report_sha256": ideal["report_sha256"],
        "previous_hash": trace["head_hash"],
        "boundary": BOUNDARY,
    }
    new_event["event_hash"] = _hash(new_event)
    result = deepcopy(trace)
    result["events"].append(new_event)
    result["head_hash"] = new_event["event_hash"]
    verify_trace(snapshot, report, result)
    return result


def fictional_walkthrough(snapshot, report):
    """Stable example from fictional data, with no real staff event."""
    proof, _ = _context(snapshot, report)
    _check(len(proof["arrivals"]) >= 2)
    first, second = proof["arrivals"][0]["task_id"], proof["arrivals"][1]["task_id"]
    trace = empty_trace(snapshot, report)
    trace = append_simulated(snapshot, report, trace, task_id=first,
                             kind="review_queued", role="engine",
                             simulated_at="2026-11-12T14:01:00Z")
    trace = append_simulated(snapshot, report, trace, task_id=first,
                             kind="evidence_viewed", role="receptionist",
                             simulated_at="2026-11-12T14:02:00Z")
    return append_simulated(snapshot, report, trace, task_id=second,
                            kind="handoff_suggested", role="manager",
                            simulated_at="2026-11-12T14:03:00Z")
