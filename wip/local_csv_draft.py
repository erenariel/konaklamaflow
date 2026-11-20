# WORK IN PROGRESS - UNTESTED DRAFT (2026-11-20). Not imported anywhere.
# Planned replacement for konaklamaflow/local_csv.py; see WIP_HANDOFF.md.
# Next step: move to konaklamaflow/local_csv.py, run tests/test_local_csv.py,
# then add tests for the new mapping/encoding/vocabulary features.
"""Local CSV -> minimized pseudonymous core input, with no network or uploads.

This is strict *data minimization*, not irreversible anonymization. Dates,
categories and availability patterns remain potentially identifying. Do not
treat exported snapshots as public or shareable without separate review.

Real property-management exports differ: semicolon delimiters, Windows-1254
encoding, Turkish headers, ``13.11.2026`` dates and ``1.234,56`` amounts are
recognised. Anything else can be declared in an explicit mapping file. Unknown
columns are still rejected, named personal columns are read and discarded,
and every value that reaches a report comes from a closed vocabulary or is a
per-run HMAC pseudonym. Error messages name rows and column positions, never
cell values.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from hashlib import sha256
import hmac
from io import StringIO
from pathlib import Path
import re
import secrets
import unicodedata
from typing import Any

from konaklamaflow.core import (BED_TYPES, BOARD_TYPES, CURRENCIES, REF_RE, RESERVATION_STATUSES,
                                InputError, parse_snapshot)
from konaklamaflow.io_safety import MAX_INPUT_BYTES, MAX_RESERVATIONS, MAX_ROOMS, read_limited_json

MAX_BLOCKS = 500
MAX_COLUMNS = 200
MAX_MAPPING_BYTES = 200_000

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
# Common Turkish and additional English headers for the same personal data.
PRIVATE_ALIASES = PRIVATE_COLUMNS | frozenset({
    "misafir", "misafir_adi", "misafir_soyadi", "misafir_adi_soyadi", "misafir_ad_soyad",
    "ad", "adi", "soyad", "soyadi", "ad_soyad", "adi_soyadi", "isim", "isim_soyisim",
    "guest", "guest_names", "guests", "tc", "tc_no", "tckn", "tc_kimlik", "tc_kimlik_no",
    "kimlik", "kimlik_no", "pasaport", "pasaport_no", "telefon", "tel", "gsm", "cep",
    "cep_telefonu", "eposta", "e_posta", "mail", "e_mail", "adres", "dogum_tarihi",
    "uyruk", "nationality", "not", "notlar", "aciklama", "ozel_istek", "ozel_istekler",
    "kart_no", "kredi_karti", "card", "company", "firma", "sirket", "vergi_no", "tax_number",
})
NAME_COLUMNS = frozenset({"guest_name", "full_name", "name", "misafir", "misafir_adi",
                          "misafir_adi_soyadi", "misafir_ad_soyad", "ad_soyad", "adi_soyadi",
                          "isim", "isim_soyisim", "guest", "guest_names", "guests"})
FIRST_NAME_COLUMNS = frozenset({"first_name", "guest_first_name", "ad", "adi"})
LAST_NAME_COLUMNS = frozenset({"last_name", "surname", "guest_last_name", "soyad", "soyadi", "misafir_soyadi"})

ROOM_COLUMNS = frozenset({"room_id", "category", "beds", "active"})
RESERVATION_COLUMNS = frozenset({
    "reservation_ref", "checkin", "checkout", "category", "status",
    "room_id", "twin_requested",
})
ROOM_REQUIRED = frozenset({"room_id", "category", "beds"})
RESERVATION_REQUIRED = frozenset({
    "reservation_ref", "checkin", "checkout", "category", "status",
})
BLOCK_REQUIRED = frozenset({"block_id", "source", "category", "start", "end", "rooms"})

_CATEGORY = ("category", "room_type", "roomtype", "room_category", "oda_tipi", "oda_turu",
             "oda_kategorisi", "kategori", "tip")
_ROOM = ("room_id", "room", "room_no", "room_number", "oda", "oda_no", "oda_numarasi", "oda_kodu")
_SOURCE = ("source", "channel", "agency", "booking_source", "kaynak", "kanal", "satis_kanali",
           "acenta", "acente")
ALIASES: dict[str, dict[str, tuple[str, ...]]] = {
    "rooms": {
        "room_id": _ROOM,
        "category": _CATEGORY,
        "beds": ("beds", "bed", "bed_type", "yatak", "yatak_tipi", "yatak_tercihi"),
        "active": ("active", "aktif", "satista", "kullanimda", "sellable"),
        "max_occupancy": ("max_occupancy", "capacity", "kapasite", "max_kisi", "max_pax", "maksimum_kisi"),
        "max_adults": ("max_adults", "max_yetiskin", "maksimum_yetiskin"),
    },
    "reservations": {
        "reservation_ref": ("reservation_ref", "reservation_id", "reservation_no", "reservation_number",
                            "booking_ref", "booking_id", "booking_no", "confirmation_number", "voucher",
                            "voucher_no", "rezervasyon_no", "rezervasyon_numarasi", "rezervasyon_id",
                            "rez_no", "res_no", "onay_no"),
        "checkin": ("checkin", "check_in", "arrival", "arrival_date", "giris", "giris_tarihi", "gelis",
                    "gelis_tarihi", "varis", "varis_tarihi"),
        "checkout": ("checkout", "check_out", "departure", "departure_date", "cikis", "cikis_tarihi",
                     "ayrilis", "ayrilis_tarihi"),
        "category": _CATEGORY,
        "status": ("status", "booking_status", "reservation_status", "durum", "rezervasyon_durumu", "statu"),
        "room_id": _ROOM,
        "twin_requested": ("twin_requested", "twin", "twin_request", "ayri_yatak"),
        "source": _SOURCE,
        "adults": ("adults", "adult", "yetiskin", "yetiskin_sayisi", "buyuk"),
        "children": ("children", "child", "cocuk", "cocuk_sayisi", "kucuk"),
        "board": ("board", "board_type", "meal_plan", "pansiyon", "pansiyon_tipi", "konsept"),
        "nightly_base": ("nightly_base", "nightly_rate", "rate", "gecelik", "gecelik_fiyat", "gecelik_ucret"),
        "total_base": ("total_base", "total", "total_amount", "toplam", "toplam_tutar", "tutar"),
        "discount_base": ("discount_base", "discount", "indirim", "indirim_tutari"),
        "currency": ("currency", "doviz", "doviz_cinsi", "para_birimi"),
        "block_id": ("block_id", "allotment", "allotment_id", "allotment_code", "kontenjan",
                     "kontenjan_kodu", "blok", "blok_kodu", "group_code", "grup_kodu"),
        "arrival_time": ("arrival_time", "eta", "varis_saati", "gelis_saati", "giris_saati"),
        "departure_time": ("departure_time", "etd", "late_checkout", "cikis_saati", "ayrilis_saati"),
    },
    "blocks": {
        "block_id": ("block_id", "id", "allotment", "allotment_id", "kontenjan", "kontenjan_kodu",
                     "blok", "blok_kodu", "grup_kodu"),
        "kind": ("kind", "type", "tur", "tip"),
        "source": _SOURCE,
        "category": _CATEGORY,
        "start": ("start", "start_date", "baslangic", "baslangic_tarihi"),
        "end": ("end", "end_date", "bitis", "bitis_tarihi"),
        "rooms": ("rooms", "room_count", "oda_sayisi", "oda_adedi", "adet"),
        "release_days": ("release_days", "release", "relis", "relis_gunu", "release_gun"),
        "cutoff": ("cutoff", "cut_off", "cutoff_date", "son_tarih", "opsiyon_tarihi"),
    },
}
REQUIRED = {"rooms": ROOM_REQUIRED, "reservations": RESERVATION_REQUIRED, "blocks": BLOCK_REQUIRED}

# Only these generic values can survive the minimization boundary. They are
# not copied from arbitrary descriptive or notes columns.
CATEGORIES = frozenset({
    "economy", "basement", "standard", "superior", "deluxe",
    "triple", "family", "suite",
})
BEDS = frozenset({"double", "twin", "flex"})
STATUSES = frozenset({"confirmed", "pending", "cancelled"})
VOCABULARY: dict[str, dict[str, tuple[str, ...]]] = {
    "category": {
        "economy": ("economy", "ekonomi", "ekonomik", "eco"),
        "basement": ("basement", "bodrum", "bodrum_kat"),
        "standard": ("standard", "standart", "standard_room", "standart_oda", "std"),
        "superior": ("superior", "superior_room", "superior_oda", "sup"),
        "deluxe": ("deluxe", "delux", "deluks", "deluxe_room", "deluxe_oda", "dlx"),
        "triple": ("triple", "triple_room", "uc_kisilik", "uc_kisilik_oda", "trp"),
        "family": ("family", "family_room", "aile", "aile_odasi", "fam"),
        "suite": ("suite", "suit", "suite_room", "suit_oda", "ste"),
    },
    "status": {
        "confirmed": ("confirmed", "confirm", "kesin", "onayli", "onaylandi", "garanti", "garantili",
                      "definite", "reserved", "rezerve", "booked"),
        "pending": ("pending", "tentative", "option", "optional", "opsiyon", "opsiyonlu", "beklemede",
                    "bekliyor", "on_request", "request", "talep"),
        "cancelled": ("cancelled", "canceled", "cancel", "iptal", "iptal_edildi", "void"),
        "checked_in": ("checked_in", "check_in", "in_house", "inhouse", "konaklayan", "konakliyor",
                       "giris_yapti", "otelde"),
        "checked_out": ("checked_out", "check_out", "departed", "cikis_yapti", "ayrildi"),
        "no_show": ("no_show", "noshow", "gelmedi", "gelmeyen"),
    },
    "beds": {
        "double": ("double", "dbl", "french", "cift", "cift_kisilik", "cift_kisilik_yatak", "king", "queen"),
        "twin": ("twin", "twn", "iki_tek", "iki_tek_yatak", "ayri", "ayri_yatak", "tek_tek"),
        "flex": ("flex", "esnek", "hollywood", "double_twin", "twin_double", "dbl_twn"),
    },
    "board": {
        "RO": ("ro", "room_only", "sadece_oda", "ob", "only_bed", "bo"),
        "BB": ("bb", "bed_breakfast", "bed_and_breakfast", "oda_kahvalti", "kahvalti", "breakfast"),
        "HB": ("hb", "half_board", "yarim_pansiyon", "yp"),
        "FB": ("fb", "full_board", "tam_pansiyon", "tp"),
        "AI": ("ai", "all_inclusive", "her_sey_dahil", "hersey_dahil", "hsd", "soft_all_inclusive", "soft_ai"),
        "UAI": ("uai", "ultra_all_inclusive", "ultra_her_sey_dahil", "ultra_hersey_dahil", "uhsd"),
    },
    "source": {
        "BOOKING": ("booking", "booking_com", "bookingcom"),
        "EXPEDIA": ("expedia", "expedia_com", "hotels_com"),
        "AIRBNB": ("airbnb",),
        "AGODA": ("agoda",),
        "HOTELBEDS": ("hotelbeds",),
        "ETSTUR": ("etstur", "ets", "ets_tur"),
        "JOLLYTUR": ("jolly", "jollytur", "jolly_tur"),
        "TATILBUDUR": ("tatilbudur",),
        "TUI": ("tui",),
        "CORAL": ("coral", "coral_travel"),
        "PEGAS": ("pegas", "pegas_touristik"),
        "ANEX": ("anex", "anex_tour"),
        "DIRECT": ("direct", "direkt", "web", "website", "web_sitesi", "otel", "hotel", "resepsiyon", "reception"),
        "WALKIN": ("walk_in", "walkin"),
        "PHONE": ("phone", "telefon", "tel"),
        "EMAIL": ("email", "e_mail", "eposta", "e_posta", "mail"),
    },
    "currency": {
        "TRY": ("try", "tl", "ytl", "turk_lirasi"),
        "EUR": ("eur", "euro", "avro"),
        "USD": ("usd", "dolar", "dollar", "us_dollar"),
        "GBP": ("gbp", "sterlin", "pound", "sterling"),
        "RUB": ("rub", "ruble", "rubl"),
    },
    "kind": {
        "allotment": ("allotment", "kontenjan", "contingent"),
        "group": ("group", "grup"),
    },
}
CURRENCY_SYMBOLS = {"€": "EUR", "$": "USD", "£": "GBP", "₺": "TRY", "₽": "RUB"}
TRUE_VALUES = frozenset({"true", "1", "yes", "evet", "var", "e", "y"})
FALSE_VALUES = frozenset({"false", "0", "no", "hayir", "yok", "h", "n"})
DATE_FORMATS = {
    "YYYY-MM-DD": (re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})"), ("y", "m", "d")),
    "DD.MM.YYYY": (re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})"), ("d", "m", "y")),
    "DD/MM/YYYY": (re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})"), ("d", "m", "y")),
    "MM/DD/YYYY": (re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})"), ("m", "d", "y")),
    "DD-MM-YYYY": (re.compile(r"(\d{1,2})-(\d{1,2})-(\d{4})"), ("d", "m", "y")),
}
TIME_SUFFIX = re.compile(r"(?:[ T]\d{1,2}[:.]\d{2}(?:[:.]\d{2})?)?")
DELIMITERS = {",": ",", ";": ";", "tab": "\t", "\t": "\t", "|": "|"}
ENCODINGS = {"auto", "utf-8", "cp1254"}

MAPPING_KEYS = {"encoding", "delimiter", "date_format", "decimal_comma", "property_id",
                "rooms", "reservations", "blocks", "values", "defaults", "policy"}
MAPPING_FILE_KEYS = {"columns", "ignore"}
MAPPING_VALUE_KEYS = {"category", "status", "beds", "board", "source", "currency"}
MAPPING_DEFAULT_KEYS = {"active", "beds", "status", "currency", "source"}

_TR_FOLD = str.maketrans({"ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
                          "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"})


def normalize_label(value: str) -> str:
    """'Giriş Tarihi' -> 'giris_tarihi'. Used for headers and closed vocabularies."""
    text = unicodedata.normalize("NFKD", value.strip().translate(_TR_FOLD))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


@dataclass
class Mapping:
    """Validated, explicit operator configuration for one property's exports."""
    encoding: str = "auto"
    delimiter: str | None = None
    date_format: str | None = None
    decimal_comma: bool | None = None
    property_id: str = "LOCAL_CSV_PROPERTY"
    columns: dict[str, dict[str, str]] = field(default_factory=dict)
    ignore: dict[str, set[str]] = field(default_factory=dict)
    values: dict[str, dict[str, str]] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)
    policy: dict[str, Any] | None = None


