# Contributing to KonaklamaFlow

Thank you for supporting open hospitality software!

1. Open an issue describing one real operational problem **without including guest records, hotel secrets, IDs or screenshots with personal data**.
2. Reproduce the problem using a minimal **fictional** JSON file based on `examples/demo.json`.
3. Fork and create a branch like `fix/overlap-case` or `feat/report-format`.
4. Add a regression test and run `python -m unittest discover -s tests -v`.
5. Open a pull request stating the behavior change, risks and whether it changes safety or privacy assumptions.
6. Maintainers review correctness, security/privacy, test coverage and documentation. Merge only after review.

AI-generated patches are welcome if they are reviewed, tested and clearly described. Synthetic fixtures only. Please keep changes focused.

### AI-assisted work and scarce Codex quota

When choosing between available AI development tools, reserve Codex for narrowly scoped, difficult architecture or constraint-solving work. Routine tests, docs, PR reviews, CI triage and small changes are handled directly through the connected GitHub workflow wherever practical. Read the [TR working agreement](docs/AI_WORK_ALLOCATION_TR.md). **Issue #62** is an example of a bounded Codex task; creating an issue does not automatically start Codex. Do not merge or deploy without review.

### Operator feedback without sensitive data

Hotel staff and independent testers can contribute without coding:
read the [TR/EN fictional test guide](docs/OPERATOR_FEEDBACK_TR_EN.md), execute one synthetic scenario and use the **Operator feedback (fictional data only)** issue template. Do not upload PMS exports, guest details or non-public access links.

Before proposing a release, check the [release channel guide](docs/RELEASE_CHANNELS_TR_EN.md). A PR and green tests are evidence of implementation, not evidence of production use.

### First issues

- Make the CLI error messages bilingual (Turkish + English).
- Improve accessibility and invalid-report validation in the offline HTML viewer.
- Strengthen twin/king bed preference policies with test vectors.
- Benchmark interval conflict detection against 10k synthetic reservations.
- Document a CSV-to-pseudonymized-JSON import contract without reading real guests.
