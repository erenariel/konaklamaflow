"""Explicitly OFFLINE AI provider registry and fixed explanation preview contract.

No SDKs, network, credentials, secrets, cloud subscription linkage, tools or
execution exist. Provider cards do not constitute partnership or API access.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re

from .experience_engine import BLOCKER_CODES

CAPABILITIES = (
    "explain_decision", "summarize_shift", "draft_guest_message", "prepare_handoff_summary"
)
MOCK_PROVIDER = "konaklamaflow-offline-mock"
STATUS = {"NOT_INTEGRATED", "MOCK_DEMO", "DISABLED"}
PROVIDER_NAMES = {
    "openai-api": "OpenAI API",
    "anthropic-api": "Anthropic API",
    "gemini-api": "Google Gemini API",
    "azure-openai": "Azure OpenAI",
    "local-model": "Self-hosted model",
    MOCK_PROVIDER: "KonaklamaFlow offline illustration",
}
_DIGEST = re.compile(r"^[a-f0-9]{64}$")
_TASK = re.compile(r"^[a-f0-9]{24}$")
_ALLOWED_STATE = {"blocked", "review_ready", "other"}
_ONLY_REVIEW_POLICY = {
    "mode": "NO_EXECUTION_READ_ONLY",
    "live_provider_calls": False,
    "pms_writes": False,
    "payments": False,
    "kbs": False,
    "guest_messages": False,
    "human_approval_required": True,
}


class OfflineProviderError(ValueError):
    """Invalid request, with no untrusted contents echoed."""


@dataclass(frozen=True)
class ProviderCard:
    provider_id: str
    display_name: str
    status: str
    capabilities: tuple[str, ...]
    official_partnership_claim: bool = False


def provider_cards() -> tuple[ProviderCard, ...]:
    """Public demo must never pretend to be connected to a third party."""
    result = []
    for pid, display in PROVIDER_NAMES.items():
        is_mock = pid == MOCK_PROVIDER
        result.append(ProviderCard(pid, display,
            "MOCK_DEMO" if is_mock else "NOT_INTEGRATED",
            CAPABILITIES if is_mock else (),
            False))
    return tuple(result)


def mock_explain_decision(*, trusted_task_id: str, trusted_report_sha256: str,
                          trusted_state: str, reason_codes: list[str]) -> dict:
    """Show fixed *translation keys* from rule reasons, not AI-generated decisions.

    The caller is responsible for sourcing these arguments from a verified,
    current, trusted rule report. This function is NOT a credential, approval,
    upstream source verification, or claim of a real model call.
    """
    if (not isinstance(trusted_task_id, str) or not _TASK.fullmatch(trusted_task_id)
            or not isinstance(trusted_report_sha256, str)
            or not _DIGEST.fullmatch(trusted_report_sha256)
            or trusted_state not in _ALLOWED_STATE
            or not isinstance(reason_codes, list)
            or len(reason_codes) > len(BLOCKER_CODES)
            or any(not isinstance(code, str) or code not in BLOCKER_CODES for code in reason_codes)
            or len(reason_codes) != len(set(reason_codes))
            or (trusted_state == "blocked") != bool(reason_codes)
            or (trusted_state == "review_ready" and reason_codes)):
        raise OfflineProviderError("Invalid minimized offline explanation request")

    return {
        "schema": "konaklamaflow.offline-ai-preview.v1",
        "provider_id": MOCK_PROVIDER,
        "status": "MOCK_DEMO",
        "banner_key": "ai.mock_not_connected",
        "source_report_sha256": trusted_report_sha256,
        "task_id": trusted_task_id,
        "state": trusted_state,
        "reason_codes": list(reason_codes),
        "explanation_message_keys": ["reason." + c.lower() for c in reason_codes]
                                    if reason_codes else ["ai.pre_review_only"],
        "next_action_key": "ai.ask_authorized_staff_to_review",
        "human_boundary": "STAFF_REVALIDATION_IN_AUTHORIZED_PMS",
        "policy": dict(_ONLY_REVIEW_POLICY),
    }


def mock_preview_digest(preview: dict) -> str:
    """Fingerprint a preview for local visual regression; NOT authentication."""
    if not isinstance(preview, dict) or preview.get("schema") != "konaklamaflow.offline-ai-preview.v1":
        raise OfflineProviderError("Invalid offline preview format")
    try:
        return sha256(json.dumps(preview, sort_keys=True, allow_nan=False,
                                 separators=(",", ":")).encode()).hexdigest()
    except (TypeError, ValueError, RecursionError, OverflowError):
        raise OfflineProviderError("Invalid offline preview format") from None