@dataclass
class CsvImport:
    """Minimized snapshot plus the memory-only labels a local screen may show."""
    snapshot: dict
    labels: dict[str, dict[str, str]]
    notes: list[str]


def _bad_mapping(where: str) -> InputError:
    return InputError(f"Invalid mapping file: {where}")


def parse_mapping(raw: Any) -> Mapping:
    """Validate a mapping object. Every target must be a supported field or value."""
    if raw is None:
        return Mapping()
    if not isinstance(raw, dict) or set(raw) - MAPPING_KEYS:
        raise _bad_mapping("unsupported top-level keys")
    mapping = Mapping()
    encoding = raw.get("encoding", "auto")
    if encoding not in ENCODINGS:
        raise _bad_mapping("encoding (auto, utf-8 or cp1254)")
    mapping.encoding = encoding
    if raw.get("delimiter") is not None:
        if raw["delimiter"] not in DELIMITERS:
            raise _bad_mapping("delimiter (',', ';', 'tab' or '|')")
        mapping.delimiter = DELIMITERS[raw["delimiter"]]
    if raw.get("date_format") is not None:
        if raw["date_format"] not in DATE_FORMATS:
            raise _bad_mapping("date_format")
        mapping.date_format = raw["date_format"]
    if raw.get("decimal_comma") is not None:
        if type(raw["decimal_comma"]) is not bool:
            raise _bad_mapping("decimal_comma (true or false)")
        mapping.decimal_comma = raw["decimal_comma"]
    if raw.get("property_id") is not None:
        if not isinstance(raw["property_id"], str) or not REF_RE.fullmatch(raw["property_id"]):
            raise _bad_mapping("property_id")
        mapping.property_id = raw["property_id"]
    for kind in ("rooms", "reservations", "blocks"):
        section = raw.get(kind, {})
        if not isinstance(section, dict) or set(section) - MAPPING_FILE_KEYS:
            raise _bad_mapping(kind)
        columns = section.get("columns", {})
        if not isinstance(columns, dict) or len(columns) > MAX_COLUMNS:
            raise _bad_mapping(f"{kind}.columns")
        resolved = {}
        for header, target in columns.items():
            if (not isinstance(header, str) or not 0 < len(header) <= 100 or not normalize_label(header)
                    or target not in ALIASES[kind]):
                raise _bad_mapping(f"{kind}.columns")
            resolved[normalize_label(header)] = target
        mapping.columns[kind] = resolved
        ignore = section.get("ignore", [])
        if (not isinstance(ignore, list) or len(ignore) > MAX_COLUMNS
                or any(not isinstance(h, str) or not 0 < len(h) <= 100 for h in ignore)):
            raise _bad_mapping(f"{kind}.ignore")
        mapping.ignore[kind] = {normalize_label(h) for h in ignore}
    values = raw.get("values", {})
    if not isinstance(values, dict) or set(values) - MAPPING_VALUE_KEYS:
        raise _bad_mapping("values")
    allowed_targets = {"status": RESERVATION_STATUSES, "beds": BED_TYPES, "board": BOARD_TYPES,
                       "currency": CURRENCIES}
    for name, table in values.items():
        if not isinstance(table, dict) or len(table) > 500:
            raise _bad_mapping(f"values.{name}")
        resolved = {}
        for label, target in table.items():
            if not isinstance(label, str) or not 0 < len(label) <= 100 or not normalize_label(label):
                raise _bad_mapping(f"values.{name}")
            if name in allowed_targets:
                if target not in allowed_targets[name]:
                    raise _bad_mapping(f"values.{name}")
            elif not isinstance(target, str) or not REF_RE.fullmatch(target):
                raise _bad_mapping(f"values.{name}")
            resolved[normalize_label(label)] = target
        mapping.values[name] = resolved
    defaults = raw.get("defaults", {})
    if not isinstance(defaults, dict) or set(defaults) - MAPPING_DEFAULT_KEYS:
        raise _bad_mapping("defaults")
    checks = {"active": lambda v: type(v) is bool, "beds": lambda v: v in BED_TYPES,
              "status": lambda v: v in RESERVATION_STATUSES, "currency": lambda v: v in CURRENCIES,
              "source": lambda v: isinstance(v, str) and REF_RE.fullmatch(v) is not None}
    for key, value in defaults.items():
        if not checks[key](value):
            raise _bad_mapping(f"defaults.{key}")
    mapping.defaults = dict(defaults)
    if raw.get("policy") is not None:
        if not isinstance(raw["policy"], dict):
            raise _bad_mapping("policy")
        mapping.policy = dict(raw["policy"])
    return mapping


