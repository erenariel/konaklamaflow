"""Build a read-only v0.3 review: python -m konaklamaflow.experience_cli input [output]."""
from __future__ import annotations

import json
import sys

from .core import InputError
from .experience_engine import evaluate, SnapshotError
from .io_safety import MAX_INPUT_BYTES, read_limited_json, write_owner_report


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) not in (1, 2):
        print('usage: python -m konaklamaflow.experience_cli snapshot.json [report.json]', file=sys.stderr)
        return 2
    try:
        source = read_limited_json(args[0], MAX_INPUT_BYTES)
        output = json.dumps(evaluate(source), indent=2, ensure_ascii=False, allow_nan=False) + '\n'
        if len(args) == 2:
            write_owner_report(args[1], output, args[0])
        else:
            print(output, end='')
    except (SnapshotError, InputError, ValueError, TypeError, OSError, UnicodeError, RecursionError):
        print('Invalid minimized operational snapshot or output path', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
