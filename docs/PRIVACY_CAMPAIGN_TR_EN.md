# KonaklamaFlow — Privacy-First Campaign & Security Roadmap (TR / EN)

**15 November 2026 · Conceptual campaign + engineering research, not a deployed zero-access hotel product or certification**

## What this PR communicates / Anlattığımız şey

- **Main concept:** *Gizliliğinizi görüyoruz. Verilerinizi görmemeyi hedefliyoruz.* / **We recognize your privacy; our goal is not to see your guest data.**
- **Design goal:** Authorized hotel client encrypts sensitive guest data locally → remote service receives a ciphertext envelope → hotel-controlled authorized device decrypts locally → human authorization remains mandatory for operational actions.
- **Current evidence:** An isolated synthetic-only browser AES-256-GCM encryption laboratory, executable source code, standard cryptography APIs and reproducible tests. Its design is defined in [the Zero-Access Vault RFC](ZERO_ACCESS_HOTEL_VAULT_TR_EN.md).
- **Current marketing medium:** [static offline privacy campaign page](../demo/privacy-campaign.html), with **four original privacy-specific concept GIFs** (one campaign hero and three explanatory scenes), plus reduced-motion posters and a responsive CSS-animated five-step encryption flow. It does not track visits, connect to external sites or access guest records.
- **Separate, unrelated operator evidence:** [signed-and-stamped first-party review](OPERATOR_FIRST_PARTY_REVIEW_2026-11-15.md) evaluated the previous fictional hotel-operations demo, **not** the new encryption lab or the future architecture.

## Claims matrix / İddia sınırları

| Statement | Can we say it now? | Required evidence |
| --- | --- | --- |
| "A fictional record can be encrypted and decrypted locally in a browser demo" | **Yes**, with project-authored tests | Reviewed exact commit and test run; warn no independent audit |
| "The project has a proposed client-held-key, zero-access architecture" | **Yes, as a research goal** | [Architecture and threat model](ZERO_ACCESS_HOTEL_VAULT_TR_EN.md) |
| "The software company cannot access production guest information" | **Not yet** | Full audited client/server implementation, source and build verification, permissions, role/device keys, malicious-update mitigation, third-party integrations |
| "All data is end-to-end encrypted" | **No** | Every covered field and integration verified; record unavoidable lawful plaintext boundaries |
| "Every hotel using KonaklamaFlow has privacy certification" | **No** | Formal audit and continuing certification program; no such program exists or certificates have been issued |
| "The only hotel PMS in the world with encryption like this" | **Unverified; do not claim** | Independently sourced worldwide competitive review |
| "GDPR/KVKK compliance is guaranteed by encryption" | **No** | Legal basis, necessity, retention, data-subject rights, privacy impact assessments, controllers/processors, hotel reporting rules |
| "The dated signed hotel-operator paper proves this vault is secure" | **No** | The review predates the vault lab and was not a crypto audit |

## Phase gates / Aşamalı mühendislik

**Phase 1 — already merged:** fixed synthetic Web Crypto AES-GCM lab and honest threat-model RFC. Tests prove *specific synthetic code paths*, not production security.

**Phase 1.1 — in this campaign PR:** additional regression proof for fresh ciphertext/nonces and no local/session storage persistence after page reload; campaign page and offline/mobile/accessibility tests. No production encryption claims.

**Phase 2 — future PRs:** define typed, versioned encrypted envelopes and tenant/role key wrap protocol *with audited established libraries* (no homegrown primitives). Add authenticated recipient public keys, integration boundaries, trusted-device lifecycle, role-based access and deny-by-default tests. Keep CI synthetic-only.

**Phase 3 — future PRs:** separation of hotel key custody from vendor backend, multi-party recovery controls, key revocation and tenant isolation; audit privileged operations. Connectors and legal reporting must document when/why plaintext is available to an authorized endpoint.

**Phase 4 — only after independent review:** third-party cryptographic assessment, real pilot consent and regulatory/privacy compliance process, public validation and publishable scope-of-protection statement.

**Phase 5 — possible future branding only:** audited `KonaklamaFlow Certified Privacy` program with a published standard, independent evaluation, validity/renewal/revocation and public per-property verification. **No certification or badge is issued today.**

## Integrity guardrails / Güven ilkeleri

1. Never expose raw guest identity records, passports, actual hotel exports, secrets or operational credentials in GitHub, tests, marketing images or the browser lab.
2. Animation **is not evidence of implemented functionality**; label concept art.
3. Never confuse a vendor's lack of automatic access with the impossibility of malicious client updates or authorized employee copying. An offline demo is not a verified E2EE deployment.
4. Avoid copying Proton artwork, branding or certification marks. This project is independent and borrows only general public cryptographic design patterns.
5. Keep the business-context hotel review and security research clearly separate; do not claim it validates cryptography.
6. Prefer future verifiable controls to absolute promises or unsupported uniqueness claims.

## References

- [Zero-Access Hotel Vault technical RFC](ZERO_ACCESS_HOTEL_VAULT_TR_EN.md)
- [KonaklamaFlow published synthetic lab](https://erenariel.github.io/konaklamaflow/privacy-vault-lab.html)
- [Public campaign after deployment](https://erenariel.github.io/konaklamaflow/privacy-campaign.html)
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [NIST key-management guidance](https://csrc.nist.gov/Projects/Key-Management/Key-Management-Guidelines)

## New campaign media / Özgün kampanya animasyonları

All four GIFs are **generated illustrative metaphors, not recordings of working encryption software**. Certified Privacy remains a hypothetical program; no certificate has been issued.

| Concept | GIF | Still image |
| --- | --- | --- |
| privacy promise | [GIF](images/privacy-promise.gif) | [Poster](images/privacy-promise-poster.jpg) |
| authorized device | [GIF](images/authorized-device.gif) | [Poster](images/authorized-device-poster.jpg) |
| zero access flow | [GIF](images/zero-access-flow.gif) | [Poster](images/zero-access-flow-poster.jpg) |
| future certification | [GIF](images/future-certification.gif) | [Poster](images/future-certification-poster.jpg) |

The campaign and README disclose the limits in Turkish and English. The images do **not** demonstrate production cryptography or independently certified security.
