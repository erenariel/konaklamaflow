# KonaklamaFlow — 10-language review reason catalogue (v0.4 candidate)

This is an **offline presentation layer**, not a translation AI, PMS adaptor, check-in service, KBS integration, or proof of native-speaker quality. Translations are **drafts pending human review**. The v0.3 rule engine is the single source of decisions and remains unchanged.

## Languages
- Turkish (tr / tr-TR)
- English (en)
- French (fr)
- Greek (el)
- Hebrew (he, RTL)
- Arabic (ar, RTL)
- German (de)
- Russian (ru)
- Spanish (es)
- Ukrainian (uk)

For each language, all **26 reason codes** and six fixed safety/UI messages have entries. An unsupported valid locale (e.g., pt-BR) returns English with `FALLBACK_EN_UNSUPPORTED_LOCALE`, never an unsupported false “fully translated” claim. All first-ten translations return `CATALOG_DRAFT_UNREVIEWED`, not “certified”.

## Code use

```python
import json
from konaklamaflow.experience_engine import evaluate
from konaklamaflow.reason_i18n import localize_code, localized_pre_review

report = evaluate(synthetic_snapshot)
assert localize_code("ROOM_CONFLICT", "he-IL")["direction"] == "rtl"
preview = localized_pre_review(synthetic_snapshot, report, "fr")
assert preview["results"][0]["reason_codes"] == report["arrivals"][0]["blockers"]
```

The function recomputes the full rule report and rejects stale/tampered data. It only emits opaque task IDs, status/reason codes, fixed localized texts and safe human-review instructions. No external booking, room, guest, total/folio, or account reference is emitted.

## Critical design constraints
- Source data remains unverified in the absence of a real, authorized source and timestamp attestation.
- The localized message is **not a check-in approval**. A "review_ready" state is a staff pre-check only, not authority to place a guest or guarantee a room.
- Do not translate `reason_code`, `task_id`, JSON keys, SHA-256 or accounting semantics.
- Use `lang` and `dir` HTML attributes, `<bdi dir="ltr">` for opaque codes, logical CSS properties, and real keyboard/VoiceOver/NVDA tests.
- Human language QA and legal translation review are required before claiming production-grade support. A syntactically complete catalogue does not establish translation correctness.
- This branch does not merge the full UI Issue #19 concept or the explainability Issue #5 branch. They remain separate draft PRs.

## Tests
- 260 reason-label combinations across 10 languages
- BCP-47 language selection, RTL direction, invalid locale and fallback
- full report decision/shape parity and no mutation
- stale/tampered source rejection and no raw guest/payment identifiers
- still no network, external API calls, writes or KBS

Related: #19, #5, #9. Merge only after human review and successful CI.


## CLI ile yerel çıktı üretimi

```sh
python -m konaklamaflow.experience_cli examples/fictional-hotel.json /tmp/konaklamaflow-report.json
python -m konaklamaflow.reason_i18n_cli examples/fictional-hotel.json /tmp/konaklamaflow-report.json el-GR /tmp/greek-pre-review.json
```

Çıktıda yalnız sabit karar kodları, çevrilen açıklamalar, opaque task ID ve insan incelemesi sınırı bulunur; misafir adı, dış rezervasyon/PMS referansı veya finans tutarları bulunmaz. Desteklenmeyen geçerli dil kodu açıkça İngilizceye düşer. Bir rapor sonradan değişirse yeni bir çeviri ile yanıltıcı biçimde ilişkilendirilmez: CLI raporu yeniden değerlendirir ve önceki çıktı dosyasını değiştirmeden reddeder.
