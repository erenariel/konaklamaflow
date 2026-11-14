"""Offline, truth-labeled synthetic evaluation of the existing v0.3 rule engine.

No AI provider, API, PMS, KBS, payment, network or production data. Each scored
observation is a (case, reservation_id, reason_code) binary label, not an
independent claim about a whole hotel stay.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import sys

from .experience_engine import BLOCKER_CODES, evaluate
from .io_safety import read_limited_json, write_owner_report

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "evaluation" / "benchmark.json"
SOURCE_FIXTURE = ROOT / "examples" / "fictional-hotel.json"
SCHEMA = "konaklamaflow.synthetic-evaluation.v1"
MUTATIONS = frozenset({
    "none", "duplicate_reference", "room_overlap", "maintenance_open",
    "channel_status_conflict", "cancelled_without_room"
})
IDENT = re.compile(r"^[A-Za-z0-9_-]{1,50}$")


class EvaluationError(ValueError):
    """Fail closed without revealing source contents."""


def _require(condition):
    if not condition:
        raise EvaluationError("Invalid synthetic evaluation input or output")


def _validated_manifest(manifest, source):
    _require(isinstance(manifest, dict) and set(manifest) == {
        "schema_version", "source_fixture", "cases"
    })
    _require(manifest["schema_version"] == SCHEMA)
    _require(manifest["source_fixture"] == "examples/fictional-hotel.json")
    _require(isinstance(source, dict) and source.get("schema_version") == "0.3")
    _require(isinstance(manifest["cases"], list) and 1 <= len(manifest["cases"]) <= 200)
    ids = set()
    reservation_ids = {
        row.get("id") for row in source.get("reservations", [])
        if isinstance(row, dict)
    } if isinstance(source.get("reservations"), list) else set()
    for case in manifest["cases"]:
        _require(isinstance(case, dict))
        _require(isinstance(case.get("id"), str)
                 and IDENT.fullmatch(case["id"]) is not None)
        _require(case["id"] not in ids)
        ids.add(case["id"])
        _require(isinstance(case.get("category"), str)
                 and IDENT.fullmatch(case["category"]) is not None)
        status = case.get("status")
        if status == "evaluated":
            _require(set(case) == {"id", "category", "status", "mutation",
                                   "reservation_id", "reason_code", "expected"})
            _require(case["mutation"] in MUTATIONS)
            _require(case["reservation_id"] in reservation_ids)
            _require(case["reason_code"] in BLOCKER_CODES)
            _require(type(case["expected"]) is bool)
        else:
            _require(status in {"unsupported", "unlabelled"})
            _require(set(case) == {"id", "category", "status", "reason"})
            _require(isinstance(case["reason"], str)
                     and 8 <= len(case["reason"]) <= 300)
    return manifest["cases"]


def _mutation(source, mutation):
    """Limited, documented transformations of public, already-synthetic data."""
    snapshot = deepcopy(source)
    bookings = {row["id"]: row for row in snapshot["reservations"]}
    if mutation == "duplicate_reference":
        bookings["KF1002"]["channel"] = bookings["KF1001"]["channel"]
        bookings["KF1002"]["external_ref"] = bookings["KF1001"]["external_ref"]
    elif mutation == "room_overlap":
        bookings["KF1002"]["room_id"] = "101"
        bookings["KF1002"]["category"] = "standard"
        bookings["KF1002"]["bed_request"] = "double"
        bookings["KF1002"]["requests"] = []
    elif mutation == "maintenance_open":
        snapshot["tasks"].append({
            "id": "EVAL_T900", "kind": "maintenance", "room_id": "101",
            "reservation_id": "KF1001", "status": "open", "priority": "high"
        })
    elif mutation == "channel_status_conflict":
        event = next(e for e in snapshot["channel_events"] if e["id"] == "E1001")
        event["status"] = "cancelled"
    elif mutation == "cancelled_without_room":
        bookings["KF1006"]["room_id"] = None
    elif mutation != "none":
        raise EvaluationError("Unknown synthetic mutation")
    return snapshot


def _prediction(report, reservation_id, reason_code):
    """Only authoritative arrivals[ID].blockers can count as a prediction."""
    _require(isinstance(report, dict) and report.get("schema_version") == "0.3"
             and report.get("mode") == "DRY_RUN_ONLY")
    policy = report.get("approval_policy")
    _require(isinstance(policy, dict) and
             policy.get("human_approval_required") is True)
    arrivals = report.get("arrivals")
    _require(isinstance(arrivals, list))
    rows = {}
    for row in arrivals:
        _require(isinstance(row, dict) and isinstance(row.get("id"), str))
        _require(row["id"] not in rows)
        blockers = row.get("blockers")
        _require(isinstance(blockers, list)
                 and len(blockers) == len(set(blockers))
                 and all(isinstance(code, str) and code in BLOCKER_CODES
                         for code in blockers))
        _require(row.get("human_approval_required") is True)
        _require(row.get("status") in {"blocked", "review_ready", "other"})
        _require(row["status"] == "blocked" if blockers else row["status"] != "blocked")
        rows[row["id"]] = blockers
    _require(reservation_id in rows)
    return reason_code in rows[reservation_id]


def _fraction(numerator, denominator):
    """Undefined metrics have null, never fabricated zero or 100%."""
    return numerator / denominator if denominator else None


def score(pairs):
    """Binary classification with one observation per labeled (case, target, code)."""
    tp = fp = tn = fn = 0
    for expected, predicted in pairs:
        _require(type(expected) is bool and type(predicted) is bool)
        if expected and predicted:
            tp += 1
        elif expected:
            fn += 1
        elif predicted:
            fp += 1
        else:
            tn += 1
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": _fraction(tp, tp + fp),
        "recall": _fraction(tp, tp + fn),
        "false_positive_rate": _fraction(fp, fp + tn),
        "false_negative_rate": _fraction(fn, fn + tp),
        "undefined_metrics": {
            name: denominator == 0 for name, denominator in {
                "precision": tp + fp,
                "recall": tp + fn,
                "false_positive_rate": fp + tn,
                "false_negative_rate": fn + tp,
            }.items()
        },
    }


def run_evaluation(manifest, source, engine=evaluate):
    cases = _validated_manifest(manifest, source)
    observations = []
    details = []
    for case in cases:
        if case["status"] != "evaluated":
            details.append({
                "id": case["id"], "category": case["category"],
                "status": case["status"], "reason": case["reason"],
            })
            continue
        # Evaluate each mutated snapshot independently, never reuse stale results.
        report = engine(_mutation(source, case["mutation"]))
        predicted = _prediction(report, case["reservation_id"], case["reason_code"])
        expected = case["expected"]
        observations.append((expected, predicted))
        details.append({
            "id": case["id"], "category": case["category"],
            "status": "pass" if expected == predicted else "fail",
            "reservation_id": case["reservation_id"],
            "reason_code": case["reason_code"],
            "expected": expected, "predicted": predicted,
        })
    metrics = score(observations)
    passed = metrics["fp"] == 0 and metrics["fn"] == 0
    return {
        "schema_version": SCHEMA,
        "mode": "DRY_RUN_ONLY",
        "dataset": "SYNTHETIC_PROJECT_AUTHORED_LABELS_NOT_INDEPENDENTLY_VALIDATED",
        "metric_unit": "one_case_one_reservation_one_reason_code_binary_label",
        "result": "pass" if passed else "fail",
        "summary": {
            "total_cases": len(cases),
            "evaluated": len(observations),
            "unsupported": sum(c["status"] == "unsupported" for c in cases),
            "unlabelled": sum(c["status"] == "unlabelled" for c in cases),
            "coverage": _fraction(len(observations), len(cases)),
            "failed_labeled_cases": metrics["fp"] + metrics["fn"],
        },
        "metrics": metrics,
        "human_override_rate": "not_measured",
        "processing_time_ms": "not_measured",
        "independent_expert_review": "not_performed",
        "cases": details,
    }


def render_markdown(report):
    metrics = report["metrics"]
    summary = report["summary"]

    def display(value):
        return "undefined (zero denominator)" if value is None else f"{value:.4f}"

    lines = [
        "# KonaklamaFlow — Synthetic Evaluation (not a live hotel result)",
        "",
        f"**Status:** {report['result']} · **Mode:** DRY_RUN_ONLY",
        f"**Coverage:** {summary['evaluated']}/{summary['total_cases']} "
        f"({display(summary['coverage'])})",
        f"**Excluded:** unsupported={summary['unsupported']}, "
        f"unlabelled={summary['unlabelled']}",
        "",
        "| TP | FP | TN | FN | Precision | Recall | FPR | FNR |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| {metrics['tp']} | {metrics['fp']} | {metrics['tn']} | {metrics['fn']} "
        f"| {display(metrics['precision'])} | {display(metrics['recall'])} "
        f"| {display(metrics['false_positive_rate'])} "
        f"| {display(metrics['false_negative_rate'])} |",
        "",
        "Unit: one labeled (case, reservation ID, reason code), binary presence.",
        "Undefined ratios are not assumed to be zero. "
        "No real pilot, actual AI call, independent expert review, "
        "human override measurement, or production reliability claim.",
        "",
        "| Case | Category | Status |",
        "| --- | --- | --- |",
    ]
    for case in report["cases"]:
        lines.append(f"| {case['id']} | {case['category']} | {case['status']} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="OFFLINE synthetic rule evaluation")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--markdown", dest="markdown_path")
    args = parser.parse_args(argv)
    try:
        manifest = read_limited_json(args.manifest)
        source = read_limited_json(str(SOURCE_FIXTURE))
        report = run_evaluation(manifest, source)
        json_output = json.dumps(report, indent=2, ensure_ascii=False,
                                 sort_keys=True, allow_nan=False) + "\n"
        markdown_output = render_markdown(report)
        if args.json_path and args.markdown_path:
            _require(Path(args.json_path).resolve() !=
                     Path(args.markdown_path).resolve())
        if args.json_path:
            write_owner_report(args.json_path, json_output,
                               args.manifest, str(SOURCE_FIXTURE),
                               *([args.markdown_path] if args.markdown_path and
                                 Path(args.markdown_path).exists() else []))
        if args.markdown_path:
            write_owner_report(args.markdown_path, markdown_output,
                               args.manifest, str(SOURCE_FIXTURE),
                               *([args.json_path] if args.json_path else []))
        if not args.json_path and not args.markdown_path:
            print(markdown_output, end="")
        return 0 if report["result"] == "pass" else 1
    except (EvaluationError, OSError, ValueError, TypeError, RecursionError):
        print("Invalid synthetic evaluation data or output destination", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
