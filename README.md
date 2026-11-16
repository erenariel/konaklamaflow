# KonaklamaFlow 🏨

**MIT-licensed, offline hotel reservation conflict reviewer and operations prototype.**  
**Rezervasyon çakışması ve oda uygunluğu incelemesine odaklanan açık kaynak, çevrimdışı otel operasyon prototipi.**

[![Tests](https://github.com/erenariel/konaklamaflow/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/erenariel/konaklamaflow/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python package](https://img.shields.io/badge/Python-0.2.0rc1%20candidate-orange)](pyproject.toml)
[![Offline demo](https://img.shields.io/badge/demo-v0.5.x%20fictional-blue)](https://erenariel.github.io/konaklamaflow/)

## Try it / Demoyu aç

- **[Interactive fictional hotel demo / Çalışan kurgusal demo](https://erenariel.github.io/konaklamaflow/)**
- **[Visual project overview / Proje tanıtımı](https://erenariel.github.io/konaklamaflow/project-overview.html)**
- [Integrated offline HTML](demo/v04-integrated-preview.html) · [Global multilingual presentation](https://erenariel.github.io/konaklamaflow/global-presentation.html)
- [Releases](https://github.com/erenariel/konaklamaflow/releases) · [Open issues](https://github.com/erenariel/konaklamaflow/issues) · [Pull requests](https://github.com/erenariel/konaklamaflow/pulls)

> **Scope / Kapsam:** This is an **offline, fictional-data prototype**, not a deployed hotel PMS. It has **no live PMS/OTA/KBS/payment integration, no automatic check-in and no live AI-provider call**. Python rules precompute deterministic review evidence for the static browser demo. Staff authorization remains separate. **Do not enter real guest records or hotel credentials.**
>
> **Bu bir canlı otel otomasyonu değildir.** Arayüz kurgusal örneklerle rezervasyon inceleme ve personel karar sınırlarını gösterir.

## What does it do? / Ne işe yarar?

| Module / Modül | Function / İşlev |
| --- | --- |
| **Reservation review / Rezervasyon kontrolü** | Displays source-linked fictional bookings, potential conflicts and deterministic reason codes instead of unsubstantiated AI decisions |
| **Room plan / Oda planı** | Distinguishes proposed room assignments, maintenance holds, housekeeping and **unverified physical occupancy** |
| **Human review / Personel incelemesi** | Explains **source → rule → evidence field → required staff action** without approving arrivals or changing an actual PMS |
| **Operational views / İş akışları** | Navigable front-office, reservation, room, folio and report-style **demonstrations**; individual controls may still be prototypes |
| **Synthetic checks / Kurgusal testler** | Reproducible project-authored benchmark and fictional decision trace with explicit limits, not measured real-hotel accuracy |

**Browser-recording provenance:** The showcase GIFs and screenshots were captured from an earlier verified offline demo snapshot; **later copy-only clarity edits may not appear** in those recordings. They are real browser recordings of fictional data, not evidence of a live hotel integration. [Original recording and source-manifest details](PROJECT_DETAILS_2026-11-15.md).

The current integrated demo is source-validated, offline and privacy-restricted. Multilingual strings are **drafts**, not professionally verified translations. See [technical details and historical feature notes](PROJECT_DETAILS_2026-11-15.md) and [current limitations](docs/LIMITATIONS.md).

## Product limits / Ürün sınırları

**Shipped today:** offline, deterministic, fictional-data reservation checks and advisory room proposals. The default Python reviewer uses a greedy room-choice heuristic; constrained inventory can require manual review even when another arrangement exists. [Current limitations](docs/LIMITATIONS.md) · [Twin-scarcity regression tests](tests/test_issue1_twin_scarcity.py) · [Additional bounded planning work (unmerged PR #86)](https://github.com/erenariel/konaklamaflow/pull/86).

**Not shipped:** real OTA/PMS/KBS/payment connections, automated room assignment, verified end-to-end encryption, vendor zero-access guarantees, and certified security controls. Fictional **visual concepts, synthetic browser-only encryption research, and threat-model drafts** are intentionally separate from the product: [visual research](docs/VISION_SHOWCASE_TR_EN.md) · [vault research and threat-model gates](docs/ZERO_ACCESS_HOTEL_VAULT_TR_EN.md). They do not establish a live feature or an external security audit.

## First-party operator feedback / İlk elden operasyon değerlendirmesi

On 15 Nov 2026, a project-affiliated reviewer submitted a signed and property-stamped **first-party assessment** of the fictional offline demo. In four observed topics, **only the reservation-conflict scenario is marked "Pass"**; the other three result boxes and the draft confirmation boxes are unmarked. Translation limitations were noted. The reviewer’s authority and assessment setting have **not** been independently authenticated. This is not independent validation, hotel certification, evidence of adoption, or live PMS testing.

[Redacted original PDF](docs/evidence/KonaklamaFlow_Operator_Review_PUBLIC_REDACTED_TR_EN_2026-11-15.pdf) · [Evidence summary](docs/OPERATOR_FIRST_PARTY_REVIEW_2026-11-15.md) · [Privacy/legal disclosure](docs/PUBLIC_EVIDENCE_DISCLOSURE_TR_EN.md)

## Run locally / Yerel kullanım

**Requirements:** Python 3.11+; offline synthetic fixtures only.

```bash
git clone https://github.com/erenariel/konaklamaflow.git
cd konaklamaflow
python -m pip install .
python -m konaklamaflow examples/demo.json --as-of 2026-11-12
python -m konaklamaflow.ops_cli examples/operations-demo.json --as-of 2026-11-12 --at-time 14:01
```

To inspect the standalone demo without Python, open [`demo/v04-integrated-preview.html`](demo/v04-integrated-preview.html). CLI inputs and reports must not contain personal data; write reports to a different file than the input.

## Engineering evidence / Teknik testler

- [GitHub Actions — automated tests](https://github.com/erenariel/konaklamaflow/actions/workflows/tests.yml): Python 3.11–3.13 unit tests and Chromium browser checks.
- [Main-run CI evidence (15 Nov 2026)](https://github.com/erenariel/konaklamaflow/actions/runs/43682701510) · [Successful demo workflow](https://github.com/erenariel/konaklamaflow/actions/runs/43682944588)
- [Merged integrated offline preview PR #67](https://github.com/erenariel/konaklamaflow/pull/67)
- [Synthetic benchmark PR #51](https://github.com/erenariel/konaklamaflow/pull/51) and [scorecard PR #58](https://github.com/erenariel/konaklamaflow/pull/58): **7/10** project-authored cases were evaluated; this is **not** a real-world accuracy percentage.
- [Architecture/limits](docs/LIMITATIONS.md) · [Release gate](docs/RELEASE_GATE_TR.md) · [Security policy](SECURITY.md)

## Releases, contributions and roadmap / Sürümler ve katkı

**Version tracks are separate:** the browser **v0.5.x fictional demo** is not the same release as the Python distribution in [`pyproject.toml`](pyproject.toml), currently **`0.2.0rc1`**. GitHub Releases [v0.1.1](https://github.com/erenariel/konaklamaflow/releases/tag/v0.1.1) and [v0.2.0rc1](https://github.com/erenariel/konaklamaflow/releases/tag/v0.2.0rc1) exist, but **neither has a separately attached, ready-to-use product ZIP or wheel asset** (checked 15 Nov 2026). **No PyPI publication is claimed or verified here.** An installable offline-demo ZIP is still proposed in [unmerged PR #73](https://github.com/erenariel/konaklamaflow/pull/73). [Release strategy and publication gates](docs/RELEASE_STRATEGY_TR_EN.md).

The immediate roadmap includes stronger interactive coverage, source-bound operator feedback, offline distribution, translation review and **future, separately authorized** integration design. See [Issues](https://github.com/erenariel/konaklamaflow/issues) and [Changelog](CHANGELOG.md). Do not infer feature completion from an open pull request.

Contributions and feedback are welcome: [CONTRIBUTING.md](CONTRIBUTING.md) · [Fictional-only operator feedback guide](docs/OPERATOR_FEEDBACK_TR_EN.md). Please never include real guest names, passports, hotel system exports, credentials or operational secrets.

**Historical comprehensive README:** [Full technical/project detail snapshot (15 Nov 2026)](PROJECT_DETAILS_2026-11-15.md). All existing detailed explanations remain available there.