def load_mapping(path: str | None) -> Mapping:
    if path is None:
        return Mapping()
    return parse_mapping(read_limited_json(path, MAX_MAPPING_BYTES))


def _decode(payload: bytes, encoding: str, label: str) -> str:
    if len(payload) > MAX_INPUT_BYTES:
        raise InputError(f"{label} CSV exceeds 2 MB safety limit")
    try:
        if encoding == "cp1254":
            text = payload.decode("cp1254")
        else:
            try:
                text = payload.decode("utf-8-sig")
            except UnicodeDecodeError:
                if encoding == "utf-8":
                    raise
                # Turkish Windows Excel saves "CSV (comma delimited)" as Windows-1254.
                text = payload.decode("cp1254")
    except UnicodeError:
        raise InputError(f"Invalid {label} CSV encoding") from None
    if "\x00" in text:
        raise InputError(f"Invalid {label} CSV encoding")
    return text


def _detect_delimiter(text: str) -> str:
    header = text.split("\n", 1)[0]
    counts = {d: header.count(d) for d in (",", ";", "\t", "|")}
    best = max(counts, key=lambda d: (counts[d], d == ","))
    return best if counts[best] else ","


@dataclass
class _Table:
    kind: str
    delimiter: str
    encoding_used: str
    fields: list[str | None]          # canonical field per column, None = dropped
    status: list[str]                 # mapped / private / ignored / empty / unknown
    private_roles: dict[int, str]     # column index -> name / first / last
    rows: list[list[str]]
    first_row: int


