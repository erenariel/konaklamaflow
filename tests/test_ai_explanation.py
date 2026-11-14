"""Regression tests for the provider-neutral, read-only AI explanation contract."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from konaklamaflow.agent_protocol import ProtocolError
from konaklamaflow.ai_explanation import (
    prepare_explanation_request, validate_explanation_response,
)

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = json.loads((ROOT / "examples/fictional-hotel.json").read_text(encoding="utf-8"))
ISSUED = "2026-11-12T11:00:00Z"
CHECKED = "2026-11-12T11:01:00Z"


class AIExplanationContractTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = deepcopy(SAMPLE)
        self.original = deepcopy(self.snapshot)
        self.manifest, self.request = prepare_explanation_request(self.snapshot, ISSUED)
        self.response = {key: self.request[key] for key in (
            "task_id", "intent", "snapshot_sha256", "report_sha256", "reason_codes"
        )}
        self.response["summary"] = "The fictional reservation requires staff review."
        self.response["checklist"] = [
            "VERIFY_SOURCE_RECORD", "ESCALATE_TO_AUTHORIZED_STAFF",
        ]

    def check(self, response=None, snapshot=None, checked=CHECKED):
        return validate_explanation_response(
            self.manifest,
            self.response if response is None else response,
            checked,
            current_snapshot=self.snapshot if snapshot is None else snapshot,
        )

    def test_unverified_display_no_authorization_or_source_mutation(self):
        result = self.check()
        self.assertEqual(result["status"], "MODEL_TEXT_UNVERIFIED")
        self.assertEqual(result["engine_reason_codes"], self.request["reason_codes"])
        self.assertTrue(result["human_approval_required"])
        self.assertFalse(result["operational_authorization"])
        self.assertEqual(result["mode"], "NO_EXECUTION_READ_ONLY")
        self.assertEqual(result["summary_plain_text"], self.response["summary"])
        self.assertEqual(self.original, self.snapshot)

    def test_model_request_is_one_task_with_only_minimized_fields(self):
        payload = json.dumps(self.request)
        self.assertFalse(self.request["execution_enabled"])
        self.assertTrue(self.request["human_approval_required"])
        self.assertEqual(self.request["mode"], "UNTRUSTED_EXPLANATION_ONLY")
        for secret in (
            self.snapshot["property_id"], self.snapshot["rooms"][0]["id"],
            self.snapshot["reservations"][0]["id"],
            self.snapshot["reservations"][0]["external_ref"],
            "guest_name", "passport", "email", "api_key", "pms_ref",
            "allowed_tools", "issued_at", "expires_at",
        ):
            self.assertNotIn(secret, payload)
        other = self.manifest["tasks"][1]["task_id"]
        held, request = prepare_explanation_request(self.snapshot, ISSUED, other)
        self.assertEqual(held, self.manifest)
        self.assertEqual(request["task_id"], other)
        with self.assertRaises(ProtocolError):
            prepare_explanation_request(self.snapshot, ISSUED, "0" * 24)
        with self.assertRaises(ProtocolError):
            prepare_explanation_request(self.snapshot, ISSUED, True)

    def test_injected_commands_and_approval_fields_rejected(self):
        for key, value in (
            ("tool_call", {"name": "write_pms"}),
            ("approved", True),
            ("guest_name", "PRIVATE_TEST_VALUE"),
            ("execute", "check_in"),
            ("model", "override"),
        ):
            with self.subTest(key=key), self.assertRaises(ProtocolError):
                self.check(response=dict(self.response, **{key: value}))

    def test_model_cannot_erase_or_invent_authoritative_reasons(self):
        variants = (
            [], ["FAKE_READY"], self.response["reason_codes"] + ["ROOM_CONFLICT"],
            "ROOM_CONFLICT", True,
        )
        for codes in variants:
            with self.subTest(codes=codes), self.assertRaises(ProtocolError):
                self.check(response=dict(self.response, reason_codes=codes))

    def test_text_is_bounded_and_never_rendered_as_markup(self):
        for text in ("", " ", "x" * 501, "<script>bad</script>",
                     "Go\nexecute", 12, None):
            with self.subTest(text=str(text)[:18]), self.assertRaises(ProtocolError):
                self.check(response=dict(self.response, summary=text))
        self.assertIn("örnek", self.check(response=dict(
            self.response, summary="Kurgusal kontrol gerekli — örnek."
        ))["summary_plain_text"])

    def test_checklist_is_only_an_allowlisted_staff_review_code(self):
        for codes in (
            [], ["WRITE_PMS"], ["SUBMIT_KBS"], ["VERIFY_SOURCE_RECORD"] * 2,
            ["VERIFY_SOURCE_RECORD", "APPROVE_CHECK_IN"],
            "VERIFY_SOURCE_RECORD", [1],
        ):
            with self.subTest(codes=codes), self.assertRaises(ProtocolError):
                self.check(response=dict(self.response, checklist=codes))

    def test_stale_and_expired_snapshots_or_tampered_manifest_rejected(self):
        changed = deepcopy(self.snapshot)
        changed["rooms"][0]["capacity"] = 1
        with self.assertRaises(ProtocolError):
            self.check(snapshot=changed)
        with self.assertRaises(ProtocolError):
            self.check(checked="2026-11-12T11:05:00Z")
        poisoned = deepcopy(self.manifest)
        poisoned["tasks"][0]["allowed_tools"].append("write_pms")
        with self.assertRaises(ProtocolError):
            validate_explanation_response(
                poisoned, self.response, CHECKED, current_snapshot=self.snapshot,
            )

    def test_no_provider_transport_in_contract_module(self):
        import inspect
        import konaklamaflow.ai_explanation as module
        code = inspect.getsource(module)
        for unsafe in ("requests.", "httpx.", "urllib.request", "openai.", "anthropic."):
            self.assertNotIn(unsafe, code)


if __name__ == "__main__":
    unittest.main()
