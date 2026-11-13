"""Synthetic read-only source-envelope checks for a future PMS adapter boundary.

No PMS SDK, connector, credentials, authentication, rate plan, government
registration, payment posting, or live network operation exists here.
The caller must separately authenticate the operator and trust the clock.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import re

from .experience_engine import SnapshotError, evaluate, validate


class SourceBoundaryError(ValueError):
    """A source claim or snapshot cannot safely be evaluated."""


_REVISION = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_SOURCE = "SYNTHETIC_READ_ONLY_MOCK"
_KEYS = {"source", "property_id", "captured_at_utc", "revision", "snapshot"}


def _utc(value):
    if not isinstance(value, str) or len(value) > 35:
        raise SourceBoundaryError("Invalid trusted UTC timestamp")
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise SourceBoundaryError("Invalid trusted UTC timestamp") from None
    if moment.tzinfo is None or moment.utcoffset() != timedelta(0):
        raise SourceBoundaryError("UTC offset required")
    return moment.astimezone(timezone.utc)


def verify_mock_source_envelope(envelope, *, expected_property_id,
                                checked_at_utc, max_age_seconds=300):
    """Validate minimized snapshot and recency; NEVER authenticate a real PMS.

    A fresh synthetic capture does not verify its contents, occupancy, staff
    identity, authorization, payment or any external system. It only enforces
    consistency of the caller-supplied mock metadata and rule report.
    """
    if (not isinstance(envelope, dict) or set(envelope) != _KEYS
            or envelope.get("source") != _SOURCE
            or not isinstance(expected_property_id, str)
            or not isinstance(envelope.get("property_id"), str)
            or envelope["property_id"] != expected_property_id
            or not isinstance(envelope.get("revision"), str)
            or not _REVISION.fullmatch(envelope["revision"])
            or type(max_age_seconds) is not int
            or not 1 <= max_age_seconds <= 900):
        raise SourceBoundaryError("Invalid mock source scope or revision")
    captured = _utc(envelope["captured_at_utc"])
    checked = _utc(checked_at_utc)
    delta = (checked - captured).total_seconds()
    if delta < 0 or delta > max_age_seconds:
        raise SourceBoundaryError("Mock source snapshot is stale or future-dated")
    try:
        snapshot = validate(envelope["snapshot"])
    except (SnapshotError, TypeError, ValueError, RecursionError, OverflowError):
        raise SourceBoundaryError("Invalid minimized source snapshot") from None
    if snapshot["property_id"] != expected_property_id:
        raise SourceBoundaryError("Source property mismatch")
    report = evaluate(snapshot)
    if report["mode"] != "DRY_RUN_ONLY" or report["approval_policy"]["pms_writes"] is not False:
        raise SourceBoundaryError("No safe read-only evaluation boundary")
    return {
        "source_kind": _SOURCE,
        "source_validity": "FRESH_SYNTHETIC_ENVELOPE_NOT_LIVE_VERIFICATION",
        "captured_at_utc": captured.isoformat(),
        "revision": envelope["revision"],
        "max_age_seconds": max_age_seconds,
        "report": report,
        "policy": {
            "live_pms_connected": False,
            "pms_writes": False,
            "payments": False,
            "kbs": False,
            "guest_messages": False,
            "human_approval_required": True,
        },
    }
