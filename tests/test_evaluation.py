"""Synthetic benchmark regressions; no live hotel outcomes or human review claims."""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from konaklamaflow import evaluation
from konaklamaflow.experience_engine import evaluate as engine_evaluate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "evaluation" / "benchmark.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def case_named(source, name):
    return next(case for case in source["cases"] if case["id"] == name)


def scores_without_provenance(report):
    result = deepcopy(report)
    result.pop("fixture_sha256")
    return result


class SyntheticEvaluationTests(unittest.TestCase):
    def test_manually_authored_truth_and_exact_baseline_counts(self):
        expected = {
            "EVAL_DUPLICATE_OTA": [
                ("EVAL_RES_A", ["DUPLICATE_CHANNEL_REF", "UNMAPPED_PMS"]),
                ("EVAL_RES_B", ["DUPLICATE_CHANNEL_REF", "UNMAPPED_PMS"])],
            "EVAL_ROOM_OVERLAP": [("EVAL_RES_A", ["ROOM_CONFLICT"]), ("EVAL_RES_B", ["ROOM_CONFLICT"])],
            "EVAL_MAINTENANCE_WINDOW": [("EVAL_RES_A", ["ROOM_INCOMPATIBLE"])],
            "EVAL_CANCELLED_ASSIGNED": [("EVAL_RES_A", ["CANCELLED_ASSIGNED", "NOT_CONFIRMED"])],
            "EVAL_CHANNEL_STATUS_CONFLICT": [("EVAL_RES_A", ["CHANNEL_STATUS_CONFLICT"])],
            "EVAL_CLEAN_NEGATIVE": [("EVAL_RES_A", [])],
            "EVAL_HALF_OPEN_ADJACENCY": [("EVAL_RES_A", []), ("EVAL_RES_B", ["ARRIVAL_NOT_TODAY", "GUEST_NOT_ARRIVED"])],
        }
        for case_id, labels in expected.items():
            case = case_named(FIXTURE, case_id)
            self.assertEqual([(x["reservation_id"], x["expected_reason_codes"]) for x in case["labels"]], labels)
        report = evaluation.evaluate_benchmark(FIXTURE)
        self.assertTrue(report["passed"])
        self.assertEqual(report["counts"], {
            "total_cases": 10, "evaluated_cases": 7, "passed_cases": 7,
            "excluded_cases": 3, "labelled_reservations": 10, "reason_decisions": 280,
        })
        self.assertEqual(report["metrics"]["confusion"], {"tp": 12, "fp": 0, "fn": 0, "tn": 268})
        self.assertEqual(report["metrics"]["case_coverage"]["value"], 0.7)
        self.assertEqual(report["metrics"]["category_coverage"]["value"], 0.833333)
        self.assertEqual(report["label_provenance"]["independent_hotel_expert_review"], "pending")

    def test_same_day_checkout_is_not_an_occupied_night(self):
        report = evaluation.evaluate_benchmark(FIXTURE)
        case = case_named(report, "EVAL_HALF_OPEN_ADJACENCY")
        self.assertTrue(case["passed"])
        for row in case["reservations"]:
            self.assertNotIn("ROOM_CONFLICT", row["actual_reason_codes"])
        self.assertEqual(case["reservations"][0]["actual_reason_codes"], [])
        self.assertTrue(case["reservations"][0]["human_approval_required"])

    def test_repeatable_order_independent_scores_and_source_immutability(self):
        before = deepcopy(FIXTURE)
        first = evaluation.evaluate_benchmark(FIXTURE)
        self.assertEqual(first, evaluation.evaluate_benchmark(FIXTURE))
        shuffled = deepcopy(FIXTURE)
        shuffled["cases"].reverse()
        shuffled["reason_code_universe"].reverse()
        for case in shuffled["cases"]:
            case["labels"].reverse()
            for label in case["labels"]:
                label["expected_reason_codes"].reverse()
            if case["snapshot"]:
                for field in ("rooms", "reservations", "channel_events", "tasks"):
                    case["snapshot"][field].reverse()
        other = evaluation.evaluate_benchmark(shuffled)
        self.assertEqual(scores_without_provenance(first), scores_without_provenance(other))
        self.assertNotEqual(first["fixture_sha256"], other["fixture_sha256"])
        self.assertEqual(FIXTURE, before)

    def test_network_tripwires_and_no_operations(self):
        with ExitStack() as stack:
            guards = [stack.enter_context(patch(target, side_effect=AssertionError("network forbidden")))
                      for target in ("socket.create_connection", "socket.socket.connect", "urllib.request.urlopen")]
            report = evaluation.evaluate_benchmark(FIXTURE)
        for guard in guards:
            guard.assert_not_called()
        self.assertEqual(report["mode"], "DRY_RUN_ONLY")
        self.assertEqual(report["approval_policy"], {
            "pms_writes": False, "payments": False, "kbs": False,
            "guest_messages": False, "human_approval_required": True,
        })
        self.assertEqual(report["human_override_rate"], {
            "status": "not_measured", "value": None, "reason": "no_real_human_approval_events",
        })

    def test_unsupported_and_unlabelled_are_not_run_or_scored(self):
        with patch.object(evaluation, "evaluate", wraps=engine_evaluate) as run:
            report = evaluation.evaluate_benchmark(FIXTURE)
        self.assertEqual(run.call_count, 7)
        excluded = [case for case in report["cases"] if case["status"] != "evaluated"]
        self.assertEqual(len(excluded), 3)
        for case in excluded:
            self.assertIsNone(case["passed"])
            self.assertIsNone(case["confusion"])
            self.assertEqual(case["reservations"], [])
            self.assertIsInstance(case["exclusion_reason"], str)
        categories = {x["category"]: x for x in report["categories"]}
        self.assertEqual(categories["split_stay_partial_cancellation"]["status"], "unsupported")
        self.assertEqual(categories["same_day_source_conflict"]["unsupported_cases"], 1)
        self.assertEqual(categories["same_day_source_conflict"]["evaluated_cases"], 1)

    def test_empty_incomplete_and_duplicate_fixture_fail_closed(self):
        variants = [None, [], {}, dict(FIXTURE, cases=[])]
        for mutate in (
            lambda x: x.pop("synthetic"),
            lambda x: x.update(synthetic=False),
            lambda x: x["cases"].append(deepcopy(x["cases"][0])),
            lambda x: x["cases"].pop(-2),  # removes only split/partial category
            lambda x: x["cases"][0].pop("labels"),
            lambda x: x["cases"][0].update(labels=[]),
            lambda x: x["cases"][0]["labels"].pop(),
            lambda x: x["cases"][0]["labels"].append(deepcopy(x["cases"][0]["labels"][0])),
            lambda x: x["cases"][0].update(snapshot=None),
            lambda x: x["cases"][0]["snapshot"]["reservations"][0].update(guest_name="SYNTHETIC_PRIVATE_VALUE"),
            lambda x: x["cases"][0]["snapshot"]["reservations"][0].update(external_ref="NON_SYNTHETIC_REFERENCE"),
            lambda x: x["cases"][0]["snapshot"]["reservations"][0].update(price_total=float("nan")),
            lambda x: x["cases"][0]["labels"][0].update(human_approval_required=False),
            lambda x: x["cases"][0]["labels"][0].update(expected_classification="approved"),
        ):
            value = deepcopy(FIXTURE)
            mutate(value)
            variants.append(value)
        for number, value in enumerate(variants):
            with self.subTest(variant=number), patch.object(evaluation, "evaluate") as run:
                with self.assertRaises(evaluation.EvaluationError):
                    evaluation.evaluate_benchmark(value)
                run.assert_not_called()

    def test_no_all_excluded_success(self):
        fixture = deepcopy(FIXTURE)
        for case in fixture["cases"]:
            if case["status"] == "evaluated":
                case.update(status="not_evaluated", labels=[], exclusion_reason="unlabelled")
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.evaluate_benchmark(fixture)

    def test_unknown_duplicate_and_missing_reason_vocabulary_fail_closed(self):
        for mutate in (
            lambda x: x["reason_code_universe"].append("UNKNOWN_REASON"),
            lambda x: x["reason_code_universe"].pop(),
            lambda x: x["reason_code_universe"].append(x["reason_code_universe"][0]),
            lambda x: x["cases"][0]["labels"][0]["expected_reason_codes"].append("UNKNOWN_REASON"),
            lambda x: x["cases"][0]["labels"][0]["expected_reason_codes"].append("DUPLICATE_CHANNEL_REF"),
            lambda x: x["cases"][0]["labels"][0]["expected_reason_codes"].append({}),
        ):
            fixture = deepcopy(FIXTURE)
            mutate(fixture)
            with self.subTest(mutate=mutate), self.assertRaises(evaluation.EvaluationError):
                evaluation.evaluate_benchmark(fixture)

    def test_exclusion_metadata_cannot_hide_truth_labels(self):
        for target, changes in (
            ("EVAL_REVISION_ORDER_UNSUPPORTED", {"exclusion_reason": None}),
            ("EVAL_PARTIAL_CANCEL_UNSUPPORTED", {"snapshot": FIXTURE["cases"][0]["snapshot"]}),
            ("EVAL_UNLABELLED_CONTROL", {"labels": FIXTURE["cases"][0]["labels"]}),
            ("EVAL_UNLABELLED_CONTROL", {"exclusion_reason": "split_stay_not_supported"}),
            ("EVAL_ROOM_OVERLAP", {"exclusion_reason": "unlabelled"}),
        ):
            fixture = deepcopy(FIXTURE)
            case_named(fixture, target).update(deepcopy(changes))
            with self.subTest(target=target), self.assertRaises(evaluation.EvaluationError):
                evaluation.evaluate_benchmark(fixture)

    def test_invalid_engine_contract_never_scores_success(self):
        snapshot = FIXTURE["cases"][0]["snapshot"]
        original = engine_evaluate(snapshot)
        mutations = (
            lambda x: x.update(mode="LIVE"),
            lambda x: x.update(snapshot_sha256="0" * 64),
            lambda x: x.update(as_of="2026-11-13"),
            lambda x: x.update(at_time="19:00"),
            lambda x: x["approval_policy"].update(payments=True),
            lambda x: x["approval_policy"].update(payments=0),
            lambda x: x["approval_policy"].update(human_approval_required=1),
            lambda x: x["arrivals"].pop(),
            lambda x: x["arrivals"].append(deepcopy(x["arrivals"][0])),
            lambda x: x["arrivals"][0].update(id="NOT_IN_SOURCE"),
            lambda x: x["arrivals"][0].update(blockers=["UNKNOWN_REASON"]),
            lambda x: x["arrivals"][0].update(blockers=["ROOM_CONFLICT", "ROOM_CONFLICT"]),
            lambda x: x["arrivals"][0].update(human_approval_required=False),
            lambda x: x["arrivals"][0].update(status="review_ready"),
        )
        for number, mutate in enumerate(mutations):
            report = deepcopy(original)
            mutate(report)
            with self.subTest(mutation=number), self.assertRaises(evaluation.EvaluationError):
                evaluation.normalize_report(report, snapshot)

    def test_mutating_engine_is_rejected_and_caller_fixture_is_intact(self):
        original = deepcopy(FIXTURE)
        def mutating_engine(source):
            report = engine_evaluate(source)
            source["reservations"].clear()
            return report
        with patch.object(evaluation, "evaluate", side_effect=mutating_engine):
            with self.assertRaises(evaluation.EvaluationError):
                evaluation.evaluate_benchmark(FIXTURE)
        self.assertEqual(FIXTURE, original)

    def test_wrong_reservation_attribution_produces_fp_and_fn(self):
        adjacency_source = case_named(FIXTURE, "EVAL_HALF_OPEN_ADJACENCY")["snapshot"]
        def misplaced_engine(source):
            report = engine_evaluate(source)
            if source == adjacency_source:
                a, b = report["arrivals"]
                a["blockers"], b["blockers"] = b["blockers"], a["blockers"]
                a["status"], b["status"] = b["status"], a["status"]
            return report
        with patch.object(evaluation, "evaluate", side_effect=misplaced_engine):
            report = evaluation.evaluate_benchmark(FIXTURE)
        self.assertFalse(report["passed"])
        self.assertEqual(report["metrics"]["confusion"], {"tp": 10, "fp": 2, "fn": 2, "tn": 266})
        case = case_named(report, "EVAL_HALF_OPEN_ADJACENCY")
        self.assertEqual(case["reservations"][0]["unexpected_reason_codes"], ["ARRIVAL_NOT_TODAY", "GUEST_NOT_ARRIVED"])
        self.assertEqual(case["reservations"][1]["missing_reason_codes"], ["ARRIVAL_NOT_TODAY", "GUEST_NOT_ARRIVED"])
        self.assertFalse(case["reservations"][0]["classification_match"])
        self.assertEqual(report["counts"]["passed_cases"], 6)

    def test_missing_and_extra_known_reason_labels_are_visible_failures(self):
        fixture = deepcopy(FIXTURE)
        # Deliberately wrong manual truth: proves the benchmark can fail instead of
        # deriving every expectation from the very engine being measured.
        label = case_named(fixture, "EVAL_CLEAN_NEGATIVE")["labels"][0]
        label.update(expected_reason_codes=["PAYMENT_REVIEW"], expected_classification="blocked")
        label = case_named(fixture, "EVAL_MAINTENANCE_WINDOW")["labels"][0]
        label.update(expected_reason_codes=[], expected_classification="review_ready")
        report = evaluation.evaluate_benchmark(fixture)
        self.assertFalse(report["passed"])
        self.assertEqual(report["metrics"]["confusion"], {"tp": 11, "fp": 1, "fn": 1, "tn": 267})
        self.assertEqual(report["counts"]["passed_cases"], 5)
        self.assertIn("Missing: PAYMENT_REVIEW", evaluation.render_markdown(report))
        self.assertIn("Unexpected: ROOM_INCOMPATIBLE", evaluation.render_markdown(report))

    def test_classification_mismatch_fails_even_with_exact_reason_labels(self):
        fixture = deepcopy(FIXTURE)
        case_named(fixture, "EVAL_CLEAN_NEGATIVE")["labels"][0]["expected_classification"] = "other"
        report = evaluation.evaluate_benchmark(fixture)
        self.assertFalse(report["passed"])
        self.assertEqual(report["metrics"]["confusion"], {"tp": 12, "fp": 0, "fn": 0, "tn": 268})
        self.assertEqual(report["metrics"]["classification_match_rate"]["value"], 0.9)

    def test_reason_rates_have_defined_denominators_and_null_zero_cases(self):
        fixture = deepcopy(FIXTURE)
        for case in fixture["cases"]:
            if case["status"] == "evaluated" and case["id"] != "EVAL_CLEAN_NEGATIVE":
                case.update(status="not_evaluated", labels=[], exclusion_reason="unlabelled")
        report = evaluation.evaluate_benchmark(fixture)
        self.assertEqual(report["metrics"]["confusion"], {"tp": 0, "fp": 0, "fn": 0, "tn": 28})
        for key in ("precision", "recall", "false_negative_rate"):
            self.assertEqual(report["metrics"][key], {
                "numerator": 0, "denominator": 0, "value": None, "undefined_reason": "zero_denominator",
            })
        self.assertEqual(report["metrics"]["false_positive_rate"], {
            "numerator": 0, "denominator": 28, "value": 0.0, "undefined_reason": None,
        })
        self.assertIn("null (zero denominator)", evaluation.render_markdown(report))

    def test_report_json_contract_and_metric_consistency(self):
        report = json.loads(json.dumps(evaluation.evaluate_benchmark(FIXTURE), allow_nan=False))
        self.assertEqual(set(report), {
            "schema_version", "benchmark_id", "benchmark_kind", "mode", "authority", "label_provenance",
            "fixture_sha256", "reason_code_universe", "scoring_unit", "passed", "counts", "metrics",
            "human_override_rate", "processing_time", "approval_policy", "categories", "cases",
        })
        self.assertEqual(report["schema_version"], "synthetic-evaluation-report.v1")
        self.assertEqual(report["benchmark_kind"], "synthetic_benchmark_not_production_validation")
        self.assertRegex(report["fixture_sha256"], r"^[0-9a-f]{64}$")
        self.assertIs(type(report["passed"]), bool)
        confusion = report["metrics"]["confusion"]
        self.assertEqual(sum(confusion.values()), report["counts"]["reason_decisions"])
        totals = {key: sum((case["confusion"] or {}).get(key, 0) for case in report["cases"]) for key in confusion}
        self.assertEqual(totals, confusion)
        for key, metric in report["metrics"].items():
            if key == "confusion":
                continue
            self.assertEqual(set(metric), {"numerator", "denominator", "value", "undefined_reason"})
            self.assertIs(type(metric["numerator"]), int)
            self.assertIs(type(metric["denominator"]), int)
            self.assertEqual(metric["value"], round(metric["numerator"] / metric["denominator"], 6))
        tp, fp, fn, tn = (confusion[k] for k in ("tp", "fp", "fn", "tn"))
        self.assertEqual(report["metrics"]["precision"]["denominator"], tp + fp)
        self.assertEqual(report["metrics"]["recall"]["denominator"], tp + fn)
        self.assertEqual(report["metrics"]["false_positive_rate"]["denominator"], fp + tn)
        self.assertEqual(report["metrics"]["false_negative_rate"]["denominator"], fn + tp)
        for case in report["cases"]:
            self.assertEqual(set(case), {"id", "category", "status", "exclusion_reason", "passed", "reservations", "confusion"})
            for row in case["reservations"]:
                self.assertEqual(set(row), {
                    "reservation_id", "expected_reason_codes", "actual_reason_codes", "missing_reason_codes",
                    "unexpected_reason_codes", "expected_classification", "actual_classification",
                    "human_approval_required", "classification_match", "human_boundary_match", "passed",
                })
                for key in ("human_approval_required", "classification_match", "human_boundary_match", "passed"):
                    self.assertIs(type(row[key]), bool)
        encoded = json.dumps(report)
        self.assertNotIn('"snapshot":', encoded)
        self.assertTrue(all("scope" not in case for case in report["cases"]))
        self.assertNotIn('"price_total":', encoded)

    def test_no_unmeasured_timing_and_opt_in_times_actual_calls(self):
        with patch.object(evaluation, "perf_counter", side_effect=AssertionError("not opted in")):
            report = evaluation.evaluate_benchmark(FIXTURE)
        self.assertEqual(report["processing_time"]["status"], "not_measured")
        self.assertIsNone(report["processing_time"]["seconds"])
        with patch.object(evaluation, "perf_counter", side_effect=list(range(14))) as clock:
            timed = evaluation.evaluate_benchmark(FIXTURE, measure_time=True)
        self.assertEqual(clock.call_count, 14)
        self.assertEqual(timed["processing_time"]["status"], "measured")
        self.assertEqual(timed["processing_time"]["seconds"], 7.0)
        self.assertEqual(timed["metrics"], report["metrics"])


