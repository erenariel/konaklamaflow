"""Generate an offline, non-authorizing explanation artifact for an existing v0.3 report.

Usage: python -m konaklamaflow.explain_cli snapshot.json report.json [output.json]
Only *already minimized* synthetic or authorized data may be supplied.
"""
from __future__ import annotations

import json
import sys

from .explainability import ExplanationError, build_explanations
from .ops_cli import _unique_object, _write_report


def _read(path: str, limit: int):
    with open(path, "rb") as stream:
        payload = stream.read(limit + 1)
    if len(payload) > limit:
        raise ExplanationError("Input too large")
    return json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) not in (2, 3):
        print("usage: python -m konaklamaflow.explain_cli snapshot.json report.json [output.json]",
              file=sys.stderr)
        return 2
    try:
        source = _read(args[0], 2_000_000)
        report = _read(args[1], 15_000_000)
        output = json.dumps(build_explanations(source, report), ensure_ascii=False,
                            sort_keys=True, indent=2, allow_nan=False) + "\n"
        if len(args) == 3:
            _write_report(args[2], output)
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
