"""Generate an offline, non-authorizing explanation artifact for an existing v0.3 report.

Usage: python -m konaklamaflow.explain_cli snapshot.json report.json [output.json]
Only *already minimized* synthetic or authorized data may be supplied.
"""
from __future__ import annotations

import json
import sys

from .explainability import ExplanationError, build_explanations
from .io_safety import MAX_INPUT_BYTES, read_limited_json, write_owner_report


def _read(path: str, limit: int):
    try:
        return read_limited_json(path, limit)
    except Exception as error:
        raise ExplanationError("Input too large") from error


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) not in (2, 3):
        print("usage: python -m konaklamaflow.explain_cli snapshot.json report.json [output.json]",
              file=sys.stderr)
        return 2
    try:
        source = _read(args[0], MAX_INPUT_BYTES)
        report = _read(args[1], MAX_INPUT_BYTES)
        output = json.dumps(build_explanations(source, report), ensure_ascii=False,
                            sort_keys=True, indent=2, allow_nan=False) + "\n"
        if len(args) == 3:
            write_owner_report(args[2], output, args[0], args[1])
        else:
            print(output, end="")
    except (ExplanationError, TypeError, ValueError, KeyError, OSError,
            UnicodeError, RecursionError, OverflowError):
        print("Invalid or stale minimized snapshot/report; no explanation written",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