class SyntheticEvaluationCliTests(unittest.TestCase):
    def run_cli(self, source, output, markdown):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = evaluation.main([str(source), "--json-output", str(output), "--markdown-output", str(markdown)])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_cli_emits_real_json_markdown_and_reproducible_scores(self):
        with tempfile.TemporaryDirectory() as directory:
            output, markdown = Path(directory) / "report.json", Path(directory) / "report.md"
            code, stdout, stderr = self.run_cli(FIXTURE_PATH, output, markdown)
            self.assertEqual(code, 0)
            self.assertEqual(stderr, "")
            self.assertIn("SYNTHETIC BENCHMARK PASS", stdout)
            self.assertIn("not production validation", stdout)
            report = json.loads(output.read_text())
            self.assertEqual(report, evaluation.evaluate_benchmark(FIXTURE))
            self.assertEqual(markdown.read_text(), evaluation.render_markdown(report))
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            before = output.read_bytes(), markdown.read_bytes()
            self.assertEqual(self.run_cli(FIXTURE_PATH, output, markdown)[0], 0)
            self.assertEqual(before, (output.read_bytes(), markdown.read_bytes()))

    def test_intentionally_wrong_labels_return_failure_exit_and_report(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = deepcopy(FIXTURE)
            label = case_named(fixture, "EVAL_CLEAN_NEGATIVE")["labels"][0]
            label.update(expected_reason_codes=["PAYMENT_REVIEW"], expected_classification="blocked")
            source = Path(directory) / "synthetic-wrong-label.json"
            source.write_text(json.dumps(fixture))
            output, markdown = Path(directory) / "report.json", Path(directory) / "report.md"
            code, stdout, stderr = self.run_cli(source, output, markdown)
            self.assertEqual(code, 1)
            self.assertIn("SYNTHETIC BENCHMARK FAIL", stdout)
            self.assertEqual(stderr, "")
            self.assertFalse(json.loads(output.read_text())["passed"])
            self.assertIn("**FAIL**", markdown.read_text())

    def test_invalid_json_and_schema_do_not_echo_values_or_create_reports(self):
        marker = "SYNTHETIC_PRIVATE_MARKER"
        payloads = [b"\xff", marker.encode(), b'{"synthetic":true,"synthetic":false}',
                    json.dumps(dict(FIXTURE, private_field=marker)).encode(), b"[NaN]"]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / (marker + ".json")
            for payload in payloads:
                with self.subTest(payload_kind=payload[:1]):
                    source.write_bytes(payload)
                    output, markdown = Path(directory) / "report.json", Path(directory) / "report.md"
                    code, stdout, stderr = self.run_cli(source, output, markdown)
                    self.assertEqual(code, 2)
                    self.assertEqual(stdout, "")
                    self.assertNotIn(marker, stderr)
                    self.assertNotIn(str(source), stderr)
                    self.assertFalse(output.exists())
                    self.assertFalse(markdown.exists())

    def test_missing_fixture_returns_redacted_error(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "SYNTHETIC_PRIVATE_PATH.json"
            code, stdout, stderr = self.run_cli(source, Path(directory) / "out.json", Path(directory) / "out.md")
            self.assertEqual(code, 2)
            self.assertEqual(stdout, "")
            self.assertNotIn(str(source), stderr)

    def test_output_cannot_clobber_fixture_via_same_path_symlink_or_hardlink(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "fixture.json"
            source.write_bytes(FIXTURE_PATH.read_bytes())
            before = source.read_bytes()
            symlink, hardlink = Path(directory) / "alias.json", Path(directory) / "hard.json"
            symlink.symlink_to(source)
            os.link(source, hardlink)
            for output in (source, symlink, hardlink):
                with self.subTest(alias=output.name):
                    code, stdout, stderr = self.run_cli(source, output, Path(directory) / "out.md")
                    self.assertEqual(code, 2)
                    self.assertEqual(stdout, "")
                    self.assertEqual(source.read_bytes(), before)
            self.assertEqual(self.run_cli(source, Path(directory) / "out.json", source)[0], 2)
            self.assertEqual(source.read_bytes(), before)

    def test_cyclic_output_symlink_is_rejected_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            cycle = Path(directory) / "cycle.json"
            cycle.symlink_to(cycle)
            code, stdout, stderr = self.run_cli(FIXTURE_PATH, cycle, Path(directory) / "report.md")
            self.assertEqual(code, 2)
            self.assertEqual(stdout, "")
            self.assertNotIn("Traceback", stderr)
            self.assertNotIn(str(cycle), stderr)

    def test_invalid_second_destination_preserves_existing_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            output.write_text("SYNTHETIC_PREVIOUS_REPORT")
            markdown = Path(directory) / "missing" / "report.md"
            code, stdout, stderr = self.run_cli(FIXTURE_PATH, output, markdown)
            self.assertEqual(code, 2)
            self.assertEqual(stdout, "")
            self.assertEqual(output.read_text(), "SYNTHETIC_PREVIOUS_REPORT")
            self.assertFalse(markdown.exists())

    def test_json_and_markdown_outputs_cannot_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "out.json"
            output.write_text("SYNTHETIC_EXISTING_FILE")
            hardlink = Path(directory) / "out.md"
            os.link(output, hardlink)
            for markdown in (output, hardlink):
                self.assertEqual(self.run_cli(FIXTURE_PATH, output, markdown)[0], 2)
                self.assertEqual(output.read_text(), "SYNTHETIC_EXISTING_FILE")


if __name__ == "__main__":
    unittest.main()
