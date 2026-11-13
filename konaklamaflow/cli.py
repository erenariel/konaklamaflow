"""CLI entry point: no network, no credentials, no PMS integration."""
import argparse
from datetime import date
import json
from pathlib import Path
import sys
from .core import review, InputError

MAX_INPUT_BYTES = 32 * 1024 * 1024


def _read_json_with_limit(path: str):
    """Fail closed before decoding unbounded input. Identifiers stay private."""
    with open(path, "rb") as stream:
        payload = stream.read(MAX_INPUT_BYTES + 1)
    if len(payload) > MAX_INPUT_BYTES:
        raise InputError("input JSON exceeds 32 MiB safety limit")
    return json.loads(payload.decode("utf-8"))


def _ensure_distinct_paths(source: str, destination: str) -> None:
    input_path, output_path = Path(source), Path(destination)
    if (input_path.resolve() == output_path.resolve()
            or (output_path.exists() and output_path.samefile(input_path))):
        raise InputError("output path must differ from input to prevent data loss")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Review pseudonymized hotel reservations without modifying the PMS")
    parser.add_argument("input", help="Pseudonymized JSON input (max 32 MiB)")
    parser.add_argument("--as-of", default=date.today().isoformat(), help="Review date YYYY-MM-DD")
    parser.add_argument("--output", help="Optional JSON report output path; must differ from input")
    args = parser.parse_args(argv)
    try:
        data = _read_json_with_limit(args.input)
        report = review(data, args.as_of)
        payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            _ensure_distinct_paths(args.input, args.output)
            Path(args.output).write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")
        return 0
    except InputError as e:
        print(f"Input rejected: {e}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError):
        print("Input rejected: unable to read JSON input or write report", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
