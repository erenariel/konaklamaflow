"""Bounded deterministic room proposals for FICTIONAL hotel snapshots only.

Independent research component: no PMS/OTA/KBS integration, no execution of
assignments, no personnel authorization, no changes to the existing rule engine.
"""
from __future__ import annotations

from datetime import date
import re

SCHEMA = "allocation-synthetic.v1"
RESULT_SCHEMA = "allocation-proposal.v1"
MAX_STAYS = 4
MAX_ROOMS = 18
MAX_HOLDS = 100
MAX_STATES = 20_000
ROOM_CATEGORIES = frozenset({"economy", "standard", "superior", "deluxe", "triple", "family"})
ROOM_BEDS = frozenset({"single", "double", "twin", "flex"})
ROOM_READINESS = frozenset({"inspected", "clean", "dirty", "in_progress", "out_of_order", "out_of_service", "unknown"})
OCCUPANCY = frozenset({"verified_vacant", "occupied", "unknown"})
STAY_STATUSES = frozenset({"confirmed", "pending", "cancelled", "no_show", "in_house", "checked_out"})
HOLD_STATUSES = frozenset({"active", "cancelled", "no_show", "checked_out"})
BEDS_REQUEST = frozenset({"none", "twin", "double", "single"})
IDENTIFIER = re.compile(r"^[A-Z][A-Z0-9_-]{0,31}$")
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SIDE_EFFECTS = {"pms_writes": False, "payments": False, "kbs": False,
                 "guest_messages": False, "room_changes": False}


class AllocationInputError(ValueError):
    """Unsafe, inconsistent or unsupported minimized synthetic input."""


class _SearchLimit(Exception):
    pass


def _reject():
    raise AllocationInputError("Invalid fictional allocation source")


def _record(value, keys, required=None):
    if type(value) is not dict or set(value) - keys or not (keys if required is None else required) <= set(value):
        _reject()
    return value


def _identifier(value):
    if type(value) is not str or IDENTIFIER.fullmatch(value) is None:
        _reject()
    return value


def _enum(value, values):
    if type(value) is not str or value not in values:
        _reject()
    return value


def _positive(value, upper):
    if type(value) is not int or not (1 <= value <= upper):
        _reject()
    return value


def _day(value):
    if type(value) is not str or DAY.fullmatch(value) is None:
        _reject()
    try:
        return date.fromisoformat(value)
    except ValueError:
        _reject()


def _window(row, start="arrival", end="departure"):
    begins, ends = _day(row[start]), _day(row[end])
    if begins >= ends:
        _reject()
    return begins, ends


def _overlaps(a, b):
    return a[0] < b[1] and b[0] < a[1]  # checkout day is excluded


def _result(status, reason, proposals=(), explored=0, rooms=0, stays=0, max_states=MAX_STATES):
    return {
        "schema_version": RESULT_SCHEMA,
        "mode": "DRY_RUN_ONLY",
        "human_approval_required": True,
        "side_effects": dict(_SIDE_EFFECTS),
        "source_validity": "UNVERIFIED_FICTIONAL_INPUT",
        "status": status,
        "reason_codes": [reason],
        "proposals": list(proposals),
        "search": {"states_explored": explored, "max_states": max_states,
                   "candidate_rooms": rooms, "requested_stays": stays},
    }


