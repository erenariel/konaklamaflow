# KonaklamaFlow — Codex icra planı (v0.4 aday çalışması)

> Durum: UYGULAMA PLANI. Burada anlatılan yetenekler henüz tamamlanmış sayılmaz. Güncel main v0.3 prototipini içerir; v0.1.1 paket sürümü ayrı korunur. Tarihsel PR #2 ve #3 birleşmiştir.

## Ürün tezi
Küçük ve butik oteller için bağımsız, mahremiyeti esas alan rezervasyon operasyon ön-kontrol ve karar destek platformu. PMS'in yerine geçtiği, kimlik işlediği, ödeme aldığı, KBS bildirdiği veya OTA hesabına bağlandığı iddia edilmez. Önce sentetik/offline; sonra yetkili read-only pilot; sonra ayrı onay ile kontrollü üretim.

## Kod ajanına değişmez koruma talimatları
1. Her işte fresh clone ve güncel main SHA kontrolü; geçmiş yeniden yazma, force-push, eski SHA restore, dal/etiket silme YOK. Noreply committer doğrula.
2. Bir iş = ayrı feature branch + draft PR + issue referansı. Mevcut #1 ve v0.1.1 tag'i koru. Main'e onaysız merge ve release YOK.
3. Gerçek PMS/OTA/CM/KBS/ödeme/kimlik/e-posta/SMS/misafir mesajı veya AI API çağrısı public demo ve CI için YOK. JSON fixture sentetik; özel e-posta ve üretim credential'ı Git'e girmez.
4. Python engine tek karar otoritesi; browser kendi check-in onayı veya oda tahsis kararı hesaplamaz. Snapshot değişimi stale -> readiness ve export geçersiz.
5. AI yalnızca açıklama, özet veya gönderilmeyen taslak üretir. Modelin söylediği onay, rol, kaynak zamanı ve hash asla yetki değildir.
6. Her PR için test kanıtı, masaüstü/mobil görüntü, klavye ve reduced-motion, no-network, güvenlik regresyonu ve kalan risk raporu gerekir.
7. Resmi üretici API yetkisi, KVKK ve bağımsız güvenlik incelemesi olmadan production entegrasyonunu açma.

## Issue sırası ve bağımlılık

| Dalga | Issue | Sonuç |
|---|---|---|
| A1 | #4 | Operator/Presentation, Light/Dark/Night Audit, erişilebilir motion |
| A2 | #5 | Why / evidence / next safe step ve engine kanıt izi |
| A3 | #9 | Mobil, a11y, görsel regresyon, performans, no-network |
| A4 | #6 | 90sn/3dk/7dk gerçek rehberli hikâye, GIF/video |
| B1 | #7 | Şeffaf AI sağlayıcı vitrini ve doğru bağlantı durumu |
| B2 | #8 | Mock AI adapter, tipli sözleşme ve kapalı provider portları |
| B3 | #10 | Offline tek dosya dağıtımını koruyan modularization |
| B4 | #17 | README/CHANGELOG/quality/privacy/brand tutarlılığı |
| C1 | #1 + #11 | Twin scarcity ve constraint solver / multiroom |
| C2 | #12 | OTA sürüm/olay ve finans semantiği |
| C3 | #13 | Yazılı izinli read-only PMS adapter ve shadow pilot |
| D1 | #14 | RBAC/MFA/tenant isolation/audit/idempotency |
| D2 | #15 | SLO, olay yönetimi ve geri dönüş planı |
| D3 | #16 | KVKK, tedarikçi izinleri ve ölçülebilir pilot |

A1 ve A2 birbirinden bağımsız açılabilir; A3 ve A4, A1/A2 doğrulanmadan merge edilmemeli. AI vitrini B1, gerçek adapterdan önce yayınlanabilir ama kartlar “Bağlı değil / Demo simülasyonu” demeli. Production readiness D dalgası doğrulanmadan ürün “canlı otel kullanımı için hazır” denemez.