def _classify(kind: str, headers: list[str], mapping: Mapping) -> tuple[list, list, dict]:
    aliases = {alias: target for target, names in ALIASES[kind].items() for alias in names}
    explicit = mapping.columns.get(kind, {})
    ignored = mapping.ignore.get(kind, set())
    fields, status, roles = [], [], {}
    for index, header in enumerate(headers):
        label = normalize_label(header)
        if not label:
            fields.append(None)
            status.append("empty")
        elif label in explicit:
            fields.append(explicit[label])
            status.append("mapped")
        elif label in ignored:
            fields.append(None)
            status.append("ignored")
        elif label in aliases:
            fields.append(aliases[label])
            status.append("mapped")
        elif label in PRIVATE_ALIASES:
            fields.append(None)
            status.append("private")
            if label in NAME_COLUMNS:
                roles[index] = "name"
            elif label in FIRST_NAME_COLUMNS:
                roles[index] = "first"
            elif label in LAST_NAME_COLUMNS:
                roles[index] = "last"
        else:
            fields.append(None)
            status.append("unknown")
    return fields, status, roles


def _read_table(payload: bytes, kind: str, mapping: Mapping, max_rows: int, *, inspect: bool = False) -> _Table:
    """Parse one capped CSV; never echo its path, headers or values."""
    text = _decode(payload, mapping.encoding, kind)
    try:
        encoding_used = "utf-8"
        payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        encoding_used = "cp1254"
    if mapping.encoding == "cp1254":
        encoding_used = "cp1254"
    delimiter = mapping.delimiter or _detect_delimiter(text)
    try:
        reader = csv.reader(StringIO(text, newline=""), delimiter=delimiter, strict=True)
        headers = next(reader, None)
        if not headers or len(headers) > MAX_COLUMNS:
            raise InputError(f"Invalid {kind} CSV header")
        fields, status, roles = _classify(kind, headers, mapping)
        rows: list[list[str]] = []
        for cells in reader:
            if not cells or all(not cell.strip() for cell in cells):
                continue
            if len(cells) != len(headers) or len(rows) >= max_rows:
                raise InputError(f"Invalid {kind} CSV row {reader.line_num} or row limit exceeded")
            rows.append(cells)
    except csv.Error:
        raise InputError(f"Invalid {kind} CSV encoding or structure") from None
    table = _Table(kind, delimiter, encoding_used, fields, status, roles, rows, 2)
    if inspect:
        return table
    unknown = [i + 1 for i, s in enumerate(status) if s == "unknown"]
    if unknown:
        raise InputError(f"Invalid CSV header or unapproved columns in {kind} file (column "
                         f"{', '.join(map(str, unknown[:10]))}); map or ignore them in a mapping file")
    for index, state in enumerate(status):
        if state == "empty" and any(row[index].strip() for row in rows):
            raise InputError(f"Unnamed {kind} CSV column {index + 1} has values; name or remove it")
    targets = [f for f in fields if f is not None]
    if len(targets) != len(set(targets)):
        raise InputError(f"Invalid CSV header: duplicated {kind} column")
    return table


