"""Generate a privacy-minimized translated pre-review from fictional v0.3 data.

Usage:
    python -m konaklamaflow.reason_i18n_cli <snapshot.json> <report.json> <locale> [output.json]

No network, model call or operational write. The output has *only* opaque task IDs,
localized rule reasons and no guest, room, PMS or payment references.
"""
from __future__ import annotations

import json
import sys

from .ops_cli import _unique_object, _write_report
from .reason_i18n import LocalizationError, localized_pre_review


def _read(path: str, size_limit: int):
    with open(path, "rb") as stream:
        payload = stream.read(size_limit + 1)
    if len(payload) > size_limit:
        raise LocalizationError("Input too large")
    return json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) not in (3, 4):
        print("Usage: python -m konaklamaflow.reason_i18n_cli snapshot.json report.json locale [output.json]",
              file=sys.stderr)
        return 2
    try:
        source = _read(args[0], 2_000_000)
        report = _read(args[1], 15_000_000)
        translated = localized_pre_review(source, report, args[2])
        output = json.dumps(translated, ensure_ascii=False, sort_keys=True,
                            indent=2, allow_nan=False) + "\n"
        if len(args) == 4:
            _write_report(args[3], output)
        else:
            print(output, end="")
        return 0
    except (LocalizationError, TypeError, ValueError, KeyError, UnicodeError,
            OSError, RecursionError, OverflowError):
        print("Could not safely translate this minimized snapshot and report", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
