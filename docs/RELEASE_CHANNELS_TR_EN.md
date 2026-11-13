# KonaklamaFlow — release channels / sürüm kanalları

**Snapshot: 13 November 2026.** The three version numbers below describe **different things**; none implies an operational hotel system.

| Surface | Current label | Meaning |
| --- | --- | --- |
| Published GitHub release | [v0.1.1](https://github.com/erenariel/konaklamaflow/releases/latest) | Last public tagged package/release at this snapshot |
| Python package metadata | `0.2.0rc1` in [pyproject.toml](../pyproject.toml) | Development release candidate; it is **not** a published stable v0.2.0 release |
| Browser presentation | v0.5 fictional workbench | Offline synthetic UI concept, **not** a certified/live PMS release |

**TR:** Demo için kullanılan v0.5 etiketi, yayınlanmış Python paketinin sürümünü değiştirmez. Reklam veya başvuruda yalnız yayımlanmış GitHub sürümünü "release" diye belirt. CI, uygulamanın belli testlerden geçtiğini gösterir; müşteri kullanımı, bağımsız güvenlik incelemesi veya gerçek entegrasyon kanıtı değildir.

**EN:** Do not collapse the demo/UI label, package metadata version and published tag into one release. Production readiness, deployment, user adoption, security certification and independent review are **unverified**.

## Releasing safely / Güvenli sürüm çıkarma

1. Fix the issue with fictional input and regression coverage. Review PR diff and privacy implications before merging.
2. Run `python -m unittest discover -s tests -v`, `python scripts/verify_commit_privacy.py`, `python scripts/generate_suite_demo.py --check` and `python scripts/generate_hotel_ops_demo.py --check`.
3. Run `python -m unittest discover -s tests/browser -v` with the optional Playwright dependency and check the commit-specific GitHub Actions results.
4. Check `pyproject.toml`, `CHANGELOG.md`, `SECURITY.md`, README badges and demo statements for consistency. Tag only a deliberately versioned, tested commit.
5. Publish release notes with compatibility and known limitations. Do not retroactively rewrite existing tags. Do not claim pilot outcomes that cannot be verified.

## Evidence we still need / Eksik kanıtlar

- Independent hotel-operator feedback obtained with explicit consent and **fictional** datasets.
- Independent code contributions/reviews and reproducible triage of real-world workflow problems.
- Transparent releases across a sustained maintenance period.
- Authorized read-only source integrations only after legal, vendor and property approval.

This guide describes project maintenance; it is not legal or security certification.
