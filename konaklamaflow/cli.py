"""CLI entry point: no network, no credentials, no PMS integration."""
import argparse
from datetime import date
from importlib import resources
import json
import sys

from .core import review, InputError
from .io_safety import MAX_INPUT_BYTES, read_limited_json, write_owner_report


def _output(report, path=None, sources=()):
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if path:
        write_owner_report(path, payload, *sources)
    else:
        print(payload, end="")
    return 0


def _run_demo(argv):
    parser = argparse.ArgumentParser(
        prog="konaklamaflow demo",
        description="Review the bundled fictional hotel snapshot; no hotel connection.",
    )
    parser.add_argument("--as-of", default="2026-11-12",
                        help="Review date YYYY-MM-DD (default: example fixture date)")
    parser.add_argument("--output", help="Optional owner-only local JSON report")
    args = parser.parse_args(argv)
    fixture = resources.files("konaklamaflow").joinpath("data", "demo.json")
    data = json.loads(fixture.read_text(encoding="utf-8"))
    return _output(review(data, args.as_of), args.output)


def _run_csv(argv):
    parser = argparse.ArgumentParser(
        prog="konaklamaflow review-csv",
        description=("Minimize two local, explicitly mapped CSV files into "
                     "pseudonymous memory-only rule input. This is NOT "
                     "irreversible anonymization or legal clearance."),
    )
    parser.add_argument("--rooms", required=True, help="Local rooms CSV")
    parser.add_argument("--reservations", required=True,
                        help="Local reservations CSV")
    parser.add_argument("--as-of", default=date.today().isoformat(),
                        help="Review date YYYY-MM-DD")
    parser.add_argument("--output",
                        help="Optional local JSON report (mode 0600); do not share")
    args = parser.parse_args(argv)
    from .local_csv import import_csv_snapshot

    snapshot = import_csv_snapshot(args.rooms, args.reservations)
    return _output(review(snapshot, args.as_of), args.output,
                   (args.rooms, args.reservations))


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv and argv[0] == "demo":
            return _run_demo(argv[1:])
        if argv and argv[0] == "review-csv":
            return _run_csv(argv[1:])
        # Existing JSON CLI syntax remains backward compatible.
        parser = argparse.ArgumentParser(
            description="Review pseudonymized hotel reservations without modifying the PMS",
        )
        parser.add_argument("input", help="Pseudonymized JSON input (max 2 MB)")
        parser.add_argument("--as-of", default=date.today().isoformat(),
                            help="Review date YYYY-MM-DD")
        parser.add_argument("--output",
                            help="Optional JSON report output path; must differ from input")
        args = parser.parse_args(argv)
        data = read_limited_json(args.input, MAX_INPUT_BYTES)
        return _output(review(data, args.as_of), args.output, (args.input,))
    except InputError as e:
        # Error messages are generic and contain no CSV cell contents.
        print(f"Input rejected: {e}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError, RecursionError, ValueError, TypeError):
        print("Input rejected: unable to read source or write report",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
