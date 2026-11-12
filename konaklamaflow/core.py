"""Deterministic hotel operations recommendations. No PMS writes or guest PII.

Input: normalized, pseudonymized JSON; see docs/INPUT_SPEC.md.
Output: issues, optional suggested room choices, and daily work queue.
There is deliberately no function to book rooms, notify a guest, or update KBS.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import re
from typing import Any

REF_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
CURRENCIES = {"TRY", "EUR", "USD", "GBP"}
RESERVATION_STATUSES = {"confirmed", "pending", "cancelled"}
BED_TYPES = {"double", "twin", "flex"}
ALLOWED_INPUT_KEYS = {"rooms", "reservations", "property_id"}
ROOM_KEYS = {"id", "category", "beds", "active", "maintenance"}
RES_KEYS = {"ref", "source", "status", "checkin", "checkout", "category", "room_id", "twin_requested", "nightly_base", "total_base", "currency"}
MAINT_KEYS = {"start", "end"}


class InputError(ValueError):
    """A normalized, non-PII input is structurally invalid."""


def require_keys(obj: Any, allowed: set[str], context: str) -> dict[str, Any]:
    if not isinstance(obj, dict):
        raise InputError(f"{context}: expected an object")
    extra = set(obj) - allowed
    if extra:
        # Do not print unknown field values: they could be sensitive.
        raise InputError(f"{context}: unsupported field names")
    return obj


def identifier(value: Any, context: str) -> str:
    if not isinstance(value, str) or not REF_RE.fullmatch(value):
        raise InputError(f"{context}: expected pseudonymous alphanumeric ID (1-40 chars)")
    return value


def read_date(value: Any, context: str) -> date:
    if not isinstance(value, str):
        raise InputError(f"{context}: expected YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise InputError(f"{context}: expected YYYY-MM-DD") from None
    if parsed.isoformat() != value:
        raise InputError(f"{context}: expected YYYY-MM-DD")
    return parsed


def read_money(value: Any, context: str) -> Decimal:
    if not isinstance(value, str):
        raise InputError(f"{context}: use a string for money, not a float")
    if not re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,2})?", value):
        raise InputError(f"{context}: use up to 12 digits and at most two decimal places")
    try:
        amount = Decimal(value)
    except InvalidOperation:
        raise InputError(f"{context}: invalid monetary amount") from None
    if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
        raise InputError(f"{context}: must be finite, nonnegative, max two decimal places")
    return amount


def optional_bool(value: Any, default: bool, context: str) -> bool:
    if value is None:
        return default
    if type(value) is not bool:
        raise InputError(f"{context}: expected true or false")
    return value


@dataclass(frozen=True)
class Window:
    start: date
    end: date

    def overlaps(self, other: "Window") -> bool:
        """Checkout/end date is exclusive. Adjacent stays are not overlapping."""
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class Room:
    id: str
    category: str
    beds: str
    active: bool
    maintenance: tuple[Window, ...]

    def available(self, stay: Window) -> bool:
        return self.active and not any(block.overlaps(stay) for block in self.maintenance)


@dataclass(frozen=True)
class Reservation:
    ref: str
    source: str
    status: str
    stay: Window
    category: str
    room_id: str | None
    twin_requested: bool
    nightly_base: Decimal | None
    total_base: Decimal | None
    currency: str | None


def parse_input(data: Any) -> tuple[str, list[Room], list[Reservation]]:
    body = require_keys(data, ALLOWED_INPUT_KEYS, "input")
    property_id = identifier(body.get("property_id", "DEMO_PROPERTY"), "property_id")
    raw_rooms, raw_reservations = body.get("rooms"), body.get("reservations")
    if not isinstance(raw_rooms, list) or not isinstance(raw_reservations, list):
        raise InputError("rooms and reservations must be lists")
    if len(raw_rooms) > 10000 or len(raw_reservations) > 100000:
        raise InputError("input exceeds prototype capacity limit")
    rooms = []
    room_ids = set()
    for i, item in enumerate(raw_rooms, 1):
        x = require_keys(item, ROOM_KEYS, f"rooms[{i}]")
        rid = identifier(x.get("id"), f"rooms[{i}].id")
        if rid in room_ids:
            raise InputError("duplicate room id")
        room_ids.add(rid)
        category = identifier(x.get("category"), f"rooms[{i}].category")
        beds = x.get("beds", "double")
        if not isinstance(beds, str) or beds not in BED_TYPES:
            raise InputError(f"rooms[{i}].beds: supported: double, twin, flex")
        if "active" in x and x["active"] is None:
            raise InputError("active: expected true or false")
        active = optional_bool(x.get("active"), True, f"rooms[{i}].active")
        raw_maintenance = x.get("maintenance", [])
        if not isinstance(raw_maintenance, list):
            raise InputError(f"rooms[{i}].maintenance must be a list")
        windows = []
        for j, m in enumerate(raw_maintenance, 1):
            m = require_keys(m, MAINT_KEYS, f"rooms[{i}].maintenance[{j}]")
            w = Window(read_date(m.get("start"), "maintenance.start"), read_date(m.get("end"), "maintenance.end"))
            if w.start >= w.end:
                raise InputError("maintenance start must precede end")
            windows.append(w)
        rooms.append(Room(rid, category, beds, active, tuple(windows)))
    reservations = []
    for i, item in enumerate(raw_reservations, 1):
        x = require_keys(item, RES_KEYS, f"reservations[{i}]")
        ref = identifier(x.get("ref"), f"reservations[{i}].ref")
        source = identifier(x.get("source"), f"reservations[{i}].source")
        status = x.get("status", "confirmed")
        if not isinstance(status, str) or status not in RESERVATION_STATUSES:
            raise InputError(f"reservations[{i}].status: unsupported status")
        stay = Window(read_date(x.get("checkin"), "checkin"), read_date(x.get("checkout"), "checkout"))
        if stay.start >= stay.end:
            raise InputError(f"reservations[{i}]: checkout must be after checkin")
        category = identifier(x.get("category"), f"reservations[{i}].category")
        room_id = x.get("room_id")
        if room_id is not None:
            room_id = identifier(room_id, f"reservations[{i}].room_id")
        if "twin_requested" in x and x["twin_requested"] is None:
            raise InputError("twin_requested: expected true or false")
        twin_requested = optional_bool(x.get("twin_requested"), False, "twin_requested")
        nightly_base, total_base = x.get("nightly_base"), x.get("total_base")
        if (nightly_base is None) != (total_base is None):
            raise InputError(f"reservations[{i}]: nightly_base and total_base must be provided together")
        nightly = read_money(nightly_base, "nightly_base") if nightly_base is not None else None
        total = read_money(total_base, "total_base") if total_base is not None else None
        currency = x.get("currency")
        if nightly is not None and (not isinstance(currency, str) or currency not in CURRENCIES):
            raise InputError(f"reservations[{i}]: supported currency required with price")
        if nightly is None and currency is not None:
            raise InputError(f"reservations[{i}]: currency must accompany price")
        reservations.append(Reservation(ref, source, status, stay, category, room_id, twin_requested, nightly, total, currency))
    return property_id, rooms, reservations


def issue(code: str, severity: str, ref: str, detail: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "reservation_ref": ref, "detail": detail}


def review(data: Any, as_of: str) -> dict[str, Any]:
    today = read_date(as_of, "as_of")
    if today == date.max:
        raise InputError("as_of: must allow a next-day arrival date")
    property_id, rooms, reservations = parse_input(data)
    room_index = {r.id: r for r in rooms}
    categories = {r.category for r in rooms}
    alerts: list[dict[str, str]] = []
    proposals: list[dict[str, str]] = []
    seen: dict[tuple[str, str], Reservation] = {}
    assigned = {r.id: [] for r in rooms}

    def warn(code: str, severity: str, reservation: Reservation, detail: str) -> None:
        alert = issue(code, severity, reservation.ref, detail)
        alert["source"] = reservation.source
        alerts.append(alert)

    for res in reservations:
        key = (res.source, res.ref)
        if key in seen:
            warn("DUPLICATE_SOURCE_REF", "critical", res, "Same source and external reference appears more than once; resolve before applying any changes")
        else:
            seen[key] = res
        if res.category not in categories:
            warn("UNKNOWN_CATEGORY", "critical", res, "Requested room category does not exist in this property")
        if res.nightly_base is not None:
            nights = (res.stay.end - res.stay.start).days
            expected = res.nightly_base * nights
            if expected != res.total_base:
                warn("BASE_PRICE_MISMATCH", "review", res, f"Expected base-only total {expected:.2f} {res.currency}; verify taxes, discounts and nightly rates manually")
        if res.status == "cancelled":
            if res.room_id is not None:
                warn("CANCELLED_HOLD_REVIEW", "review", res, "Cancelled booking has a room assignment; verify manually in the source PMS")
            continue
        if res.room_id:
            room = room_index.get(res.room_id)
            if not room:
                warn("UNKNOWN_ROOM", "critical", res, "Assigned room does not exist")
                continue
            if room.category != res.category:
                warn("CATEGORY_MISMATCH", "critical", res, "Assigned room category differs from booked category; review authorized upgrade policy")
            if not room.available(res.stay):
                warn("ROOM_OUT_OF_SERVICE", "critical", res, "Assigned room is inactive or overlaps maintenance")
            if res.twin_requested and room.beds == "double":
                warn("TWIN_NOT_GUARANTEED", "review", res, "Twin bed request cannot be guaranteed in this room")
            if res.status in {"confirmed", "pending"}:
                assigned[room.id].append(res)
        elif res.status == "confirmed" and res.stay.start >= today:
            pass  # unassigned confirmed reservations considered for proposals below

    for room_id, held in assigned.items():
        held.sort(key=lambda r: (r.stay.start, r.source, r.ref))
        # A sweep flags every participant once, including nested/connected stays.
        # Pairwise warnings both missed the first guest and grew quadratically.
        conflicts: set[int] = set()
        longest = None
        for index, current in enumerate(held):
            if longest is not None and current.stay.start < held[longest].stay.end:
                conflicts.update((longest, index))
                if current.stay.end > held[longest].stay.end:
                    longest = index
            else:
                longest = index
        for index in sorted(conflicts):
            warn("ROOM_OVERLAP", "critical", held[index], "Assigned room overlaps another active booking or hold; manual resolution required")

    # Never propose a room for a duplicate source reference. Proposal is advisory only.
    ref_counts = Counter((r.source, r.ref) for r in reservations)
    duplicated = {k for k, n in ref_counts.items() if n > 1}
    planned: dict[str, list[Window]] = {r.id: [] for r in rooms}
    todo = sorted(
        (r for r in reservations if r.status == "confirmed" and r.room_id is None and r.stay.start >= today),
        key=lambda r: (r.stay.start, 0 if r.twin_requested else 1, r.source, r.ref),
    )
    for res in todo:
        if (res.source, res.ref) in duplicated or res.category not in categories:
            continue
        candidates = []
        for room in sorted(rooms, key=lambda r: r.id):
            if room.category != res.category or not room.available(res.stay):
                continue
            if any(existing.stay.overlaps(res.stay) for existing in assigned[room.id]):
                continue
            if any(win.overlaps(res.stay) for win in planned[room.id]):
                continue
            if res.twin_requested and room.beds == "double":
                continue
            candidates.append(room)
        if not candidates:
            warn("NO_SAFE_ROOM_PROPOSAL", "critical", res, "No free compatible room; do not confirm or promise a room")
            continue
        # Preserve scarce twin-capable rooms for constrained guests; heuristic, not global optimization.
        bed_order = ("twin", "flex", "double") if res.twin_requested else ("double", "flex", "twin")
        candidates.sort(key=lambda r: (bed_order.index(r.beds), r.id))
        chosen = candidates[0]
        planned[chosen.id].append(res.stay)
        proposals.append({"reservation_ref": res.ref, "source": res.source, "room_id": chosen.id, "kind": "MANUAL_APPROVAL_REQUIRED"})

    tomorrow = today + timedelta(days=1)
    tomorrow_arrivals = sorted(
        [{"reservation_ref": r.ref, "source": r.source, "category": r.category,
          "assigned_room": r.room_id, "status": r.status}
         for r in reservations if r.stay.start == tomorrow and r.status in {"confirmed", "pending"}],
        key=lambda x: (x["source"], x["reservation_ref"]),
    )
    count_critical = sum(i["severity"] == "critical" for i in alerts)
    return {
        "schema_version": "1.0", "project": "KonaklamaFlow", "mode": "DRY_RUN_ONLY",
        "property_id": property_id, "as_of": today.isoformat(),
        "summary": {"rooms": len(rooms), "reservations": len(reservations),
                    "critical_alerts": count_critical, "review_alerts": len(alerts) - count_critical,
                    "room_proposals": len(proposals), "tomorrow_arrivals": len(tomorrow_arrivals)},
        "issues": alerts, "room_proposals": proposals,
        "tomorrow_arrivals": tomorrow_arrivals,
        "disclaimer": "Advisory only. Human approval and checks in the actual PMS are required. No KBS or OTA updates are made.",
    }
