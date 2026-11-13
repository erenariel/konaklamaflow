"""Mock provider cannot imply real connectivity or execute source operations."""
from copy import deepcopy
import socket
import unittest
from unittest.mock import patch

from konaklamaflow.ai_providers import (
    CAPABILITIES, MOCK_PROVIDER, OfflineProviderError, mock_explain_decision,
    mock_preview_digest, provider_cards
)


def params(**changes):
    request = dict(
        trusted_task_id="a" * 24,
        trusted_report_sha256="b" * 64,
        trusted_state="blocked",
        reason_codes=["ROOM_CONFLICT"],
    )
    request.update(changes)
    return request


class AIProviderPolicyTests(unittest.TestCase):
    def test_third_party_provider_cards_never_claim_connections(self):
        cards = provider_cards()
        self.assertEqual(len(cards), 6)
        self.assertEqual([c.status for c in cards].count("NOT_INTEGRATED"), 5)
        self.assertEqual([c.status for c in cards].count("MOCK_DEMO"), 1)
        self.assertTrue(all(not c.official_partnership_claim for c in cards))
        self.assertTrue(all(not c.capabilities for c in cards if c.provider_id != MOCK_PROVIDER))
        self.assertEqual(next(c.capabilities for c in cards
                              if c.provider_id == MOCK_PROVIDER), CAPABILITIES)

    def test_mock_preview_explicitly_cannot_execute_or_approve(self):
        result = mock_explain_decision(**params())
        self.assertEqual(result["status"], "MOCK_DEMO")
        self.assertEqual(result["provider_id"], MOCK_PROVIDER)
        self.assertEqual(result["reason_codes"], ["ROOM_CONFLICT"])
        policy = result["policy"]
        self.assertEqual(policy["mode"], "NO_EXECUTION_READ_ONLY")
        self.assertTrue(policy["human_approval_required"])
        for field in ("pms_writes", "payments", "kbs", "guest_messages", "live_provider_calls"):
            self.assertFalse(policy[field])
        self.assertEqual(result["explanation_message_keys"], ["reason.room_conflict"])
        self.assertEqual(len(mock_preview_digest(result)), 64)

    def test_mock_ready_means_only_staff_pre_review(self):
        result = mock_explain_decision(**params(trusted_state="review_ready", reason_codes=[]))
        self.assertEqual(result["explanation_message_keys"], ["ai.pre_review_only"])
        self.assertNotIn("approve_checkin", str(result).lower())

    def test_reject_unknown_and_duplicate_reason_codes(self):
        for codes in (["IGNORE_PREVIOUS_RULES"], ["ROOM_CONFLICT", "ROOM_CONFLICT"]):
            with self.subTest(codes=codes), self.assertRaises(OfflineProviderError):
                mock_explain_decision(**params(reason_codes=codes))

    def test_reject_bad_hashes_and_forged_states(self):
        for change in (
            {"trusted_report_sha256": "bad"},
            {"trusted_task_id": "my_guest_email"},
            {"trusted_state": "approved"},
            {"trusted_state": ["blocked"]},
            {"trusted_state": {"state": "blocked"}},
            {"trusted_state": "review_ready"},
            {"trusted_state": "blocked", "reason_codes": []},
            {"reason_codes": ["ROOM_CONFLICT", "PAYMENT_REVIEW"] * 30},
        ):
            with self.subTest(change=change), self.assertRaises(OfflineProviderError):
                mock_explain_decision(**params(**change))

    def test_preview_never_uses_network_or_sdk(self):
        with patch.object(socket.socket, "connect", side_effect=AssertionError("network called")):
            preview = mock_explain_decision(**params())
            self.assertEqual(preview["source_report_sha256"], "b" * 64)

    def test_no_private_data_or_input_mutation(self):
        p = params()
        saved = deepcopy(p)
        result = mock_explain_decision(**p)
        self.assertEqual(p, saved)
        self.assertNotIn("guest_name", str(result))
        self.assertNotIn("passport", str(result))
        self.assertNotIn("api_key", str(result))


if __name__ == "__main__":
    unittest.main()