def _missing_required(table: _Table, mapping: Mapping) -> list[str]:
    present = {f for f in table.fields if f is not None}
    required = set(REQUIRED[table.kind])
    if table.kind == "rooms" and "beds" in mapping.defaults:
        required.discard("beds")
    if table.kind == "reservations" and "status" in mapping.defaults:
        required.discard("status")
    return sorted(required - present)


def _records(table: _Table) -> list[tuple[int, dict[str, str], dict[str, str]]]:
    """Rows as (row number, field values, private role values)."""
    records = []
    for offset, cells in enumerate(table.rows):
        values = {f: cells[i].strip() for i, f in enumerate(table.fields) if f is not None}
        private = {role: cells[i].strip() for i, role in table.private_roles.items()}
        records.append((table.first_row + offset, values, private))
    return records


def _token(key: bytes, kind: bytes, value: str) -> str:
    if not isinstance(value, str) or not (1 <= len(value) <= 128):
        raise InputError("Invalid CSV reference value")
    # Random secret is memory-only and unique per invocation. Stable linkage
    # survives between the CSV inputs *within one invocation*, not across
    # separate reports. No reversible lookup table is saved.
    prefix, length = {b"room": ("R_", 24), b"booking": ("B_", 24), b"source": ("S_", 16),
                      b"guest": ("G_", 24), b"block": ("K_", 24)}[kind]
    return prefix + hmac.new(key, kind + b"\0" + value.encode("utf-8"), sha256).hexdigest()[:length].upper()


