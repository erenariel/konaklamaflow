"""Offline synthetic accuracy benchmark, never an operational decision engine."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

from .core import InputError
from .experience_engine import BLOCKER_CODES, SnapshotError, evaluate, validate
from .io_safety import ensure_output_not_input, read_limited_json, write_owner_report

SCHEMA = "synthetic-benchmark.v1"
REPORT_SCHEMA = "synthetic-evaluation-report.v1"
CATEGORIES = (
    "duplicate_ota_reference", "room_overlap", "maintenance_overlap",
    "cancelled_assigned", "same_day_source_conflict", "split_stay_partial_cancellation",
)
EXCLUSIONS = {"revision_history_not_supported", "split_stay_not_supported", "unlabelled"}
CLASSES = {"blocked", "review_ready", "other"}
POLICY = {"pms_writes": False, "payments": False, "kbs": False,
          "guest_messages": False, "human_approval_required": True}
ID = re.compile(r"^[A-Z][A-Z0-9_-]{0,63}$")


class EvaluationError(ValueError):
    """Invalid fixtures or engine contracts cannot produce success metrics."""


def _fail():
    raise EvaluationError("Invalid synthetic benchmark or engine report")


def _object(value, fields):
    if type(value) is not dict or set(value) != set(fields):
        _fail()


def _identifier(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        _fail()


def _hash(value):
    try:
        return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    except (TypeError, ValueError, RecursionError):
        _fail()


def validate_benchmark(raw):
    """Strict, bounded fixture envelope; reuse the existing minimized input validator."""
    _object(raw, {"schema_version", "benchmark_id", "synthetic", "label_provenance",
                  "reason_code_universe", "cases"})
    if raw["schema_version"] != SCHEMA or raw["synthetic"] is not True:
        _fail()
    _identifier(raw["benchmark_id"])
    if raw["label_provenance"] != {
        "method": "manual_rule_spec", "independent_hotel_expert_review": "pending"
    }:
        _fail()
    universe = raw["reason_code_universe"]
    if (type(universe) is not list or any(type(c) is not str for c in universe)
            or len(universe) != len(set(universe)) or set(universe) != BLOCKER_CODES):
        _fail()
    if type(raw["cases"]) is not list or not 1 <= len(raw["cases"]) <= 100:
        _fail()
    try:
        # Also reject nonfinite values anywhere, before invoking the engine.
        _hash(raw)
        suite = deepcopy(raw)
    except (TypeError, RecursionError):
        _fail()
    seen, categories = set(), set()
    evaluated = 0
    for case in suite["cases"]:
        _object(case, {"id", "category", "status", "scope", "exclusion_reason", "snapshot", "labels"})
        _identifier(case["id"])
        if case["id"] in seen:
            _fail()
        seen.add(case["id"])
        if type(case["category"]) is not str or case["category"] not in CATEGORIES:
            _fail()
        categories.add(case["category"])
        if (type(case["scope"]) is not str or not 1 <= len(case["scope"]) <= 400
                or any(ord(c) < 32 for c in case["scope"])):
            _fail()
        status = case["status"]
        if status not in ("evaluated", "unsupported", "not_evaluated"):
            _fail()
        if type(case["labels"]) is not list:
            _fail()
        if status == "unsupported":
            if (case["snapshot"] is not None or case["labels"]
                    or case["exclusion_reason"] not in ("revision_history_not_supported", "split_stay_not_supported")):
                _fail()
            continue
        try:
            snapshot = validate(case["snapshot"])
        except (SnapshotError, InputError, TypeError, ValueError, RecursionError):
            _fail()
        if (snapshot["property_id"] != "EVAL_SYNTHETIC" or not snapshot["reservations"]
                or len(snapshot["rooms"]) > 20 or len(snapshot["reservations"]) > 20
                or len(snapshot["channel_events"]) > 40 or len(snapshot["tasks"]) > 40):
            _fail()
        # A test-only namespace is a guardrail, not proof of anonymization.
        for collection, fields in (("rooms", ("id",)),
                                   ("reservations", ("id", "external_ref", "pms_ref", "room_id")),
                                   ("channel_events", ("id", "external_ref", "reservation_id")),
                                   ("tasks", ("id", "room_id", "reservation_id"))):
            for item in snapshot[collection]:
                for field in fields:
                    value = item.get(field)
                    if value is not None and not value.startswith("EVAL_"):
                        _fail()
        if status == "not_evaluated":
            if case["labels"] or case["exclusion_reason"] != "unlabelled":
                _fail()
            continue
        evaluated += 1
        if case["exclusion_reason"] is not None:
            _fail()
        expected_ids = {r["id"] for r in snapshot["reservations"]}
        labels = set()
        for label in case["labels"]:
            _object(label, {"reservation_id", "expected_reason_codes", "expected_classification",
                            "human_approval_required"})
            rid = label["reservation_id"]
            if type(rid) is not str or rid not in expected_ids or rid in labels:
                _fail()
            labels.add(rid)
            codes = label["expected_reason_codes"]
            if (type(codes) is not list or any(type(c) is not str for c in codes)
                    or len(codes) != len(set(codes)) or not set(codes) <= BLOCKER_CODES):
                _fail()
            if (type(label["expected_classification"]) is not str
                    or label["expected_classification"] not in CLASSES
                    or label["human_approval_required"] is not True):
                _fail()
            # In this output contract any blocker must have blocked classification.
            if bool(codes) != (label["expected_classification"] == "blocked"):
                _fail()
        if labels != expected_ids:
            _fail()
    if categories != set(CATEGORIES) or not evaluated:
        _fail()
    suite["cases"].sort(key=lambda c: c["id"])
    suite["reason_code_universe"] = sorted(universe)
    return suite


def normalize_report(report, snapshot):
    """Normalize authoritative suite rows, without reproducing any hotel rule."""
    validated = validate(snapshot)
    policy = report.get("approval_policy") if type(report) is dict else None
    if (type(policy) is not dict or set(policy) != set(POLICY)
            or any(policy[k] is not value for k, value in POLICY.items())):
        _fail()
    if (type(report) is not dict or report.get("schema_version") != "0.3"
            or report.get("mode") != "DRY_RUN_ONLY"
            or report.get("property_id") != snapshot["property_id"]
            or report.get("as_of") != snapshot["as_of"]
            or report.get("at_time") != validated["at_time"]
            or report.get("snapshot_sha256") != _hash(validated)):
        _fail()
    rows = report.get("arrivals")
    if type(rows) is not list:
        _fail()
    expected_ids = {r["id"] for r in snapshot["reservations"]}
    normalized = {}
    for row in rows:
        if type(row) is not dict or type(row.get("id")) is not str:
            _fail()
        rid, codes = row["id"], row.get("blockers")
        if rid not in expected_ids or rid in normalized:
            _fail()
        if (type(codes) is not list or any(type(c) is not str for c in codes)
                or len(codes) != len(set(codes)) or not set(codes) <= BLOCKER_CODES
                or type(row.get("status")) is not str or row["status"] not in CLASSES
                or row.get("human_approval_required") is not True
                or bool(codes) != (row["status"] == "blocked")):
            _fail()
        normalized[rid] = {"reason_codes": sorted(codes), "classification": row["status"],
                           "human_approval_required": True}
    if set(normalized) != expected_ids:
        _fail()
    return normalized


def _rate(numerator, denominator):
    return {"numerator": numerator, "denominator": denominator,
            "value": round(numerator / denominator, 6) if denominator else None,
            "undefined_reason": None if denominator else "zero_denominator"}


def score_rows(labels, actual, universe):
    """Micro counts over (case, reservation, code), not deduplicated case-level alerts."""
    counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    results = []
    for label in sorted(labels, key=lambda x: x["reservation_id"]):
        rid = label["reservation_id"]
        expected, observed = set(label["expected_reason_codes"]), set(actual[rid]["reason_codes"])
        missing, unexpected = sorted(expected - observed), sorted(observed - expected)
        counts["tp"] += len(expected & observed)
        counts["fp"] += len(unexpected)
        counts["fn"] += len(missing)
        counts["tn"] += len(set(universe) - (expected | observed))
        matches = actual[rid]["classification"] == label["expected_classification"]
        boundary = actual[rid]["human_approval_required"] == label["human_approval_required"]
        results.append({"reservation_id": rid, "expected_reason_codes": sorted(expected),
                        "actual_reason_codes": sorted(observed), "missing_reason_codes": missing,
                        "unexpected_reason_codes": unexpected,
                        "expected_classification": label["expected_classification"],
                        "actual_classification": actual[rid]["classification"],
                        "human_approval_required": actual[rid]["human_approval_required"],
                        "classification_match": matches, "human_boundary_match": boundary,
                        "passed": not missing and not unexpected and matches and boundary})
    return counts, results


def evaluate_benchmark(raw, *, measure_time=False):
    """Run only the local Python evaluator; excluded cases never enter scoring."""
    suite = validate_benchmark(raw)
    results, counts = [], {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    labelled, exact, class_matches, evaluated, passed = 0, 0, 0, 0, 0
    seconds = 0.0
    for case in suite["cases"]:
        entry = {k: case[k] for k in ("id", "category", "status", "exclusion_reason")}
        # Do not echo arbitrary fixture prose or snapshots in public reports.
        entry.update({"passed": None, "reservations": [], "confusion": None})
        if case["status"] == "evaluated":
            source = deepcopy(case["snapshot"])
            before = _hash(source)
            start = perf_counter() if measure_time else None
            try:
                report = evaluate(source)
            except (SnapshotError, InputError, TypeError, ValueError, KeyError, RecursionError):
                _fail()
            if measure_time:
                seconds += perf_counter() - start
            if _hash(source) != before:
                _fail()
            rows = normalize_report(report, case["snapshot"])
            tally, scores = score_rows(case["labels"], rows, suite["reason_code_universe"])
            evaluated += 1
            success = all(x["passed"] for x in scores)
            passed += int(success)
            labelled += len(scores)
            exact += sum(x["passed"] for x in scores)
            class_matches += sum(x["classification_match"] for x in scores)
            for key in counts:
                counts[key] += tally[key]
            entry.update({"passed": success, "reservations": scores, "confusion": tally})
        results.append(entry)
    tp, fp, fn, tn = (counts[k] for k in ("tp", "fp", "fn", "tn"))
    categories = []
    for category in CATEGORIES:
        statuses = [r["status"] for r in results if r["category"] == category]
        categories.append({"category": category,
                           "status": "evaluated" if "evaluated" in statuses else "unsupported" if "unsupported" in statuses else "not_evaluated",
                           "evaluated_cases": statuses.count("evaluated"),
                           "unsupported_cases": statuses.count("unsupported"),
                           "unlabelled_cases": statuses.count("not_evaluated")})
    return {
        "schema_version": REPORT_SCHEMA, "benchmark_id": suite["benchmark_id"],
        "benchmark_kind": "synthetic_benchmark_not_production_validation", "mode": "DRY_RUN_ONLY",
        "authority": "experience_engine.evaluate", "label_provenance": suite["label_provenance"],
        "fixture_sha256": _hash(raw), "reason_code_universe": suite["reason_code_universe"],
        "scoring_unit": "case_id/reservation_id/reason_code",
        "passed": passed == evaluated,
        "counts": {"total_cases": len(results), "evaluated_cases": evaluated, "passed_cases": passed,
                   "excluded_cases": len(results) - evaluated, "labelled_reservations": labelled,
                   "reason_decisions": labelled * len(suite["reason_code_universe"])},
        "metrics": {"confusion": counts, "precision": _rate(tp, tp + fp),
                    "recall": _rate(tp, tp + fn), "false_positive_rate": _rate(fp, fp + tn),
                    "false_negative_rate": _rate(fn, fn + tp),
                    "exact_reservation_match_rate": _rate(exact, labelled),
                    "classification_match_rate": _rate(class_matches, labelled),
                    "case_coverage": _rate(evaluated, len(results)),
                    "category_coverage": _rate(sum(c["evaluated_cases"] > 0 for c in categories), len(CATEGORIES))},
        "human_override_rate": {"status": "not_measured", "value": None,
                                "reason": "no_real_human_approval_events"},
        "processing_time": {"status": "measured" if measure_time else "not_measured",
                            "seconds": seconds if measure_time else None,
                            "scope": "sum_of_local_evaluator_calls_only_no_io_no_network_no_staff_time"},
        "approval_policy": dict(POLICY), "categories": categories, "cases": results,
    }


def render_markdown(report):
    """Human readable synthetic benchmark, with explicit support and denominators."""
    lines = ["# KonaklamaFlow — synthetic benchmark", "",
             "Not production validation or a live hotel/AI pilot. DRY_RUN_ONLY; human review remains required.",
             "Labels: manual rule specifications; independent hotel-expert review pending.", "",
             "Result: **" + ("PASS" if report["passed"] else "FAIL") + "**", "",
             "Scoring unit: `(case_id, reservation_id, reason_code)`; unsupported/unlabelled cases excluded.",
             "Reason universe: " + str(len(report["reason_code_universe"])) + " codes; TN depends on this universe.", "",
             "| Metric | Value | Numerator / denominator |", "|---|---:|---|" ]
    for key in sorted(report["metrics"]):
        metric = report["metrics"][key]
        if key == "confusion":
            continue
        value = str(metric["value"]) if metric["value"] is not None else "null (zero denominator)"
        lines.append(f"| {key} | {value} | {metric['numerator']} / {metric['denominator']} |")
    lines += ["", "Confusion: " + json.dumps(report["metrics"]["confusion"], sort_keys=True),
              "", "| Case | Category | Status | Result / exclusion |", "|---|---|---|---|"]
    for case in report["cases"]:
        outcome = ("PASS" if case["passed"] else "FAIL") if case["passed"] is not None else case["exclusion_reason"]
        lines.append(f"| {case['id']} | {case['category']} | {case['status']} | {outcome} |")
        for row in case["reservations"]:
            if not row["passed"]:
                lines.append(f"| {row['reservation_id']} | Missing: {', '.join(row['missing_reason_codes']) or 'none'} | Unexpected: {', '.join(row['unexpected_reason_codes']) or 'none'} | classification match: {row['classification_match']} |")
    lines += ["", "human_override_rate: **not_measured** (no real approval events).",
              "processing_time: " + json.dumps(report["processing_time"], sort_keys=True),
              "", "Fixture SHA-256: `" + report["fixture_sha256"] + "`", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline synthetic benchmark; not production validation")
    parser.add_argument("fixture")
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    parser.add_argument("--measure-time", action="store_true")
    args = parser.parse_args(argv)
    try:
        ensure_output_not_input(args.json_output, args.fixture, args.markdown_output)
        ensure_output_not_input(args.markdown_output, args.fixture, args.json_output)
        raw = read_limited_json(args.fixture)
        report = evaluate_benchmark(raw, measure_time=args.measure_time)
        encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"
        markdown = render_markdown(report)
        # Prepare BOTH files before replacing either existing report. Each final
        # rename is atomic; two paths cannot be a single filesystem transaction.
        with ExitStack() as stack:
            staged = []
            for target, content in ((args.json_output, encoded), (args.markdown_output, markdown)):
                destination = Path(target)
                if destination.exists() and not destination.is_file():
                    _fail()
                directory = stack.enter_context(TemporaryDirectory(dir=destination.parent))
                pending = Path(directory) / "report"
                write_owner_report(str(pending), content)
                staged.append((pending, destination))
            for pending, destination in staged:
                os.replace(pending, destination)
    except (EvaluationError, InputError, OSError, ValueError, TypeError, RuntimeError):
        print("Synthetic benchmark rejected: invalid input, output path or engine contract; no success claimed.", file=sys.stderr)
        return 2
    print("SYNTHETIC BENCHMARK " + ("PASS" if report["passed"] else "FAIL") + ": not production validation")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
