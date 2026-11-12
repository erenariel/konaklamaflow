# KonaklamaFlow • AI destekli otel operasyonları hedef mimarisi

**Sürüm hedefi:** v0.3 konseptten modüler v1.0 işletim katmanına geçiş. **Mevcut ürün durumu:** v0.3 entegrasyonu kurgusal tarayıcı demosu ve önceden pseudonimleştirilmiş veri için deterministik Python inceleme adaptörüdür. Kimliksiz veri kullanıldığı yalnızca alan biçiminden kanıtlanamaz. Gerçek PMS/LLM/OTA entegrasyonu yoktur.

## 1. Ürün vizyonu ve kapsam

Otel çalışanının veri arama, birden fazla ekrandan tutar karşılaştırma, oda alternatifi bulma, departmanlar arası hatırlatma ve takip gibi tekrar eden işlerini azalt; **kimlik doğrulama, misafir empatisi, şikâyet yönetimi, ödeme, KBS, konaklama hakkı ve nihai oda teslimi** gibi yetki veya hukuki sorumluluk gerektiren işlemlerde insan denetimini koru. Vizyon, insanı otelden çıkarmak değil, **onun misafire ayırdığı zamanı artırmak**.

Projenin arayüzü bir PMS gibi geniş modüllere sahip olabilir; fakat ilk gerçek dağıtım şekli yeni PMS değil, *mevcut PMS'ye bağlanan izinli operasyon ve denetim katmanı* olmalıdır. Gerçek entegrasyon ileride yetkilendirilirse kaynak sistem kaydı esas alınacaktır; bugünkü kurgusal snapshot güncel PMS kaydı sayılmaz.

## 2. Otel içi olayın uçtan uca yaşam döngüsü

```
Rezervasyon oluşturuldu/değişti/iptal oldu
      │
      ▼
Yetkili kanal yönetimi/OTA/PMS bağlayıcısı
      │
      ▼
Güvenli veri şeması ve kaynak kaydı (provider, property, source_id, revision)
      │
      ▼
Rezervasyon eşleştirme motoru
      ├── Kesin eşleşme (sabit dış kod + tesis + tarih + tutar + oda/rate)
      ├── Belirsiz eşleşme → insan incelemesi
      └── Çelişki / iptal / çift kayıt → güvenli durdurma
      │
      ▼
Oda uygunluk motoru (yatak, kategori, kapasite, HK, OOO, konaklama aralığı)
      │
      ▼
Vardiya görev orkestratörü / AI önerisi
      │
      ▼
Yetkili personelin fiziksel kimlik doğrulaması, PMS/folyo ve uygun resmî kayıt
      │
      ▼
İzinli komut çalıştırıcısı: taze revizyon + onay + idempotency + audit
      │
      ▼
Gerçek check-in onay sonucu, oda anahtarı teslimi ve misafir karşılaması
```

### 2.1 Birden fazla acenteden aynı rezervasyon

Güvenilir çözüm **ad/soyad benzerliğine** dayanmaz. Bunun yerine kuruma ait tesis ID, sağlayıcı ID, sabit rezervasyon/kaynak ID ve versiyon, giriş-çıkış tarihi, oda sayısı, oda tipi/rate-plan, konaklama bedeli/parabirimi ve rezervasyon statüsü kullanılır. Aynı kişi birden çok ayrı rezervasyona sahip olabilir. Ad veya soyad tahminine göre otomatik birleştirme yapılmaz. Farklı sağlayıcılarda ilişki zinciri yalnızca yetkili provider referansıyla kurulur. `source_id` + `revision` + `event_id` tekilleştirilir; sonradan gelen iptal/kısmi değişim eski kaydı sessizce ezmez.

Kanal yönetim sisteminin zaten PMS'ye işlediği bir rezervasyon yeniden yazılmamalıdır. `duplicate` veya `already_synced` olarak işaretlenip bir kişiye inceleme görevi açılır. Kısmi eşleşmeler hiçbir zaman otomatik check-in durumuna geçmez.

### 2.2 Oda atama için kriterler

- Geçerli kalış aralığı `[arrival, departure)`; iki rezervasyon arasında tarih çakışması olmamalı.
- Rezervasyon statüsü ve garantisi; iptal/no-show/opsiyonel farklıdır.
- Oda kategorisi, satış sözleşmesi, kişi/çocuk sayısı, yatak tipi ve zorunlu olanaklar karşılaştırılmalı.
- Housekeeping durumu yalnızca `inspected` ise check-in için hazır kabul edilebilir. `clean` ile `inspected` ayrı durumlar olmalıdır.
- OOO/OOS oda satışta veya oda önerisinde kullanılmaz. Yakın zamanda bitecek iş emrine güvenip odanın hazır olacağı varsayılamaz.
- Engelli erişimi, alerji, bebek yatağı, bitişik oda gibi kritik gereksinimlerde personel teyidi gerekir; özel talepler sözleşmeye göre mümkünlük/garanti ayrımı taşımalıdır.
- Nadir twin veya erişilebilir oda gibi kısıtlı stok korunmalı. Basit greedy sezgisi *genel optimizasyon değildir*. İleride constraint solver + insan incelemesi gerekir.
- Oda değişiminde mevcut ve sonraki konaklama, housekeeping ve kapı kartı revizyonu yeniden denetlenmeli.

