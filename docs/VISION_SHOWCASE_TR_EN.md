# KonaklamaFlow — Animated Product & Interface Design Showcase

**15 November 2026 · Browser-recorded demo evidence and future interface design studies are presented separately.**

## A. Recorded product GIFs / Gerçek demo GIF'leri

These three GIFs are unaltered browser recordings of an earlier reviewed **fictional offline demo**. They document specific interactions at that earlier revision, not every currently implemented feature and not live PMS/OTA/KBS/payment/AI integrations.

| Product view | Recorded GIF | Reduced-motion poster |
| --- | --- | --- |
| AI Review Workflow | [ai-command-tour.gif](images/ai-command-tour.gif) | [poster](images/ai-command-tour-poster.png) |
| Room Plan & Housekeeping | [roomplan-story.gif](images/roomplan-story.gif) | [poster](images/roomplan-story-poster.png) |
| Operations Overview | [overview-pulse.gif](images/overview-pulse.gif) | [poster](images/overview-pulse-poster.png) |

**Provenance:** Historical [README details](../PROJECT_DETAILS_2026-11-15.md), [showcase review guide](DEMO_SHOWCASE_TR.md), and original recording code in `scripts/record_demo_tour.py`. Later copy-only changes may not appear in the earlier captures.

## B. Interface design directions / Arayüz tasarım çalışmaları

The three original animated studies describe the product team's intended **visual organization and interaction direction**: explainable reservation review, room-operation visibility and human-governed decision support. They are **not recordings of implemented functionality**.

| Design study / Tasarım | Animation / Animasyon | Still poster / Sabit görsel | Proposed design goal |
| --- | --- | --- | --- |
| **Decision Review Workspace** | [GIF](images/vision-ai-command-core.gif) | [JPG](images/vision-ai-command-core-poster.jpg) | Put reservation sources, rule explanations and staff review in a readable workspace |
| **Room Operations Grid** | [GIF](images/vision-smart-room-grid.gif) | [JPG](images/vision-smart-room-grid-poster.jpg) | Make room states, housekeeping and maintenance holds legible at a glance |
| **Operations Intelligence Overview** | [GIF](images/vision-executive-intelligence.gif) | [JPG](images/vision-executive-intelligence-poster.jpg) | Present operational indicators and shift priorities in an integrated summary |

The images preserve their original file names so existing links do not break. All assets are local and staged by the explicit allowlist in `scripts/stage_demo_site.py`; they do not load remote scripts, images or tracking assets. The animations have six 180-ms frames each. Users requesting reduced motion receive static posters via `picture/source`.

### Public presentation text / Kamuya açık kısa açıklama

> **TR:** KonaklamaFlow'un uzun vadeli arayüz tasarımını yansıtan üç özgün animasyon. Güncel demoda çalışan özelliklerin ekran kaydı değildir.
>
> **EN:** Three original animations illustrating KonaklamaFlow's long-term interface direction. Interface concepts only — not current product functionality.

These two sentences are sufficient for the public-facing gallery; detailed scope and provenance remain in this document and the repository. Product claims are grounded by linked actual demo captures and tests rather than visual concepts.

## Evaluation integrity / Değerlendirme güvenilirliği

The [signed and stamped first-party operator worksheet](evidence/KonaklamaFlow_Operator_Review_PUBLIC_REDACTED_TR_EN_2026-11-15.pdf) evaluates the **fictional offline hotel-operations demo**, not the design studies. Its review was self-reported in a hotel setting and is **not independent certification**.

**Public pages:** [Product overview / Ürün ve tasarım](https://erenariel.github.io/konaklamaflow/project-overview.html#vizyon) · [Repository README](../README.md).
