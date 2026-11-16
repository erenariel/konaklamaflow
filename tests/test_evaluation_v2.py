"""Benchmark v2 integrity, exclusion, repeatability and visible failures."""
from __future__ import annotations

from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from konaklamaflow.evaluation import EvaluationError
from konaklamaflow.evaluation_v2 import (
    DEFAULT_MANIFEST_V2, SOURCE_FIXTURE, _scenario,
    main, render_markdown_v2, run_evaluation_v2,
)


class BenchmarkV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(DEFAULT_MANIFEST_V2.read_text(encoding="utf-8"))
        cls.source = json.loads(SOURCE_FIXTURE.read_text(encoding="utf-8"))

    def test_43_cases_have_explicit_scoring_and_exclusion_accounting(self):
        report = run_evaluation_v2(self.manifest, self.source)
        summary = report["summary"]
        self.assertEqual(summary["total_cases"], 43)
        self.assertEqual(summary["evaluated"], 40)
        self.assertEqual(summary["unsupported"], 2)
        self.assertEqual(summary["unlabelled"], 1)
        self.assertEqual(summary["coverage"], 40 / 43)
        self.assertEqual(summary["distinct_scenarios"], 23)
        self.assertGreaterEqual(summary["distinct_reason_codes"], 15)
        self.assertEqual(summary["passed_labeled_cases"] +
                         summary["failed_labeled_cases"], 40)
        m = report["metrics"]
        self.assertEqual(m["tp"] + m["tn"] + m["fp"] + m["fn"], 40)
        self.assertEqual(m["fp"] + m["fn"],
                         summary["failed_labeled_cases"])
        self.assertEqual(report["mode"], "DRY_RUN_ONLY")
        self.assertEqual(report["independent_expert_review"], "not_performed")
        self.assertEqual(report["processing_time_ms"], "not_measured")
        self.assertEqual(report["human_override_rate"], "not_measured")
        self.assertEqual(len(report["manifest_sha256"]), 64)

    def test_real_engine_ran_on_every_labeled_case_and_reports_are_repeatable(self):
        snapshot = deepcopy(self.source)
        manifest = deepcopy(self.manifest)
        result1 = run_evaluation_v2(manifest, snapshot)
        result2 = run_evaluation_v2(manifest, snapshot)
        self.assertEqual(result1, result2)
        self.assertEqual(manifest, self.manifest)
        self.assertEqual(snapshot, self.source)
        measured = [c for c in result1["cases"] if c["status"] in ("pass", "fail")]
        self.assertEqual(len(measured), 40)
        self.assertTrue(all(c["outcome"] in {"TP", "TN", "FP", "FN"}
                            and type(c["expected"]) is bool
                            and type(c["predicted"]) is bool
                            and c["rationale"] for c in measured))

    def test_failure_case_is_explicit_in_json_and_markdown(self):
        manifest = deepcopy(self.manifest)
        first = manifest["cases"][0]
        first["expected"] = False  # deliberately contradicts held cancelled room
        result = run_evaluation_v2(manifest, self.source)
        case = next(c for c in result["cases"] if c["id"] == first["id"])
        self.assertEqual(case["status"], "fail")
        self.assertEqual(case["outcome"], "FP")
        self.assertFalse(case["expected"])
        self.assertTrue(case["predicted"])
        self.assertGreaterEqual(result["summary"]["failed_labeled_cases"], 1)
        md = render_markdown_v2(result)
        self.assertIn(first["id"], md)
        self.assertIn("FP for KF1006/CANCELLED_ASSIGNED", md)
        self.assertIn("Label disagreement detail", md)

    def test_manifest_cannot_hide_failing_case_as_unsupported(self):
        manifest = deepcopy(self.manifest)
        manifest["cases"][0] = {
            "id": manifest["cases"][0]["id"],
            "category": "cancelled_hold", "status": "unsupported",
            "reason": "NO_PARTIAL_CANCELLATION_MODEL",
        }
        with self.assertRaises(EvaluationError):
            run_evaluation_v2(manifest, self.source)

    def test_duplicate_scenario_target_pair_and_bad_rationale_are_rejected(self):
        manifest = deepcopy(self.manifest)
        manifest["cases"][1].update({
            "scenario": manifest["cases"][0]["scenario"],
            "reservation_id": manifest["cases"][0]["reservation_id"],
            "reason_code": manifest["cases"][0]["reason_code"],
        })
        with self.assertRaises(EvaluationError):
            run_evaluation_v2(manifest, self.source)
        manifest = deepcopy(self.manifest)
        manifest["cases"][0]["rationale"] = "short"
        with self.assertRaises(EvaluationError):
            run_evaluation_v2(manifest, self.source)

    def test_arbitrary_patch_and_unknown_code_are_rejected(self):
        manifest = deepcopy(self.manifest)
        manifest["cases"][0]["scenario"] = "eval_arbitrary_json"
        with self.assertRaises(EvaluationError):
            run_evaluation_v2(manifest, self.source)
        manifest = deepcopy(self.manifest)
        manifest["cases"][0]["reason_code"] = "FAKE_METRIC"
        with self.assertRaises(EvaluationError):
            run_evaluation_v2(manifest, self.source)
        manifest = deepcopy(self.manifest)
        manifest["cases"][0]["guest_email"] = "FORBIDDEN"
        with self.assertRaises(EvaluationError):
            run_evaluation_v2(manifest, self.source)

    def test_synthetic_scenarios_leave_source_immutable(self):
        for name in ("none", "duplicate_reference", "room_overlap",
                     "maintenance_open", "duplicate_pms", "same_day_checkout"):
            with self.subTest(scenario=name):
                original = deepcopy(self.source)
                generated = _scenario(self.source, name)
                self.assertEqual(self.source, original)
                self.assertIsNot(generated, self.source)

    def test_json_cli_and_markdown_include_all_measured_cases(self):
        with tempfile.TemporaryDirectory() as folder:
            json_path = Path(folder) / "benchmark-v2.json"
            md_path = Path(folder) / "benchmark-v2.md"
            self.assertEqual(main(["--json", str(json_path),
                                   "--markdown", str(md_path)]), 0)
            report = json.loads(json_path.read_text())
            md = md_path.read_text()
            self.assertEqual(len(report["cases"]), 43)
            self.assertIn("Measured cases (including all failures)", md)
            self.assertIn("Excluded — not scored", md)
            self.assertIn("not independent", md.lower()) if "not independent" in md.lower() else self.assertIn("no independent", md.lower())
            self.assertEqual(json_path.stat().st_mode & 0o077, 0)
            self.assertEqual(md_path.stat().st_mode & 0o077, 0)
            self.assertEqual(main(["--json", str(DEFAULT_MANIFEST_V2)]), 2)

    def test_cli_strict_fails_when_an_author_label_disagrees(self):
        with tempfile.TemporaryDirectory() as folder:
            altered = deepcopy(self.manifest)
            altered["cases"][0]["expected"] = False
            path = Path(folder) / "altered.json"
            path.write_text(json.dumps(altered), encoding="utf-8")
            with redirect_stdout(StringIO()):
                self.assertEqual(main(["--manifest", str(path)]), 0)
                self.assertEqual(main(["--manifest", str(path), "--strict"]), 1)


if __name__ == "__main__":
    unittest.main()
