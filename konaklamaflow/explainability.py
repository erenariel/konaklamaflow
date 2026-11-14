"""Deterministic, non-authorizing evidence map for v0.3 review results.

This module does not decide readiness, infer identity, verify payment, read
live PMS records, call an AI provider or write to external services. All
evidence paths are constant allowlisted *field names*, never guest values.
"""
from __future__ import annotations

from hashlib import sha256
import json

from .experience_engine import BLOCKER_CODES, SnapshotError, evaluate

EXPLANATION_SCHEMA = "konaklamaflow.explanations.v1"
POLICY_BOUNDARY = "MANUAL_REVALIDATION_AND_APPROVAL_IN_AUTHORIZED_PMS_ONLY"

# Field paths identify model input *signals*; they are NOT proof of live state.
EVIDENCE = {
    "CANCELLED_ASSIGNED": ("reservations[].status", "reservations[].room_id"),
    "NOT_CONFIRMED": ("reservations[].status",),
    "UNMAPPED_PMS": ("reservations[].pms_ref", "channel_events[].status"),
    "DUPLICATE_CHANNEL_REF": ("reservations[].channel", "reservations[].external_ref"),
    "DUPLICATE_PMS_REF": ("reservations[].pms_ref",),
    "NO_ASSIGNED_ROOM": ("reservations[].room_id",),
    "ROOM_INCOMPATIBLE": ("rooms[].category", "rooms[].capacity", "rooms[].bed",
                          "rooms[].amenities", "rooms[].maintenance", "reservations[].requests"),
    "HOUSEKEEPING_NOT_INSPECTED": ("rooms[].housekeeping", "tasks[].status"),
    "ROOM_CONFLICT": ("reservations[].room_id", "reservations[].arrival",
                      "reservations[].departure"),
    "IDENTITY_STAFF_REVIEW": ("reservations[].identity_signal",),
    "PAYMENT_REVIEW": ("reservations[].payment_signal",),
    "ARRIVAL_NOT_TODAY": ("reservations[].arrival", "as_of"),
    "GUEST_NOT_ARRIVED": ("reservations[].arrival_state",),
    "BEFORE_CHECKIN_TIME": ("as_of", "at_time", "reservations[].arrival"),
    "DEPARTURE_NOT_VERIFIED": ("reservations[].arrival_state", "reservations[].departure"),
    "ALREADY_IN_HOUSE": ("reservations[].status", "reservations[].arrival_state"),
    "SPECIAL_REQUEST_REVIEW": ("reservations[].requests",),
    "REQUEST_AMENITY_UNAVAILABLE": ("reservations[].requests", "rooms[].amenities"),
    "CONFLICTING_BED_REQUEST": ("reservations[].bed_request", "reservations[].requests"),
    "MAINTENANCE_TASK_OPEN": ("tasks[].kind", "tasks[].status", "tasks[].room_id"),
    "HOUSEKEEPING_TASK_OPEN": ("tasks[].kind", "tasks[].status", "tasks[].room_id"),
    "CHANNEL_EVENT_REVIEW": ("channel_events[].status", "channel_events[].reservation_id"),
    "CHANNEL_REFERENCE_MISMATCH": ("channel_events[].channel", "channel_events[].external_ref",
                                   "channel_events[].reservation_id"),
    "CHANNEL_STATUS_CONFLICT": ("channel_events[].status", "reservations[].status"),
    "CORE_REVIEW_REQUIRED": ("engine_report.tasks[].reasons",),
    "HISTORICAL_STAY": ("reservations[].arrival", "as_of"),
    "NO_SHOW_RELEASE_REVIEW": ("reservations[].status", "reservations[].room_id"),
    "PMS_REGISTRATION_NOT_CONFIRMED": ("reservations[].pms_registration",),
}
# Unknown reason codes must never be silently explained as an authoritative fact.
UNMAPPED_CODES = BLOCKER_CODES - set(EVIDENCE)
if UNMAPPED_CODES:
    raise RuntimeError("Missing non-authorizing evidence mapping")

