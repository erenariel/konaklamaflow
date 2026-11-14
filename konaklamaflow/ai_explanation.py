"""Offline, provider-neutral boundary for untrusted AI explanations.

This module never calls a provider, dispatches tools, authorizes an operation,
or reads/writes PMS, KBS, payment, identity or guest communication systems.
The deterministic Python report remains the sole source of rule decisions.
"""
from __future__ import annotations

from typing import Any

from .agent_protocol import ProtocolError
from .suite_agent_protocol import make_suite_handoff, verify_suite_suggestion

_CHECKLIST = frozenset({
    "VERIFY_SOURCE_RECORD",
    "VERIFY_ROOM_AND_HOUSEKEEPING",
    "VERIFY_REQUESTS_WITH_STAFF",
    "ESCALATE_TO_AUTHORIZED_STAFF",
})
_RESPONSE_KEYS = frozenset({
    "task_id", "intent", "snapshot_sha256", "report_sha256",
    "reason_codes", "summary", "checklist",
})
_REFERENCE_KEYS = ("task_id", "intent", "snapshot_sha256", "report_sha256")


def prepare_explanation_request(
    trusted_snapshot: Any,
    issued_at: str,
    task_id: str | None = None,
    *,
    validity_seconds: int = 300,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (private trusted manifest, minimal model request) for one task.

    Never send the manifest or original snapshot to an AI provider.
    """
    manifest = make_suite_handoff(trusted_snapshot, issued_at, validity_seconds)
    if not manifest["tasks"]:
        raise ProtocolError("No eligible review task")
    if task_id is not None and (type(task_id) is not str or not task_id):
        raise ProtocolError("Invalid task reference")
    selected = next(
        (task for task in manifest["tasks"]
         if task["task_id"] == (task_id or manifest["tasks"][0]["task_id"])),
        None,
    )
    if selected is None:
        raise ProtocolError("Unknown review task")
    request = {
        "schema": "konaklamaflow.ai-explanation-request.v1",
        "mode": "UNTRUSTED_EXPLANATION_ONLY",
        "task_id": selected["task_id"],
        "intent": selected["intent"],
        "state": selected["state"],
        "reason_codes": list(selected["reason_codes"]),
        "snapshot_sha256": manifest["snapshot_sha256"],
        "report_sha256": manifest["report_sha256"],
        "allowed_checklist_codes": sorted(_CHECKLIST),
        "max_summary_chars": 500,
        "human_approval_required": True,
        "execution_enabled": False,
        "instruction": (
            "Explain only supplied rule reason codes. Do not invent evidence, "
            "claim authorization, approve check-in, contact a guest, ask for "
            "secrets, or execute operations. Return strictly structured JSON."
        ),
    }
    return manifest, request


def validate_explanation_response(
    retained_manifest: Any,
    model_response: Any,
    checked_at: str,
    *,
    current_snapshot: Any,
) -> dict[str, Any]:
    """Check AI wording against freshly reevaluated, trusted engine output.

    A validated explanation is UNVERIFIED model text, never staff approval.
    Display plain text using textContent, not HTML or Markdown rendering.
    """
    if not isinstance(model_response, dict) or set(model_response) != _RESPONSE_KEYS:
        raise ProtocolError("Invalid explanation response shape")
    if any(type(model_response.get(key)) is not str for key in _REFERENCE_KEYS):
        raise ProtocolError("Invalid explanation reference")
    verify_suite_suggestion(
        retained_manifest,
        {key: model_response[key] for key in _REFERENCE_KEYS},
        checked_at,
        current_snapshot=current_snapshot,
    )
    task = next(
        task for task in retained_manifest["tasks"]
        if task["task_id"] == model_response["task_id"]
    )
    codes = model_response["reason_codes"]
    if not isinstance(codes, list) or codes != task["reason_codes"] or any(
        type(code) is not str for code in codes
    ):
        raise ProtocolError("Explanation cannot change engine reason codes")
    summary = model_response["summary"]
    if (type(summary) is not str or not summary.strip()
            or len(summary) > 500 or not summary.isprintable()
            or "<" in summary or ">" in summary):
        raise ProtocolError("Unsafe or invalid explanation text")
    checklist = model_response["checklist"]
    if (not isinstance(checklist, list) or not 1 <= len(checklist) <= 4
            or any(type(code) is not str or code not in _CHECKLIST for code in checklist)
            or len(set(checklist)) != len(checklist)):
        raise ProtocolError("Unsupported explanation checklist")
    return {
        "status": "MODEL_TEXT_UNVERIFIED",
        "mode": "NO_EXECUTION_READ_ONLY",
        "task_id": task["task_id"],
        "engine_state": task["state"],
        "engine_reason_codes": list(task["reason_codes"]),
        "summary_plain_text": summary,
        "review_checklist_codes": list(checklist),
        "human_approval_required": True,
        "operational_authorization": False,
        "display_warning": (
            "AI-generated wording is unverified. Original Python rule "
            "results and authorized staff review take precedence."
        ),
    }