### 2.3 Check-in durum makinesi

`OTA_RECEIVED → PMS_MATCHED → ROOM_PROPOSED → HK_INSPECTED → STAFF_IDENTITY_VERIFIED → PAYMENT_REVIEWED → STAFF_APPROVED → PMS_CHECKIN_CONFIRMED → OFFICIAL_REPORT_CONFIRMED → KEY_DELIVERED`

Bu bir örnek durum şemasıdır, otel/ülke politikasına göre her adımın sırası farklı olabilir. Kritik geçişler gerçek PMS'yle doğrulanmadan ilerlememelidir. KBS arızasında veya gönderim sonucunun bilinmediği durumda **başarılı bildirildi** mesajı üretilmez; yetkili resepsiyon görevlisi prosedürü uygular.

## 3. Modül kataloğu — hedef özellikler

| # | Modül | Personel/AI işlevi | Geliştirme safhası |
|---|---|---|---|
| 01 | Yönetim kokpiti | Bugünkü giriş/çıkış, engel, kat statüsü ve görev riskleri | v0.3 demo çalışıyor |
| 02 | Reservation Inbox | OTA/CM/PMS olayları, değişim/iptal sürümleri | v0.3 örnek veri |
| 03 | Reconciliation Engine | Kurgusal kaynak ilişkisi, tekrar ve çelişki incelemesi | v0.3 temel tutarlılık kontrolü; sağlayıcı doğrulaması değil |
| 04 | Akıllı oda atama | Tüm kalış süresince uygunluk, yatak/kat/özellik | v0.3 temel öneri |
| 05 | Check-in Preparation | Adım adım hazır olma ve insan devir noktaları | v0.3 demo çalışıyor |
| 06 | Grafik oda planı | Kat/oda renklendirmesi, bakım ve temizlik | v0.3 demo çalışıyor |
| 07 | Housekeeping | DND, maid atama, kontrol listesi, oda şefi onayı | v0.3 kısmi demo |
| 08 | Engineering | OOO/OOS, iş emri, SLA, servis geçmişi | v0.3 kısmi demo |
| 09 | Guest Relations | Özel talepler, şikâyet, dil ve empatik devir | v0.3 gönderilmeyen taslak |
| 10 | Folyo ve FinOps | Gecelik fiyat, rate plan ve City Ledger mutabakatı | tasarım, **para işlem yok** |
| 11 | Channel / Distribution | Stok ve rate senkron kontrolü, stop-sale | tasarım, **canlı API yok** |
| 12 | Revenue & Forecast | Doluluk, ADR, RevPAR, overbooking riski | tasarım, sentetik tutarlar |
| 13 | Sales & Marketing | Segment kampanyaları, sezon ve teklif taslağı | planlandı |
| 14 | Concierge & Transfers | Havalimanı transferi, servis talepleri, karşılama | planlandı |
| 15 | Audit & Night Shift | Gün sonu ön kontrolleri, kasa tutarsızlığı, no-show | planlandı |
| 16 | Access & Security | RBAC, MFA, tenant isolation, signed audit | planlandı — üretim için şart |
| 17 | AI Orchestrator | İki asistan için salt okunur inceleme sözleşmesi; gelecekte tool policy | Gerçek LLM/dispatcher ve işlem yetkisi yok |
| 18 | Analytics & Quality | Hata yakalama, yanlış pozitif, kişi-zaman tasarrufu | pilotta ölçülecek |

## 4. Departman rolleri ve izinler

- **Resepsiyon görevlisi:** Kurgusal/safe inceleme kayıtlarını görür; yetkili PMS'de nihai kimlik-check-in gerçekleştirebilir.
- **Kat görevlisi:** Kendine atanan oda listesini görür; temizlik bitti işareti gönderir; kendi başına işletmenin check-in kararını değiştiremez.
- **Kat şefi:** Oda temizlik kalitesini bağımsız doğrular (`inspected`).
- **Teknik servis:** Arıza ve OOO/OOS süresini yönetir; iş bitince housekeeping onayı ayrıca gerekir.
- **Guest relations:** Şikâyet, VIP, erişim gereksinimi, yanlış vaat ve hassas talepleri insan olarak değerlendirir.
- **Finans / Sweet tipi ajan:** Folyoyu ve ödeme uyuşmazlığını işaretler; para hareketi ayrıca izinli PSP/PMS ve yetkili onay gerektirir.
- **Rezervasyon / Smart tipi ajan:** Kanal bildirimlerini ve kaynak eşleştirmesini izler; nihai kayıt/oda sözünü vermeden önce kural motoruna danışır.
- **Otel yöneticisi:** Entegrasyon erişimi, politikalar, fiyat ve kullanıcı yetkileri için son sorumluluk.
- **AI motoru:** İnsan hesabı veya şifresi kullanamaz; ayrı sınırlı service identity ile yalnızca tanımlı araç ve veri kapsamını kullanır.

