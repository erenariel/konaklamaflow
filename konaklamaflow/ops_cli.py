"""Read-only operations command line; emits a report without side effects."""
from __future__ import annotations
import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import InputError
from .operations import plan_operations


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise InputError("Duplicate JSON fields")
        obj[key] = value
    return obj


def _write_report(path, output):
    """Replace the complete report atomically with owner-only permissions."""
    target = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as stream:
            temporary = stream.name
            stream.write(output)
        os.replace(temporary, target)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build a privacy-first hotel check-in review queue")
    parser.add_argument("input", help="Pseudonymized JSON snapshot")
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--at-time", default="14:00")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args(argv)
    try:
        with open(args.input, "rb") as stream:
            payload = stream.read(2_000_001)
        if len(payload) > 2_000_000:
            raise InputError("Snapshot exceeds 2 MB limit")
        snapshot = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)
        result = plan_operations(snapshot, args.as_of, args.at_time)
        output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            _write_report(args.output, output)
        else:
            print(output, end="")
        return 0
    except (InputError, ValueError, RecursionError):
        print("Input rejected: invalid operational snapshot", file=sys.stderr)
    except (OSError, UnicodeError, json.JSONDecodeError):
        print("Input rejected: failed to read snapshot or write report", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
