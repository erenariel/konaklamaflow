# v0.3 entegrasyon kapsamı ve doğrulanabilirlik notu

Bu belge mimari kararı ve inceleme sınırını kaydeder. Nihai commit, test/Actions ve PR sonuçları, gerçekten çalıştırılan kontrollerin bağlantılarıyla PR açıklamasında/çalışma raporunda verilir; burada henüz gerçekleşmemiş sonuç üretilmez.

## Girdi ve sıra

Kullanıcının `KonaklamaFlow_v03.zip` paketi incelendi. İncelenen ZIP SHA-256 değeri: `0979490e835e22869cffa7fac9f9ef052648118fb6c875a803f8c7e19619c680`. Paket 19 dosya/661013 açılmış bayt içeriyor. Path traversal, yinelenen arşiv yolu ve symlink gibi riskler açmadan önce kontrol edildi. Paketten komut veya canlı entegrasyon çalıştırılmadı.

[`CODEX_INTEGRATION_TR.md`](CODEX_INTEGRATION_TR.md) kaynak paketteki haliyle korundu ve entegrasyon sırası esas alındı. Paket `README.md`, `__init__.py` veya mevcut yapılandırmaların üzerine topluca kopyalanmadı; mevcut v0.2 modülleri ve testleri kaldırılmadı. Önceki denetimde hazırlanmış yerel güvenlik düzeltmeleri doğrulanmış kaynak yaması olarak yeni dala aktarıldı; eski temizlenmemiş Git geçmişi kullanılmadı. Main ve PR #2'nin geliştirme dalı değiştirilmedi.

## Başlangıç kaynağı ve Git kimliği

Yeni çalışma temiz GitHub geçmişiyle açılmış clone ve `feat/hotel-operations-suite-v03` geliştirme dalı kullanır. Doğrulamada esas alınan temiz uçlar:

| Ref | Temiz SHA |
|---|---|
| KonaklamaFlow main | bcf025b1d102b64a5bc6eb295b007574650ddca2 |
| v0.2 geliştirme dalı / PR #2 head | 07a2251804cead1691953f978b1fffabc2176610 |
| v0.1.1 | c6b8f88cf7066da3f8b8cd9abebfba03c0650d08 |
| profil deposu main | 9608457eba67981e2b4597d24d65c5953cbe3285 |

Author ve committer için GitHub noreply kullanılmalıdır. Her cihaz/CI kimliği ayrıca doğrulanmalıdır; global ayarın geçmişte yapılmış olması bugün etkin olduğunu kanıtlamaz. Bu belgeye kişisel e-posta veya özel denetim bulgusu eklenmez.

## Mimari karar

Kaynak paketteki bağımsız 0.3 rezervasyon mantığı kalıcı ikinci otorite yapılmaz. `experience_engine.py`, 0.3 alanlarını v0.2 `operations.py`/çekirdek kontrollerine uyarlar; kişi kapasitesi, özel talep ve kanal ilişkisi incelemesi bu ortak kararların üzerine eklenir. “PMS kodu dolu” veya “kimlik sinyali true” tek başına yetkili eşleşme/işlem kanıtı değildir.

Tarayıcı, Python'dan üretilen `operations-evaluation.json` raporunu gösterir. UI'nın yerel housekeeping/görev simülasyonu bir PMS revizyonu veya yeni bir yetkili inceleme sonucu oluşturmaz. Housekeeping, görev veya kanal simülasyonu sonrası rapor eski kabul edilir; sıfırlamaya kadar hazır sonucu ve rapor dışa aktarımı geçersizleşir. Hazır sonucu yeniden hesaplanmış gibi gösterilmez. Böylece görsel senaryo ile güvenilir karar kaynağı ayrılır.

0.3 şema alanları, para semantiği ve rapor kullanımı [V03_SCHEMA_TR.md](V03_SCHEMA_TR.md) içinde açıklanır.

Python birim testleri Playwright gerektirmemelidir. Paket içindeki tarayıcı testleri `tests/browser/` altında tutulmalı; Chromium yolu yalnızca açık ortam değişkeniyle seçilmeli veya Playwright'ın kurulu varsayılanı kullanılmalıdır. Önceki v0.2 ve yeni 0.3 testleri beraber korunur.

## İşlev ve sınır

- OTA/CM kayıtları: kurgusal alan/ilişki ve tutarlılık incelemesi; gerçek Booking.com, Expedia, Trip.com/Ctrip bağlantısı değildir.
- Check-in/oda: kategori, kişi kapasitesi, yatak, temizlik/teknik bloke ve zaman aralığı için öneri; gerçek oda tahsisi veya tamamlanmış giriş değildir.
- Görev/misafir ilişkileri: kurgusal kuyruğa aktarma ve gönderilmeyen kurallı taslak; gerçek personel yetkisi veya mesaj gönderimi değildir.
- Gelir/folyo/audit: kurgusal tutarların sınırlı incelemesi; günlük tanımlı muhasebe, gerçek tahsilat veya üretim gece audit'i değildir.
- İki AI: salt okunur görev/inceleme sözleşmesi ve hedef policy mimarisi; gerçek model/araç yürütücüsü değildir.

Kalıcı audit/idempotency, RBAC/MFA, tenant izolasyonu, kaynak revizyon kilidi ve sunucuda insan onayı gelecekte ayrıca uygulanıp test edilmelidir. Geçerli bir JSON hash'i veya iki asistanın aynı cevabı güvenlik/yetki kanıtı değildir. Ayrıntılar [`ENTEGRASYON_SOZLESMESI_TR.md`](ENTEGRASYON_SOZLESMESI_TR.md) ve [`GUVENLIK_TEHDIT_MODELI_TR.md`](GUVENLIK_TEHDIT_MODELI_TR.md) içindedir.

## Araştırma ve kaynak disiplini

[`RESEARCH_MATRIX_TR.md`](RESEARCH_MATRIX_TR.md), ElektraWeb yardım sayfaları, Sistem Otel resmî ürün sayfasından bağlanan GitBook kılavuzu ve Sedna'nın üreticisi Kod Yazılım'ın ürün açıklamasına dayanır. Bunlar ürün davranışının bağımsız testi değildir. Özel kod, ekran, görsel varlık veya kılavuz metni çoğaltılmaz; üretici ortaklığı/sertifikasyonu varsayılmaz.

## Devam öncelikleri

1. Sentetik stale/duplicate/reordered olay senaryoları ve yanlış hazır sınıflandırmasını engelleyen regresyon testleri.
2. Şema sürümleme; para birimi/tutar ve çoklu oda/rate-plan sözleşmesi; kaynak revizyonunun açık anlamı.
3. Yetkili read-only adaptör için ayrı güvenlik tasarımı, property kapsamı ve veri minimizasyonu.
4. Kalıcı ve tenant kapsamlı idempotency/audit; bilinmeyen dış işlem sonucunu mutabakat olmadan yeniden denememe.
5. İzinli sentetik personel değerlendirmesi ve ölçüm yöntemi. Büyük otel ölçeği, kullanıcı benimsenmesi veya zaman kazanımı henüz kanıtlanmış değildir.

Bu geliştirme main'e otomatik birleştirme veya yeni sürüm yayımlama yetkisi vermez. PR ve release kararı kullanıcı onayını bekler. Canlı PMS, ödeme, KBS, gerçek check-in ve kimlik belgesi işlemleri etkinleştirilmez.
