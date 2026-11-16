"""Local CSV -> minimized pseudonymous core input, with no network or uploads.

This is strict *data minimization*, not irreversible anonymization. Dates,
categories and availability patterns remain potentially identifying. Do not
treat exported snapshots as public or shareable without separate review.
"""
from __future__ import annotations

import csv
from hashlib import sha256
import hmac
from io import StringIO
from pathlib import Path
import secrets

from .core import InputError, parse_input
from .io_safety import MAX_INPUT_BYTES, MAX_RESERVATIONS, MAX_ROOMS

# Unknown columns are rejected rather than accidentally copied to reports.
# These explicitly named columns are read locally but entirely discarded.
PRIVATE_COLUMNS = frozenset({
    "guest_name", "first_name", "last_name", "full_name", "name", "surname",
    "guest_first_name", "guest_last_name", "guest_email", "email",
    "guest_phone", "phone", "phone_number", "mobile_phone",
    "guest_address", "address", "passport", "passport_number",
    "id_number", "national_id", "date_of_birth", "dob",
    "guest_notes", "notes", "remarks", "special_requests",
    "payment_card", "credit_card", "card_number", "card_expiry",
    "cvv", "payment_token", "guest_id", "guest_identifier",
})
ROOM_COLUMNS = frozenset({"room_id", "category", "beds", "active"})
RESERVATION_COLUMNS = frozenset({
    "reservation_ref", "checkin", "checkout", "category", "status",
    "room_id", "twin_requested",
})
ROOM_REQUIRED = frozenset({"room_id", "category", "beds"})
RESERVATION_REQUIRED = frozenset({
    "reservation_ref", "checkin", "checkout", "category", "status",
})
# Only these generic values can survive the minimization boundary. They are
# not copied from arbitrary descriptive or notes columns.
CATEGORIES = frozenset({
    "economy", "basement", "standard", "superior", "deluxe",
    "triple", "family", "suite",
})
BEDS = frozenset({"double", "twin", "flex"})
STATUSES = frozenset({"confirmed", "pending", "cancelled"})


def _read_csv(path: str, allowed: frozenset[str], required: frozenset[str],
              max_rows: int) -> list[dict[str, str]]:
    """Read one capped UTF-8 CSV; never echo its path, headers or values."""
    with open(path, "rb") as stream:
        payload = stream.read(MAX_INPUT_BYTES + 1)
    if len(payload) > MAX_INPUT_BYTES:
        raise InputError("CSV input exceeds 2 MB safety limit")
    try:
        decoded = payload.decode("utf-8-sig")
        if "\x00" in decoded:
            raise InputError("Invalid CSV encoding")
        reader = csv.reader(StringIO(decoded, newline=""), strict=True)
        headers = next(reader, None)
        if (not headers or len(headers) > 64 or len(set(headers)) != len(headers)
                or not required <= set(headers)
                or any(header not in (allowed | PRIVATE_COLUMNS)
                       for header in headers)):
            raise InputError("Invalid CSV header or unapproved columns")
        rows: list[dict[str, str]] = []
        for cells in reader:
            if not cells:
                continue
            if len(cells) != len(headers) or len(rows) >= max_rows:
                raise InputError("Invalid CSV row or row limit exceeded")
            rows.append(dict(zip(headers, cells)))
        return rows
    except (UnicodeError, csv.Error, StopIteration):
        raise InputError("Invalid CSV encoding or structure") from None


def _generic(value: str, allowed: frozenset[str], label: str) -> str:
    # Use closed vocabulary so a descriptive field cannot accidentally contain
    # a person's name or a free-text message in the public rule report.
    if value not in allowed:
        raise InputError(f"Invalid CSV {label}")
    return value


def _flag(value: str, label: str, default: bool) -> bool:
    if value == "":
        return default
    if value in ("true", "TRUE", "1", "yes"):
        return True
    if value in ("false", "FALSE", "0", "no"):
        return False
    raise InputError(f"Invalid CSV {label}")


def _token(key: bytes, kind: bytes, value: str) -> str:
    if not isinstance(value, str) or not (1 <= len(value) <= 128):
        raise InputError("Invalid CSV reference value")
    # Random secret is memory-only and unique per invocation. Stable linkage
    # survives between the two CSV inputs *within one invocation*, not across
    # separate reports. No reversible lookup table is saved.
    return ("R_" if kind == b"room" else "B_") + hmac.new(
        key, kind + b"\0" + value.encode("utf-8"), sha256
    ).hexdigest()[:24].upper()


def import_csv_snapshot(rooms_path: str, reservations_path: str) -> dict:
    """Minimize two local CSV files to the established core JSON schema.

    The original CSV files remain unchanged. No intermediary JSON is written.
    The caller must keep input files and returned report local/private.
    """
    if Path(rooms_path).resolve() == Path(reservations_path).resolve():
        raise InputError("Rooms and reservations CSV must be different files")
    rooms_raw = _read_csv(rooms_path, ROOM_COLUMNS, ROOM_REQUIRED, MAX_ROOMS)
    bookings_raw = _read_csv(
        reservations_path, RESERVATION_COLUMNS, RESERVATION_REQUIRED,
        MAX_RESERVATIONS,
    )
    secret = secrets.token_bytes(32)
    rooms: list[dict] = []
    for row in rooms_raw:
        rooms.append({
            "id": _token(secret, b"room", row["room_id"]),
            "category": _generic(row["category"], CATEGORIES, "category"),
            "beds": _generic(row["beds"], BEDS, "beds"),
            "active": _flag(row.get("active", ""), "active", False),
        })
    reservations: list[dict] = []
    for row in bookings_raw:
        room_id = row.get("room_id", "")
        item = {
            "ref": _token(secret, b"booking", row["reservation_ref"]),
            "source": "LOCAL_CSV",
            "status": _generic(row["status"], STATUSES, "status"),
            "checkin": row["checkin"],
            "checkout": row["checkout"],
            "category": _generic(row["category"], CATEGORIES, "category"),
            "twin_requested": _flag(
                row.get("twin_requested", ""), "twin_requested", False
            ),
        }
        if room_id:
            item["room_id"] = _token(secret, b"room", room_id)
        reservations.append(item)

    # Reuse existing structural, date, category and collision validation.
    # Core validation errors never contain actual input cell values.
    minimized = {
        "property_id": "LOCAL_CSV_PROPERTY",
        "rooms": rooms,
        "reservations": reservations,
    }
    parse_input(minimized)
    return minimized
