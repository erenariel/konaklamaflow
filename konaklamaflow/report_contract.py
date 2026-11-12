"""Allowlisted, non-authorizing operations report contract.

Identifiers must already be pseudonymized at source. Syntax validation cannot
prove anonymity or authenticate an upstream identity/payment/status assertion.
"""
from __future__ import annotations

from collections import Counter
import re
from typing import Any

from .core import InputError, identifier, read_date

STATES = {"READY_FOR_HUMAN_CHECKIN_REVIEW", "BLOCKED_FOR_HUMAN_REVIEW", "REVIEW_EXISTING_CHECKIN"}
REASONS = {
    "room_unassigned", "room_status_unverified", "room_not_clean", "room_not_inspected",
    "maintenance_hold", "duplicate_reservation", "departure_not_verified",
    "identity_needs_authorized_verification", "payment_review_needed",
    "reservation_not_confirmed", "arrival_date_not_today", "before_checkin_time",
    "guest_not_arrived", "already_marked_checked_in", "past_arrival_needs_review",
    "DUPLICATE_SOURCE_REF", "UNKNOWN_CATEGORY", "BASE_PRICE_MISMATCH", "UNKNOWN_ROOM",
    "CATEGORY_MISMATCH", "ROOM_OUT_OF_SERVICE", "TWIN_NOT_GUARANTEED", "ROOM_OVERLAP",
    "NO_SAFE_ROOM_PROPOSAL", "CANCELLED_HOLD_REVIEW",
}
CHECKS = {"identity_reviewed_by_authorized_staff", "payment_review_complete",
          "room_clean_and_inspected", "registration_confirmed_by_authorized_system"}
SUMMARY = {"arrivals_total", "ready_for_review", "blocked", "already_checked_in_requires_review"}
DISCLAIMER = ("No check-in, payment, room assignment, guest notification or government registration has been executed. "
              "Identity and registration signals are unverified demo inputs unless provided by an authorized trusted system.")
ACTION = "MANUAL_APPROVAL_IN_AUTHORIZED_PMS_ONLY"


def _reject() -> None:
    raise InputError("Invalid operations report contract")


def _shape(value: Any, keys: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        _reject()


def _clock(value: Any) -> None:
    if not isinstance(value, str) or re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", value) is None:
        _reject()


def validate_report(report: Any) -> None:
    """Reject unknown fields, malformed tasks and inconsistent readiness/counts."""
    _shape(report, {"schema_version", "mode", "property_id", "as_of", "at_time", "snapshot_sha256",
                    "checkin_policy", "summary", "tasks", "disclaimer"})
    if report["schema_version"] != "0.2-prototype" or report["mode"] != "DRY_RUN_ONLY" or report["disclaimer"] != DISCLAIMER:
        _reject()
    identifier(report["property_id"], "property_id")
    read_date(report["as_of"], "as_of")
    if report["as_of"] == "9999-12-31":
        _reject()
    _clock(report["at_time"])
    if not isinstance(report["snapshot_sha256"], str) or re.fullmatch(r"[a-f0-9]{64}", report["snapshot_sha256"]) is None:
        _reject()
    _shape(report["checkin_policy"], {"checkin_time", "checkout_time"})
    for value in report["checkin_policy"].values():
        _clock(value)
    _shape(report["summary"], SUMMARY)
    if any(type(v) is not int or v < 0 for v in report["summary"].values()):
        _reject()
    if not isinstance(report["tasks"], list) or len(report["tasks"]) > 5000:
        _reject()
    seen = set()
    for task in report["tasks"]:
        _shape(task, {"task_id", "reservation_ref", "source", "room_id", "category", "stay", "state", "checklist", "reasons", "required_action"})
        task_id = task["task_id"]
        if not isinstance(task_id, str) or re.fullmatch(r"[a-f0-9]{24}", task_id) is None or task_id in seen:
            _reject()
        seen.add(task_id)
        for key in ("reservation_ref", "source", "category"):
            identifier(task[key], key)
        if task["room_id"] is not None:
            identifier(task["room_id"], "room_id")
        _shape(task["stay"], {"checkin", "checkout"})
        start = read_date(task["stay"]["checkin"], "checkin")
        end = read_date(task["stay"]["checkout"], "checkout")
        if start >= end:
            _reject()
        if not isinstance(task["state"], str) or task["state"] not in STATES or task["required_action"] != ACTION:
            _reject()
        _shape(task["checklist"], CHECKS)
        if any(type(v) is not bool for v in task["checklist"].values()):
            _reject()
        reasons = task["reasons"]
        if not isinstance(reasons, list) or any(not isinstance(v, str) or v not in REASONS for v in reasons) or len(set(reasons)) != len(reasons):
            _reject()
        ready = task["state"] == "READY_FOR_HUMAN_CHECKIN_REVIEW"
        if ready:
            if reasons or task["room_id"] is None or task["stay"]["checkin"] != report["as_of"]:
                _reject()
            if not all(task["checklist"][k] for k in CHECKS - {"registration_confirmed_by_authorized_system"}):
                _reject()
        elif not reasons:
            _reject()
        if (task["state"] == "REVIEW_EXISTING_CHECKIN") != ("already_marked_checked_in" in reasons):
            _reject()
    counts = Counter(task["state"] for task in report["tasks"])
    if report["summary"] != {
        "arrivals_total": len(report["tasks"]),
        "ready_for_review": counts["READY_FOR_HUMAN_CHECKIN_REVIEW"],
        "blocked": counts["BLOCKED_FOR_HUMAN_REVIEW"],
        "already_checked_in_requires_review": counts["REVIEW_EXISTING_CHECKIN"],
    }:
        _reject()
