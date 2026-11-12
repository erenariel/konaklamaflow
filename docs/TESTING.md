# Testing KonaklamaFlow

Run checks from the repository root with Python 3.11 or newer. The runtime and test suite use only the Python standard library.

```bash
python -m unittest discover -s tests -v
python -m konaklamaflow examples/demo.json --as-of 2026-11-12 --output report.json
```

The suite currently has 23 tests covering room overlaps, adjacent stays, maintenance, cancelled holds, bed requests, duplicate references, price consistency, deterministic output, and input validation. The local `report.json` is ignored by Git; never commit private operational reports.

## Check the fictional demo

The demo contains five fictional rooms and five fictional reservations. Its report should match `examples/demo-report.json`, including one critical alert, two review alerts, one room proposal, and three next-day arrivals. Compare parsed JSON objects if your platform uses different line endings.

Open `demo/viewer.html` in a browser. Confirm the embedded report renders, then select `examples/demo-report.json` with the file picker. Both views should show the same figures. No server, login, or external API is needed. Use only fictional data when sharing screenshots or bug reports.

## Browser regression tests

Browser checks are optional development dependencies, separate from the dependency-free Python engine:

```bash
python -m pip install -e '.[browser]'
python -m playwright install chromium
python -m unittest discover -s tests/browser -v
```

The nine Chromium checks cover valid import, keyboard access to the file picker, malformed and unsupported reports, summary consistency, the 3 MB limit, retrying the same file, HTML-as-text rendering, reset, concurrent imports, mobile overflow, keyboard-operated issue filters, accurate demo/import labels, and absence of network requests. They load the self-contained HTML into a browser page; they do not test the hosting service.

In environments with a preinstalled Chromium, set `KONAKLAMAFLOW_CHROMIUM` to its executable path. CI installs the Playwright-managed browser.

## Continuous integration

The [tests workflow](https://github.com/erenariel/konaklamaflow/actions/workflows/tests.yml) runs the unit suite and fictional demo on Python 3.11, 3.12, and 3.13 for pushes and pull requests. Inspect the run for the commit you are reviewing; a previous successful run does not validate later changes.

A separate Chromium job runs the browser regression suite. The Pages workflow publishes only the fictional viewer and its preview images after a successful push CI run on this repository's main branch; private reports and repository administration notes are not included.

## Add a regression test

1. Build the smallest fictional input that reproduces the issue.
2. Assert the expected operational result or rejected input.
3. Verify the test fails before the fix and passes afterwards.
4. Run the complete suite and demo before submitting a pull request.

Tests and CI are evidence of the checked behavior. They are not production certification, proof of anonymization, or an independent security audit.

## Refresh the presentation assets

The preview images use only the embedded fictional report and repository-owned SVG artwork. After installing the browser extra, run:

```bash
python scripts/capture_previews.py
```

This captures the report panel and a 1200×630 share card into `docs/images/`. It does not read an operator report or contact the network. You can use `KONAKLAMAFLOW_CHROMIUM` as described above when using a preinstalled browser.
