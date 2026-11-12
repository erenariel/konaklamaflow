# Changelog

## Unreleased

- Present the demo with a warm boutique-hotel visual identity, architectural SVG illustration, clearer report cards, and responsive layouts.
- Show critical alerts first, add keyboard-operated severity filters, and explain known issue types in Turkish while retaining original report details.
- Distinguish the fictional sample from a selected report without making assumptions about uploaded content.
- Add reproducible report screenshots and a 1200×630 social preview; no external fonts, trackers, or image requests are introduced.
- Extend browser coverage to nine checks, including issue filters, report labels, and 320/390/768/1280-pixel layouts.

## [0.1.1] — 2026-11-12

- Validate schema 1.0 dry-run reports before rendering, including rows, dates, summary totals and advisory-only proposals.
- Keep the last valid report after a failed import; show private-data-safe inline errors.
- Add keyboard access, demo reset, same-file retry and protection against stale asynchronous file reads.
- Add seven Chromium regression checks and a browser CI job; keep the Python engine free of runtime dependencies.
- Add a tested-commit-only static demo deployment workflow, real CI badge, fictional screenshot and contribution templates.
- Focus public documentation on the product, testing and maintenance; remove application-planning and obsolete setup notes from the current tree.

## [0.1.0] — 2026-11-12 (prepared locally; not a published GitHub release)

- First deterministic hotel reservation dry-run reviewer.
- Typed input schema, privacy-preserving identifiers and explicit forbidden fields.
- Double booking, status, category, room maintenance, bed request and nightly-base-total checks.
- Date-based arrival queue and advisory room allocation suggestions.
- 23 standard-library unit tests and fictional demo.
- Offline browser report viewer (file picker, no network) for fictional or appropriately pseudonymized reports.
- MIT license, CI workflow, contribution process, security and product roadmap.
- Hardened error privacy, bounded monetary input, maximum-date validation and ignored local report output.

No live PMS connections, production users, deployments or releases are implied.
