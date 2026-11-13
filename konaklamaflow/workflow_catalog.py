"""Vendor-neutral, synthetic hotel workflow and staff-role reference catalog.

Inspired by *publicly described* ElektraWeb, Sistem Otel and Sedna workflows,
not copied UI, proprietary vendor code, or a live product/API integration.
No identity, guest data, credentials or financial writes are possible.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json

ROLE_SCOPES = {
    "reception": ("room_read", "booking_read", "guest_safe_read", "folio_safe_read", "request_draft"),
    "housekeeping": ("room_read", "hk_read", "maintenance_read", "request_draft"),
    "finance": ("folio_safe_read", "ledger_read", "reports_read", "request_draft"),
    "manager": ("room_read", "booking_read", "guest_safe_read", "folio_safe_read",
                "hk_read", "maintenance_read", "ledger_read", "reports_read",
                "review_requests", "request_draft"),
    "auditor": ("room_read", "booking_read", "folio_safe_read", "ledger_read",
                "reports_read", "audit_read"),
}
PRINCIPALS = (
    {"staff_id": "DEMO-REC-001", "login_id": "sample.reception",
     "display_name": "Sample Reception", "role": "reception", "department": "Front Office"},
    {"staff_id": "DEMO-HK-002", "login_id": "sample.housekeeping",
     "display_name": "Sample Housekeeping", "role": "housekeeping", "department": "Housekeeping"},
    {"staff_id": "DEMO-FIN-003", "login_id": "sample.finance",
     "display_name": "Sample Finance", "role": "finance", "department": "Accounting"},
    {"staff_id": "DEMO-MGR-004", "login_id": "sample.manager",
     "display_name": "Sample Manager", "role": "manager", "department": "Management"},
    {"staff_id": "DEMO-AUD-005", "login_id": "sample.auditor",
     "display_name": "Sample Auditor", "role": "auditor", "department": "Internal Audit"},
)
VENDORS = (
    {"id": "elektraweb", "name": "ElektraWeb", "source":
     "https://yardim.elektraweb.com/detayli-anlatim/onburo-kontrol-paneli",
     "integration": "NOT_CONNECTED"},
    {"id": "sistemotel", "name": "Sistem Otel", "source":
     "https://sistemotel.gitbook.io/sistem-otel-kullanim-klavuzu/sistem_otel_programi_rezervasyon/31_rezervasyon_olusturma",
     "integration": "NOT_CONNECTED"},
    {"id": "sedna", "name": "Sedna (Kod Yazılım)", "source":
     "https://kod.com.tr/Product/SednaHotel",
     "integration": "NOT_CONNECTED"},
)
# Structured, original design: no source text is copied from vendor handbooks.
FLOWS = (
    ("reservation_intake", "Rezervasyon ve grup taslağı",
     "Confirm channel identity, hotel scope, stay dates, category capacity and option deadline.",
     ("channel_reference", "arrival_departure", "room_capacity", "staff_review"),
     ("reception", "manager"), "STAFF_REVIEW"),
    ("room_blocking", "Oda planı ve blokaj",
     "Compare overlapping inventory holds, housekeeping and maintenance without assigning rooms.",
     ("overlap_check", "maintenance", "housekeeping", "category_match"),
     ("reception", "housekeeping", "manager"), "STAFF_REVIEW"),
    ("arrival_preflight", "Giriş hazırlığı",
     "Require verified arrival date, room inspection, identity authority and folio account.",
     ("identity_review", "room_readiness", "folio_review", "arrival_time"),
     ("reception", "manager"), "STAFF_REVIEW"),
    ("checkout_preflight", "Çıkış ve bakiye kontrolü",
     "Check open room/master folio balances and account routing; no checkout is performed.",
     ("departure", "folio_balance", "agency_receivable", "invoice_review"),
     ("reception", "finance", "manager"), "STAFF_REVIEW"),
    ("folio_postings", "Folyo ve harcama incelemesi",
     "Review room, minibar, restaurant and extra charges, refunds and transfer audit.",
     ("posting_types", "payment_separation", "currency", "reconciliation"),
     ("finance", "manager"), "STAFF_REVIEW"),
    ("agency_credit", "Acenteler ve City Ledger",
     "Separate agency receivables from collected payments, validate legal name and due date.",
     ("legal_entity", "credit_terms", "invoice_policy", "aging"),
     ("finance", "manager"), "STAFF_REVIEW"),
    ("night_audit", "Gün sonu ve audit",
     "Check expected arrivals/departures, missing rates, open tasks, folio balances and audit lock.",
     ("arrivals", "departures", "zero_rate", "trial_balance", "audit_lock"),
     ("finance", "manager"), "MISSING_TRUSTED_SOURCE"),
    ("housekeeping", "Kat hizmetleri ve teknik bakım",
     "Keep housekeeping inspected/dirty state separate from maintenance out-of-order holds.",
     ("room_cleanliness", "work_orders", "stock", "supervisor_check"),
     ("housekeeping", "manager"), "STAFF_REVIEW"),
    ("rate_contracts", "Fiyat, kontenjan ve allotment",
     "Check agency-specific dates, release limits, commission and stop-sale conditions.",
     ("agency_rates", "release_day", "stop_sale", "room_nights"),
     ("reception", "manager"), "MISSING_TRUSTED_SOURCE"),
    ("guest_profile", "Misafir profili ve veri koruma",
     "List only required fields; request legal basis and least-privilege controls before PII access.",
     ("identity_minimization", "purpose", "retention", "role_scope"),
     ("reception", "manager"), "AUTHORIZATION_REQUIRED"),
    ("invoicing", "Fatura ve mali uyum",
     "Separate folio posting preview from fiscal invoice issuance and tax/currency validation.",
     ("invoice_region", "tax_rules", "exchange_source", "fiscal_authority"),
     ("finance", "manager"), "MISSING_TRUSTED_SOURCE"),
    ("analytics", "Doluluk, bütçe ve performans",
     "Summarize synthetic rate/room performance without inventing real occupancy or accounting.",
     ("room_nights", "rate_plan", "agency_segments", "budget"),
     ("finance", "manager", "auditor"), "STAFF_REVIEW"),
    ("handover", "Personel devri ve görevler",
     "Prepare explanatory task drafts with accountable owner and no external notification.",
     ("task_owner", "source_revision", "shift_handover", "audit_trace"),
     ("reception", "housekeeping", "finance", "manager"), "STAFF_REVIEW"),
    ("external_integrations", "PMS, OTA, KBS entegrasyon sınırı",
     "Classify each external action as disconnected until vendor credentials, consent, audit and API contract.",
     ("api_permissions", "least_privilege", "sandbox", "human_approval"),
     ("manager", "auditor"), "AUTHORIZATION_REQUIRED"),
)
FLOW_CODES = {f[0] for f in FLOWS}
BLOCKED_ACTIONS = ("checkin", "checkout", "pms_write", "kbs_submit",
                   "charge_card", "mail_order", "invoice_issue", "guest_message_send",
                   "identity_upload", "vendor_api", "log_export")


class WorkflowPermissionError(ValueError):
    """Demo-only authorization guard; never usable as production auth."""


def role_preview(staff_id: str) -> dict:
    """An informational role snapshot, not a token or real login."""
    person = next((x for x in PRINCIPALS if x["staff_id"] == staff_id), None)
    if not person:
        raise WorkflowPermissionError("Unknown demo operator")
    return {**person, "scopes": list(ROLE_SCOPES[person["role"]]),
            "authentication": "NOT_AUTHENTICATED_DEMO_IDENTITY",
            "can_execute_real_operations": False}


def request_simulation(staff_id: str, workflow_id: str, action: str) -> dict:
    """Fail closed for all real actions; safe plan contains no personal data."""
    principal = role_preview(staff_id)
    if not isinstance(workflow_id, str) or workflow_id not in FLOW_CODES:
        raise WorkflowPermissionError("Unknown workflow")
    if action != "preview":
        raise WorkflowPermissionError("Actions require a real authenticated service")
    flow = next(f for f in FLOWS if f[0] == workflow_id)
    if principal["role"] not in flow[4]:
        raise WorkflowPermissionError("Role cannot preview this workflow")
    content = {"id": flow[0], "name": flow[1], "description": flow[2],
               "checks": list(flow[3]), "owner_roles": list(flow[4]),
               "status": flow[5], "source_type": "SYNTHETIC_NOT_VERIFIED"}
    return {
        "schema": "konaklamaflow.workflow-draft.v1",
        "operator_id": principal["staff_id"],
        "workflow": content,
        "requires_human_approval": True,
        "real_actions_enabled": False,
        "source_verified": False,
        "next_step": "VERIFY_REAL_SOURCE_AND_AUTHORIZED_OPERATOR",
    }


def public_catalog() -> dict:
    """Machine-readable UI/source catalog, with intentionally fictional operators."""
    data = {"schema": "konaklamaflow.public-workflows.v1",
            "mode": "OFFLINE_READ_ONLY_DEMO",
            "personnel": [role_preview(x["staff_id"]) for x in PRINCIPALS],
            "vendors": list(VENDORS),
            "flows": [{
                 "id": f[0], "name": f[1], "description": f[2],
                 "checks": list(f[3]), "roles": list(f[4]), "status": f[5],
                 "source_type": "SYNTHETIC_NOT_VERIFIED",
                 "human_approval_required": True
            } for f in FLOWS],
            "prohibited_live_actions": list(BLOCKED_ACTIONS),
            "policy": {"pii_allowed": False, "network": False, "pms_writes": False,
                       "payment_collection": False, "kbs": False,
                       "real_authentication": False, "human_approval_required": True}}
    data["integrity_sha256"] = sha256(json.dumps(
        {k:v for k,v in data.items() if k!="integrity_sha256"},
        ensure_ascii=True, sort_keys=True, separators=(",",":")
    ).encode()).hexdigest()
    return data
