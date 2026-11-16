"""Bounded, all-or-nothing room planning on fictional hotel snapshots.

Research-only companion to room_allocation_solver.propose_group. The legacy
API and the live demo are deliberately untouched. This module cannot book a
room, read personal data, or authorize hotel operations.
"""
from __future__ import annotations

from time import monotonic

from .room_allocation_solver import (
    SCHEMA, ROOM_CATEGORIES, ROOM_BEDS, ROOM_READINESS, OCCUPANCY,
    STAY_STATUSES, HOLD_STATUSES, BEDS_REQUEST, AllocationInputError,
    _record, _identifier, _enum, _positive, _window, _overlaps, _result, _reject,
)

MAX_GLOBAL_ROOMS = 200
MAX_GLOBAL_STAYS = 200
MAX_GLOBAL_HOLDS = 4_000
MAX_GLOBAL_STATES = 250_000
MAX_GLOBAL_SECONDS = 30.0
DEFAULT_STATES = 100_000
DEFAULT_SECONDS = 12.0


class _BudgetExceeded(Exception):
    def __init__(self, reason):
        self.reason = reason


def _report(status, reason, *, assignments=(), explored=0, rooms=0, stays=0,
            max_states=DEFAULT_STATES, max_seconds=DEFAULT_SECONDS):
    result = _result(status, reason, assignments, explored, rooms, stays, max_states)
    result["search"]["strategy"] = "BOUNDED_GLOBAL_BACKTRACKING_RESEARCH"
    result["search"]["max_seconds"] = max_seconds
    return result