def _generic(value: str, allowed: frozenset[str], label: str) -> str:
    # Use closed vocabulary so a descriptive field cannot accidentally contain
    # a person's name or a free-text message in the public rule report.
    if value not in allowed:
        raise InputError(f"Invalid CSV {label}")
    return value


def _vocab(value: str, name: str, mapping: Mapping, where: str) -> str:
    label = normalize_label(value)
    custom = mapping.values.get(name, {})
    if label in custom:
        return custom[label]
    for target, names in VOCABULARY[name].items():
        if label in names:
            return target
    raise InputError(f"Invalid CSV {name} ({where}); add it to values.{name} in a mapping file")


def _flag(value: str, label: str, default: bool) -> bool:
    if value == "":
        return default
    folded = normalize_label(value)
    if folded in TRUE_VALUES:
        return True
    if folded in FALSE_VALUES:
        return False
    raise InputError(f"Invalid CSV {label}")


def _date(value: str, mapping: Mapping, where: str) -> str:
    text = value.strip()
    formats = [mapping.date_format] if mapping.date_format else ["YYYY-MM-DD", "DD.MM.YYYY"]
    for name in formats:
        pattern, order = DATE_FORMATS[name]
        match = re.fullmatch(pattern.pattern + TIME_SUFFIX.pattern, text)
        if match:
            parts = dict(zip(order, (int(g) for g in match.groups()[:3])))
            try:
                return date(parts["y"], parts["m"], parts["d"]).isoformat()
            except ValueError:
                break
    raise InputError(f"Invalid CSV date ({where}); use YYYY-MM-DD or DD.MM.YYYY, or set date_format")


def _clock(value: str, where: str) -> str | None:
    if not value:
        return None
    match = re.fullmatch(r"(\d{1,2})[:.](\d{2})(?:[:.]\d{2})?", value)
    if not match or int(match.group(1)) > 23 or int(match.group(2)) > 59:
        raise InputError(f"Invalid CSV time ({where}); use HH:MM")
    return f"{int(match.group(1)):02d}:{match.group(2)}"


def _count(value: str, where: str) -> int | None:
    if not value:
        return None
    match = re.fullmatch(r"(\d{1,3})(?:[.,]0+)?", value)
    if not match:
        raise InputError(f"Invalid CSV guest or room count ({where})")
    return int(match.group(1))


def _money(value: str, mapping: Mapping, where: str) -> str | None:
    text = re.sub(r"\s", "", value)
    for symbol in CURRENCY_SYMBOLS:
        text = text.replace(symbol, "")
    text = re.sub(r"(?i)(try|tl|eur|usd|gbp|rub)$", "", text)
    if not text:
        return None
    if not re.fullmatch(r"[0-9.,]+", text):
        raise InputError(f"Invalid CSV amount ({where})")
    if mapping.decimal_comma is True:
        text = text.replace(".", "").replace(",", ".")
    elif mapping.decimal_comma is False:
        text = text.replace(",", "")
    elif "," in text and "." in text:
        decimal = "," if text.rfind(",") > text.rfind(".") else "."
        thousands = "." if decimal == "," else ","
        text = text.replace(thousands, "").replace(decimal, ".")
    elif "," in text:
        text = text.replace(",", ".") if re.fullmatch(r"\d+,\d{1,2}", text) else text.replace(",", "")
    elif "." in text and not re.fullmatch(r"\d+\.\d{1,2}", text):
        text = text.replace(".", "")
    if not re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,2})?", text):
        raise InputError(f"Invalid CSV amount ({where})")
    return text


def _currency(value: str, mapping: Mapping, where: str) -> str | None:
    if not value:
        return mapping.defaults.get("currency")
    stripped = value.strip()
    if stripped in CURRENCY_SYMBOLS:
        return CURRENCY_SYMBOLS[stripped]
    if stripped.upper() in CURRENCIES:
        return stripped.upper()
    return _vocab(stripped, "currency", mapping, where)


def _guest_name(private: dict[str, str]) -> str | None:
    name = private.get("name") or " ".join(p for p in (private.get("first"), private.get("last")) if p)
    folded = " ".join(normalize_label(name).split("_"))
    return folded or None


