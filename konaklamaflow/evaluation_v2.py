"""Benchmark v2: transparent, project-authored synthetic rule-label evaluation.

Each scored unit is ONE (scenario, reservation, reason-code) boolean label.
Multiple labels may share a scenario; these are NOT independent hotel stays.
A mismatch is recorded as FP/FN, never silently removed from the denominator.
No hotel data, live PMS/OTA/KBS calls, guest identities or network traffic.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

from .evaluation import (
    EvaluationError, SOURCE_FIXTURE, _mutation, _prediction, _require,
    render_markdown as render_legacy_markdown, score,
)
from .experience_engine import BLOCKER_CODES, evaluate
from .io_safety import read_limited_json, write_owner_report

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_V2 = ROOT / "evaluation" / "benchmark_v2.json"
SCHEMA_V2 = "konaklamaflow.synthetic-evaluation.v2"
IDENT = re.compile(r"^[A-Za-z0-9_-]{1,50}$")
EXCLUSIONS = frozenset({
    "NO_EVENT_REVISION_MODEL",
    "NO_PARTIAL_CANCELLATION_MODEL",
    "SPLIT_STAY_TRUTH_UNREVIEWED",
})
# These are named, reviewed transformations on a PUBLIC FICTIONAL fixture.
# No arbitrary JSON patch or user-supplied script can be embedded in a label.
SCENARIOS = frozenset({
    "none", "duplicate_reference", "room_overlap", "maintenance_open",
    "channel_status_conflict", "cancelled_without_room", "duplicate_pms",
    "category_mismatch", "twin_mismatch", "contradictory_beds", "dirty_room",
    "out_of_service", "payment_review", "identity_unverified",
    "pms_missing", "future_arrival", "guest_expected", "before_checkin",
    "no_show", "amenity_missing", "task_closed", "pms_recorded",
    "same_day_checkout",
})
LEGACY_SCENARIOS = frozenset({
    "none", "duplicate_reference", "room_overlap", "maintenance_open",
    "channel_status_conflict", "cancelled_without_room",
})


def _validated_manifest(manifest, source):
    _require(type(manifest) is dict and set(manifest) == {
        "schema_version", "source_fixture", "method", "cases"
    })
    _require(manifest["schema_version"] == SCHEMA_V2)
    _require(manifest["source_fixture"] == "examples/fictional-hotel.json")
    _require(manifest["method"] == "author_labeled_single_reason_observation")
    _require(type(source) is dict and source.get("schema_version") == "0.3")
    cases = manifest["cases"]
    _require(type(cases) is list and 30 <= len(cases) <= 50)
    ids = set()
    tuples = set()
    known_res = {r["id"] for r in source["reservations"]}
    evaluated = excluded = positive = negative = 0
    for item in cases:
        _require(type(item) is dict)
        case_id = item.get("id")
        _require(type(case_id) is str and IDENT.fullmatch(case_id) is not None
                 and case_id not in ids)
        ids.add(case_id)
        _require(type(item.get("category")) is str
                 and IDENT.fullmatch(item["category"]) is not None)
        if item.get("status") == "evaluated":
            _require(set(item) == {
                "id", "category", "status", "scenario", "reservation_id",
                "reason_code", "expected", "rationale",
            })
            _require(item["scenario"] in SCENARIOS)
            _require(item["reservation_id"] in known_res)
            _require(item["reason_code"] in BLOCKER_CODES)
            _require(type(item["expected"]) is bool)
            _require(type(item["rationale"]) is str
                     and 20 <= len(item["rationale"]) <= 250)
            key = (item["scenario"], item["reservation_id"],
                   item["reason_code"])
            _require(key not in tuples)
            tuples.add(key)
            evaluated += 1
            positive += item["expected"]
            negative += not item["expected"]
        else:
            _require(item.get("status") in {"unsupported", "unlabelled"})
            _require(set(item) == {"id", "category", "status", "reason"})
            _require(item["reason"] in EXCLUSIONS)
            excluded += 1
    _require(evaluated >= 30 and positive >= 10 and negative >= 10
             and excluded >= 2)
    _require(len({c["scenario"] for c in cases
                  if c["status"] == "evaluated"}) >= 12)
    return cases


def _scenario(source, name):
    """Rebuild each synthetic case from the same original fixture."""
    _require(name in SCENARIOS)
    if name in LEGACY_SCENARIOS:
        return _mutation(source, name)

    snapshot = deepcopy(source)
    bookings = {b["id"]: b for b in snapshot["reservations"]}
    rooms = {r["id"]: r for r in snapshot["rooms"]}
    a, b = bookings["KF1001"], bookings["KF1002"]
    if name == "duplicate_pms":
        b["pms_ref"] = a["pms_ref"]
    elif name == "category_mismatch":
        a["category"] = "superior"
    elif name == "twin_mismatch":
        a["bed_request"] = "twin"
        a["requests"] = []
    elif name == "contradictory_beds":
        a["requests"] = ["twin", "double"]
    elif name == "dirty_room":
        rooms["101"]["housekeeping"] = "dirty"
    elif name == "out_of_service":
        rooms["101"]["housekeeping"] = "out_of_service"
    elif name == "payment_review":
        a["payment_signal"] = "review"
    elif name == "identity_unverified":
        a["identity_signal"] = "pending_staff"
    elif name == "pms_missing":
        a["pms_ref"] = None
    elif name == "future_arrival":
        a["arrival"] = "2026-11-13"
    elif name == "guest_expected":
        a["arrival_state"] = "expected"
    elif name == "before_checkin":
        snapshot["at_time"] = "13:00"
    elif name == "no_show":
        a["status"] = "no_show"
        a["arrival_state"] = "expected"
    elif name == "amenity_missing":
        a["requests"] = ["accessible"]
    elif name == "task_closed":
        task = next(t for t in snapshot["tasks"] if t["id"] == "T1001")
        task["status"] = "done"
    elif name == "pms_recorded":
        a["pms_registration"] = "recorded_by_authorized_staff"
    elif name == "same_day_checkout":
        b.update({
            "arrival": "2026-11-15", "departure": "2026-11-17",
            "room_id": "101", "category": "standard",
            "bed_request": "double", "requests": [],
        })
    else:
        raise EvaluationError("Unknown synthetic scenario")
    return snapshot


def run_evaluation_v2(manifest, source, engine=evaluate):
    """Report all observed mismatches without manufacturing a pass."""
    cases = _validated_manifest(manifest, source)
    original = deepcopy(source)
    snapshots = {}
    details = []
    pairs = []
    per_category = {}
    for case in cases:
        if case["status"] != "evaluated":
            details.append({
                "id": case["id"], "category": case["category"],
                "status": case["status"], "reason": case["reason"],
            })
            continue
        variant = case["scenario"]
        if variant not in snapshots:
            snapshots[variant] = _scenario(original, variant)
        # An explicit new run per case is intentional: labels are not
        # independent, but all observed predictions use the real rule engine.
        snapshot = deepcopy(snapshots[variant])
        result = engine(deepcopy(snapshot))
        predicted = _prediction(snapshot, result, case["reservation_id"],
                                case["reason_code"])
        expected = case["expected"]
        pairs.append((expected, predicted))
        outcome = ("TP" if expected and predicted
                   else "FN" if expected else "FP" if predicted else "TN")
        row = {
            "id": case["id"], "category": case["category"],
            "scenario": variant, "status": "pass" if expected == predicted else "fail",
            "outcome": outcome, "reservation_id": case["reservation_id"],
            "reason_code": case["reason_code"],
            "expected": expected, "predicted": predicted,
            "rationale": case["rationale"],
        }
        details.append(row)
        per_category.setdefault(case["category"], []).append(
            (expected, predicted))
    metrics = score(pairs)
    failures = metrics["fn"] + metrics["fp"]
    count = len(cases)
    supported = len(pairs)
    manifest_fingerprint = sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": SCHEMA_V2,
        "mode": "DRY_RUN_ONLY",
        "dataset": "FICTIONAL_PROJECT_AUTHORED_NOT_INDEPENDENTLY_VALIDATED",
        "metric_unit": "scenario_reservation_reason_code_binary_label",
        "method": manifest["method"],
        "manifest_sha256": manifest_fingerprint,
        "result": "pass" if not failures else "fail",
        "summary": {
            "total_cases": count, "evaluated": supported,
            "passed_labeled_cases": supported - failures,
            "failed_labeled_cases": failures,
            "unsupported": sum(c["status"] == "unsupported" for c in cases),
            "unlabelled": sum(c["status"] == "unlabelled" for c in cases),
            "coverage": supported / count,
            "distinct_scenarios": len(snapshots),
            "distinct_reason_codes": len({c["reason_code"] for c in cases
                                          if c["status"] == "evaluated"}),
            "label_agreement": (supported - failures) / supported,
        },
        "metrics": metrics,
        "by_category": {
            k: {"observations": len(v), "metrics": score(v)}
            for k, v in sorted(per_category.items())
        },
        "human_override_rate": "not_measured",
        "processing_time_ms": "not_measured",
        "independent_expert_review": "not_performed",
        "cases": details,
    }


def render_markdown_v2(report):
    """Display failure cases and exclusions, never just a flattering rate."""
    if report.get("schema_version") != SCHEMA_V2:
        raise EvaluationError("Invalid benchmark v2 report")
    s, m = report["summary"], report["metrics"]
    def ratio(value):
        return "undefined" if value is None else f"{value:.3f}"
    lines = [
        "# KonaklamaFlow — Benchmark v2 (project-authored, fictional only)",
        "",
        f"**Result:** {report['result']} · **Mode:** DRY_RUN_ONLY",
        f"**Coverage:** {s['evaluated']}/{s['total_cases']} ({ratio(s['coverage'])})",
        f"**Labeled agreement:** {s['passed_labeled_cases']}/{s['evaluated']} "
        f"({ratio(s['label_agreement'])}); **mismatches:** {s['failed_labeled_cases']}",
        f"**Distinct fictional snapshots:** {s['distinct_scenarios']}; "
        f"**distinct reason codes:** {s['distinct_reason_codes']}",
        f"**Excluded:** unsupported={s['unsupported']}, "
        f"unlabelled={s['unlabelled']}",
        f"**TP={m['tp']}, FP={m['fp']}, TN={m['tn']}, FN={m['fn']}**",
        f"Precision={ratio(m['precision'])}, Recall={ratio(m['recall'])}, "
        f"FPR={ratio(m['false_positive_rate'])}, "
        f"FNR={ratio(m['false_negative_rate'])}",
        "",
        "Unit: one (scenario, reservation ID, reason code) presence label; "
        "multiple labels may use the same synthetic scenario.",
        "Labels and mutation design are project-authored; no independent "
        "expert, real hotel accuracy or external pilot is claimed.",
        "Unsupported and unlabelled cases are excluded from scored metrics, "
        "but included in total coverage.",
        "No live AI/PMS/OTA/KBS, guest data, payments or check-in writes.",
        "",
        "## Measured cases (including all failures)",
        "",
        "| Case | Scenario | Reservation | Code | Expected | Observed | Outcome |",
        "| --- | --- | --- | --- | :---: | :---: | --- |",
    ]
    for c in report["cases"]:
        if c["status"] in {"unsupported", "unlabelled"}:
            continue
        lines.append(
            f"| {c['id']} | {c['scenario']} | {c['reservation_id']} | "
            f"{c['reason_code']} | {str(c['expected']).lower()} | "
            f"{str(c['predicted']).lower()} | {c['outcome']} |"
        )
    lines += ["", "## Excluded — not scored", "",
              "| Case | Type | Reason |", "| --- | --- | --- |"]
    for c in report["cases"]:
        if c["status"] in {"unsupported", "unlabelled"}:
            lines.append(f"| {c['id']} | {c['status']} | {c['reason']} |")
    lines += ["", "## Label disagreement detail", ""]
    errors = [c for c in report["cases"] if c["status"] == "fail"]
    if not errors:
        lines.append("No mismatches observed for the **project-authored** "
                     "scored labels; this does **not** establish independent accuracy.")
    else:
        for c in errors:
            lines.append(
                f"- **{c['id']}**: {c['outcome']} for {c['reservation_id']}/"
                f"{c['reason_code']}; expected={c['expected']}, "
                f"observed={c['predicted']}. Rationale: {c['rationale']}"
            )
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Offline, transparent project-authored Benchmark v2"
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_V2))
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--markdown", dest="markdown_path")
    parser.add_argument(
        "--strict", action="store_true",
        help="Exit 1 on any labeled disagreement (diagnostic default is 0)",
    )
    args = parser.parse_args(argv)
    try:
        manifest = read_limited_json(args.manifest)
        source = read_limited_json(str(SOURCE_FIXTURE))
        report = run_evaluation_v2(manifest, source)
        json_output = json.dumps(report, indent=2, ensure_ascii=False,
                                 sort_keys=True, allow_nan=False) + "\n"
        markdown_output = render_markdown_v2(report)
        if args.json_path and args.markdown_path:
            _require(Path(args.json_path).resolve() !=
                     Path(args.markdown_path).resolve())
        if args.json_path:
            write_owner_report(args.json_path, json_output,
                               args.manifest, str(SOURCE_FIXTURE),
                               *([args.markdown_path] if args.markdown_path
                                  and Path(args.markdown_path).exists() else []))
        if args.markdown_path:
            write_owner_report(args.markdown_path, markdown_output,
                               args.manifest, str(SOURCE_FIXTURE),
                               *([args.json_path] if args.json_path else []))
        if not args.json_path and not args.markdown_path:
            print(markdown_output, end="")
        # Diagnostic command records mismatches without failing CI. Strict
        # is available when a release demands zero labeled mismatches.
        return 1 if args.strict and report["result"] == "fail" else 0
    except (EvaluationError, OSError, ValueError, TypeError, RecursionError):
        print("Invalid synthetic benchmark v2 input or output", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
