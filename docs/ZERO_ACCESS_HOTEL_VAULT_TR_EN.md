# RFC — Zero-Access Hospitality Vault / Sıfır Erişimli Otel Veri Kasası

**Status: architectural proposal + synthetic-only browser cryptography lab. NOT IMPLEMENTED in the PMS, NOT SECURITY-AUDITED, NOT PRODUCTION-READY.**

## 1. Product promise / Ürün vaadi

**Goal:** KonaklamaFlow's service operator, host administrator and software maintainer must **not have plaintext guest identity records by default**, even if they can read the encrypted database. Only explicitly authorized hotel personnel holding valid **client-side decryption keys** should decrypt data for documented operational purposes.

**Turkish:** Veritabanını veya sunucuyu kontrol eden kişi, personel cihazındaki çözme anahtarına sahip olmadıkça pasaport, iletişim bilgisi, kimlik görseli veya özel misafir notlarını okuyamamalı. **İşletme sahibi de ancak kendisine yetki verilmişse** veriyi açabilir; sistem sahibinin her otelde gizli bir anahtarı olmaz.

**No false security claims:** This architecture does **not** mean an authorized employee cannot copy data, a compromised device is safe, a maliciously updated web client could never leak keys, metadata is invisible, third-party OTA systems become encrypted, or a regulation has certified the product. Current KonaklamaFlow is an offline fictional demo. The isolated lab encrypts a **synthetic object in the browser**, with no server and no real guest information.

## 2. Threat model and data classes

| Actor / attack | Target protection | Residual risk |
| --- | --- | --- |
| Database-only breach / stolen backup | Encrypted records unusable without client keys | Metadata, size, timing, record counts may remain visible |
| Honest-but-curious cloud operator / developer | No service-side guest decryption key, no plaintext access by ordinary admin query | A malicious app update, compromised build pipeline or client can still steal plaintext/keys |
| Unauthorized hotel employee | Role/tenant-scoped key access, audited releases to required workflows | An authorized staff member may screenshot/export what they can read; revocation cannot delete prior copies |
| Lost staff device / forgotten passphrase | Hotel-controlled recovery trustees, device revocation and documented rekey | **Without recovery material, old ciphertext may be permanently unrecoverable** |
| OTA/PHOBS/Booking.com/KBS imports | Minimize retention; encrypt as soon as possible; authorized boundary for lawful reporting | Third parties and ingestion gateways can see plaintext. **Cannot claim E2EE for that path** unless sources themselves use E2EE |
| Hotel owner / vendor owner | Vendor owner does not receive tenant guest keys automatically | Hotel owner can access records when explicitly authorized, consistent with hotel duties |

**Protect with tenant- and record-level encryption:** name, government ID/passport fields, phone, email, guest notes, identity scans, attachments, sensitive folio comments and communication content. Use minimum server-side operational metadata only after documented privacy analysis; even room number + dates can be identifying.

**Never ingest real guest records** into the current demo, lab, CI, GitHub Issues or public test fixtures.

## 3. Proposed production architecture (NOT built yet)

1. **Client and identity:** Serve a pinned, integrity-verifiable client over HTTPS; authenticate staff with phishing-resistant MFA; protect local keys with WebAuthn/OS keystores where supported. Keep authorizations distinct from key possession.
2. **Keys:** Generate random, independent per-record data encryption keys (DEKs) with audited cryptography. Encrypt data with **AES-256-GCM** (fresh nonce, authenticated tenant/record/context AAD). Protect DEKs with per-hotel/role vault encryption keys; wrap tenant/role keys to **verified staff public keys** using reviewed HPKE/recipient-key protocols. Version envelopes and bind key IDs.
3. **Server:** Store ciphertext, encrypted/wrapped keys and minimal operational projections. **Never** store plaintext DEKs, unwrapped user private keys, a global decryption secret, or a developer backdoor. Enforce server-side tenant isolation and access authorization *in addition to* encryption; do not equate encryption with RBAC.
4. **Operational projections:** Reservation conflict, room inventory, housekeeping and cash operations need selected fields. Prefer fictional/pseudonymous identifiers, limited disclosure, explicit processing purposes and client-side evaluation when feasible. Search, date-range queries, analytics and backups require dedicated leakage review; encrypted fields cannot be blindly indexed like plaintext.
5. **Sharing & role lifecycle:** Client-side sharing to verified recipients, guest-by-guest / time- or role-bounded key access, signed invitations, a strong audit trail (purpose, request, approval, read/export event). Staff exit requires device/token revocation, key rewrapping/rotation and acknowledgement that past exports remain.
6. **Regulated integrations:** OTA import and accommodation/KBS reporting need legally authorized plaintext **at some trust boundary**. Keep integration processors separate, access-scoped and transparent. Never suppress legally required identity reporting; do not claim the vendor cannot access data *at any point* if a vendor-controlled gateway receives plaintext.
7. **Recovery:** Document hotel-controlled multi-trustee recovery (for example, required approval by two designated hotel-controlled trustees), secure rotation, offline backups and loss recovery. The **vendor never acts as a sole recovery trustee**. Rehearse lost-device and lost-key situations with synthetic data.
8. **Supply chain & verification:** Client release signing/pinning, reproducible builds, third-party cryptographic audit, penetration testing, transparency log or update consent. A software vendor able to change served JavaScript can threaten client-side encryption; zero-access claims require defenses and ongoing governance.
9. **Compliance:** Data processing agreements, retention/deletion, breach notification, subject rights, lawful purpose, access logs and hotel-specific regulations remain necessary. Encryption is **a security measure, not automatic GDPR/KVKK compliance**.

