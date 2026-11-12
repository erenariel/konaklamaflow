"""CLI entry point: no network, no credentials, no PMS integration."""
import argparse
from datetime import date
import json
from pathlib import Path
import sys
from .core import review, InputError


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Review pseudonymized hotel reservations without modifying the PMS")
    parser.add_argument("input", help="Pseudonymized JSON input")
    parser.add_argument("--as-of", default=date.today().isoformat(), help="Review date YYYY-MM-DD")
    parser.add_argument("--output", help="Optional JSON report output path")
    args = parser.parse_args(argv)
    try:
        with open(args.input, encoding="utf-8") as stream:
            data = json.load(stream)
        report = review(data, args.as_of)
        payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            Path(args.output).write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")
        return 0
    except InputError as e:
        print(f"Input rejected: {e}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError, json.JSONDecodeError):
        print("Input rejected: unable to read JSON input or write report", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
