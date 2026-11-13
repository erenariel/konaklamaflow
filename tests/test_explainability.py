"""Evidence explanations are non-authorizing and tied to a full source report."""
from copy import deepcopy
from pathlib import Path
import json
import unittest

from konaklamaflow.explainability import (
    BLOCKER_CODES, EVIDENCE, REASON_ACTIONS, ExplanationError,
    build_explanations, POLICY_BOUNDARY
)
from konaklamaflow.experience_engine import evaluate

ROOT = Path(__file__).resolve().parents[1]


class ExplainabilityTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads((ROOT / "examples/fictional-hotel.json").read_text())
        self.report = evaluate(self.source)

    def test_all_existing_blockers_have_explicit_safe_evidence_and_staff_action(self):
        self.assertEqual(set(EVIDENCE), BLOCKER_CODES)
        self.assertEqual(set(REASON_ACTIONS), BLOCKER_CODES)
        for code in BLOCKER_CODES:
            self.assertTrue(EVIDENCE[code])
            self.assertTrue(REASON_ACTIONS[code])
            self.assertTrue(all(path[0].isalpha() for path in EVIDENCE[code]))

    def test_full_report_parity_and_no_mutations(self):
        source_before, report_before = deepcopy(self.source), deepcopy(self.report)
        out = build_explanations(self.source, self.report)
        self.assertEqual(source_before, self.source)
        self.assertEqual(report_before, self.report)
        self.assertEqual(out["mode"], "NO_EXECUTION_READ_ONLY")
        self.assertEqual(out["source_validity"], "UNVERIFIED_MINIMIZED_SNAPSHOT")
        self.assertIsNone(out["source_revision"])
        self.assertIsNone(out["source_captured_at"])
        self.assertEqual(out["human_approval_boundary"], POLICY_BOUNDARY)
        self.assertEqual(out, build_explanations(self.source, self.report))

    def test_explanation_follows_authoritative_blockers(self):
        out = build_explanations(self.source, self.report)
        self.assertEqual(len(out["arrivals"]), len(self.report["arrivals"]))
        for raw, explained in zip(self.report["arrivals"], out["arrivals"]):
            self.assertEqual(raw["task_id"], explained["task_id"])
            self.assertEqual(raw["status"], explained["state"])
            self.assertEqual(raw["blockers"], [reason["reason_code"] for reason in explained["reasons"]])
            self.assertEqual(explained["ready_means"], "PRE_REVIEW_ONLY_NOT_CHECKIN")
            for reason in explained["reasons"]:
                self.assertTrue(reason["human_approval_required"])
                self.assertEqual(reason["source_validity"], "UNVERIFIED_MINIMIZED_SNAPSHOT")
                self.assertEqual(reason["message_key"], "reason." + reason["reason_code"].lower())
                self.assertTrue(all(x.startswith(("rooms[].", "reservations[].",
                    "channel_events[].", "tasks[].", "as_of", "at_time",
                    "engine_report.")) for x in reason["evidence_field_paths"]))

    def test_stale_and_forged_reports_are_rejected_without_echo(self):
        s = deepcopy(self.source)
        s["rooms"][0]["capacity"] = s["rooms"][0]["capacity"] + 1
        with self.assertRaisesRegex(ExplanationError, "stale"):
            build_explanations(s, self.report)
        fake = deepcopy(self.report)
        fake["arrivals"][0]["blockers"].append("NOT_CONFIRMED")
        with self.assertRaises(ExplanationError):
            build_explanations(self.source, fake)
        with self.assertRaises(ExplanationError):
            build_explanations(self.source, {})
        with self.assertRaises(ExplanationError):
            build_explanations(self.source, None)

    def test_no_sensitive_values_in_explanation(self):
        out = build_explanations(self.source, self.report)
        flat = json.dumps(out, sort_keys=True)
        for booking in self.source["reservations"]:
            # Guest/source-facing identifiers are never forwarded to the read-only handoff.
            for name in ("external_ref", "pms_ref", "id", "room_id"):
                value = booking.get(name)
                if value is not None and len(str(value)) >= 5:
                    self.assertNotIn('"' + str(value) + '"', flat)
        for forbidden in ("email", "passport", "phone", "credit_card", "payment_card",
                          "approve_checkin", "pms_write", "guest_name"):
            self.assertNotIn('"' + forbidden + '"', flat)

    def test_invalid_raw_snapshot_fails_privately(self):
        s = deepcopy(self.source)
        s["reservations"][0]["unexpected_guest_note"] = "VERY_PRIVATE_DATA"
        with self.assertRaises(ExplanationError) as caught:
            build_explanations(s, self.report)
        self.assertNotIn("VERY_PRIVATE_DATA", str(caught.exception))

    def test_source_identity_cannot_prove_live_review(self):
        out = build_explanations(self.source, self.report)
        self.assertEqual(out["authoritative_decision"], "PYTHON_RULE_ENGINE_ONLY")
        self.assertTrue(all(row["human_approval_boundary"] == POLICY_BOUNDARY for row in out["arrivals"]))


if __name__ == "__main__":
    unittest.main()