### Data flow (future)

```text
Hotel staff authenticated browser (authorized device)
  | guest identity -> LOCAL audited encryption; role-specific key
  v
Encrypted record + encrypted record key + minimized operational projection
  | HTTPS (ciphertext)
  v
Service database (NO plaintext keys) -> backup / synchronization
  | ciphertext back to authorized device
  v
Hotel staff device: verify role and key -> LOCAL decryption -> purpose-bound display
```

## 4. Isolated Phase-1 synthetic lab (implemented in this PR)

`demo/privacy-vault-lab.html` is a **standalone browser-only demonstration**. It encrypts a fixed, invented JSON record using Web Crypto **AES-256-GCM**, with a fresh random per-demo vault key wrapped under a passphrase-derived AES-GCM key (**PBKDF2-HMAC-SHA-256 / 600,000 iterations**), fresh salts/nonces and authenticated tenant/record IDs. The readable example and the produced ciphertext are shown only in the browser; neither is transmitted or persisted by application code. Decryption requires the passphrase and rejects tampering or wrong keys. `connect-src 'none'` blocks app-generated network requests. Keys and output are **ephemeral**; a refresh loses state unless the user copied ciphertext elsewhere.

- This uses PBKDF2 only because it is available in standard Web Crypto without extra dependencies. **For production evaluate an audited memory-hard KDF such as Argon2id**, documented device key custody and qualified cryptographic review.
- This is **not** a multi-user vault, recovery mechanism, server integration, third-party secure messaging or proof that a malicious browser extension/operator update cannot exfiltrate keys.
- The lab has one **fixed fictional sample**. Do not type or upload real passport, guest, staff, hotel, identity, payment or reservation data.
- **Passphrase length != passphrase strength.** For actual use, high-entropy secrets, rate limiting, device protections and defense against offline guessing are essential. Password-based encryption does not remove human error.
- Nonce reuse with the same AES-GCM key would be dangerous: this lab uses new independent keys/nonces per encryption. Before production, formally review record-key rotation, key/version migration, nonce generation, error behavior and AAD canonicalization.
- The test demonstrates **browser crypto correctness under an isolated fictional scenario**; no independent security validation is implied.

## 5. Acceptance gates before any marketing claim

- [ ] Independent crypto/threat-model review; no proprietary/homegrown algorithms or unsafe key reuse
- [ ] Deterministic privacy and authorization tests: cross-tenant, cross-role, rollback, wrong key, tamper, browser storage, offline import/export and backup restore
- [ ] Document OTA/PHOBS/KBS plaintext trust boundaries and data-controller responsibilities
- [ ] Role public-key verification and revocation, two-trustee recovery and incident exercises
- [ ] Measured key lifetime/rotation/recovery and auditable permission flows
- [ ] Web build integrity and malicious-update resistance reviewed; pen test and secure deployment checklist
- [ ] Separate deployment/pilot consent, hotel approval, privacy impact assessment where required
- [ ] **Only after all gates and real deployment evidence:** consider a narrowly scoped public statement about encrypted fields and verified server non-access

## 6. Sources

- Proton's own account of **zero-access vs. E2EE**: https://proton.me/learn/encryption/types-of-encryption/zero-access
- Proton Pass documented vault model: https://proton.me/support/pass-vault
- Proton's sharing architecture: https://proton.me/blog/proton-pass-security-model
- OWASP Cryptographic Storage guidance: https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
- NIST SP 800-57 key management guidelines: https://csrc.nist.gov/Projects/Key-Management/Key-Management-Guidelines
- Proton's account/data recovery warning: https://proton.me/support/reset-password

**Brand and claims:** Inspired by public cryptographic patterns, **not affiliated with or endorsed by Proton**. Never label the current lab a Proton-equivalent certified or audited E2EE hotel system.