def propose_global_room_plan(source, *, max_states=DEFAULT_STATES,
                             max_seconds=DEFAULT_SECONDS):
    """Return a complete advisory plan or no plan, never a partial assignment.

    Reuses the existing fictional allocation input contract. Search is
    deterministic until a work/time cap is reached. The time cap is a
    fail-closed safety valve, not a benchmark or an optimization guarantee.
    """
    if type(max_states) is not int or not (1 <= max_states <= MAX_GLOBAL_STATES):
        _reject()
    if type(max_seconds) not in (int, float) or not (0 < max_seconds <= MAX_GLOBAL_SECONDS):
        _reject()
    _record(source, {"schema_version", "source_kind", "rooms", "stays", "holds"})
    if source["schema_version"] != SCHEMA or source["source_kind"] != "fictional":
        _reject()
    rooms, stays, holds = source["rooms"], source["stays"], source["holds"]
    if any(type(rows) is not list for rows in (rooms, stays, holds)):
        _reject()
    if (len(rooms) > MAX_GLOBAL_ROOMS or len(stays) > MAX_GLOBAL_STAYS
            or len(holds) > MAX_GLOBAL_HOLDS):
        return _report("manual_review_required", "SEARCH_SCOPE_EXCEEDED",
                       rooms=min(len(rooms), MAX_GLOBAL_ROOMS),
                       stays=min(len(stays), MAX_GLOBAL_STAYS),
                       max_states=max_states, max_seconds=max_seconds)
    if not stays:
        return _report("manual_review_required", "NO_STAYS_REQUESTED",
                       rooms=len(rooms), max_states=max_states, max_seconds=max_seconds)

    room_index = {}
    maintenance = {}
    for room in rooms:
        _record(room, {"id", "category", "capacity", "bed", "readiness",
                       "occupancy", "maintenance"})
        rid = _identifier(room["id"])
        if rid in room_index:
            _reject()
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
        room_index[rid] = room
        maintenance[rid] = spans

    stay_index = {}
    windows = {}
    for stay in stays:
        _record(stay, {"id", "arrival", "departure", "category", "persons",
                       "bed_request", "status"})
        sid = _identifier(stay["id"])
        if sid in stay_index:
            _reject()
        _enum(stay["category"], ROOM_CATEGORIES)
        _positive(stay["persons"], 8)
        _enum(stay["bed_request"], BEDS_REQUEST)
        _enum(stay["status"], STAY_STATUSES)
        windows[sid] = _window(stay)
        stay_index[sid] = stay

    held = {rid: [] for rid in room_index}
    pending_release = {rid: [] for rid in room_index}
    seen_holds = set()
    for hold in holds:
        _record(hold, {"id", "room_id", "arrival", "departure",
                       "status", "release_confirmed"})
        hid, rid = _identifier(hold["id"]), _identifier(hold["room_id"])
        if hid in seen_holds or rid not in room_index:
            _reject()
        seen_holds.add(hid)
        status = _enum(hold["status"], HOLD_STATUSES)
        released = hold["release_confirmed"]
        if type(released) is not bool or (status == "active" and released):
            _reject()
        window = _window(hold)
        if not released:
            held[rid].append(window)
            if status != "active":
                pending_release[rid].append(window)

    if any(stay["status"] != "confirmed" for stay in stay_index.values()):
        return _report("manual_review_required", "STAY_STATUS_REQUIRES_REVIEW",
                       rooms=len(rooms), stays=len(stays),
                       max_states=max_states, max_seconds=max_seconds)

    candidates = {}
    uncertain = False
    unreleased = False
    for sid, stay in stay_index.items():
        feasible = []
        span = windows[sid]
        for rid, room in room_index.items():
            if (room["category"] != stay["category"] or
                    room["capacity"] < stay["persons"] or
                    (stay["bed_request"] != "none" and
                     stay["bed_request"] != room["bed"])):
                continue
            if any(_overlaps(span, m) for m in maintenance[rid]):
                continue
            if any(_overlaps(span, h) for h in pending_release[rid]):
                unreleased = True
            if room["readiness"] == "unknown" or room["occupancy"] == "unknown":
                uncertain = True
            if room["readiness"] != "inspected" or room["occupancy"] != "verified_vacant":
                continue
            if any(_overlaps(span, h) for h in held[rid]):
                continue
            feasible.append(rid)
        candidates[sid] = tuple(sorted(
            feasible,
            key=lambda rid: (
                stay["bed_request"] == "none" and room_index[rid]["bed"] == "twin",
                rid,
            ),
        ))

    # Strict bed requirements and smaller domains are considered first. The
    # same input set produces the same ordering independently of list order.
    order = sorted(stay_index, key=lambda sid: (
        len(candidates[sid]), stay_index[sid]["bed_request"] == "none",
        windows[sid][0], sid,
    ))
    assigned = {}
    by_room = {rid: [] for rid in room_index}
    explored = 0
    deadline = monotonic() + max_seconds

    def solve(i):
        nonlocal explored
        if monotonic() >= deadline:
            raise _BudgetExceeded("SEARCH_TIME_LIMIT_REACHED")
        if i == len(order):
            return True
        sid = order[i]
        for rid in candidates[sid]:
            if explored >= max_states:
                raise _BudgetExceeded("SEARCH_LIMIT_REACHED")
            explored += 1
            span = windows[sid]
            if any(_overlaps(span, other) for other in by_room[rid]):
                continue
            assigned[sid] = rid
            by_room[rid].append(span)
            if solve(i + 1):
                return True
            by_room[rid].pop()
            del assigned[sid]
        return False

    try:
        solved = solve(0)
    except _BudgetExceeded as error:
        return _report("manual_review_required", error.reason,
                       explored=explored, rooms=len(rooms), stays=len(stays),
                       max_states=max_states, max_seconds=max_seconds)

    if not solved:
        code = ("HELD_ROOM_RELEASE_NOT_VERIFIED" if unreleased else
                "ROOM_READINESS_UNVERIFIED" if uncertain else
                "NO_FEASIBLE_PROPOSAL")
        status = "manual_review_required" if uncertain or unreleased else "no_solution"
        return _report(status, code, explored=explored,
                       rooms=len(rooms), stays=len(stays),
                       max_states=max_states, max_seconds=max_seconds)

    proposals = [
        {"stay_id": sid, "room_id": assigned[sid],
         "reason_codes": ["EXACT_CATEGORY_AND_CAPACITY",
                          "HARD_BED_REQUEST_SATISFIED",
                          "NO_CONFLICT_WITH_DECLARED_HOLDS"],
         "human_approval_required": True}
        for sid in sorted(stay_index)
    ]
    return _report("proposed", "ALL_CONSTRAINTS_SATISFIED_IN_FICTIONAL_SNAPSHOT",
                   assignments=proposals, explored=explored,
                   rooms=len(rooms), stays=len(stays),
                   max_states=max_states, max_seconds=max_seconds)