## 5. İki AI asistanı: güvenli görev dağılımı

**AI-1 (operasyon/tarama):** Yetkili adaptörlerin ürettiği kişi bilgisi dışarıda bırakılmış rezervasyon olaylarını okur, öncelik önerir, bed/oda kategorisi/özel istek eşleşme görevleri oluşturur.

**AI-2 (doğrulama/dil):** Deterministik motorun ürettiği uyarıları açıklar; sahte güven düzeyi veya hayali sistem erişimi üretmez, personel için çok dilli mesaj *taslağı* verir. Belirsiz vakayı zorlamaz; `NEEDS_HUMAN_REVIEW` döndürür.

**Hedef policy engine:** Gerçek entegrasyon eklenmeden önce kimlik, KBS, ödeme, cihaz/oda anahtarı ve rezervasyon değiştirme gibi aksiyonlar arayüzden bağımsız sunucu yetkisiyle korunmalıdır. Bugün bu aksiyonları çalıştıran araç bulunmaz; çalışan RBAC/onay sunucusu olduğu iddia edilmez. `read`, `recommend`, `prepare`, `approve`, `execute` farklı yetkilerdir. AI'nın metin üreterek kendisine yetki vermesi mümkün olmamalıdır. Tools, e-posta ve misafir notları **güvenilmez içerik** kabul edilir; prompt injection kontrolü yapılır.

**Freshness & trust (üretim öncesi gereklilik):** Okunan kaydın revizyonu (`snapshot_version`) ve envanter güncellemesi kural motoruna girdi olur. Her öneri sürelidir; işleme geçmeden önce kaynakta tekrar okunur. İki asistanın aynı yanlışı yapabilmesi mümkündür; ikinci model bağımsız doğruluk garantisi değildir.

## 6. İnsan merkezli misafir yolculuğu

| Aşama | Otomasyonun yapacağı | İnsanın sahip olduğu karar |
|---|---|---|
| Rezervasyon öncesi | Tesis bilgisi, oda ve tarih uygunluğu kontrolü; teklif taslağı | Fiyat politikası, istisna, sözleşme |
| Rezervasyon geldi | Kaynak eşleştirmesi, konfirmasyon ve oda talebi analizi | Belirsiz veya çelişkili kayıtları çözme |
| Giriş günü | Oda durumunu kontrol ve sıra önceliklendirme | Kimlik doğrulama, hukuki kayıt, oda teslimi |
| Konaklama | HK, transfer, küçük servis talepleri, takip | Şikâyet ve misafir ilişkileri |
| Çıkış | Folyo ön kontrolü, bakiye farkı uyarısı | Tahsilat/fatura/nihai check-out |
| Sonrası | Memnuniyet analizi, pazarlama taslağı | Gönderim izni, verinin silinmesi ve müşteri ilişkileri |

## 7. Operasyonun başarısını nasıl ölçeceğiz?

Zorunlu test/saha ölçümleri: `false_positive_rate`, `false_negative_rate`, `safety_block_rate`, `manual_override_count`, `reconciliation_precision`, `room_conflict_detection`, `time_to_staff_review`, `median_prepare_time`, `P95_prepare_time`, `integration_failure_rate`, `OTA_revision_lag`, `audit_completion`, `guest_feedback`. Gerçek saha kanıtı olmadan “0 hata”, “%99 memnuniyet” veya “milisaniyede check-in” iddiasında bulunulmaz.

## 8. Açık kaynak geliştirme ilkeleri

Özgün arayüz, sağlayıcıdan bağımsız veri modeli, açık test verisi, kamuya açık demo, katılımcı issue'lar, CI, teknik dokümantasyon ve güvenlik raporlama; bunlar uzun vadeli sürdürülebilirliği güçlendirir. Kod depo sahibi olmak, resmî API/sertifika sahibi olmak anlamına gelmez. Kullanıcı sayısı, pilot veya ortaklık iddiaları kanıtlanmadan eklenmez.

## Entegrasyon kararı: tek otorite, açık simülasyon sınırı

`experience_engine.py`, mevcut v0.2 `operations.py`/çekirdek kurallarını yeniden kullanır; 0.3 snapshot alanlarını bunlara uyarlayıp kapasite, özel talep ve kanal ilişkisi kontrolleri ekler. Tarayıcı, Python tarafından üretilen raporu gösterir. Yerel bir housekeeping/görev etkileşimi yeni bir PMS snapshot veya insan onayı yaratmaz; eski raporun güncelliği bozulursa hazır sonucu korunmuş gibi sunulmamalıdır. Teknik sözleşme ve henüz uygulanmamış sunucu sınırları için [Entegrasyon Sözleşmesi](ENTEGRASYON_SOZLESMESI_TR.md) esas alınır.
