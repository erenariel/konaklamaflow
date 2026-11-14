"""Privacy-minimizing hotel front-desk readiness and action planning.

No PMS write operations, identity document handling, KBS submissions or payment calls.
The result is a decision-support checklist, never a completed check-in.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import date, time
from hashlib import sha256
import json
import re
from typing import Any

from .core import InputError, parse_input, review
from .report_contract import DISCLAIMER, validate_report

ID = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
ALLOWED_ROOT = {"property_id", "rooms", "reservations", "room_operations", "arrival_checks", "settings"}
ROOM_OP_KEYS = {"room_id", "housekeeping", "inspection", "maintenance_hold"}
ARRIVAL_KEYS = {"source", "ref", "arrival_state", "identity_status", "registration_status", "payment_review", "early_checkin_authorized"}
SETTINGS_KEYS = {"checkin_time", "checkout_time"}
HOUSEKEEPING = {"clean", "dirty", "inspecting", "out_of_service"}
INSPECTION = {"approved", "pending"}
ARRIVAL = {"expected", "arrived", "checked_in", "checked_out"}
IDENTITY = {"not_checked", "pending", "verified_by_authorized_staff"}
REGISTRATION = {"not_checked", "pending", "confirmed_by_authorized_system"}
PAYMENT = {"not_applicable", "cleared", "review"}


def _object(value: Any, allowed: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(f"{where}: must be an object")
    if set(value) - allowed:
        raise InputError(f"{where}: unsupported fields (never submit personal data)")
    return value


def _id(value: Any, where: str) -> str:
    if not isinstance(value, str) or ID.fullmatch(value) is None:
        raise InputError(f"{where}: pseudonymous identifier required")
    return value


def _enum(value: Any, choices: set[str], where: str) -> str:
    if not isinstance(value, str) or value not in choices:
        raise InputError(f"{where}: invalid status")
    return value


def _bool(value: Any, where: str) -> bool:
    if type(value) is not bool:
        raise InputError(f"{where}: true or false required")
    return value


def _clock(value: Any, where: str) -> time:
    if not isinstance(value, str) or re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", value) is None:
        raise InputError(f"{where}: use 24-hour HH:MM")
    return time.fromisoformat(value)


def _snapshot_hash(data: dict[str, Any]) -> str:
    canonical = json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def plan_operations(data: Any, as_of: str, at_time: str = "14:00") -> dict[str, Any]:
    """Generate deterministic, review-only tasks from a pseudonymized snapshot.

    status 'ready_for_review' does NOT mean a guest was checked in. A trusted
    backend must verify identities, payment, KBS and role-based approvals.
    """
    if not isinstance(data, dict):
        raise InputError("input: object required")
    _object(data, ALLOWED_ROOT, "input")
    now_time = _clock(at_time, "at_time")
    # Bound the offline prototype before invoking the reservation engine.
    for field, limit in (("rooms", 500), ("reservations", 5000), ("room_operations", 500), ("arrival_checks", 5000)):
        if not isinstance(data.get(field, []), list) or len(data.get(field, [])) > limit:
            raise InputError("Operational snapshot exceeds supported list limits")
    for room in data.get("rooms", []):
        if isinstance(room, dict) and isinstance(room.get("maintenance"), list) and len(room["maintenance"]) > 100:
            raise InputError("Too many maintenance windows")
    # Use one owned snapshot for validation, hashing and planning. The caller must
    # still capture a consistent source revision before calling this function.
    data = deepcopy(data)
    # Reuse the existing reservation engine for category, date and overlap validation.
    reservation_data = {k: v for k, v in data.items() if k in {"property_id", "rooms", "reservations"}}
    base_report = review(reservation_data, as_of)
    property_id, rooms, reservations = parse_input(reservation_data)
    by_room = {r.id: r for r in rooms}

    settings = _object(data.get("settings", {}), SETTINGS_KEYS, "settings")
    checkin_time = _clock(settings.get("checkin_time", "14:00"), "checkin_time")
    checkout_time = _clock(settings.get("checkout_time", "12:00"), "checkout_time")

    if not isinstance(data.get("room_operations", []), list):
        raise InputError("room_operations: list required")
    room_operations: dict[str, dict[str, Any]] = {}
    for number, item in enumerate(data.get("room_operations", []), 1):
        obj = _object(item, ROOM_OP_KEYS, f"room_operations[{number}]")
        if set(obj) != ROOM_OP_KEYS:
            raise InputError("room_operations: all room status signals are required")
        room_id = _id(obj.get("room_id"), "room_id")
        if room_id not in by_room or room_id in room_operations:
            raise InputError("room_operations: unknown or duplicated room ID")
        room_operations[room_id] = {
            "housekeeping": _enum(obj.get("housekeeping", "dirty"), HOUSEKEEPING, "housekeeping"),
            "inspection": _enum(obj.get("inspection", "pending"), INSPECTION, "inspection"),
            "maintenance_hold": _bool(obj.get("maintenance_hold", False), "maintenance_hold"),
        }
    if not isinstance(data.get("arrival_checks", []), list):
        raise InputError("arrival_checks: list required")
    arrival_checks: dict[tuple[str, str], dict[str, Any]] = {}
    for number, item in enumerate(data.get("arrival_checks", []), 1):
        obj = _object(item, ARRIVAL_KEYS, f"arrival_checks[{number}]")
        key = (_id(obj.get("source"), "source"), _id(obj.get("ref"), "ref"))
        if key in arrival_checks:
            raise InputError("arrival_checks: duplicated reservation key")
        arrival_checks[key] = {
            "arrival_state": _enum(obj.get("arrival_state", "expected"), ARRIVAL, "arrival_state"),
            "identity_status": _enum(obj.get("identity_status", "not_checked"), IDENTITY, "identity_status"),
            "registration_status": _enum(obj.get("registration_status", "not_checked"), REGISTRATION, "registration_status"),
            "payment_review": _enum(obj.get("payment_review", "review"), PAYMENT, "payment_review"),
            "early_checkin_authorized": _bool(obj.get("early_checkin_authorized", False), "early_checkin_authorized"),
        }
    keys = {(r.source, r.ref) for r in reservations}
    if set(arrival_checks) - keys:
        raise InputError("arrival_checks: unknown reservation reference")
    snapshot = _snapshot_hash(data)
    report_flags: dict[tuple[str, str], list[str]] = {}
    for issue in base_report["issues"]:
        # Review-level bed and price warnings also require reception attention.
        key = (issue["source"], issue["reservation_ref"])
        report_flags.setdefault(key, []).append(issue["code"])
    duplicated = Counter((r.source, r.ref) for r in reservations)
    # Cancellation is not evidence of physical departure when the same source
    # explicitly still reports a checked-in occupant. Keep that contradiction
    # visible for staff and prevent another arrival from appearing ready.
    active = [r for r in reservations if r.status in {"pending", "confirmed"}
              or arrival_checks.get((r.source, r.ref), {}).get("arrival_state") == "checked_in"]
    result: list[dict[str, Any]] = []
    asof_day = date.fromisoformat(as_of)
    unreleased_rooms = set()
    for previous in active:
        previous_state = arrival_checks.get((previous.source, previous.ref), {}).get("arrival_state", "expected")
        if previous.room_id and previous.status == "cancelled" and previous_state == "checked_in":
            unreleased_rooms.add(previous.room_id)
        if previous.room_id and previous.stay.start < asof_day and previous.stay.end <= asof_day and previous_state != "checked_out":
            if previous.stay.end == asof_day or previous_state == "checked_in":
                unreleased_rooms.add(previous.room_id)
    for occurrence, r in enumerate(sorted(active, key=lambda v: (v.stay.start, v.source, v.ref)), 1):
        key = (r.source, r.ref)
        status = arrival_checks.get(key, {
            "arrival_state": "expected", "identity_status": "not_checked",
            "registration_status": "not_checked", "payment_review": "review",
            "early_checkin_authorized": False,
        })
        if status["arrival_state"] == "checked_out":
            continue
        if r.stay.end <= asof_day and status["arrival_state"] != "checked_in":
            continue  # Completed historical stays do not clutter the arrival queue.
        reasons = []
        room_state = room_operations.get(r.room_id) if r.room_id else None
        if r.room_id is None:
            reasons.append("room_unassigned")
        elif not room_state:
            reasons.append("room_status_unverified")
        else:
            if room_state["housekeeping"] != "clean":
                reasons.append("room_not_clean")
            if room_state["inspection"] != "approved":
                reasons.append("room_not_inspected")
            if room_state["maintenance_hold"]:
                reasons.append("maintenance_hold")
        # Calendar adjacency is not proof that the previous occupant has left.
        # Even early arrival authorization cannot override an unverified departure.
        if r.room_id in unreleased_rooms:
            reasons.append("departure_not_verified")
        if duplicated[key] > 1:
            reasons.append("duplicate_reservation")
        reasons.extend(report_flags.get(key, []))
        if status["identity_status"] != "verified_by_authorized_staff":
            reasons.append("identity_needs_authorized_verification")
        if status["payment_review"] == "review":
            reasons.append("payment_review_needed")
        # PMS registration is a record in the authorized hotel system.
        # It does not file a KBS notification and does not complete check-in.
        if status["registration_status"] != "confirmed_by_authorized_system":
            reasons.append("pms_registration_not_confirmed")
        if r.status != "confirmed":
            reasons.append("reservation_not_confirmed")
        if r.stay.start != asof_day:
            reasons.append("arrival_date_not_today")
        if r.stay.start == asof_day and now_time < checkin_time and not status["early_checkin_authorized"]:
            reasons.append("before_checkin_time")
        if status["arrival_state"] == "expected":
            reasons.append("guest_not_arrived")
        if status["arrival_state"] == "checked_in":
            reasons.append("already_marked_checked_in")
        if r.stay.start < asof_day and status["arrival_state"] != "checked_in":
            reasons.append("past_arrival_needs_review")
        unique_reasons = list(dict.fromkeys(reasons))
        if status["arrival_state"] == "checked_in":
            state = "REVIEW_EXISTING_CHECKIN"
        elif unique_reasons:
            state = "BLOCKED_FOR_HUMAN_REVIEW"
        else:
            state = "READY_FOR_HUMAN_CHECKIN_REVIEW"
        task_id = sha256(f"{property_id}|{r.source}|{r.ref}|{occurrence}|{as_of}|{at_time}|{snapshot}|checkin-review".encode()).hexdigest()[:24]
        result.append({
            "task_id": task_id,
            "reservation_ref": r.ref, "source": r.source,
            "room_id": r.room_id, "category": r.category,
            "stay": {"checkin": r.stay.start.isoformat(), "checkout": r.stay.end.isoformat()},
            "state": state,
            "checklist": {
                "identity_reviewed_by_authorized_staff": status["identity_status"] == "verified_by_authorized_staff",
                "payment_review_complete": status["payment_review"] in {"cleared", "not_applicable"},
                "room_clean_and_inspected": bool(room_state and room_state["housekeeping"] == "clean" and room_state["inspection"] == "approved"),
                "registration_confirmed_by_authorized_system": status["registration_status"] == "confirmed_by_authorized_system",
            },
            "reasons": unique_reasons,
            "required_action": "MANUAL_APPROVAL_IN_AUTHORIZED_PMS_ONLY",
        })
    counts = Counter(item["state"] for item in result)
    report = {
        "schema_version": "0.2-prototype",
        "mode": "DRY_RUN_ONLY", "property_id": property_id,
        "as_of": as_of, "at_time": at_time,
        "snapshot_sha256": snapshot,
        "checkin_policy": {"checkin_time": checkin_time.strftime("%H:%M"), "checkout_time": checkout_time.strftime("%H:%M")},
        "summary": {"arrivals_total": len(result), "ready_for_review": counts["READY_FOR_HUMAN_CHECKIN_REVIEW"], "blocked": counts["BLOCKED_FOR_HUMAN_REVIEW"], "already_checked_in_requires_review": counts["REVIEW_EXISTING_CHECKIN"]},
        "tasks": result,
        "disclaimer": DISCLAIMER,
    }
    validate_report(report)
    return report