def import_csv_data(rooms_payload: bytes, reservations_payload: bytes, blocks_payload: bytes | None = None,
                    mapping: Mapping | None = None, *, link_guests: bool = False,
                    rooms_active: bool | None = None) -> CsvImport:
    """Minimize CSV bytes to the core JSON schema; returns memory-only labels too.

    ``link_guests`` derives a per-run pseudonymous guest key from name columns
    so the same guest booked twice through different channels can be flagged.
    The key is never reversible without the in-memory secret and is not labelled.
    """
    mapping = mapping or Mapping()
    if rooms_active is not None:
        mapping.defaults = dict(mapping.defaults, active=rooms_active)
    secret = secrets.token_bytes(32)
    labels: dict[str, dict[str, str]] = {"rooms": {}, "reservations": {}, "sources": {}, "blocks": {}}
    notes: list[str] = []

    def token(kind: bytes, value: str, group: str | None = None) -> str:
        result = _token(secret, kind, value)
        if group is not None:
            labels[group][result] = value
        return result

    def source_code(value: str, where: str) -> str:
        if not value:
            return mapping.defaults.get("source", "LOCAL_CSV")
        label = normalize_label(value)
        if label in mapping.values.get("source", {}):
            return mapping.values["source"][label]
        for code, names in VOCABULARY["source"].items():
            if label in names:
                return code
        return token(b"source", value, "sources")

    tables = {"rooms": _read_table(rooms_payload, "rooms", mapping, MAX_ROOMS),
              "reservations": _read_table(reservations_payload, "reservations", mapping, MAX_RESERVATIONS)}
    if blocks_payload is not None:
        tables["blocks"] = _read_table(blocks_payload, "blocks", mapping, MAX_BLOCKS)
    for table in tables.values():
        missing = _missing_required(table, mapping)
        if missing:
            raise InputError(f"Invalid CSV header: {table.kind} file is missing {', '.join(missing)}")

    rooms: list[dict] = []
    room_table = tables["rooms"]
    if "active" not in room_table.fields and "active" not in mapping.defaults:
        notes.append("ROOMS_INACTIVE_WITHOUT_ACTIVE_COLUMN")
    for number, row, _ in _records(room_table):
        where = f"rooms row {number}"
        if not row.get("room_id"):
            raise InputError(f"Invalid CSV reference value ({where})")
        room = {
            "id": token(b"room", row["room_id"], "rooms"),
            "category": _vocab(row.get("category", ""), "category", mapping, where),
            "beds": (_vocab(row["beds"], "beds", mapping, where) if row.get("beds")
                     else _generic(mapping.defaults.get("beds", ""), BEDS, f"beds ({where})")),
            "active": _flag(row.get("active", ""), f"active ({where})", mapping.defaults.get("active", False)),
        }
        for key in ("max_occupancy", "max_adults"):
            count = _count(row.get(key, ""), where)
            if count is not None:
                room[key] = count
        rooms.append(room)

    blocks: list[dict] = []
    if "blocks" in tables:
        for number, row, _ in _records(tables["blocks"]):
            where = f"blocks row {number}"
            if not row.get("block_id"):
                raise InputError(f"Invalid CSV reference value ({where})")
            block = {
                "id": token(b"block", row["block_id"], "blocks"),
                "kind": _vocab(row["kind"], "kind", mapping, where) if row.get("kind") else "allotment",
                "source": source_code(row.get("source", ""), where),
                "category": _vocab(row.get("category", ""), "category", mapping, where),
                "start": _date(row.get("start", ""), mapping, where),
                "end": _date(row.get("end", ""), mapping, where),
                "rooms": _count(row.get("rooms", ""), where),
            }
            if row.get("release_days"):
                block["release_days"] = _count(row["release_days"], where)
            if row.get("cutoff"):
                block["cutoff"] = _date(row["cutoff"], mapping, where)
            blocks.append(block)

    reservations: list[dict] = []
    booking_table = tables["reservations"]
    if "block_id" in booking_table.fields and "blocks" not in tables:
        notes.append("BLOCK_COLUMN_IGNORED_WITHOUT_BLOCKS_FILE")
    price_notes = set()
    for number, row, private in _records(booking_table):
        where = f"reservations row {number}"
        if not row.get("reservation_ref"):
            raise InputError(f"Invalid CSV reference value ({where})")
        status = (_vocab(row["status"], "status", mapping, where) if row.get("status")
                  else mapping.defaults.get("status"))
        if status is None:
            raise InputError(f"Invalid CSV status ({where})")
        item: dict[str, Any] = {
            "ref": token(b"booking", row["reservation_ref"], "reservations"),
            "source": source_code(row.get("source", ""), where),
            "status": status,
            "checkin": _date(row.get("checkin", ""), mapping, where),
            "checkout": _date(row.get("checkout", ""), mapping, where),
            "category": _vocab(row.get("category", ""), "category", mapping, where),
            "twin_requested": _flag(row.get("twin_requested", ""), f"twin_requested ({where})", False),
        }
        if row.get("room_id"):
            item["room_id"] = token(b"room", row["room_id"], "rooms")
        for key in ("adults", "children"):
            count = _count(row.get(key, ""), where)
            if count is not None:
                item[key] = count
        if row.get("board"):
            item["board"] = _vocab(row["board"], "board", mapping, where)
        for key in ("arrival_time", "departure_time"):
            clock = _clock(row.get(key, ""), where)
            if clock is not None:
                item[key] = clock
        nightly = _money(row.get("nightly_base", ""), mapping, where)
        total = _money(row.get("total_base", ""), mapping, where)
        discount = _money(row.get("discount_base", ""), mapping, where)
        if nightly is not None and total is not None:
            currency = _currency(row.get("currency", ""), mapping, where)
            if currency is None:
                price_notes.add("PRICE_CHECK_SKIPPED_WITHOUT_CURRENCY")
            else:
                item.update(nightly_base=nightly, total_base=total, currency=currency)
                if discount is not None:
                    item["discount_base"] = discount
        elif nightly is not None or total is not None:
            price_notes.add("PRICE_CHECK_NEEDS_NIGHTLY_AND_TOTAL")
        if row.get("block_id") and "blocks" in tables:
            item["block_id"] = token(b"block", row["block_id"], "blocks")
        if link_guests:
            name = _guest_name(private)
            if name:
                item["guest_key"] = token(b"guest", name)
        reservations.append(item)
    notes.extend(sorted(price_notes))
    if link_guests and not booking_table.private_roles:
        notes.append("GUEST_LINKING_WITHOUT_NAME_COLUMNS")

    # Reuse existing structural, date, category and collision validation.
    # Core validation errors never contain actual input cell values.
    minimized: dict[str, Any] = {
        "property_id": mapping.property_id,
        "rooms": rooms,
        "reservations": reservations,
    }
    if blocks:
        minimized["blocks"] = blocks
    if mapping.policy is not None:
        minimized["policy"] = mapping.policy
    parse_snapshot(minimized)
    return CsvImport(minimized, labels, notes)