REASON_ACTIONS = {
    "CANCELLED_ASSIGNED": "review_cancelled_room_hold",
    "NOT_CONFIRMED": "verify_reservation_with_staff",
    "UNMAPPED_PMS": "verify_pms_link_in_source_system",
    "DUPLICATE_CHANNEL_REF": "compare_source_reservations",
    "DUPLICATE_PMS_REF": "review_duplicate_pms_mapping",
    "NO_ASSIGNED_ROOM": "review_room_plan_and_inventory",
    "ROOM_INCOMPATIBLE": "review_room_attributes_and_stay",
    "HOUSEKEEPING_NOT_INSPECTED": "request_authorized_housekeeping_check",
    "ROOM_CONFLICT": "resolve_overlapping_room_holds",
    "IDENTITY_STAFF_REVIEW": "request_authorized_identity_check",
    "PAYMENT_REVIEW": "request_authorized_finance_review",
    "ARRIVAL_NOT_TODAY": "confirm_arrival_date_and_policy",
    "GUEST_NOT_ARRIVED": "verify_arrival_with_reception",
    "BEFORE_CHECKIN_TIME": "review_checkin_time_policy",
    "DEPARTURE_NOT_VERIFIED": "verify_guest_departure_and_room_release",
    "ALREADY_IN_HOUSE": "review_existing_occupancy",
    "SPECIAL_REQUEST_REVIEW": "review_special_request_with_staff",
    "REQUEST_AMENITY_UNAVAILABLE": "review_required_room_amenities",
    "CONFLICTING_BED_REQUEST": "resolve_bed_request_conflict",
    "MAINTENANCE_TASK_OPEN": "request_maintenance_clearance",
    "HOUSEKEEPING_TASK_OPEN": "request_housekeeping_clearance",
    "CHANNEL_EVENT_REVIEW": "review_unresolved_channel_event",
    "CHANNEL_REFERENCE_MISMATCH": "manually_match_source_event",
    "CHANNEL_STATUS_CONFLICT": "reconcile_channel_status_with_staff",
    "CORE_REVIEW_REQUIRED": "inspect_core_engine_diagnostics",
    "HISTORICAL_STAY": "review_historical_arrival",
    "NO_SHOW_RELEASE_REVIEW": "hold_no_show_room_until_staff_releases_it",
    "PMS_REGISTRATION_NOT_CONFIRMED": "review_pms_registration_separately_from_kbs",
}
if set(REASON_ACTIONS) != set(EVIDENCE):
    raise RuntimeError("Explanation action coverage mismatch")


class ExplanationError(ValueError):
    """An input could not be proven to match the authoritative rule engine."""


def _digest(value):
    return sha256(json.dumps(value, ensure_ascii=True, sort_keys=True,
                             allow_nan=False, separators=(",", ":")).encode()).hexdigest()


def _guarded_report(snapshot, report):
    """Reject stale, tampered, or caller-produced reports without echoing data."""
    try:
        current = evaluate(snapshot)
    except (SnapshotError, TypeError, ValueError, RecursionError, OverflowError):
        raise ExplanationError("Invalid minimized snapshot or report") from None
    if not isinstance(report, dict) or current != report:
        raise ExplanationError("Report is stale, mismatched or untrusted")
    if (current.get("mode") != "DRY_RUN_ONLY"
            or current.get("approval_policy", {}).get("human_approval_required") is not True
            or current.get("approval_policy", {}).get("pms_writes") is not False
            or current.get("approval_policy", {}).get("payments") is not False
            or current.get("approval_policy", {}).get("kbs") is not False):
        raise ExplanationError("Report has no safe approval boundary")
    return current


def build_explanations(snapshot, report):
    """Provide evidence *keys*, never values; staff-only review is enforced.

    Not an authorization, source validation, payment result, identity verification,
    real-time room guarantee, audit trail, or any form of automatic approval.
    """
    current = _guarded_report(snapshot, report)
    rows = []
    for row in current["arrivals"]:
        blockers = row["blockers"]
        if len(blockers) != len(set(blockers)) or set(blockers) - BLOCKER_CODES:
            raise ExplanationError("Unrecognized blocking reasons")
        state = row["status"]
        if ((state == "review_ready" and blockers)
                or (state == "blocked" and not blockers)
                or state not in {"blocked", "review_ready", "other"}
                or row.get("human_approval_required") is not True):
            raise ExplanationError("Inconsistent review state")
        reasons = [{
            "reason_code": code,
            "message_key": "reason." + code.lower(),
            "evidence_field_paths": list(EVIDENCE[code]),
            "source_validity": "UNVERIFIED_MINIMIZED_SNAPSHOT",
            "next_safe_staff_action_key": "staff." + REASON_ACTIONS[code],
            "human_approval_required": True,
        } for code in blockers]
        rows.append({
            "task_id": row["task_id"],
            "state": state,
            "ready_means": "PRE_REVIEW_ONLY_NOT_CHECKIN",
            "reasons": reasons,
            "human_approval_boundary": POLICY_BOUNDARY,
        })
    events = []
    for item in current["event_reviews"]:
        codes = item["reason_codes"]
        if set(codes) - BLOCKER_CODES:
            raise ExplanationError("Unrecognized channel reasons")
        events.append({
            "reason_codes": list(codes),
            "source_validity": "UNVERIFIED_MINIMIZED_SNAPSHOT",
            "message_keys": ["reason." + c.lower() for c in codes],
            "human_approval_boundary": POLICY_BOUNDARY,
        })
    return {
        "schema": EXPLANATION_SCHEMA,
        "mode": "NO_EXECUTION_READ_ONLY",
        "snapshot_sha256": current["snapshot_sha256"],
        "report_sha256": _digest(current),
        "source_validity": "UNVERIFIED_MINIMIZED_SNAPSHOT",
        "source_captured_at": None,  # the source schema has no trusted capture proof
        "source_revision": None,
        "authoritative_decision": "PYTHON_RULE_ENGINE_ONLY",
        "human_approval_boundary": POLICY_BOUNDARY,
        "arrivals": rows,
        "event_reviews": events,
    }