## Sunum için vazgeçilmezler
- Operator Mode bilgi yoğun, düşük hareketli, okunabilir; Presentation Mode 16:9 sahne, altyazı, ilerleme, tek ana odak, anlaşılır CTA.
- Koyu ve Night Audit temaları; renk tek anlam taşımaz, ikon ve açık metin eklenir.
- Hikâye: Problem → Kanıt → Motor kararı → AI açıklaması (mock/optional) → Personel adımı → Sonuç (yalnızca pre-review).
- GIF/video gerçek çalışan demo tarayıcısından çıkar; gerçek model çağrısı olmayan hareket “AI cevap verdi” diye sunulmaz.
- Kayıtların senaryo revizyonu ve commit SHA'sı gösterilir; alternatif statik poster ve alt metin bulunur.
- Play/pause/step/replay/x1/x1.5/x2 ve prefers-reduced-motion zorunlu.

## AI sağlayıcı politikası
- UI: OpenAI API, Anthropic API, Gemini API, Azure OpenAI, Local model seçenekleri; doğru durumu ve bağlantı türüyle.
- ChatGPT Business/Plus/Pro aboneliği otomatik API anahtarı değildir; API organizasyonu ve faturalaması ayrıdır. “ChatGPT Cloud” ismi belirsiz API entegrasyonu gibi pazarlanmasın.
- İzinli resmi marka görseli yoksa salt metin kartı; OpenAI/Anthropic partnerlik, endorsement ve marka lisansı uydurulmaz.
- Public demo/CI: ZERO network, ZERO secret, ZERO guest PII. Gerçek API denemesi ayrı, sunucu tarafında, yetkili test hesabıyla ve maliyet sınırıyla tasarlanır.

## Açıklanabilirlik kabul sözleşmesi
Her kritik karar için: reason_code, evidence field path, synthetic/verified kaynak etiketi, captured_at ve source_revision yalnızca güvenilir veri varsa, next safe staff action, human approval boundary. Bilinmiyorsa “bilinmiyor” yaz. AI, BLOCKED durumunu READY'ye çeviremez. Oda önerisi gerçek envanter garantisi değildir. Finans toplamı günlük gelir veya tahsilat değildir.

## PR ve CI kapanış şablonu
Issue #N, değişiklik özeti, dahil/hariç sınırlar, test çıktısı + CI URL + SHA, 1440/768/375/320 ekran görüntüsü, temalar/reduced motion, PII/secret scan, no-network, Python report parity, geri alınabilirlik, kalan riskler ve tüm ürün iddiaları belgelenmeli.

## Üretim kabul kapıları
G0: Sentetik, çevrimdışı, güvenlik regresyonu.
G1: Bağımsız ürün/kod incelemesi, erişilebilirlik ve gizlilik raporu.
G2: Üretici ve otel tarafından yazılı yetkili read-only sandbox/shadow pilot.
G3: Tenant isolation, MFA, RBAC, audit, idempotency, concurrency, observability, recovery, hukuk/gizlilik incelemesi.
G4: Kontrollü canary, gerçek insan onayı, ölçülmüş pilot, olay yönetimi ve rollback; yalnızca izinli kapsam.

Bu kapılar “sıfır risk” veya otomatik 10/10 anlamına gelmez. Prototip olgunluğu ile gerçek operasyon güvenliği ayrı değerlendirilir.

## Codex'e ilk görev
Önce #4: 3 tema × 2 mod UX tasarımı ve en küçük test edilebilir PR. 10 sayfa, 4 hikâye, Python report parity, önceki viewer'lar ve CI korunacak. Tek HTML'den modülerleşmeyi #10'a bırak. API/network açma. Ardından #5, #9, #6 ayrı PR. Her PR için gerçek tarayıcı görselleri ve koşul raporu üret; main'e merge etme.