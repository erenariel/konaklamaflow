"""Embed the deterministic suite report in its offline viewer.

The browser displays a generated report instead of maintaining a second rule
engine. Run after regenerating examples/operations-evaluation.json; CI uses
--check to reject stale fixtures or embedded data. Only fictional fixtures belong
in this repository. No external services or credentials are used.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from konaklamaflow.experience_engine import evaluate  # noqa: E402

START = '// BEGIN GENERATED_SUITE_DATA'
END = '// END GENERATED_SUITE_DATA'


def safe_json(value):
    """Prevent any JSON text from terminating its inline HTML script element."""
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            .replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
            .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))


def embed(document, snapshot, report):
    if document.count(START) != 1 or document.count(END) != 1:
        raise ValueError('Missing or duplicate generated data markers')
    start = document.index(START)
    end = document.index(END, start) + len(END)
    block = (START + '\nconst INITIAL_DATA=' + safe_json(snapshot) + ';\n'
             + 'const INITIAL_EVALUATION=' + safe_json(report) + ';\n' + END)
    return document[:start] + block + document[end:]


def capture_previews():
    from playwright.sync_api import sync_playwright
    options = {'headless': True}
    if os.environ.get('KONAKLAMAFLOW_CHROMIUM'):
        options['executable_path'] = os.environ['KONAKLAMAFLOW_CHROMIUM']
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**options)
        try:
            for name, width, height in [('desktop-preview.png', 1440, 1000), ('mobile-preview.png', 390, 844)]:
                page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=1)
                errors = []
                requests = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('request', lambda request: requests.append(request.url))
                page.set_content((ROOT / 'demo/hotel-suite.html').read_text(encoding='utf-8'))
                page.locator('.metrics').first.wait_for(state='visible')
                if errors or requests:
                    raise ValueError('Offline preview failed')
                page.screenshot(path=str(ROOT / 'demo' / name), full_page=True, animations='disabled')
                page.close()
        finally:
            browser.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail instead of changing stale HTML')
    parser.add_argument('--screenshots', action='store_true', help='Capture desktop/mobile previews with optional Playwright')
    args = parser.parse_args(argv)
    try:
        snapshot = json.loads((ROOT / 'examples/fictional-hotel.json').read_text(encoding='utf-8'))
        report = json.loads((ROOT / 'examples/operations-evaluation.json').read_text(encoding='utf-8'))
        if evaluate(snapshot) != report:
            print('Suite report fixture is stale; regenerate it with the Python engine.', file=sys.stderr)
            return 1
        path = ROOT / 'demo/hotel-suite.html'
        current = path.read_text(encoding='utf-8')
        generated = embed(current, snapshot, report)
        if args.check:
            if generated != current:
                print('Offline suite data is stale; run scripts/generate_suite_demo.py.', file=sys.stderr)
                return 1
        else:
            path.write_text(generated, encoding='utf-8')
        if args.screenshots:
            if args.check:
                print('--screenshots cannot be combined with read-only --check.', file=sys.stderr)
                return 2
            capture_previews()
        print('Suite fixture and offline viewer match the Python rule report.')
        return 0
    except (ValueError, OSError, UnicodeError, TypeError):
        print('Could not verify the fictional suite fixtures or generated HTML.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
