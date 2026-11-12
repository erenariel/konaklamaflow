"""Second-AI handoff contract: suggestions, not self-executing commands.

This module deliberately implements *no* authenticated approvals, PMS writes, KBS,
identity verification, payments, or credential management.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any


class ProtocolError(ValueError):
    pass


def _utc(value: str) -> datetime:
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise ProtocolError("Invalid UTC timestamp") from None
    if stamp.tzinfo is None or stamp.utcoffset() != timedelta(0):
        raise ProtocolError("UTC timestamp with timezone is required")
    return stamp.astimezone(timezone.utc)


def make_handoff(review: dict[str, Any], issued_at: str, validity_seconds: int = 300) -> dict[str, Any]:
    """Build machine-readable review tasks with stable no-write, expiring references.

    A manifest is not an authorization token. A production integration must
    independently authenticate the operator and verify a fresh PMS snapshot.
    """
    issued = _utc(issued_at)
    if not (30 <= validity_seconds <= 600):
        raise ProtocolError("Validity must be 30..600 seconds")
    if review.get("mode") != "DRY_RUN_ONLY" or not isinstance(review.get("tasks"), list):
        raise ProtocolError("Expected a dry-run operations report")
    snapshot_hash = review.get("snapshot_sha256")
    if not isinstance(snapshot_hash, str) or len(snapshot_hash) != 64 or any(c not in '0123456789abcdef' for c in snapshot_hash):
        raise ProtocolError("Invalid snapshot checksum")
    tasks = []
    seen = set()
    for item in review["tasks"]:
        task_id = item.get("task_id")
        if not isinstance(task_id, str) or len(task_id) != 24 or task_id in seen:
            raise ProtocolError("Invalid or duplicate task id")
        seen.add(task_id)
        # Never pass a credential, guest name, passport number or email to another AI.
        tasks.append({
            "task_id": task_id,
            "reservation_ref": item["reservation_ref"],
            "source": item["source"],
            "state": item["state"],
            "reason_codes": list(item["reasons"]),
            "intent": "SUGGEST_RECEPTION_REVIEW",
            "allowed_tools": ["explain_status", "prepare_checklist"],
            "forbidden_tools": ["write_pms", "send_guest_message", "submit_kbs", "capture_payment", "read_identity_document"],
        })
    expires = issued + timedelta(seconds=validity_seconds)
    return {
        "protocol": "konaklamaflow.agent-handoff.v1",
        "mode": "NO_EXECUTION_READ_ONLY",
        "snapshot_sha256": snapshot_hash,
        "issued_at": issued.isoformat(), "expires_at": expires.isoformat(),
        "tasks": tasks,
        "disclaimer": "Never interpret this as permission for autonomous check-in. A trusted runtime must re-fetch current PMS data and require authorized human approval for writes.",
    }


def verify_suggestion(handoff: dict[str, Any], suggestion: dict[str, Any], checked_at: str) -> bool:
    """Validate an AI explanation reference; does not approve/execute an action."""
    now = _utc(checked_at)
    if not handoff or handoff.get("protocol") != "konaklamaflow.agent-handoff.v1":
        raise ProtocolError("Unknown handoff protocol")
    if not (_utc(handoff["issued_at"]) <= now < _utc(handoff["expires_at"])):
        raise ProtocolError("Handoff expired or not yet valid")
    if not isinstance(suggestion, dict) or set(suggestion) != {"task_id", "intent", "snapshot_sha256"}:
        raise ProtocolError("Invalid suggestion shape")
    if suggestion["snapshot_sha256"] != handoff["snapshot_sha256"]:
        raise ProtocolError("Stale or mismatched source snapshot")
    allowed = any(t["task_id"] == suggestion["task_id"] for t in handoff["tasks"])
    if not allowed or suggestion["intent"] != "SUGGEST_RECEPTION_REVIEW":
        raise ProtocolError("Unsupported action")
    return True
