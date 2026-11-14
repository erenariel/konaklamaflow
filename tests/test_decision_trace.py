"""No production audit claims: only a tamper-evident fictional local chain."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from konaklamaflow.decision_trace import (
    TraceError, empty_trace, append_simulated, fictional_walkthrough, verify_trace,
)
from konaklamaflow.experience_engine import evaluate
from konaklamaflow.trace_cli import main

FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "fictional-hotel.json"


class DecisionTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.report = evaluate(cls.source)

    def test_witness_is_deterministic_non_authorizing_and_minimized(self):
        original_source, original_report = deepcopy(self.source), deepcopy(self.report)
        trace = fictional_walkthrough(self.source, self.report)
        self.assertTrue(verify_trace(self.source, self.report, trace))
        self.assertEqual(trace, fictional_walkthrough(self.source, self.report))
        self.assertEqual(len(trace["events"]), 3)
        self.assertEqual(trace["mode"], "DRY_RUN_ONLY")
        self.assertIn("NO_AUTHORIZATION", trace["boundary"])
        self.assertEqual(self.source, original_source)
        self.assertEqual(self.report, original_report)
        flat = json.dumps(trace)
        for forbidden in ("guest_email", "passport", "phone", "payment_card", "guest_name",
                          "pms_write", "approved_by", "access_token"):
            self.assertNotIn('"' + forbidden + '"', flat)

    def test_all_events_exactly_bound_to_explanations_and_hash(self):
        trace = fictional_walkthrough(self.source, self.report)
        self.assertEqual(trace["events"][0]["sequence"], 1)
        self.assertEqual(trace["events"][1]["previous_hash"],
                         trace["events"][0]["event_hash"])
        self.assertEqual(trace["head_hash"], trace["events"][-1]["event_hash"])
        self.assertEqual(trace["events"][0]["snapshot_sha256"],
                         self.report["snapshot_sha256"])

    def test_tamper_payload_is_rejected(self):
        baseline = fictional_walkthrough(self.source, self.report)
        scenarios = [
            lambda x: x["events"][0].update(simulated_role="manager"),
            lambda x: x["events"][0].update(kind="payment_captured"),
            lambda x: x["events"][0].update(reason_codes=[]),
            lambda x: x["events"][0].update(evidence_field_paths=[]),
            lambda x: x["events"][0].update(previous_hash="f" * 64),
            lambda x: x["events"][0].update(event_hash="e" * 64),
            lambda x: x["events"][0].update(sequence=4),
            lambda x: x["events"][0].update(guest_email="synthetic@example.invalid"),
            lambda x: x.update(head_hash="a" * 64),
            lambda x: x["events"].pop(0),
            lambda x: x["events"].reverse(),
            lambda x: x["events"].append(deepcopy(x["events"][-1])),
            lambda x: x.update(source_validity="LIVE_VERIFIED"),
        ]
        for fn in scenarios:
            candidate = deepcopy(baseline)
            fn(candidate)
            with self.subTest(fn=fn), self.assertRaises(TraceError):
                verify_trace(self.source, self.report, candidate)

    def test_exact_report_and_source_bound(self):
        trace = fictional_walkthrough(self.source, self.report)
        modified = deepcopy(self.report)
        modified["arrivals"][0]["blockers"].append("PAYMENT_REVIEW")
        with self.assertRaises(TraceError):
            verify_trace(self.source, modified, trace)
        modified_source = deepcopy(self.source)
        modified_source["rooms"][0]["capacity"] = 3
        with self.assertRaises(TraceError):
            verify_trace(modified_source, self.report, trace)

    def test_disallowed_role_action_extra_fields_and_replay(self):
        t = empty_trace(self.source, self.report)
        task = self.report["arrivals"][0]["task_id"]
        with self.assertRaises(TraceError):
            append_simulated(self.source, self.report, t, task_id=task,
                             kind="approve_checkin", role="manager",
                             simulated_at="2026-11-12T14:01:00Z")
        with self.assertRaises(TraceError):
            append_simulated(self.source, self.report, t, task_id=task,
                             kind="review_queued", role="manager",
                             simulated_at="2026-11-12T14:01:00Z")
        with self.assertRaises(TraceError):
            append_simulated(self.source, self.report, t, task_id=task,
                             kind="review_queued", role="engine",
                             simulated_at="2026-11-12T99:99:99Z")
        self.assertEqual(t["events"], [])
        one = append_simulated(self.source, self.report, t, task_id=task,
                               kind="review_queued", role="engine",
                               simulated_at="2026-11-12T14:01:00Z")
        with self.assertRaises(TraceError):
            append_simulated(self.source, self.report, one, task_id=task,
                             kind="review_queued", role="engine",
                             simulated_at="2026-11-12T14:01:00Z")
        with self.assertRaises(TraceError):
            append_simulated(self.source, self.report, one, task_id=task,
                             kind="evidence_viewed", role="receptionist",
                             simulated_at="2026-11-12T14:00:00Z")

    def test_external_anchor_can_detect_replaced_head(self):
        trace = fictional_walkthrough(self.source, self.report)
        self.assertTrue(verify_trace(self.source, self.report, trace,
                                     expected_head=trace["head_hash"]))
        with self.assertRaises(TraceError):
            verify_trace(self.source, self.report, trace, expected_head="f" * 64)

    def test_cli_export_verify_and_protected_output(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "trace.json"
            self.assertEqual(main(["--output", str(path)]), 0)
            self.assertEqual(main(["--verify", str(path)]), 0)
            self.assertEqual(path.stat().st_mode & 0o077, 0)
            value = json.loads(path.read_text(encoding="utf-8"))
            value["events"][0]["kind"] = "approve_checkin"
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(main(["--verify", str(path)]), 2)

    def test_cli_refuses_to_overwrite_fixture(self):
        self.assertEqual(main(["--output", str(FIXTURE)]), 2)


if __name__ == "__main__":
    unittest.main()
