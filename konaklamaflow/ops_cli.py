"""Read-only operations command line; emits a report without side effects."""
from __future__ import annotations
import argparse
from datetime import date
import json
import sys
from .core import InputError
from .io_safety import MAX_INPUT_BYTES, read_limited_json, write_owner_report
from .operations import plan_operations

# Kept for older in-repo callers. New code should import io_safety directly.
from .io_safety import unique_object as _unique_object  # noqa: E402
_write_report = write_owner_report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build a privacy-first hotel check-in review queue")
    parser.add_argument("input", help="Pseudonymized JSON snapshot")
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--at-time", default="14:00")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args(argv)
    try:
        snapshot = read_limited_json(args.input, MAX_INPUT_BYTES)
        result = plan_operations(snapshot, args.as_of, args.at_time)
        output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            write_owner_report(args.output, output, args.input)
        else:
            print(output, end="")
        return 0
    except (InputError, ValueError, RecursionError):
        print("Input rejected: invalid operational snapshot", file=sys.stderr)
    except (OSError, UnicodeError):
        print("Input rejected: failed to read snapshot or write report", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
