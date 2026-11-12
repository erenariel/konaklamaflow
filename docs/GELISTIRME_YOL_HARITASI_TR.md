# 4 aşamalı uygulama planı ve kabul ölçütleri

Bu yol haritası planlanmış işler içerir. Aşağıdaki tarihler taahhüt değildir. Sürüm numaraları hedefi temsil eder, otomatik devreye girmez. “Planlandı” adımları uygulanmış işlev veya kullanıcı sonucu olarak başvuruya yazılmaz.

## Aşama A — Güvenli Git / mevcut repo bütünlüğü

**Önkoşul:** Codex e-posta metaverisi temizliği, yedekleme, revizyon SHA doğrulaması, PR #2 ve v0.1.1 etiket kontrolü tamamlanmış olmalı.

- Önce eski kişisel e-postaların Git geçmişinden temizlendiği ve yeni Git noreply ayarının bu çalışma ortamında etkin olduğu doğrulanır; başka cihaz ve CI kimlikleri ayrıca kontrol edilir.
- Eski dallar ile yeni repo arasında yanlış force push/merge oluşmasını engellemek için *fresh clone* kullanılır.
- `v0.3` yeni dosyaları, v0.2 Python çekirdeğine zarar vermeden bağımsız özellik dalında eklenir.
- CI ve security scan, yeni/daha önceki testleri birlikte çalıştırır.

**Kabul:** Eski commitlerde `main` ve `feature` güncel erişilebilir ref'lerinde kişisel e-posta sıfır; CI başarılı, PR kayıpsız.

## Aşama B — Gerçekçi ama kişisel verisiz işlevsel demo

- Hedef senaryo paketi: kurgusal 20–60 oda (mevcut örnek 18 odadır); bireysel/grup rezervasyon, iptal, oda değişimi, HK, transfer, OOO/OOS, folyo mock, gece audit.
- OTA olay akışı: `created`, `modified`, `cancelled`, `duplicate`, `unknown`, `rate mismatch`, `guest request`.
- Aynı rezervasyonun CM → PMS ve OTA → CM yolları uyumlu olarak birleştirilir, çelişki insan kuyruğuna gönderilir.
- Mobil maid paneli ve ayrıntılı check list; resepsiyon KPI; gelir yönetimi kurgusal dashboard.
- Oda tahsis motoruna constraint solver / global optimisation; senaryolu golden tests ve property-based tests.
- Üretim ortamına hazırlanabilecek UX: WCAG 2.2 AA, klavye navigasyonu, telefon ekranında erişilebilir tablo/drawer.

**Kabul:** Tamamen offline senaryo demosu, gerçek kişi verisi sıfır, erişilebilirlik ve regresyon testleri başarı, dış trafik sıfır.

## Aşama C — Onaylı otel pilotu, *önce read-only*

- Otel yönetiminden yazılı pilot kapsamı, güvenlik ve veri işleme onayı alınır.
- Salt okunur izinli PMS export/API adaptörü ve müşteri kimliğinden arındırılmış snapshot kullanılır.
- Operasyon kayıtları yalnızca yerel yetkili personel tarafından kontrol edilir, sorunlar sonuçlarıyla etiketlenir.
- Değişiklik, iptal, gün sonu ve bağlantı hatasında `fail closed` davranışı test edilir.
- Bağımsız personelin haftalık geri bildirimi, yanlış pozitif ve zaman ölçümleri alınır.

**Kabul:** Ölçülen gerçek operasyon yararı; doğrulanabilir anonimleştirilmiş pilot raporu; hiçbir resmî/finansal otomatik işlem yok.

## Aşama D — Resmî yetkili entegrasyon & AI otomasyon

- Üretici ve channel manager API sözleşmeleri; sandbox, PCI/PII, security review.
- Kısıtlı service accounts; otonom ajan değil **policy-enforced tool execution**.
- İşlem öncesi personel onayı, idempotency, transaction log, retry ve rollback.
- Resmî kayıt, ödeme, sözleşmeli fiyat, yetki ve vergi süreçlerine dair profesyonel hukuk/denetim onayı.
- Kademeli test: sandbox → shadow → canary → yetkili production.

**Kabul hedefi:** Tanımlı yetki dışı işlem testlerinin tamamı engellenmeli; hata ve düzeltme kayıtları tutarlı olmalı, denetim ve pilot kabul ölçütleri önceden tanımlanmalıdır. Bu hedef, bugün ölçülmüş “sıfır risk” veya olumlu pilot sonucu değildir.

## Başvuru stratejisi ve açık kaynak katılımcılığı

OpenAI Codex for Open Source başvurusu yapılacaksa programın güncel resmî koşulları başvuru anında ayrıca doğrulanmalıdır. Bu belge bir uygunluk değerlendirmesi veya kabul tahmini değildir. Uydurma yıldız, sahte pilot, birbirini tekrar eden yapay PR veya reklam amaçlı commit sayısı üretmek yerine özgün katkıları, dış geliştirici issue'larını, gerçek personel testlerini ve düzenli bakımı belgelemek daha değerli olur. Kesin kabul/altı aylık Pro garantisi yoktur.
