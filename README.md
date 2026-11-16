# KonaklamaFlow 🏨

**MIT-licensed, offline hotel reservation conflict reviewer and operations prototype.**  
**Rezervasyon çakışması ve oda uygunluğu incelemesine odaklanan açık kaynak, çevrimdışı otel operasyon prototipi.**

[![Tests](https://github.com/erenariel/konaklamaflow/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/erenariel/konaklamaflow/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python package](https://img.shields.io/badge/Python-0.2.0rc2%20candidate-orange)](pyproject.toml)
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

**Shipped today:** offline deterministic reservation reviews, a small bounded repair step and an independent 200-room **synthetic scenario** solver (not live optimization). The [room allocation lab](https://erenariel.github.io/konaklamaflow/global-allocation-lab.html) shows precomputed 18/60/200-room plans. [Limitations](docs/LIMITATIONS.md) · [Merged room repair #86](https://github.com/erenariel/konaklamaflow/pull/86) · [Merged global lab #90](https://github.com/erenariel/konaklamaflow/pull/90).

**Not shipped:** real OTA/PMS/KBS/payment connections, automated room assignment, verified end-to-end encryption, vendor zero-access guarantees, and certified security controls. Fictional **visual concepts, synthetic browser-only encryption research, and threat-model drafts** are intentionally separate from the product: [visual research](docs/VISION_SHOWCASE_TR_EN.md) · [vault research and threat-model gates](docs/ZERO_ACCESS_HOTEL_VAULT_TR_EN.md). They do not establish a live feature or an external security audit.

## Validation status / Doğrulama sınırları

GitHub CI confirms code and offline UI regressions, not independent hotel accuracy. The original [10-case benchmark](docs/EVALUATION_TR.md) has 7 scored / 3 excluded; the new [Benchmark v2](docs/BENCHMARK_V2_TR_EN.md) contains **40 project-labeled observations from 23 fictional scenarios, plus 3 explicit exclusions**. FP/FN disagreements are shown, not hidden. Neither benchmark is a real-hotel pilot.

## 60-second quickstart / 60 saniyelik başlangıç

**Requirements:** Python 3.11+; use **fictional files only**.

```bash
git clone https://github.com/erenariel/konaklamaflow.git
cd konaklamaflow
python -m pip install .
konaklamaflow demo
konaklamaflow review-csv --rooms examples/csv/rooms.csv --reservations examples/csv/reservations.csv --as-of 2026-11-12
```

This runs the bundled 5-room scenario and then a local minimized CSV review. No PMS writes, network calls or genuine guests. [CSV contract and privacy warnings](docs/LOCAL_CSV_TR_EN.md) · [Offline viewer](https://erenariel.github.io/konaklamaflow/) · [Local tests](docs/TESTING.md).

## Engineering evidence / Teknik testler

- [GitHub Actions — automated tests](https://github.com/erenariel/konaklamaflow/actions/workflows/tests.yml): Python 3.11–3.13 unit tests and Chromium browser checks.
- [Main-run CI evidence (15 Nov 2026)](https://github.com/erenariel/konaklamaflow/actions/runs/43682701510) · [Successful demo workflow](https://github.com/erenariel/konaklamaflow/actions/runs/43682944588)
- [Merged integrated offline preview PR #67](https://github.com/erenariel/konaklamaflow/pull/67)
- [Benchmark v2 methodology and full FP/FN case list](docs/BENCHMARK_V2_TR_EN.md) · [V1 10-case synthetic scorecard](https://erenariel.github.io/konaklamaflow/synthetic-scorecard.html) (7 labeled, 3 excluded). Neither represents independent accuracy.
- [Architecture/limits](docs/LIMITATIONS.md) · [Release gate](docs/RELEASE_GATE_TR.md) · [Security policy](SECURITY.md)

## Releases, contributions and roadmap / Sürümler ve katkı

**Version tracks are separate:** the public fictional browser demo is v0.5.x-era; the Python package in [pyproject.toml](pyproject.toml) is now **v0.2.0rc2 candidate, not yet published**. Existing GitHub Releases [v0.1.1](https://github.com/erenariel/konaklamaflow/releases/tag/v0.1.1) and [v0.2.0rc1](https://github.com/erenariel/konaklamaflow/releases/tag/v0.2.0rc1) have no attached wheel/ZIP assets. The [offline product ZIP is already available via Pages](https://erenariel.github.io/konaklamaflow/konaklamaflow-offline-demo.zip). CI now checks wheel/sdist in a clean installation and retains candidate artifacts; **TestPyPI, PyPI and a new permanent GitHub Release still require separate verification and publication**. [Release plan](docs/RELEASE_STRATEGY_TR_EN.md).

Next priorities: independent review of Benchmark v2 labels, real privacy audit, and independently supervised fictional user trials. Live PMS/OTA work needs separate authorization. See [Issues](https://github.com/erenariel/konaklamaflow/issues) and [Changelog](CHANGELOG.md). Do not infer feature completion from an open pull request.

Contributions and feedback are welcome: [CONTRIBUTING.md](CONTRIBUTING.md) · [Fictional-only operator feedback guide](docs/OPERATOR_FEEDBACK_TR_EN.md). Please never include real guest names, passports, hotel system exports, credentials or operational secrets.

**Historical comprehensive README:** [Full technical/project detail snapshot (15 Nov 2026)](PROJECT_DETAILS_2026-11-15.md). All existing detailed explanations remain available there.
