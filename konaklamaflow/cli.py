"""CLI entry point: no network, no credentials, no PMS integration."""
import argparse
from datetime import date
import json
import sys
from .core import review, InputError
from .io_safety import MAX_INPUT_BYTES, read_limited_json, write_owner_report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Review pseudonymized hotel reservations without modifying the PMS")
    parser.add_argument("input", help="Pseudonymized JSON input (max 2 MB)")
    parser.add_argument("--as-of", default=date.today().isoformat(), help="Review date YYYY-MM-DD")
    parser.add_argument("--output", help="Optional JSON report output path; must differ from input")
    args = parser.parse_args(argv)
    try:
        data = read_limited_json(args.input, MAX_INPUT_BYTES)
        report = review(data, args.as_of)
        payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            write_owner_report(args.output, payload, args.input)
        else:
            print(payload, end="")
        return 0
    except InputError as e:
        print(f"Input rejected: {e}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError, RecursionError):
        print("Input rejected: unable to read JSON input or write report", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