def propose_group(source, *, max_states=MAX_STATES):
    """Return advisory all-or-nothing matching, never a room assignment.

    Category is exact; requested bed is a hard constraint. Process the most
    constrained stay first and prefer non-twin rooms for flexible requests.
    Search is bounded, with no claim of globally optimal objective cost.
    """
    if type(max_states) is not int or not (1 <= max_states <= MAX_STATES):
        _reject()
    _record(source, {"schema_version", "source_kind", "rooms", "stays", "holds"})
    if source["schema_version"] != SCHEMA or source["source_kind"] != "fictional":
        _reject()
    rooms, stays, holds = source["rooms"], source["stays"], source["holds"]
    if any(type(items) is not list for items in (rooms, stays, holds)):
        _reject()
    if len(stays) > MAX_STAYS or len(rooms) > MAX_ROOMS or len(holds) > MAX_HOLDS:
        return _result("manual_review_required", "SEARCH_SCOPE_EXCEEDED",
                       rooms=min(len(rooms), MAX_ROOMS), stays=min(len(stays), MAX_STAYS), max_states=max_states)
    if not stays:
        return _result("manual_review_required", "NO_STAYS_REQUESTED",
                       rooms=len(rooms), stays=0, max_states=max_states)

    ids = set()
    indexed_rooms = {}
    maintenance = {}
    for room in rooms:
        _record(room, {"id", "category", "capacity", "bed", "readiness", "occupancy", "maintenance"})
        ident = _identifier(room["id"])
        if ident in ids:
            _reject()
        ids.add(ident)
        _enum(room["category"], ROOM_CATEGORIES)
        _positive(room["capacity"], 8)
        _enum(room["bed"], ROOM_BEDS)
        _enum(room["readiness"], ROOM_READINESS)
        _enum(room["occupancy"], OCCUPANCY)
        if type(room["maintenance"]) is not list or len(room["maintenance"]) > 12:
            _reject()
        spans = []
        for item in room["maintenance"]:
            _record(item, {"start", "end"})
            spans.append(_window(item, "start", "end"))
        indexed_rooms[ident] = room
        maintenance[ident] = spans

    stay_windows, indexed_stays = {}, {}
    for stay in stays:
        _record(stay, {"id", "arrival", "departure", "category", "persons", "bed_request", "status"})
        ident = _identifier(stay["id"])
        if ident in indexed_stays:
            _reject()
        _enum(stay["category"], ROOM_CATEGORIES)
        _positive(stay["persons"], 8)
        _enum(stay["bed_request"], BEDS_REQUEST)
        _enum(stay["status"], STAY_STATUSES)
        stay_windows[ident] = _window(stay)
        indexed_stays[ident] = stay

    held = {ident: [] for ident in indexed_rooms}
    unverified_releases = {ident: [] for ident in indexed_rooms}
    seen_holds = set()
    for hold in holds:
        _record(hold, {"id", "room_id", "arrival", "departure", "status", "release_confirmed"})
        ident = _identifier(hold["id"])
        room_id = _identifier(hold["room_id"])
        if ident in seen_holds or room_id not in indexed_rooms:
            _reject()
        seen_holds.add(ident)
        state = _enum(hold["status"], HOLD_STATUSES)
        released = hold["release_confirmed"]
        if type(released) is not bool or (state == "active" and released):
            _reject()
        span = _window(hold)
        if not released:
            held[room_id].append(span)
            if state != "active":
                unverified_releases[room_id].append(span)

    if any(stay["status"] != "confirmed" for stay in stays):
        return _result("manual_review_required", "STAY_STATUS_REQUIRES_REVIEW",
                       rooms=len(rooms), stays=len(stays), max_states=max_states)

    def basic_match(room, stay):
        return (room["category"] == stay["category"]
                and room["capacity"] >= stay["persons"]
                and (stay["bed_request"] == "none" or room["bed"] == stay["bed_request"]))

    candidates = {}
    uncertain = False
    unreleased = False
    for sid, stay in indexed_stays.items():
        viable = []
        window = stay_windows[sid]
        for rid, room in indexed_rooms.items():
            if not basic_match(room, stay):
                continue
            if any(_overlaps(window, span) for span in maintenance[rid]):
                continue
            if any(_overlaps(window, span) for span in unverified_releases[rid]):
                unreleased = True
            if room["occupancy"] == "unknown" or room["readiness"] == "unknown":
                uncertain = True
            # Only explicitly verified vacant + inspected is a proposal.
            if room["occupancy"] != "verified_vacant" or room["readiness"] != "inspected":
                continue
            if any(_overlaps(window, span) for span in held[rid]):
                continue
            viable.append(rid)
        candidates[sid] = sorted(viable, key=lambda rid: (stay["bed_request"] == "none"
                                                        and indexed_rooms[rid]["bed"] == "twin", rid))
    order = sorted(indexed_stays, key=lambda sid: (len(candidates[sid]),
                     indexed_stays[sid]["bed_request"] == "none", stay_windows[sid][0], sid))
    assignments = {}
    explored = 0

    def solve(i):
        nonlocal explored
        if i == len(order):
            return True
        sid = order[i]
        for rid in candidates[sid]:
            if any(other_rid == rid and _overlaps(stay_windows[sid], stay_windows[other_sid])
                   for other_sid, other_rid in assignments.items()):
                continue
            if explored >= max_states:
                raise _SearchLimit
            explored += 1
            assignments[sid] = rid
            if solve(i + 1):
                return True
            del assignments[sid]
        return False

    try:
        found = solve(0)
    except _SearchLimit:
        return _result("manual_review_required", "SEARCH_LIMIT_REACHED", explored=explored,
                       rooms=len(rooms), stays=len(stays), max_states=max_states)
    if not found:
        code = ("HELD_ROOM_RELEASE_NOT_VERIFIED" if unreleased
                else "ROOM_READINESS_UNVERIFIED" if uncertain
                else "NO_FEASIBLE_PROPOSAL")
        kind = "manual_review_required" if unreleased or uncertain else "no_solution"
        return _result(kind, code, explored=explored, rooms=len(rooms), stays=len(stays), max_states=max_states)
    proposals = [
        {"stay_id": sid, "room_id": assignments[sid],
         "reason_codes": ["EXACT_CATEGORY_AND_CAPACITY", "HARD_BED_REQUEST_SATISFIED",
                          "NO_CONFLICT_WITH_DECLARED_HOLDS"],
         "human_approval_required": True}
        for sid in sorted(indexed_stays)
    ]
    return _result("proposed", "ALL_CONSTRAINTS_SATISFIED_IN_FICTIONAL_SNAPSHOT",
                   proposals, explored=explored, rooms=len(rooms), stays=len(stays), max_states=max_states)
