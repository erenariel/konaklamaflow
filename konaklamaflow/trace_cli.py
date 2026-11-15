"""Only-offline fictional decision trace exporter and verifier.

Usage:
    python -m konaklamaflow.trace_cli --output /tmp/trace.json
    python -m konaklamaflow.trace_cli --verify /tmp/trace.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .experience_engine import evaluate
from .io_safety import read_limited_json, write_owner_report
from .decision_trace import fictional_walkthrough, verify_trace, TraceError

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "fictional-hotel.json"


def main(argv=None):
    parser = argparse.ArgumentParser(description="FICTIONAL non-authorizing trace")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", help="Write fictional trace to a separate JSON file")
    mode.add_argument("--verify", help="Check a previously generated fictional trace file")
    args = parser.parse_args(argv)
    try:
        source = read_limited_json(str(FIXTURE))
        report = evaluate(source)
        if args.output:
            trace = fictional_walkthrough(source, report)
            verify_trace(source, report, trace)
            output = json.dumps(trace, ensure_ascii=False, sort_keys=True,
                                indent=2, allow_nan=False) + "\n"
            write_owner_report(args.output, output, str(FIXTURE))
            print("Verified synthetic trace written (NOT a real operational audit)")
        else:
            trace = read_limited_json(args.verify)
            verify_trace(source, report, trace)
            print("Synthetic trace verified (NOT proof of staff identity or authorization)")
    except (OSError, ValueError, TypeError, RecursionError, OverflowError, TraceError):
        print("Invalid fictional trace or unsafe output path", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
