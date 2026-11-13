"""Fiction-only hotel operations domain and strictly read-only reporting.

Not a full PMS or fiscal/identity/payment processor. No network, AI, OTA,
identity storage, KBS or posting write. All values are fictional. Only a future
authorized backend may handle regulated identities or actual settlement.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import re

class HotelOpsError(ValueError):
    """Input invalid; do not include source values in errors."""

BOARD_TYPES = frozenset({"BB", "HB", "RO", "FB"})
PAYMENT_TYPES = frozenset({"city_ledger", "self_payment"})
METHODS = frozenset({"cash", "credit_card", "mail_order", "bank_transfer"})
STATUS = frozenset({"confirmed", "option", "waitlist", "cancelled", "in_house", "checked_out"})
DOC_TYPES = frozenset({"passport", "eu_identity", "national_id", "driving_licence", "other"})
CATEGORIES = frozenset({"economy","standard","superior","deluxe","triple","family"})
_F = re.compile(r"^[A-Z0-9_-]{1,48}$")
_C = re.compile(r"^[A-Z]{3}$")
_ALLOW_TOP = {"schema_version", "property_id", "as_of", "default_currency", "fictional",
              "privacy_policy", "rooms", "agencies", "guests", "reservations", "folios",
              "report_catalog", "fx_rates", "payment_methods", "board_types",
              "reservation_statuses", "report_versions", "contact_fields_schema"}
_POSTINGS = {"ROOM", "RESTAURANT", "MINIBAR", "TRANSFER", "EXTRA_BED",
             "EXTRA_STAY", "FX_DIFFERENCE", "ADJUSTMENT", "OTHER"}
_ACCOUNTING_MISSING = {"requires_accounting","requires_fiscal","requires_audit",
                       "requires_housekeeping","requires_budget","requires_system_logs",
                       "requires_mail_permissions","requires_safe_ledger",
                       "requires_invoicing","requires_expense_ledger","requires_rm_data"}
_SUPPORTED_REPORTS = {"active_folios","monthly_revenue","detailed_revenue","folio_analysis",
                      "daily_balance","transactions","grouped_transactions","room_list",
                      "room_rate_control","agency_monthly","agency_sales","agency_annual",
                      "blockage_report","extra_bed","advance_payment","posting_invoice",
                      "occupancy","city_ledger","exchange_rates","reservation_list","guest_list"}


def _bad():
    raise HotelOpsError("Invalid fictional hotel-operations snapshot")

def _day(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        _bad()
    try:
        d = date.fromisoformat(value)
    except ValueError:
        _bad()
    return d

def _id(value):
    if not isinstance(value, str) or _F.fullmatch(value) is None:
        _bad()
    return value

def _amount(value, *, positive=False):
    if not isinstance(value, str) or not re.fullmatch(r"(?:0|[1-9]\d{0,9})\.\d{2}", value):
        _bad()
    try:
        n = Decimal(value)
    except InvalidOperation:
        _bad()
    if positive and n <= 0:
        _bad()
    return n

def _unique(rows, field):
    result = [_id(row[field]) for row in rows]
    if len(result) != len(set(result)):
        _bad()
    return set(result)

def _dict_array(v, length):
    if not isinstance(v, list) or len(v) > length or any(not isinstance(x, dict) for x in v):
        _bad()
    return v

def _guard_guest(guest):
    # Synthetic demo may show identity field *definitions*, not actual documents.
    allowed = {"id","surname","given_name","identity_type","country",
               "preferred_language","title","gender","identity_number",
               "turkish_national_id","birth_place","date_of_birth","address",
               "telephone","email","privacy_status"}
    if set(guest) != allowed or guest["privacy_status"] != "NO_REAL_PERSONAL_DATA":
        _bad()
    if any(guest[k] is not None for k in
           ("identity_number","turkish_national_id","birth_place","date_of_birth",
            "address","telephone","email")):
        _bad()
    if guest["identity_type"] not in DOC_TYPES:
        _bad()
    if guest["country"] not in {"TR", "DE", "FR", "GB", "GR", "IL", "SA", "RU",
                               "ES", "UA", "US", "IT", "PT", "CN", "JP"}:
        _bad()
    if not str(guest["surname"]).startswith("DEMO_") or guest["given_name"] != "ÖRNEK":
        _bad()


def validate_fictional_hotel(data):
    """Canonical copy: reject unexpected fields and unsafe sample identities."""
    if not isinstance(data, dict) or set(data) != _ALLOW_TOP:
        _bad()
    try:
        x = deepcopy(data)
    except (TypeError, RecursionError, ValueError):
        _bad()
    if (x["schema_version"] != "0.5-fiction-only" or x["fictional"] is not True
        or x["privacy_policy"] != "SYNTHETIC_NO_REAL_IDENTITIES"):
        _bad()
    _id(x["property_id"]); _day(x["as_of"])
    if x["default_currency"] != "TRY":
        _bad()
    rooms = _dict_array(x["rooms"], 500)
    agencies = _dict_array(x["agencies"], 100)
    guests = _dict_array(x["guests"], 1000)
    reservations = _dict_array(x["reservations"], 5000)
    folios = _dict_array(x["folios"], 5000)
    reports = _dict_array(x["report_catalog"], 100)
    room_ids=_unique(rooms,"id")
    agency_ids=_unique(agencies,"id")
    guest_ids=_unique(guests,"id")
    booking_ids=_unique(reservations,"id")
    _unique(folios,"id")
    if (len({r.get("id") for r in reports}) != len(reports)
        or any(not isinstance(r.get("id"),str) or
               re.fullmatch(r"[a-z][a-z_]{1,47}",r["id"]) is None for r in reports)):
        _bad()
    room_map={r["id"]:r for r in rooms}
    for r in rooms:
        if (r["category"] not in CATEGORIES or type(r["capacity"]) is not int
            or not 1 <= r["capacity"] <= 20 or r["bed"] not in {"double","twin","flex","single"}
            or r["housekeeping"] not in {"inspected","dirty","clean","maintenance","out_of_order"}
            or type(r["blocked"]) is not bool or not isinstance(r["assets"],list)
            or any(not isinstance(a,str) or len(a)>48 for a in r["assets"])):
            _bad()
    for a in agencies:
        if (a["type"] not in {"direct","ota","wholesale","agency"}
            or a["settlement_currency"] not in {"EUR","TRY","USD","GBP"}
            or type(a["city_ledger_terms_days"]) is not int
            or not 0 <= a["city_ledger_terms_days"] <= 365):
            _bad()
    for guest in guests: _guard_guest(guest)
    holdings=[]
    for res in reservations:
        if (res["agency_id"] not in agency_ids or res["status"] not in STATUS
            or res["board"] not in BOARD_TYPES or res["payment_type"] not in PAYMENT_TYPES
            or res["commission_type"] not in {"net","commission","none"}
            or res["currency"] not in {"TRY","EUR","USD","GBP"}
            or not isinstance(res["name"],str) or not res["name"].startswith("ÖRNEK")
            or not isinstance(res["rooms"],list) or not 1 <= len(res["rooms"]) <= 12):
            _bad()
        start=_day(res["checkin"]);end=_day(res["checkout"])
        if end<=start or (end-start).days>366: _bad()
        if res["option_expiry"] is not None: _day(res["option_expiry"])
        if res["agency_ref"] is not None: _id(res["agency_ref"])
        for portion in res["rooms"]:
            if (portion["category"] not in CATEGORIES or
                type(portion["adults"]) is not int or type(portion["children"]) is not int or
                not 1 <= portion["adults"] <= 20 or not 0 <= portion["children"] <= 12):
                _bad()
            rid=portion["room_id"]
            if rid is not None:
                if rid not in room_ids: _bad()
                room=room_map[rid]
                if (room["category"]!=portion["category"] or
                    portion["adults"]+portion["children"]>room["capacity"]):
                    _bad()
                if res["status"] in {"confirmed","in_house"}:
                    if room["blocked"]: _bad()
                    holdings.append((rid,start,end))
            if not isinstance(portion["guest_ids"],list) or any(g not in guest_ids for g in portion["guest_ids"]):
                _bad()
            nightly=_dict_array(portion["nightly_rates"],366)
            expected={(start+timedelta(days=i)).isoformat() for i in range((end-start).days)}
            observed=[n["date"] for n in nightly]
            if len(observed)!=len(set(observed)) or set(observed)!=expected:
                _bad()
            for n in nightly: _amount(n["amount"])
    for i,(rid,a,b) in enumerate(holdings):
        for rid2,c,d in holdings[i+1:]:
            if rid==rid2 and max(a,c)<min(b,d): _bad()
    for f in folios:
        if (f["reservation_id"] not in booking_ids or
            f["room_id"] is not None and f["room_id"] not in room_ids or
            f["payer_type"] not in {"agency","guest"} or
            f["status"] not in {"open","closed","void"} or
            f["currency"] not in {"TRY","EUR","USD","GBP"} or
            f["invoice_status"] not in {"not_issued","draft"}):
            _bad()
        if (f["payer_type"]=="agency") != (f["agency_id"] is not None): _bad()
        if f["agency_id"] is not None and f["agency_id"] not in agency_ids: _bad()
        if f["city_ledger_due"] is not None: _day(f["city_ledger_due"])
        posting_ids=set()
        for p in _dict_array(f["postings"],5000):
            if p["id"] in posting_ids: _bad()
            posting_ids.add(_id(p["id"]))
            if p["kind"] not in _POSTINGS: _bad()
            _day(p["date"]);_amount(p["amount"],positive=True)
        payment_ids=set()
        for p in _dict_array(f["payments"],5000):
            if p["id"] in payment_ids: _bad()
            payment_ids.add(_id(p["id"]))
            if p["method"] not in METHODS: _bad()
            _day(p["date"]);_amount(p["amount"],positive=True)
    for item in reports:
        if item["status"] not in _ACCOUNTING_MISSING|{"implemented"}: _bad()
        if (item["status"]=="implemented") != (item["id"] in _SUPPORTED_REPORTS): _bad()
    if set(_SUPPORTED_REPORTS) - {r["id"] for r in reports}: _bad()
    if x["payment_methods"]!=["cash","credit_card","mail_order","bank_transfer"]: _bad()
    for rate in _dict_array(x["fx_rates"],100):
        if rate["to"]!="TRY" or rate["source"]!="FICTIONAL_DEMO_RATE": _bad()
        if _C.fullmatch(rate["currency"]) is None: _bad()
        _day(rate["as_of"])
        if not isinstance(rate["rate"],str) or re.fullmatch(r"\d{1,6}\.\d{4}",rate["rate"]) is None: _bad()
    return x


def _report_rows(snapshot):
    rooms=snapshot["rooms"];bookings=snapshot["reservations"]
    folios=snapshot["folios"];agencies={a["id"]:a for a in snapshot["agencies"]}
    overview=[]
    postings=[];payments=[];receivables=[];price_control=[]
    for res in bookings:
        for item in res["rooms"]:
            for nightly in item["nightly_rates"]:
                price_control.append({"reservation_id":res["id"],"date":nightly["date"],
                                      "room":item["room_id"] or "UNASSIGNED",
                                      "category":item["category"],"amount":nightly["amount"],
                                      "currency":res["currency"]})
    for f in folios:
        debit=sum((_amount(p["amount"]) for p in f["postings"]),Decimal("0.00"))
        credit=sum((_amount(p["amount"]) for p in f["payments"]),Decimal("0.00"))
        balance=debit-credit
        item={"folio_id":f["id"],"reservation_id":f["reservation_id"],
              "room_id":f["room_id"],"payer_type":f["payer_type"],
              "agency":agencies[f["agency_id"]]["name"] if f["agency_id"] else None,
              "agency_legal_name":agencies[f["agency_id"]]["legal_name"] if f["agency_id"] else None,
              "currency":f["currency"],"postings":f"{debit:.2f}",
              "payments":f"{credit:.2f}","balance":f"{balance:.2f}",
              "status":f["status"],"due_date":f["city_ledger_due"],
              "invoice_status":f["invoice_status"],"folio_note":f["explanation"]}
        overview.append(item)
        if f["payer_type"]=="agency" and balance>0 and f["status"]=="open":
            receivables.append(item)
        for p in f["postings"]:
            postings.append({"folio_id":f["id"],"reservation_id":f["reservation_id"],
                             "room_id":f["room_id"],"date":p["date"],"kind":p["kind"],
                             "amount":p["amount"],"currency":f["currency"],
                             "description":p["description"]})
        for p in f["payments"]:
            payments.append({"folio_id":f["id"],"date":p["date"],"method":p["method"],
                             "amount":p["amount"],"currency":f["currency"]})
    return overview,postings,payments,receivables,price_control


def build_operations_report(source):
    """Show only derived synthetic reports; never imply fiscal-compliant mizan."""
    x=validate_fictional_hotel(source)
    overview,postings,payments,receivables,prices=_report_rows(x)
    reports={}
    for entry in x["report_catalog"]:
        reports[entry["id"]]={"id":entry["id"],"label":entry["label"],
                              "status":entry["status"],"rows":[]}
    def put(key, rows): reports[key]["rows"]=rows
    put("active_folios",[f for f in overview if f["status"]=="open"])
    put("folio_analysis",overview)
    put("transactions",postings+payments)
    put("posting_invoice",postings)
    put("detailed_revenue",postings)
    put("room_list",x["rooms"])
    put("room_rate_control",prices)
    put("reservation_list",[{k:v for k,v in r.items() if k!="notes"} for r in x["reservations"]])
    put("guest_list",[{"id":g["id"],"given_name":g["given_name"],"surname":g["surname"],
                       "country":g["country"],"identity_status":"NOT_COLLECTED_DEMO"}
                      for g in x["guests"]])
    put("blockage_report",[r for r in x["rooms"] if r["blocked"] or r["housekeeping"]=="maintenance"])
    put("city_ledger",receivables)
    put("exchange_rates",x["fx_rates"])
    put("extra_bed",[p for p in postings if p["kind"]=="EXTRA_BED"])
    put("advance_payment",[p for p in payments if p["date"]<x["as_of"]])
    put("occupancy",[{"room":r["id"],"occupied_in_snapshot":any(
        r["id"]==part["room_id"] and res["checkin"]<=x["as_of"]<res["checkout"]
        and res["status"]=="in_house" for res in bookings for part in res["rooms"])}
        for r in x["rooms"]])
    balance=defaultdict(lambda: {"debit":Decimal("0.00"),"credit":Decimal("0.00")})
    grouped=defaultdict(lambda:Decimal("0.00"))
    monthly=defaultdict(lambda:Decimal("0.00"))
    agency_monthly=defaultdict(lambda:Decimal("0.00"))
    agency_yearly=defaultdict(lambda:Decimal("0.00"))
    agency_detail=[]
    for f in overview:
        balance[f["currency"]]["debit"]+=Decimal(f["postings"])
        balance[f["currency"]]["credit"]+=Decimal(f["payments"])
    for p in postings:
        grouped[(p["kind"],p["currency"])]+=Decimal(p["amount"])
        monthly[(p["date"][:7],p["currency"])]+=Decimal(p["amount"])
        f=next((v for v in overview if v["folio_id"]==p["folio_id"]),None)
        if f and f["agency"]:
            agency_monthly[(f["agency"],p["date"][:7],p["currency"])]+=Decimal(p["amount"])
            agency_yearly[(f["agency"],p["date"][:4],p["currency"])]+=Decimal(p["amount"])
            agency_detail.append({**p,"agency":f["agency"],"legal_name":f["agency_legal_name"]})
    put("daily_balance",[{"currency":currency,"postings":f"{v['debit']:.2f}",
                          "payments":f"{v['credit']:.2f}",
                          "net":f"{v['debit']-v['credit']:.2f}"} for currency,v in sorted(balance.items())])
    put("monthly_revenue",[{"month":k[0],"currency":k[1],"total":f"{v:.2f}"} for k,v in sorted(monthly.items())])
    put("grouped_transactions",[{"posting_type":k[0],"currency":k[1],"total":f"{v:.2f}"} for k,v in sorted(grouped.items())])
    put("agency_monthly",[{"agency":k[0],"month":k[1],"currency":k[2],"total":f"{v:.2f}"} for k,v in sorted(agency_monthly.items())])
    put("agency_annual",[{"agency":k[0],"year":k[1],"currency":k[2],"total":f"{v:.2f}"} for k,v in sorted(agency_yearly.items())])
    put("agency_sales",agency_detail)
    for item in reports.values():
        if item["status"]!="implemented" and item["rows"]: _bad()
    return {"schema":"konaklamaflow.hotel-ops-report.v1","mode":"READ_ONLY_SYNTHETIC",
            "property_id":x["property_id"],"as_of":x["as_of"],"report_count":len(reports),
            "folios":overview,"city_ledger":receivables,
            "reports":reports,"safety":{"guest_identity_data":False,"pms_writes":False,
            "ota_writes":False,"fiscal_invoices":False,"payments":False,"kbs":False,
            "live_exchange_rates":False,"human_approval_required":True}}


def draft_new_reservation(source, request):
    """Validate a multi-room draft; never assign or save rooms, collect identity, or write PMS."""
    x=validate_fictional_hotel(source)
    if not isinstance(request,dict) or set(request)!={"checkin","checkout","agency_id",
        "board","payment_type","status","rooms"}: _bad()
    checkin=_day(request["checkin"]);checkout=_day(request["checkout"])
    if checkin>=checkout or (checkout-checkin).days>366: _bad()
    if (request["agency_id"] not in {a["id"] for a in x["agencies"]}
        or request["board"] not in BOARD_TYPES
        or request["payment_type"] not in PAYMENT_TYPES
        or request["status"] not in {"confirmed","option","waitlist"}): _bad()
    parts=request["rooms"]
    if not isinstance(parts,list) or not 1<=len(parts)<=12: _bad()
    category_max=defaultdict(int)
    for r in x["rooms"]: category_max[r["category"]]=max(category_max[r["category"]],r["capacity"])
    for part in parts:
        if not isinstance(part,dict) or set(part)!={"category","adults","children"}: _bad()
        category=part["category"]
        if category not in category_max or type(part["adults"]) is not int or type(part["children"]) is not int: _bad()
        total=part["adults"]+part["children"]
        if part["adults"]<1 or part["children"]<0 or total>category_max[category]: _bad()
    ids=[int(r["id"].rsplit("-",1)[1]) for r in x["reservations"] if re.fullmatch(r"KFD-\d{4}-\d{4}",r["id"])]
    return {"reservation_draft_id":f"KFD-{checkin.year}-{max(ids,default=0)+1:04d}",
            "status":"STAFF_REVIEW_REQUIRED_NOT_SAVED",
            "hotel_property":x["property_id"],"room_count":len(parts),
            "total_persons":sum(p["adults"]+p["children"] for p in parts),
            "selected_room_ids":[],"folio_ids":[],"kbs_submitted":False,
            "payment_collected":False,"requires_source_pms_inventory_check":True}
