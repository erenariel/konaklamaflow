"""Offline benchmark tests: fail closed for wrong labels, attribution and reports."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from konaklamaflow.evaluation import (
    DEFAULT_MANIFEST, SOURCE_FIXTURE, EvaluationError, _prediction,
    main, render_markdown, run_evaluation, score,
)
from konaklamaflow.experience_engine import evaluate


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        cls.source = json.loads(SOURCE_FIXTURE.read_text(encoding="utf-8"))

    def test_actual_synthetic_scenarios_and_coverage(self):
        result = run_evaluation(self.manifest, self.source)
        self.assertEqual(result["mode"], "DRY_RUN_ONLY")
        self.assertEqual(result["result"], "pass")
        self.assertEqual(result["summary"]["total_cases"], 10)
        self.assertEqual(result["summary"]["evaluated"], 7)
        self.assertEqual(result["summary"]["unsupported"], 2)
        self.assertEqual(result["summary"]["unlabelled"], 1)
        self.assertEqual(result["metrics"]["tp"], 5)
        self.assertEqual(result["metrics"]["tn"], 2)
        self.assertEqual(result["metrics"]["fp"], 0)
        self.assertEqual(result["metrics"]["fn"], 0)
        self.assertEqual(result["human_override_rate"], "not_measured")

    def test_input_immutable_and_repeatable(self):
        original_manifest = deepcopy(self.manifest)
        original_source = deepcopy(self.source)
        first = run_evaluation(self.manifest, self.source)
        second = run_evaluation(self.manifest, self.source)
        self.assertEqual(first, second)
        self.assertEqual(self.manifest, original_manifest)
        self.assertEqual(self.source, original_source)

    def test_false_positive_and_false_negative_are_failures(self):
        result = score([(True, False), (False, True)])
        self.assertEqual((result["tp"], result["fp"], result["tn"], result["fn"]),
                         (0, 1, 0, 1))
        self.assertEqual(result["precision"], 0)
        self.assertEqual(result["recall"], 0)
        self.assertEqual(result["false_positive_rate"], 1)
        self.assertEqual(result["false_negative_rate"], 1)

    def test_zero_denominators_are_null_not_zero(self):
        result = score([])
        for field in ("precision", "recall", "false_positive_rate",
                      "false_negative_rate"):
            self.assertIsNone(result[field])
            self.assertTrue(result["undefined_metrics"][field])

    def test_wrong_label_causes_failure(self):
        manifest = deepcopy(self.manifest)
        manifest["cases"][0]["expected"] = False
        result = run_evaluation(manifest, self.source)
        self.assertEqual(result["result"], "fail")
        self.assertEqual(result["metrics"]["fp"], 1)
        self.assertEqual(result["summary"]["failed_labeled_cases"], 1)

    def test_wrong_reservation_attribution_rejected(self):
        report = evaluate(self.source)
        self.assertFalse(_prediction(report, "KF1010", "CANCELLED_ASSIGNED"))
        report["arrivals"][0]["blockers"].append("CANCELLED_ASSIGNED")
        self.assertTrue(_prediction(report, "KF1001", "CANCELLED_ASSIGNED"))
        self.assertFalse(_prediction(report, "KF1010", "CANCELLED_ASSIGNED"))

    def test_unknown_code_in_output_fails_closed(self):
        report = evaluate(self.source)
        report["arrivals"][0]["blockers"].append("NOT_A_REAL_REASON")
        with self.assertRaises(EvaluationError):
            _prediction(report, "KF1001", "ROOM_CONFLICT")

    def test_unknown_label_in_manifest_fails_closed(self):
        manifest = deepcopy(self.manifest)
        manifest["cases"][0]["reason_code"] = "FABRICATED"
        with self.assertRaises(EvaluationError):
            run_evaluation(manifest, self.source)

    def test_unsupported_is_not_allowed_to_hide_measured_case(self):
        manifest = deepcopy(self.manifest)
        manifest["cases"][0]["status"] = "unsupported"
        with self.assertRaises(EvaluationError):
            run_evaluation(manifest, self.source)

    def test_invalid_fixture_field_fails_closed(self):
        bad = deepcopy(self.source)
        bad["reservations"][0]["guest_email"] = "FORBIDDEN"
        with self.assertRaises(ValueError):
            run_evaluation(self.manifest, bad)

    def test_tampered_report_cannot_score(self):
        def tampering_engine(raw):
            report = evaluate(raw)
            report["approval_policy"]["human_approval_required"] = False
            return report
        with self.assertRaises(EvaluationError):
            run_evaluation(self.manifest, self.source, engine=tampering_engine)

    def test_output_json_and_markdown_are_synthetic_only(self):
        report = run_evaluation(self.manifest, self.source)
        parsed = json.loads(json.dumps(report, allow_nan=False))
        self.assertEqual(parsed["metric_unit"],
                         "one_case_one_reservation_one_reason_code_binary_label")
        md = render_markdown(parsed)
        self.assertIn("not a live hotel result", md)
        self.assertIn("independent expert review", md)
        self.assertIn("7/10", md)

    def test_cli_writes_both_formats_with_owner_only_permissions(self):
        with tempfile.TemporaryDirectory() as folder:
            json_path = Path(folder) / "evaluation.json"
            md_path = Path(folder) / "evaluation.md"
            self.assertEqual(main(["--json", str(json_path),
                                   "--markdown", str(md_path)]), 0)
            self.assertEqual(json.loads(json_path.read_text())["result"], "pass")
            self.assertIn("Synthetic Evaluation", md_path.read_text())
            self.assertEqual(json_path.stat().st_mode & 0o077, 0)

    def test_cli_must_not_overwrite_input(self):
        with self.assertRaises(Exception) if False else self.subTest("return-code"):
            self.assertEqual(main(["--json", str(DEFAULT_MANIFEST)]), 2)


if __name__ == "__main__":
    unittest.main()
