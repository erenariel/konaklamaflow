# Deterministic explanation contract (v0.4 proposal)

This add-on is deliberately **not** a new rules engine. It enriches the authoritative v0.3 Python evaluation with an allowlisted description of which input *fields* relate to a decision. It neither checks live source validity nor authorizes any action.

## API

```python
from konaklamaflow.experience_engine import evaluate
from konaklamaflow.explainability import build_explanations

report = evaluate(minimized_fictional_snapshot)
explanation = build_explanations(minimized_fictional_snapshot, report)
```

The result uses `konaklamaflow.explanations.v1` and includes:
- source snapshot and full report SHA-256 integrity links
- `task_id` (opaque), `state`, all exact `reason_code`s from the rule report
- `message_key` for future multilingual explanations, `evidence_field_paths` with **no raw field values**, and `next_safe_staff_action_key`
- `source_validity = UNVERIFIED_MINIMIZED_SNAPSHOT`; `source_revision` and `source_captured_at` are `null` because the current v0.3 schema has no trusted capture proof
- `human_approval_boundary` saying the decision is **human pre-review only, not check-in**.

## Security properties
A caller-provided report is re-evaluated against the supplied minimized snapshot and rejected if even one field differs. Neither SHA nor human-friendly status constitutes authorization. No network, APIs, identity, credentials, payments or KBS calls. This output contains *field names* such as `rooms[].housekeeping`, not actual guest or room identifiers. Outputs for cancelled and stale records are not silently treated as approved.

### Supported flow
1. Authoritative trusted process obtains minimized synthetic or separately authorized/pseudonymized source snapshot.
2. Python rules create read-only report.
3. This module validates full parity and creates safe explanation keys.
4. Local presentation maps message keys into audited translations. The model may explain the keys **but cannot modify decision status**.
5. Staff confirms actual PMS/room/identity and performs any authorized operation outside this package.

### Known limitations
This first contract does not prove the upstream source, source revision, timestamp, translation correctness or operator identity. It is not linked to the HTML viewer yet. The next integration should use an explicitly versioned report extension or dedicated explanation artifact and preserve the generated-fixture and browser parity tests. The 10-language demo remains a separate prototype pending full i18n integration (Issue #19).

Issue #5. No production feature claim until CI and review.

## Bağımsız çevrimdışı CLI

```sh
python -m konaklamaflow.experience_cli examples/fictional-hotel.json /tmp/suite-report.json
python -m konaklamaflow.explain_cli examples/fictional-hotel.json /tmp/suite-report.json /tmp/explanations.json
```

CLI kaynak raporu tekrar hesaplayarak eşleştirir. Girdi geçersiz/eskiyse hata içeriğini yansıtmaz ve önceki çıktı dosyasını değiştirmez. Örnek yalnızca kurgusal veriye uygundur; gerçek misafir kayıtlarıyla kullanılmamalıdır.
