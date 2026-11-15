# Open-source maintainer evidence / Açık kaynak bakım kanıtları

**15 November 2026 — evidence register, not an acceptance claim.** OpenAI's public [Codex for Open Source](https://openai.com/form/codex-for-oss/) criteria emphasize meaningful usage, ecosystem value and active maintenance, including PR review, issue triage and release management.

| Check | Verifiable public evidence | Current interpretation |
| --- | --- | --- |
| Public OSS license | [MIT license](../LICENSE), [repository](https://github.com/erenariel/konaklamaflow) | Public reusable source |
| Technical maintenance | [Tests CI](https://github.com/erenariel/konaklamaflow/actions/workflows/tests.yml), [test cases](../tests/) | Reproducible unit + browser checks; not certification |
| Issue triage | [Open issues](https://github.com/erenariel/konaklamaflow/issues), [contribution guide](../CONTRIBUTING.md) | Trackable backlog; independent feedback not yet established |
| PR history | [Pull requests](https://github.com/erenariel/konaklamaflow/pulls) | Maintainer-led work and recorded changes; not independent peer review |
| Release management | [Published releases](https://github.com/erenariel/konaklamaflow/releases), [release channel guide](RELEASE_CHANNELS_TR_EN.md) | v0.1.1 tagged; candidate and demo are distinct |
| Safe operator workflow | [Synthetic feedback guide](OPERATOR_FEEDBACK_TR_EN.md), [security policy](../SECURITY.md) | No PII; no real PMS/OTA/KBS actions |
| Maintainer night-shift trial / bakımcının gece vardiyası denemesi | Maintainer statement on 15 November 2026, recorded below | The author tried the fictional offline demo during their own night shift. No guest record was copied into the repository |
| Genuine adoption / gerçek kullanım | None independently verified | **Not yet demonstrated.** A self-trial is not an independent hotel pilot |

**TR:** GitHub yıldızları, indirmeler, kullanıcılar, otel pilotları veya incelemeleri hakkında kanıtsız rakamlar kullanmayacağız. Kendi yazdığımız kod ve GIF'ler kullanım kanıtı değildir. Dış katılımcıların doğrulanmış katkıları, güvenilir sürüm geçmişi ve izinli operatör değerlendirmeleri asıl eksik alanlardır.

**EN:** The roadmap is to attract *genuine* third-party users and contributions, document independently reproducible cases, improve safety and release reliability, and maintain the software over time. Metrics must come from actual repository or consenting tester records, never simulated accounts, stars or testimonials.

## Maintainer operating loop / Bakım rutini

1. Triage new reproducible issues; classify security, correctness, accessibility and documentation impacts. Remove sensitive material from public reports rather than echoing it.
2. Reproduce with fictional input and add a failing test before fixing.
3. Review PR diffs for correctness, privacy boundaries, input safety and backward compatibility.
4. Verify checks for the **exact merge SHA** and publish accurate release notes; don't turn green CI into a production-safety claim.
5. Invite real external feedback ethically and credit contributors only with their permission.

## Maintainer night-shift trial / Bakımcının gece vardiyası denemesi

**15 November 2026.** The maintainer, who works a hotel night shift, tried KonaklamaFlow during that shift. The trial used the fictional offline demo. It was not connected to the hotel PMS, did not send a KBS notification, and did not take payment. No guest name, reservation code, or PMS screenshot was brought into this repository.

**TR:** Bunu bakımcı kendi vardiyasında denedi. Gerçek bir kullanıcı denemesidir. Bağımsız bir otel pilotu, ölçülmüş zaman kazancı veya üçüncü kişi onayı değildir.

**EN:** This is a real self-reported user trial by the maintainer. It is not an independent pilot, a measured time saving, or third-party endorsement.

**The current project is still an early offline prototype.** This record improves transparency; it does not establish the program's broader-adoption criterion or guarantee selection.
