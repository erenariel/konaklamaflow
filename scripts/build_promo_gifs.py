"""Compatibility entry point for actual, source-bound offline browser recordings.

The original promotional composer is superseded by record_demo_tour.py.
No artificial counters, painted overlays or unmatched GIFs are emitted here.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
from record_demo_tour import ROOT, SHOWCASES, record_showcase


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, default=ROOT / 'demo/v04-integrated-preview.html')
    parser.add_argument('--out', type=Path, default=ROOT / 'docs/images')
    args = parser.parse_args(argv)
    if args.html.resolve() != (ROOT / 'demo/v04-integrated-preview.html').resolve():
        parser.error('Only the reviewed integrated demo may be recorded')
    try:
        for name in SHOWCASES:
            output = args.out / (name + '.gif')
            metadata = record_showcase(name, output)
            output.with_suffix('.json').write_text(json.dumps(metadata, indent=2) + chr(10), encoding='utf-8')
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, ImportError):
        print('Could not record the offline fictional browser showcase.', file=sys.stderr)
        return 2
    print('Recorded actual browser GIFs, posters and source-bound manifests; no network or live operations.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
