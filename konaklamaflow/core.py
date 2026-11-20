"""Deterministic hotel operations recommendations. No PMS writes or guest PII.

Input: normalized, pseudonymized JSON; see docs/INPUT_SPEC.md.
Output: issues, optional suggested room choices, and daily work queue.
There is deliberately no function to book rooms, notify a guest, or update KBS.

Input schema 1.0 files remain valid. Every field added in schema 1.1
(stay statuses, guest counts, board, blocks/allotments, room-move segments,
arrival/departure times and a property policy) is optional.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import re
from typing import Any

REF_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
CLOCK_RE = re.compile(r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")
# ISO 4217 codes with at most two minor units. Three-decimal currencies
# (KWD, BHD, ...) are excluded because money strings keep two decimals.
CURRENCIES = {
    "TRY", "EUR", "USD", "GBP", "RUB", "CHF", "AED", "SAR", "QAR", "AZN",
    "GEL", "KZT", "UAH", "PLN", "CZK", "HUF", "RON", "SEK", "NOK", "DKK",
    "ILS", "JPY", "CNY", "KRW", "INR", "AUD", "CAD",
}
RESERVATION_STATUSES = {"confirmed", "pending", "cancelled", "checked_in", "checked_out", "no_show"}
BED_TYPES = {"double", "twin", "flex"}
BOARD_TYPES = {"RO", "BB", "HB", "FB", "AI", "UAI"}
BLOCK_KINDS = {"allotment", "group"}
ALLOWED_INPUT_KEYS = {"rooms", "reservations", "property_id", "blocks", "policy"}
ROOM_KEYS = {"id", "category", "beds", "active", "maintenance", "max_occupancy", "max_adults"}
RES_KEYS = {
    "ref", "source", "status", "checkin", "checkout", "category", "room_id", "twin_requested",
    "nightly_base", "total_base", "currency",
    # schema 1.1 (all optional)
    "nightly_rates", "discount_base", "adults", "children", "board", "guest_key",
    "block_id", "segments", "arrival_time", "departure_time",
}
MAINT_KEYS = {"start", "end"}
SEGMENT_KEYS = {"room_id", "start", "end"}
BLOCK_KEYS = {"id", "kind", "source", "category", "start", "end", "rooms", "release_days", "cutoff"}
POLICY_KEYS = {"checkin_time", "checkout_time", "turnover_minutes", "horizon_nights"}

MAX_BLOCKS = 500
MAX_SEGMENTS = 10
MAX_GUESTS = 20
MAX_RATE_NIGHTS = 366
# Category/night accounting (capacity reserves, availability, blocks) covers
# this many nights from the review date. Room-level overlap checks stay exact.
ACCOUNTING_NIGHTS = 400

# Statuses that keep a recorded room physically held.
HOLD_STATUSES = {"confirmed", "pending", "checked_in", "no_show"}
# Statuses that represent a sold stay that must have a room.
COMMITTED_STATUSES = {"confirmed", "checked_in"}
BREAKFAST_BOARDS = {"BB", "HB", "FB", "AI", "UAI"}
LUNCH_BOARDS = {"FB", "AI", "UAI"}
DINNER_BOARDS = {"HB", "FB", "AI", "UAI"}


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


def read_count(value: Any, context: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise InputError(f"{context}: expected a whole number from {low} to {high}")
    return value


def read_clock(value: Any, context: str) -> str:
    if not isinstance(value, str) or not CLOCK_RE.fullmatch(value):
        raise InputError(f"{context}: expected HH:MM (24-hour clock)")
    return value


def _minutes(clock: str) -> int:
    return int(clock[:2]) * 60 + int(clock[3:])


def _shift(day: date, days: int) -> date:
    """Date arithmetic that clamps instead of raising near year 1 or 9999."""
    try:
        return day + timedelta(days=days)
    except OverflowError:
        return date.max if days > 0 else date.min


@dataclass(frozen=True)
class Window:
    start: date
    end: date

    def overlaps(self, other: "Window") -> bool:
        """Checkout/end date is exclusive. Adjacent stays are not overlapping."""
        return self.start < other.end and other.start < self.end

    def covers(self, night: date) -> bool:
        return self.start <= night < self.end


@dataclass(frozen=True)
class Room:
    id: str
    category: str
    beds: str
    active: bool
    maintenance: tuple[Window, ...]
    max_occupancy: int | None = None
    max_adults: int | None = None

    def available(self, stay: Window) -> bool:
        return self.active and not any(block.overlaps(stay) for block in self.maintenance)

    def fits(self, adults: int | None, children: int | None) -> bool:
        """Unknown guest counts or unknown room capacity are never rejected."""
        if adults is None:
            return True
        if self.max_occupancy is not None and adults + (children or 0) > self.max_occupancy:
            return False
        return self.max_adults is None or adults <= self.max_adults


@dataclass(frozen=True)
class Segment:
    """One part of a stay with a planned room move."""
    room_id: str
    stay: Window


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
    nightly_rates: tuple[Decimal, ...] | None = None
    discount_base: Decimal | None = None
    adults: int | None = None
    children: int | None = None
    board: str | None = None
    guest_key: str | None = None
    block_id: str | None = None
    segments: tuple[Segment, ...] = ()
    arrival_time: str | None = None
    departure_time: str | None = None

    @property
    def has_room(self) -> bool:
        return self.room_id is not None or bool(self.segments)

    def first_room(self) -> str | None:
        return self.segments[0].room_id if self.segments else self.room_id

    def last_room(self) -> str | None:
        return self.segments[-1].room_id if self.segments else self.room_id


@dataclass(frozen=True)
class Block:
    """Allotment or group block: rooms held per night until release."""
    id: str
    kind: str
    source: str
    category: str
    stay: Window
    rooms: int
    release_days: int
    cutoff: date | None

    def release_date(self, night: date) -> date:
        return self.cutoff if self.cutoff is not None else _shift(night, -self.release_days)


@dataclass(frozen=True)
class Policy:
    checkin_time: str = "14:00"
    checkout_time: str = "12:00"
    turnover_minutes: int = 60
    horizon_nights: int = 14


@dataclass(frozen=True)
class Snapshot:
    property_id: str
    rooms: list[Room]
    reservations: list[Reservation]
    blocks: list[Block]
    policy: Policy


def _parse_rooms(raw_rooms: list[Any]) -> list[Room]:
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
        max_occupancy = max_adults = None
        if x.get("max_occupancy") is not None:
            max_occupancy = read_count(x["max_occupancy"], f"rooms[{i}].max_occupancy", 1, MAX_GUESTS)
        if x.get("max_adults") is not None:
            max_adults = read_count(x["max_adults"], f"rooms[{i}].max_adults", 1, MAX_GUESTS)
        if max_occupancy is not None and max_adults is not None and max_adults > max_occupancy:
            raise InputError(f"rooms[{i}]: max_adults cannot exceed max_occupancy")
        rooms.append(Room(rid, category, beds, active, tuple(windows), max_occupancy, max_adults))
    return rooms


def _parse_segments(raw: Any, stay: Window, context: str) -> tuple[Segment, ...]:
    if not isinstance(raw, list) or not 2 <= len(raw) <= MAX_SEGMENTS:
        raise InputError(f"{context}.segments: expected 2-{MAX_SEGMENTS} room-move segments")
    segments = []
    for j, item in enumerate(raw, 1):
        s = require_keys(item, SEGMENT_KEYS, f"{context}.segments[{j}]")
        window = Window(read_date(s.get("start"), "segments.start"), read_date(s.get("end"), "segments.end"))
        if window.start >= window.end:
            raise InputError(f"{context}.segments: each segment needs start before end")
        segments.append(Segment(identifier(s.get("room_id"), f"{context}.segments[{j}].room_id"), window))
    if segments[0].stay.start != stay.start or segments[-1].stay.end != stay.end:
        raise InputError(f"{context}.segments: segments must cover checkin to checkout exactly")
    for left, right in zip(segments, segments[1:]):
        if left.stay.end != right.stay.start:
            raise InputError(f"{context}.segments: segments must be contiguous")
        if left.room_id == right.room_id:
            raise InputError(f"{context}.segments: consecutive segments need different rooms")
    return tuple(segments)


def _parse_reservations(raw_reservations: list[Any]) -> list[Reservation]:
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
        raw_rates = x.get("nightly_rates")
        if nightly_base is not None and raw_rates is not None:
            raise InputError(f"reservations[{i}]: use nightly_base or nightly_rates, not both")
        price_given = nightly_base is not None or raw_rates is not None
        if price_given != (total_base is not None):
            raise InputError(f"reservations[{i}]: nightly_base and total_base must be provided together")
        nightly = read_money(nightly_base, "nightly_base") if nightly_base is not None else None
        rates = None
        nights = (stay.end - stay.start).days
        if raw_rates is not None:
            if not isinstance(raw_rates, list) or not 1 <= len(raw_rates) <= MAX_RATE_NIGHTS:
                raise InputError(f"reservations[{i}].nightly_rates: expected one amount per night")
            rates = tuple(read_money(value, "nightly_rates") for value in raw_rates)
            if len(rates) != nights:
                raise InputError(f"reservations[{i}].nightly_rates: expected one amount per night")
        total = read_money(total_base, "total_base") if total_base is not None else None
        currency = x.get("currency")
        if price_given and (not isinstance(currency, str) or currency not in CURRENCIES):
            raise InputError(f"reservations[{i}]: supported currency required with price")
        if not price_given and currency is not None:
            raise InputError(f"reservations[{i}]: currency must accompany price")
        discount = None
        if x.get("discount_base") is not None:
            if not price_given:
                raise InputError(f"reservations[{i}]: discount_base needs a nightly price and total_base")
            discount = read_money(x["discount_base"], "discount_base")
            gross = sum(rates, Decimal("0")) if rates is not None else nightly * nights
            if discount > gross:
                raise InputError(f"reservations[{i}]: discount_base exceeds the base accommodation amount")
        adults = children = None
        if x.get("adults") is not None:
            adults = read_count(x["adults"], f"reservations[{i}].adults", 0, MAX_GUESTS)
        if x.get("children") is not None:
            children = read_count(x["children"], f"reservations[{i}].children", 0, MAX_GUESTS)
        if adults is not None and adults + (children or 0) == 0:
            raise InputError(f"reservations[{i}]: at least one guest is required")
        if adults is not None and adults + (children or 0) > MAX_GUESTS:
            raise InputError(f"reservations[{i}]: guest count exceeds prototype limit")
        board = x.get("board")
        if board is not None and (not isinstance(board, str) or board not in BOARD_TYPES):
            raise InputError(f"reservations[{i}].board: supported: RO, BB, HB, FB, AI, UAI")
        guest_key = identifier(x["guest_key"], f"reservations[{i}].guest_key") if x.get("guest_key") is not None else None
        block_id = identifier(x["block_id"], f"reservations[{i}].block_id") if x.get("block_id") is not None else None
        segments: tuple[Segment, ...] = ()
        if x.get("segments") is not None:
            if room_id is not None:
                raise InputError(f"reservations[{i}]: use room_id or segments, not both")
            segments = _parse_segments(x["segments"], stay, f"reservations[{i}]")
        arrival_time = read_clock(x["arrival_time"], "arrival_time") if x.get("arrival_time") is not None else None
        departure_time = read_clock(x["departure_time"], "departure_time") if x.get("departure_time") is not None else None
        reservations.append(Reservation(
            ref, source, status, stay, category, room_id, twin_requested, nightly, total, currency,
            rates, discount, adults, children, board, guest_key, block_id, segments,
            arrival_time, departure_time,
        ))
    return reservations


def _parse_blocks(raw: Any, categories: set[str]) -> list[Block]:
    if raw is None:
        return []
    if not isinstance(raw, list) or len(raw) > MAX_BLOCKS:
        raise InputError("blocks: expected a list within the prototype limit")
    blocks, ids = [], set()
    for i, item in enumerate(raw, 1):
        x = require_keys(item, BLOCK_KEYS, f"blocks[{i}]")
        block_id = identifier(x.get("id"), f"blocks[{i}].id")
        if block_id in ids:
            raise InputError("duplicate block id")
        ids.add(block_id)
        kind = x.get("kind", "allotment")
        if not isinstance(kind, str) or kind not in BLOCK_KINDS:
            raise InputError(f"blocks[{i}].kind: supported: allotment, group")
        source = identifier(x.get("source"), f"blocks[{i}].source")
        category = identifier(x.get("category"), f"blocks[{i}].category")
        if category not in categories:
            raise InputError(f"blocks[{i}].category: no room of this category exists")
        stay = Window(read_date(x.get("start"), "blocks.start"), read_date(x.get("end"), "blocks.end"))
        if stay.start >= stay.end:
            raise InputError(f"blocks[{i}]: start must precede end")
        rooms = read_count(x.get("rooms"), f"blocks[{i}].rooms", 1, 500)
        if x.get("release_days") is not None and x.get("cutoff") is not None:
            raise InputError(f"blocks[{i}]: use release_days or cutoff, not both")
        release_days = 0
        if x.get("release_days") is not None:
            release_days = read_count(x["release_days"], f"blocks[{i}].release_days", 0, 365)
        cutoff = read_date(x["cutoff"], "blocks.cutoff") if x.get("cutoff") is not None else None
        blocks.append(Block(block_id, kind, source, category, stay, rooms, release_days, cutoff))
    return blocks


def _parse_policy(raw: Any) -> Policy:
    if raw is None:
        return Policy()
    x = require_keys(raw, POLICY_KEYS, "policy")
    defaults = Policy()
    return Policy(
        read_clock(x.get("checkin_time", defaults.checkin_time), "policy.checkin_time"),
        read_clock(x.get("checkout_time", defaults.checkout_time), "policy.checkout_time"),
        read_count(x.get("turnover_minutes", defaults.turnover_minutes), "policy.turnover_minutes", 0, 720),
        read_count(x.get("horizon_nights", defaults.horizon_nights), "policy.horizon_nights", 1, 60),
    )


def parse_snapshot(data: Any) -> Snapshot:
    body = require_keys(data, ALLOWED_INPUT_KEYS, "input")
    property_id = identifier(body.get("property_id", "DEMO_PROPERTY"), "property_id")
    raw_rooms, raw_reservations = body.get("rooms"), body.get("reservations")
    if not isinstance(raw_rooms, list) or not isinstance(raw_reservations, list):
        raise InputError("rooms and reservations must be lists")
    from .io_safety import MAX_RESERVATIONS, MAX_ROOMS
    if len(raw_rooms) > MAX_ROOMS or len(raw_reservations) > MAX_RESERVATIONS:
        raise InputError("input exceeds prototype capacity limit")
    rooms = _parse_rooms(raw_rooms)
    reservations = _parse_reservations(raw_reservations)
    blocks = _parse_blocks(body.get("blocks"), {room.category for room in rooms})
    return Snapshot(property_id, rooms, reservations, blocks, _parse_policy(body.get("policy")))


def parse_input(data: Any) -> tuple[str, list[Room], list[Reservation]]:
    """Backward-compatible parser used by the operations and suite engines."""
    snapshot = parse_snapshot(data)
    return snapshot.property_id, snapshot.rooms, snapshot.reservations


def issue(code: str, severity: str, ref: str, detail: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "reservation_ref": ref, "detail": detail}


def _occupancy(res: Reservation, today: date) -> list[tuple[str | None, Window]]:
    """Room windows a stay occupies. A guest still checked in after checkout
    keeps the room through tonight, so it cannot be offered to an arrival."""
    end = res.stay.end
    if res.status == "checked_in" and end < today:
        end = _shift(today, 1)
    if res.segments:
        parts = [(s.room_id, s.stay) for s in res.segments]
        last_room, last = parts[-1]
        parts[-1] = (last_room, Window(last.start, max(last.end, end)))
        return parts
    return [(res.room_id, Window(res.stay.start, end))]


def _effective_stay(res: Reservation, today: date) -> Window:
    if res.status == "checked_in" and res.stay.end < today:
        return Window(res.stay.start, _shift(today, 1))
    return res.stay


class _Planner:
    """Room and category-night accounting shared by greedy, repair and split plans.

    Room level: a proposal never overlaps a recorded hold or another proposal.
    Category level: rooms must stay free for guests already in house without a
    recorded room, and for unsold allotment/group rooms before their release.
    With no such guests or blocks this adds no constraint, so the original
    proposal behaviour is unchanged.
    """

    def __init__(self, rooms, holds, floating, blocks, today, pickup):
        self.rooms = rooms
        self.holds = holds
        self.lo = today.toordinal()
        self.hi = _shift(today, ACCOUNTING_NIGHTS).toordinal()
        self.today = today
        self.planned: dict[str, list[tuple[Reservation, Window]]] = {room.id: [] for room in rooms}
        self.occupied: dict[tuple[str, int], set[str]] = defaultdict(set)
        self.floating = floating
        self.rooms_by_category: dict[str, list[Room]] = defaultdict(list)
        for room in rooms:
            self.rooms_by_category[room.category].append(room)
        self.blocks_by_category: dict[str, list[Block]] = defaultdict(list)
        for block in blocks:
            self.blocks_by_category[block.category].append(block)
        self.block_index = {block.id: block for block in blocks}
        # Block members that already consume a room; proposals add to it.
        self.pickup: Counter = Counter(pickup)
        self._sellable: dict[tuple[str, int], int] = {}
        # Cached unsold block rooms per category-night, updated incrementally.
        self._reserve: dict[tuple[str, int], int] = {}
        for room in rooms:
            for _, window in holds[room.id]:
                for night in self.nights(window):
                    if self.room_sellable(room, night):
                        self.occupied[(room.category, night)].add(room.id)

    def nights(self, window: Window) -> range:
        return range(max(window.start.toordinal(), self.lo), min(window.end.toordinal(), self.hi))

    @staticmethod
    def room_sellable(room: Room, night: int) -> bool:
        return room.active and not any(
            m.start.toordinal() <= night < m.end.toordinal() for m in room.maintenance)

    def sellable(self, category: str, night: int) -> int:
        key = (category, night)
        if key not in self._sellable:
            self._sellable[key] = sum(
                1 for room in self.rooms_by_category.get(category, ()) if self.room_sellable(room, night))
        return self._sellable[key]

    def holding(self, block: Block, night: int) -> bool:
        """Block covers the night and its rooms are not yet released to free sale."""
        day = date.fromordinal(night)
        return block.stay.covers(day) and block.release_date(day) > self.today

    def unsold(self, block: Block, night: int) -> int:
        return max(0, block.rooms - self.pickup[(block.id, night)])

    def reserve(self, category: str, night: int) -> int:
        key = (category, night)
        if key not in self._reserve:
            self._reserve[key] = sum(self.unsold(block, night)
                                     for block in self.blocks_by_category.get(category, ())
                                     if self.holding(block, night))
        return self._reserve[key]

    def own_block(self, res: Reservation) -> Block | None:
        block = self.block_index.get(res.block_id) if res.block_id else None
        return block if block is not None and block.category == res.category else None

    def capacity_ok(self, res: Reservation, window: Window) -> bool:
        own = self.own_block(res)
        for night in self.nights(window):
            # A block member may take one of its own block's unsold rooms.
            own_room = own is not None and self.holding(own, night) and self.unsold(own, night) > 0
            used = (len(self.occupied[(res.category, night)]) + self.floating[(res.category, night)]
                    + self.reserve(res.category, night) - (1 if own_room else 0))
            if used + 1 > self.sellable(res.category, night):
                return False
        return True

    def free_room(self, room: Room, res: Reservation, window: Window) -> bool:
        return (room.category == res.category and room.available(window)
                and not (res.twin_requested and room.beds == "double")
                and room.fits(res.adults, res.children)
                and not any(w.overlaps(window) for _, w in self.holds[room.id])
                and not any(w.overlaps(window) for _, w in self.planned[room.id]))

    def count_pickup(self, own: Block, night: int, step: int) -> None:
        key = (own.category, night)
        before = self.unsold(own, night)
        self.pickup[(own.id, night)] += step
        if key in self._reserve and self.holding(own, night):
            self._reserve[key] += self.unsold(own, night) - before

    def place(self, res: Reservation, room: Room, window: Window) -> None:
        self.planned[room.id].append((res, window))
        own = self.own_block(res)
        for night in self.nights(window):
            self.occupied[(room.category, night)].add(room.id)
            if own is not None and own.stay.covers(date.fromordinal(night)):
                self.count_pickup(own, night, 1)

    def unplace(self, res: Reservation, room: Room, window: Window) -> None:
        entries = self.planned[room.id]
        del entries[next(i for i, (other, w) in enumerate(entries) if other is res and w == window)]
        own = self.own_block(res)
        for night in self.nights(window):
            self.occupied[(room.category, night)].discard(room.id)
            if own is not None and own.stay.covers(date.fromordinal(night)):
                self.count_pickup(own, night, -1)


def _turnover_conflict(departing: Reservation, arriving: Reservation, policy: Policy) -> bool:
    """Same-day turnover only matters when a time was actually recorded."""
    if departing.departure_time is None and arriving.arrival_time is None:
        return False
    leaves = _minutes(departing.departure_time or policy.checkout_time)
    arrives = _minutes(arriving.arrival_time or policy.checkin_time)
    return arrives < leaves + policy.turnover_minutes


def _room_turnover_risk(planner: _Planner, room: Room, res: Reservation, window: Window, policy: Policy) -> bool:
    entries = planner.holds[room.id] + planner.planned[room.id]
    return any(w.end == window.start and _turnover_conflict(other, res, policy) for other, w in entries)


def _recover_small_safe_plan(
    requests: list[Reservation],
    rooms: list[Room],
    planner: _Planner,
) -> dict[tuple[str, str], str] | None:
    """Bounded fallback when the normal greedy room suggestion misses a valid plan.

    Scope is deliberately small (at most 8 stays / 18 rooms / 20,000
    candidate placements). There is no global-optimum claim and no PMS write.
    A failed or exhausted search leaves the original advisory output intact.
    The planner must hold recorded stays only; proposals made here are undone
    unless every request can be placed.
    """
    if not requests or len(requests) > 8 or len(rooms) > 18:
        return None

    options: dict[tuple[str, str], list[Room]] = {}
    for res in requests:
        compatible = [room for room in rooms if planner.free_room(room, res, res.stay)]
        if not compatible:
            return None
        bed_order = ("twin", "flex", "double") if res.twin_requested else ("double", "flex", "twin")
        compatible.sort(key=lambda room: (bed_order.index(room.beds), room.id))
        options[(res.source, res.ref)] = compatible

    ordered = sorted(
        requests,
        key=lambda res: (len(options[(res.source, res.ref)]),
                         0 if res.twin_requested else 1,
                         res.stay.start, res.source, res.ref),
    )
    matches: dict[tuple[str, str], str] = {}
    states = 0

    def search(index: int) -> bool:
        nonlocal states
        if index == len(ordered):
            return True
        res = ordered[index]
        key = (res.source, res.ref)
        for room in options[key]:
            if any(window.overlaps(res.stay) for _, window in planner.planned[room.id]):
                continue
            if states >= 20_000:
                return False
            states += 1
            if not planner.capacity_ok(res, res.stay):
                continue
            planner.place(res, room, res.stay)
            matches[key] = room.id
            if search(index + 1):
                return True
            planner.unplace(res, room, res.stay)
            del matches[key]
        return False

    return dict(matches) if search(0) else None


def _split_stay_plan(res: Reservation, rooms: list[Room], planner: _Planner) -> list[tuple[Room, Window]] | None:
    """One planned room move when no single room is free for the whole stay."""
    if (res.stay.end - res.stay.start).days < 2 or not planner.capacity_ok(res, res.stay):
        return None
    bed_order = ("twin", "flex", "double") if res.twin_requested else ("double", "flex", "twin")
    ordered = sorted((room for room in rooms if room.category == res.category),
                     key=lambda room: (bed_order.index(room.beds), room.id))
    # Prefer the longest first segment: the guest settles in and moves once, late.
    split = _shift(res.stay.end, -1)
    while split > res.stay.start:
        first, second = Window(res.stay.start, split), Window(split, res.stay.end)
        firsts = [room for room in ordered if planner.free_room(room, res, first)]
        seconds = [room for room in ordered if planner.free_room(room, res, second)] if firsts else []
        for room_a in firsts:
            room_b = next((room for room in seconds if room.id != room_a.id), None)
            if room_b is not None:
                return [(room_a, first), (room_b, second)]
        split = _shift(split, -1)
    return None


def _meal_forecast(reservations: list[Reservation], today: date) -> list[dict[str, Any]]:
    """Breakfast for guests who slept the previous night; dinner for guests
    staying tonight; lunch only for full in-house days (arrival/departure-day
    lunch depends on property policy and is not counted)."""
    forecast = []
    for day in (today, _shift(today, 1)):
        previous = _shift(day, -1)
        meals = {meal: {"adults": 0, "children": 0} for meal in ("breakfast", "lunch", "dinner")}
        without_board = without_count = 0
        for res in reservations:
            if res.status not in COMMITTED_STATUSES:
                continue
            stay = _effective_stay(res, today)
            slept, staying = stay.covers(previous) and previous < day, stay.covers(day)
            if not (slept or staying):
                continue
            if res.board is None:
                without_board += 1
                continue
            served = []
            if slept and res.board in BREAKFAST_BOARDS:
                served.append("breakfast")
            if slept and staying and res.board in LUNCH_BOARDS:
                served.append("lunch")
            if staying and res.board in DINNER_BOARDS:
                served.append("dinner")
            if not served:
                continue
            if res.adults is None:
                without_count += 1
                continue
            for meal in served:
                meals[meal]["adults"] += res.adults
                meals[meal]["children"] += res.children or 0
        forecast.append({"date": day.isoformat(), **meals,
                         "reservations_without_board": without_board,
                         "reservations_without_guest_count": without_count})
    return forecast


def review(data: Any, as_of: str) -> dict[str, Any]:
    today = read_date(as_of, "as_of")
    if today == date.max:
        raise InputError("as_of: must allow a next-day arrival date")
    snapshot = parse_snapshot(data)
    property_id, rooms, reservations = snapshot.property_id, snapshot.rooms, snapshot.reservations
    policy = snapshot.policy
    room_index = {r.id: r for r in rooms}
    block_index = {b.id: b for b in snapshot.blocks}
    categories = {r.category for r in rooms}
    tomorrow = today + timedelta(days=1)
    alerts: list[dict[str, str]] = []
    proposals: list[dict[str, str]] = []
    seen: dict[tuple[str, str], Reservation] = {}
    holds: dict[str, list[tuple[Reservation, Window]]] = {r.id: [] for r in rooms}
    lo, hi = today.toordinal(), _shift(today, ACCOUNTING_NIGHTS).toordinal()
    floating: Counter = Counter()

    def warn(code: str, severity: str, reservation: Reservation, detail: str) -> None:
        alert = issue(code, severity, reservation.ref, detail)
        alert["source"] = reservation.source
        alerts.append(alert)

    def nights(window: Window) -> range:
        return range(max(window.start.toordinal(), lo), min(window.end.toordinal(), hi))

    for res in reservations:
        key = (res.source, res.ref)
        if key in seen:
            warn("DUPLICATE_SOURCE_REF", "critical", res, "Same source and external reference appears more than once; resolve before applying any changes")
        else:
            seen[key] = res
        if res.category not in categories:
            warn("UNKNOWN_CATEGORY", "critical", res, "Requested room category does not exist in this property")
        if res.total_base is not None:
            nights_count = (res.stay.end - res.stay.start).days
            gross = (sum(res.nightly_rates, Decimal("0")) if res.nightly_rates is not None
                     else res.nightly_base * nights_count)
            expected = gross - (res.discount_base or Decimal("0"))
            if expected != res.total_base:
                warn("BASE_PRICE_MISMATCH", "review", res, f"Expected base-only total {expected:.2f} {res.currency}; verify taxes, discounts and nightly rates manually")
        if res.status == "cancelled":
            if res.has_room:
                warn("CANCELLED_HOLD_REVIEW", "review", res, "Cancelled booking has a room assignment; verify manually in the source PMS")
            continue
        if res.status != "checked_out":
            emitted: set[str] = set()

            def once(code: str, severity: str, detail: str) -> None:
                if code not in emitted:
                    emitted.add(code)
                    warn(code, severity, res, detail)

            checked = res.status in {"confirmed", "pending", "checked_in"}
            for room_id, window in _occupancy(res, today):
                if room_id is None:
                    continue
                room = room_index.get(room_id)
                if not room:
                    once("UNKNOWN_ROOM", "critical", "Assigned room does not exist")
                    if res.status in COMMITTED_STATUSES:
                        for night in nights(window):
                            floating[(res.category, night)] += 1
                    continue
                if checked:
                    if room.category != res.category:
                        once("CATEGORY_MISMATCH", "critical", "Assigned room category differs from booked category; review authorized upgrade policy")
                    if not room.available(window):
                        once("ROOM_OUT_OF_SERVICE", "critical", "Assigned room is inactive or overlaps maintenance")
                    if res.twin_requested and room.beds == "double":
                        once("TWIN_NOT_GUARANTEED", "review", "Twin bed request cannot be guaranteed in this room")
                    if not room.fits(res.adults, res.children):
                        once("OCCUPANCY_EXCEEDS_ROOM", "critical", "Guest count exceeds the assigned room's recorded capacity; move the stay or confirm an authorized extra bed")
                holds[room.id].append((res, window))
        # Stay-status consistency (schema 1.1 statuses).
        if res.status in {"checked_in", "checked_out", "no_show"} and res.stay.start > today:
            warn("STATUS_DATE_CONFLICT", "review", res, "Status says the stay started, ended or was a no-show, but the arrival date is in the future; correct the source record")
        if res.status == "checked_in" and res.stay.end < today:
            warn("CHECKOUT_OVERDUE", "critical", res, "Guest is still recorded as checked in after the checkout date; the room stays blocked until the departure is confirmed")
        if not res.has_room and (
                res.status == "checked_in"
                or (res.status == "confirmed" and res.stay.start < today < res.stay.end)):
            warn("IN_HOUSE_WITHOUT_ROOM", "critical", res, "Stay has started but no room is recorded; locate the guest or record the no-show before selling rooms")
            for night in nights(_effective_stay(res, today)):
                floating[(res.category, night)] += 1
        if res.status == "no_show" and res.has_room and res.stay.end > today:
            warn("NO_SHOW_HOLD_REVIEW", "review", res, "A room is still held for a no-show; release it under the property's no-show policy before reselling")
        if res.status == "pending" and res.stay.start in (today, tomorrow):
            warn("PENDING_ARRIVAL_DECISION", "review", res, "Pending (option) booking arrives today or tomorrow; confirm or release it so the room plan is reliable")
        if res.block_id is not None and res.status in {"confirmed", "pending", "checked_in"}:
            block = block_index.get(res.block_id)
            if block is None:
                warn("BLOCK_NOT_FOUND", "review", res, "Reservation references an allotment or group block that is not in this snapshot")
            elif (res.category != block.category or res.source != block.source
                  or res.stay.start < block.stay.start or res.stay.end > block.stay.end):
                warn("BLOCK_MISMATCH", "review", res, "Reservation category, source or dates fall outside its allotment or group block; verify the contract")

    overlapped: set[int] = set()
    for room_id, held in holds.items():
        held.sort(key=lambda item: (item[1].start, item[0].source, item[0].ref))
        # A sweep flags every participant once, including nested/connected stays.
        # Pairwise warnings both missed the first guest and grew quadratically.
        conflicts: set[int] = set()
        longest = None
        for index, (_, current) in enumerate(held):
            if longest is not None and current.start < held[longest][1].end:
                conflicts.update((longest, index))
                if current.end > held[longest][1].end:
                    longest = index
            else:
                longest = index
        for index in sorted(conflicts):
            res = held[index][0]
            if id(res) not in overlapped:
                overlapped.add(id(res))
                warn("ROOM_OVERLAP", "critical", res, "Assigned room overlaps another active booking or hold; manual resolution required")

    # Same-day turnover risk between recorded stays (only when a time was recorded).
    for room_id, held in holds.items():
        departures: dict[date, list[Reservation]] = defaultdict(list)
        for res, window in held:
            if window.end >= today:
                departures[window.end].append(res)
        for res, window in held:
            if any(other is not res and _turnover_conflict(other, res, policy)
                   for other in departures.get(window.start, ())):
                warn("SAME_DAY_TURNOVER_RISK", "review", res, "Arrival on the previous guest's departure day leaves less than the housekeeping turnover time; agree an arrival time or another room")

    # The same guest holding identical dates through two different sources is
    # the classic OTA + direct double booking. References alone are not used:
    # numbering is per channel and equal references can be a coincidence. The
    # optional guest_key is a per-run pseudonym (see local_csv), never a name.
    # Same-source bookings by one guest are usually multi-room and not flagged.
    duplicate_flagged: set[int] = set()
    by_guest: dict[tuple[str, Window], list[Reservation]] = defaultdict(list)
    for res in reservations:
        if res.guest_key is not None and res.status in {"confirmed", "pending", "checked_in"}:
            by_guest[(res.guest_key, res.stay)].append(res)
    for group in by_guest.values():
        if len({r.source for r in group}) < 2:
            continue
        for res in sorted(group, key=lambda r: (r.source, r.ref)):
            if id(res) not in duplicate_flagged:
                duplicate_flagged.add(id(res))
                warn("POSSIBLE_DUPLICATE_BOOKING", "review", res, "The same pseudonymous guest holds identical dates through another source; confirm this is not an OTA and direct double booking before assigning rooms")

    # Block pickup beyond contracted rooms (review, by deterministic order).
    block_members: dict[str, list[Reservation]] = defaultdict(list)
    for res in reservations:
        if res.block_id in block_index and res.status in COMMITTED_STATUSES:
            block_members[res.block_id].append(res)
    for block in snapshot.blocks:
        members = sorted(block_members.get(block.id, []), key=lambda r: (r.stay.start, r.source, r.ref))
        beyond: set[int] = set()
        for night in nights(block.stay):
            day = date.fromordinal(night)
            covering = [res for res in members if res.stay.covers(day)]
            for res in covering[block.rooms:]:
                beyond.add(id(res))
        for res in members:
            if id(res) in beyond:
                warn("BLOCK_OVERBOOKED", "review", res, "Pickup exceeds the rooms contracted for this allotment or group block on at least one night; confirm the extra rooms")

    # Never propose a room for a duplicate source reference. Proposal is advisory only.
    ref_counts = Counter((r.source, r.ref) for r in reservations)
    duplicated = {k for k, n in ref_counts.items() if n > 1}

    def own_block(res: Reservation) -> Block | None:
        block = block_index.get(res.block_id) if res.block_id else None
        return block if block is not None and block.category == res.category else None

    # Block members that already consume a room (recorded room or in house
    # without one) count as pickup; unassigned arrivals count once proposed.
    base_pickup: Counter = Counter()
    for res in reservations:
        own = own_block(res)
        if own is None or res.status not in {"confirmed", "pending", "checked_in"}:
            continue
        if res.has_room:
            windows = [window for room_id, window in _occupancy(res, today)
                       if room_id in room_index or res.status in COMMITTED_STATUSES]
        elif res.status == "checked_in" or (res.status == "confirmed" and res.stay.start < today < res.stay.end):
            windows = [_effective_stay(res, today)]
        else:
            windows = []
        for window in windows:
            for night in nights(window):
                if own.stay.covers(date.fromordinal(night)):
                    base_pickup[(own.id, night)] += 1
    planner = _Planner(rooms, holds, floating, snapshot.blocks, today, base_pickup)
    todo = sorted(
        (r for r in reservations if r.status == "confirmed" and not r.has_room and r.stay.start >= today),
        key=lambda r: (r.stay.start, 0 if r.twin_requested else 1, r.source, r.ref),
    )
    missing: list[Reservation] = []
    turnover_risk: list[Reservation] = []
    for res in todo:
        if (res.source, res.ref) in duplicated or res.category not in categories:
            continue
        candidates = []
        if planner.capacity_ok(res, res.stay):
            candidates = [room for room in sorted(rooms, key=lambda r: r.id)
                          if planner.free_room(room, res, res.stay)]
        if not candidates:
            missing.append(res)
            continue
        # Preserve scarce twin-capable rooms for constrained guests; heuristic, not global optimization.
        # Rooms that would squeeze a recorded early arrival or late departure come last.
        bed_order = ("twin", "flex", "double") if res.twin_requested else ("double", "flex", "twin")
        candidates.sort(key=lambda r: (_room_turnover_risk(planner, r, res, res.stay, policy),
                                       bed_order.index(r.beds), r.id))
        chosen = candidates[0]
        if _room_turnover_risk(planner, chosen, res, res.stay, policy):
            turnover_risk.append(res)
        planner.place(res, chosen, res.stay)
        proposals.append({"reservation_ref": res.ref, "source": res.source, "room_id": chosen.id, "kind": "MANUAL_APPROVAL_REQUIRED"})

    # Repair only proven greedy misses in a small snapshot. Never replace an
    # existing safe partial plan unless every eligible stay can be proposed.
    if missing:
        eligible = [
            res for res in todo
            if (res.source, res.ref) not in duplicated and res.category in categories
        ]
        repair = _Planner(rooms, holds, floating, snapshot.blocks, today, base_pickup)
        recovered = _recover_small_safe_plan(eligible, rooms, repair)
        if recovered is not None:
            proposals = [
                {"reservation_ref": res.ref, "source": res.source,
                 "room_id": recovered[(res.source, res.ref)],
                 "kind": "MANUAL_APPROVAL_REQUIRED"}
                for res in eligible
            ]
            missing = []
            turnover_risk = [res for res in eligible if _room_turnover_risk(
                repair, room_index[recovered[(res.source, res.ref)]], res, res.stay, policy)]
            planner = repair
    for res in missing:
        warn("NO_SAFE_ROOM_PROPOSAL", "critical", res, "No free compatible room; do not confirm or promise a room")
    for res in turnover_risk:
        warn("SAME_DAY_TURNOVER_RISK", "review", res, "Proposed room is turned over the same day with a recorded early arrival or late departure; agree an arrival time or choose another room")

    split_proposals: list[dict[str, Any]] = []
    for res in missing:
        plan = _split_stay_plan(res, rooms, planner)
        if plan is None:
            continue
        for room, window in plan:
            planner.place(res, room, window)
        split_proposals.append({
            "reservation_ref": res.ref, "source": res.source, "kind": "MANUAL_APPROVAL_REQUIRED",
            "segments": [{"room_id": room.id, "start": window.start.isoformat(), "end": window.end.isoformat()}
                         for room, window in plan],
        })
        warn("ROOM_MOVE_OPTION", "review", res, "No single room is free for the whole stay; a plan with one room move is listed for staff decision")

    # Category availability by sold (booked) category: the familiar
    # "rooms sold per room type" view, independent of physical assignment.
    horizon = range(lo, min(_shift(today, policy.horizon_nights).toordinal(), hi))
    committed: Counter = Counter()
    pending: Counter = Counter()
    pending_used: Counter = Counter()
    unassigned_pending: list[Reservation] = []
    for res in reservations:
        if res.category not in categories:
            continue
        held_no_show = res.status == "no_show" and res.has_room
        if res.status in COMMITTED_STATUSES or held_no_show:
            for night in nights(_effective_stay(res, today)):
                committed[(res.category, night)] += 1
        elif res.status == "pending":
            for night in nights(res.stay):
                pending[(res.category, night)] += 1
                if res.has_room:
                    pending_used[(res.category, night)] += 1
            if not res.has_room:
                unassigned_pending.append(res)
    pickup_committed: Counter = Counter()
    for block_id, members in block_members.items():
        block = block_index[block_id]
        for res in members:
            for night in nights(_effective_stay(res, today)):
                if block.stay.covers(date.fromordinal(night)):
                    pickup_committed[(block_id, night)] += 1
    # Same block bookkeeping as proposals, but counting sold (committed) pickup.
    demand = _Planner(rooms, {room.id: [] for room in rooms}, Counter(), snapshot.blocks, today, pickup_committed)
    sellable = planner.sellable
    availability = []
    for category in sorted(categories):
        rows = []
        for night in horizon:
            reserve = demand.reserve(category, night)
            rows.append({
                "date": date.fromordinal(night).isoformat(),
                "sellable": sellable(category, night),
                "committed": committed[(category, night)],
                "block_reserve": reserve,
                "pending": pending[(category, night)],
                "free": sellable(category, night) - committed[(category, night)] - reserve,
            })
        availability.append({"category": category, "nights": rows})

    # Would confirming each unassigned pending booking overbook its category?
    for res in sorted(unassigned_pending, key=lambda r: (r.stay.start, r.source, r.ref)):
        own = own_block(res)
        plan_nights, fits_all = [], True
        for night in nights(res.stay):
            from_block = own is not None and demand.holding(own, night) and demand.unsold(own, night) > 0
            free = (sellable(res.category, night) - committed[(res.category, night)]
                    - demand.reserve(res.category, night) - pending_used[(res.category, night)]
                    + (1 if from_block else 0))
            if free < 1:
                fits_all = False
                break
            plan_nights.append((night, from_block))
        if not fits_all:
            warn("PENDING_EXCEEDS_CAPACITY", "review", res, "Confirming this pending booking would overbook its room category on at least one night")
            continue
        for night, from_block in plan_nights:
            if from_block:
                demand.count_pickup(own, night, 1)
            else:
                pending_used[(res.category, night)] += 1

    blocks_report = []
    for block in sorted(snapshot.blocks, key=lambda b: b.id):
        held_unsold = released_unsold = peak = 0
        next_release: date | None = None
        unsold_by_release: Counter = Counter()
        for night in nights(block.stay):
            day = date.fromordinal(night)
            taken = pickup_committed[(block.id, night)]
            peak = max(peak, taken)
            unsold = max(0, block.rooms - taken)
            release = block.release_date(day)
            if release <= today:
                released_unsold += unsold
            else:
                held_unsold += unsold
                if unsold:
                    unsold_by_release[release] += unsold
                    next_release = release if next_release is None else min(next_release, release)
        blocks_report.append({
            "block_id": block.id, "kind": block.kind, "source": block.source, "category": block.category,
            "start": block.stay.start.isoformat(), "end": block.stay.end.isoformat(), "rooms": block.rooms,
            "release_days": None if block.cutoff is not None else block.release_days,
            "cutoff": block.cutoff.isoformat() if block.cutoff is not None else None,
            "picked_up_peak": peak,
            "held_unsold_room_nights": held_unsold,
            "released_unsold_room_nights": released_unsold,
            "next_release_date": next_release.isoformat() if next_release else None,
            "unsold_at_next_release": unsold_by_release[next_release] if next_release else 0,
        })

    tomorrow_arrivals = sorted(
        [{"reservation_ref": r.ref, "source": r.source, "category": r.category,
          "assigned_room": r.first_room(), "status": r.status}
         for r in reservations if r.stay.start == tomorrow and r.status in {"confirmed", "pending"}],
        key=lambda x: (x["source"], x["reservation_ref"]),
    )
    today_departures = sorted(
        [{"reservation_ref": r.ref, "source": r.source, "room_id": r.last_room(),
          "departure_time": r.departure_time, "status": r.status}
         for r in reservations if r.stay.end == today and r.status in COMMITTED_STATUSES],
        key=lambda x: (x["source"], x["reservation_ref"]),
    )
    room_moves = sorted(
        [{"reservation_ref": r.ref, "source": r.source, "date": left.stay.end.isoformat(),
          "from_room": left.room_id, "to_room": right.room_id}
         for r in reservations if r.status in COMMITTED_STATUSES
         for left, right in zip(r.segments, r.segments[1:]) if left.stay.end in (today, tomorrow)],
        key=lambda x: (x["date"], x["source"], x["reservation_ref"]),
    )
    count_critical = sum(i["severity"] == "critical" for i in alerts)
    return {
        "schema_version": "1.1", "project": "KonaklamaFlow", "mode": "DRY_RUN_ONLY",
        "property_id": property_id, "as_of": today.isoformat(),
        "summary": {"rooms": len(rooms), "reservations": len(reservations),
                    "critical_alerts": count_critical, "review_alerts": len(alerts) - count_critical,
                    "room_proposals": len(proposals), "tomorrow_arrivals": len(tomorrow_arrivals),
                    "split_stay_proposals": len(split_proposals), "today_departures": len(today_departures),
                    "room_moves": len(room_moves)},
        "issues": alerts, "room_proposals": proposals,
        "split_stay_proposals": split_proposals,
        "tomorrow_arrivals": tomorrow_arrivals,
        "today_departures": today_departures,
        "room_moves": room_moves,
        "availability": availability,
        "meal_forecast": _meal_forecast(reservations, today),
        "blocks": blocks_report,
        "disclaimer": "Advisory only. Human approval and checks in the actual PMS are required. No KBS or OTA updates are made.",
    }
