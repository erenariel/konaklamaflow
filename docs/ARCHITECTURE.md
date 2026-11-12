# Architecture / Mimari

```text
[Hotel-approved, privacy-filtered input] -- fictional/pseudonymized JSON
                         |
                         v
                  [strict validation]
                         |
                         v
                 [deterministic rules]
                      /       \
                     v         v
            [alerts and checks] [room suggestions]
                      \       /
                       v     v
                 [JSON dry-run report]
                         |
                         v
            [Human reviews authorized PMS]
```

**No authentication, browser automation, KBS handling, guest chat, API keys, payment capture or persistence.** This first release is a *pure analysis core* so it is easy to test and review.

## Extendability

An eventual adapter can be written by the hotel/operator using the vendor's published integration API. It should:

- possess only narrow read-only credentials during early pilots;
- remove name/passport/phone/address/email before normalization;
- use an irreversible mapping to per-property synthetic IDs;
- make no change without a separate approval and audit step;
- never transmit guest personal data to AI inference providers by default;
- maintain separate spaces for different properties;
- meet applicable legal requirements through local legal assessment.

Any LLM can *explain* a generated report, but the core conflict calculations must stay deterministic and have testable acceptance criteria. Do not allow an LLM to act on PMS or government systems without authorization and verification.
