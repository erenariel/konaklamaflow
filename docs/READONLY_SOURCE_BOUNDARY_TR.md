# Synthetic-only PMS source boundary — integration readiness starter

This module is an optional mock interface for future **read-only** authorized PMS adapters. There is no vendor API call, network, SDK, authentication, tenant authorization or live data ingestion. A "fresh" mock envelope is not proof of a real hotel room or guest status.

## Invariants
- Exact object envelope fields, only `SYNTHETIC_READ_ONLY_MOCK` source tag.
- Trusted caller must pass an expected property scope; the snapshot property must match that scope.
- UTC capture timestamp must be earlier than the trusted UTC check time, within a bounded TTL.
- Opaque allowlisted revision identifier, not a personal or booking ID.
- `experience_engine.validate` fails closed for unexpected fields, non-minimized shape and bad relations.
- A fresh report has `DRY_RUN_ONLY` and staff approval boundaries. There are no writes or live actions.

## Integration plan (not implemented)
1. Obtain written authority from hotel and PMS vendor for API access, separate sandbox and data processing terms.
2. Authenticate staff and tenant server-side; trusted clock and source revision must be attested outside model/browser control.
3. Minimize and pseudonymize source data **before** crossing the integration boundary; the pattern of a field alone does not establish anonymity.
4. Test read-only adapter against vendor documented API, cancellation/race/revision/clock-skew and no-network fallback.
5. Independently audit security, KVKK, audit/incident controls and user pilot before any controlled production stage.
6. KBS, payment, message sending and government registration are separate legally bound processes, not part of this module.

## Example (synthetic)
```python
from konaklamaflow.source_boundary import verify_mock_source_envelope
output = verify_mock_source_envelope(
    synthetic_envelope, expected_property_id="SAMPLE_HOTEL_01",
    checked_at_utc="2026-11-13T00:03:00Z")
assert output["policy"]["pms_writes"] is False
```

Issue #13 and #14. No live readiness claim.
