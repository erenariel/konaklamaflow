# Maintenance roadmap

KonaklamaFlow is an early offline reservation review prototype. This roadmap tracks useful work for hotel operators and contributors. Planned items are not current features.

## Current baseline

- Python CLI, pseudonymized JSON input, deterministic rules, and an offline report viewer.
- MIT license and fictional fixtures.
- Unit tests and GitHub Actions on Python 3.11, 3.12, and 3.13.

## Next priorities

| Work | Completion criteria |
| --- | --- |
| Invalid report handling | The viewer rejects malformed reports clearly and keeps a usable screen. |
| Accessibility | Keyboard navigation, file-picker focus, readable alerts, and mobile layout are checked. |
| Operational test coverage | Synthetic scenarios cover split stays and constrained bed availability; unsupported cases are documented. |
| Import contract | A documented CSV-to-JSON mapping removes identity data before input; no live PMS access is needed. |
| Clearer local guidance | Turkish and English CLI instructions explain errors and required manual review. |

Discuss a feature in an issue before making a large change. Scope it to an observable outcome and include fictional acceptance examples.

## Feedback and triage

Ask willing operators which daily check is unclear or time-consuming. Request a description, not a PMS export. Turn a reproducible problem into a synthetic fixture and record the expected result. Track actual feedback and accepted changes; do not treat untested suggestions as measured impact.

Contributors can help by reproducing reported issues, improving documentation, testing the viewer with a keyboard, and reviewing synthetic hotel scenarios.

## Releases

Keep the changelog aligned with implemented behavior. Check CI for the release commit, verify the demo, and document compatibility changes before tagging a release. Do not label the prototype production-ready without the necessary review and evidence.

## Longer-term work

Property policies, a stable input schema, an audit format, and vendor-supported read-only adapters require separate designs and review. Any adapter must have property and vendor authorization. Guest messaging, official KBS reporting, and writes to live hotel systems remain outside this prototype.