def _read_capped(path: str, label: str) -> bytes:
    with open(path, "rb") as stream:
        payload = stream.read(MAX_INPUT_BYTES + 1)
    if len(payload) > MAX_INPUT_BYTES:
        raise InputError(f"{label} CSV exceeds 2 MB safety limit")
    return payload


def import_csv_files(rooms_path: str, reservations_path: str, blocks_path: str | None = None,
                     mapping: Mapping | None = None, *, link_guests: bool = False,
                     rooms_active: bool | None = None) -> CsvImport:
    paths = [p for p in (rooms_path, reservations_path, blocks_path) if p is not None]
    if len({Path(p).resolve() for p in paths}) != len(paths):
        raise InputError("Rooms, reservations and blocks CSV must be different files")
    return import_csv_data(
        _read_capped(rooms_path, "rooms"), _read_capped(reservations_path, "reservations"),
        _read_capped(blocks_path, "blocks") if blocks_path is not None else None,
        mapping, link_guests=link_guests, rooms_active=rooms_active)


def import_csv_snapshot(rooms_path: str, reservations_path: str, *, blocks_path: str | None = None,
                        mapping: Mapping | None = None, link_guests: bool = False,
                        rooms_active: bool | None = None) -> dict:
    """Minimize local CSV files to the established core JSON schema.

    The original CSV files remain unchanged. No intermediary JSON is written.
    The caller must keep input files and returned report local/private.
    """
    return import_csv_files(rooms_path, reservations_path, blocks_path, mapping,
                            link_guests=link_guests, rooms_active=rooms_active).snapshot


def inspect_csv(payload: bytes, kind: str, mapping: Mapping | None = None) -> dict:
    """Describe how a CSV would be read, by column position. Never echoes
    unknown header text or any cell value; recognised headers are shown in
    their normalised vocabulary form only."""
    if kind not in ALIASES:
        raise InputError("kind must be rooms, reservations or blocks")
    mapping = mapping or Mapping()
    limit = {"rooms": MAX_ROOMS, "reservations": MAX_RESERVATIONS, "blocks": MAX_BLOCKS}[kind]
    table = _read_table(payload, kind, mapping, limit, inspect=True)
    columns = []
    for index, (target, state) in enumerate(zip(table.fields, table.status)):
        entry: dict[str, Any] = {"position": index + 1, "status": state}
        if target is not None:
            entry["field"] = target
        if state == "private":
            entry["handling"] = "read and discarded"
        columns.append(entry)
    return {
        "kind": kind,
        "encoding": table.encoding_used,
        "delimiter": {"\t": "tab"}.get(table.delimiter, table.delimiter),
        "data_rows": len(table.rows),
        "columns": columns,
        "unknown_columns": [c["position"] for c in columns if c["status"] == "unknown"],
        "missing_required": _missing_required(table, mapping),
        "ready": not any(c["status"] == "unknown" for c in columns) and not _missing_required(table, mapping),
    }
