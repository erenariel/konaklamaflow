"""Read-only operations command line; emits a report without side effects."""
from __future__ import annotations
import argparse
from datetime import date
import json
import sys
from .core import InputError
from .operations import plan_operations


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build a privacy-first hotel check-in review queue")
    parser.add_argument("input", help="Pseudonymized JSON snapshot")
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--at-time", default="14:00")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args(argv)
    try:
        with open(args.input, encoding="utf-8") as stream:
            snapshot = json.load(stream)
        result = plan_operations(snapshot, args.as_of, args.at_time)
        output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            with open(args.output, "w", encoding="utf-8") as stream:
                stream.write(output)
        else:
            print(output, end="")
        return 0
    except (InputError, ValueError):
        print("Input rejected: invalid operational snapshot", file=sys.stderr)
    except (OSError, UnicodeError, json.JSONDecodeError):
        print("Input rejected: failed to read snapshot or write report", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
