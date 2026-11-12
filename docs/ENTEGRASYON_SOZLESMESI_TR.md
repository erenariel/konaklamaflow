# Entegrasyon ve veri sözleşmesi

**Durum:** v0.3, kurgusal veriyle çalışan salt okunur inceleme prototipidir. Aşağıdaki sunucu yetkilendirmesi, kalıcı olay deposu ve işlem yürütme akışı hedef mimaridir; çalışan canlı hizmet değildir. Kişisel veriyi yalnızca regex ile denetlemek anonimleştirme sayılmaz.

## Çalışan sınır ve uyarlama

`experience_engine.evaluate(...)`, 0.3 şemasındaki kurgusal snapshot'ı doğrular; rezervasyon ve oda hazırlığı için mevcut `operations.plan_operations(...)` / çekirdek kararlarına bağlanan adaptör kullanır. Kapasite, talep ve kanal eşleştirme kontrolleri bu ortak kararların üzerine eklenir. Ayrı bir v0.3 check-in kural motoru işletilmez.

`demo/hotel-suite.html`, Python'da üretilen raporla beslenen görsel demodur. Tarayıcıdaki görev/housekeeping etkileşimi kurgusal yerel simülasyondur; gerçek envanter revizyonu, yetkili personel onayı veya güncel Python hesaplaması yerine geçmez. Demo değişikliği eski raporu geçersiz hale getiriyorsa “hazır” sonucu yeniden üretilmiş gibi sunulmamalıdır. Aynı durumun JavaScript'te ikinci bir bağımsız karar motoruyla tahmin edilmesi entegrasyon yolu değildir.

Mevcut paket ağ üzerinden PMS/OTA/AI çağrısı yapmaz. Oda atamaz, kimlik doğrulamaz, para hareketi veya KBS bildirimi gerçekleştirmez. PMS/OTA/channel manager, olası yetkili bağlantıda da kaynak kaydın gerçek sahibidir. Mevcut dosya sözleşmesinin alanları ve kurgusal fiyat toplamının anlamı [V03_SCHEMA_TR.md](V03_SCHEMA_TR.md) içindedir.

## Gelecekteki olay zarfı — tasarım

Aşağıdaki örnek canlı endpoint değildir; mevcut 0.3 dosya şemasına doğrudan gönderilmemelidir. İzinli sağlayıcı adaptörü kişisel alanları kaynağında dışarıda bırakmalıdır.

```json
{
  "event_id": "OPAQUE_EVENT_ID",
  "property_id": "OPAQUE_PROPERTY_ID",
  "source": "channel_manager",
  "source_reservation_id": "OPAQUE_SOURCE_ID",
  "source_revision": "REVISION_0042",
  "received_at": "2026-11-12T10:00:00Z",
  "event_kind": "updated",
  "stay": {"arrival": "2026-11-12", "departure": "2026-11-14"},
  "rate_plan": "OPAQUE_RATE_PLAN_ID",
  "room_category": "standard",
  "guest_count": 2,
  "room_count": 1,
  "total": {"amount_minor": 12345, "currency": "EUR"},
  "guest_identity_verified": false
}
```

Gerekli güven sınırları:

1. `property_id`, rol ve erişim kapsamı istemciden alınarak yetki kazanamaz; kimliği doğrulanmış servis bağlamıyla eşleştirilir. Tenant anahtarı tüm sorgu, önbellek, idempotency ve audit kayıtlarına dahil edilir.
2. Sağlayıcı kimliği, imza/OAuth ve servis yetkisi sunucuda doğrulanır. Kaynak olayındaki metinler veya AI çıktısı bir araç çalıştırma talimatı olamaz.
3. `source_revision`, sağlayıcının tanımladığı sıralama modeliyle değerlendirilir. Rastgele revision metnini sözlük sırasına koymak “en yeni” kaydı kanıtlamaz. Eski/tekrarlanan olay güncel durumu ezmez; bilinmeyen sıralama insan incelemesine gider.
4. Eksik alan, çelişki, bilinmeyen oda/kaynak veya belirsiz eşleşme otomatik olarak tamamlanmış sayılmaz. `NEEDS_HUMAN_REVIEW` tercih edilir.
5. Kimlik ve ödeme durumları yalnızca kaynak sinyalidir. Bu alanların `true`/“hazır” olması gerçek kimlik, para veya KBS sonucunun doğrulanması değildir.

## Eşleştirme ve oda politikası

Kaynak anahtarı `(property_id, source, source_reservation_id)` olarak tutulur; aynı dış kod farklı kanalda aynı rezervasyon kabul edilmez. PMS eşleştirmesi, yalnızca dolu bir `pms_ref` veya benzer isimle kesinleşmez. Kaynak ilişkisi, tarih/statü, kategori/rate-plan, oda sayısı, kişi sayısı, para birimi ve tutar tutarlılığı incelenmelidir. Veri yoksa eşleşme kanıtı uydurulmaz.

Tarih aralığı `[arrival, departure)` biçimindedir. Takvimde ardışık rezervasyonlar çakışmayabilir; önceki misafirin gerçekten çıktığı ayrıca doğrulanmalıdır. Pending blokajlar, OOO/OOS, temizlik/kontrol eksikliği ve güncel envanter belirsizliği oda önerisini engelleyebilir. Önerilen oda, kaynağa yazılmış tahsis veya misafire verilen garanti değildir. Greedy seçim global optimizasyon kanıtı değildir.

Kritik talepler; erişilebilirlik, alerji veya bebek yatağı gibi durumlarda açık kapasite/olanak ve yetkili personel teyidi gerektirir. Serbest metin misafir notu, kimlik belgesi, telefon, e-posta, ödeme kartı veya erişim anahtarı inceleme snapshot'ına ve AI zarfına girmez.

## İki asistanın sözleşmesi

- **AI-1:** İzinli, en aza indirilmiş olay/rapor verisinden inceleme görevi önerir.
- **AI-2:** Deterministik engel kodlarını açıklar veya insan için gönderilmeyen taslak hazırlar.
- **Güvenilir kural/policy katmanı:** Tarih, oda/kanal ilişkisi ve izinleri doğrular. AI metni izin üretemez.
- **Yetkili personel:** Gerçek kararları ayrı yetkili PMS sürecinde verir; bu paket o süreci yürütmez.

Mevcut `agent_protocol.py` v0.2 salt okunur görev referanslarını denetler. Suite akışında `make_suite_handoff(...)` ve `verify_suite_suggestion(..., current_snapshot=...)`, son suite kararlarına dayanır; kapasite/özel talep/kanal engelleri iç tanı raporuna bakılarak atlanamaz. Manifest, güncel rapor ve kontrol zamanı güvenilir çağırandan gelmelidir; AI'nın kendi gönderdiği rapor veya tarih “güvenilir kaynak” yerine kullanılamaz. Hash ve TTL, kaynağın kimliğini doğrulamaz. Manifest yetki token'ı değildir; `verify_suggestion` sonucunun doğru olması işlem yürütme onayı değildir. Gerçek LLM çağrısı ve tool dispatcher yoktur.

## İleride insan onayı ve yürütme kapısı — uygulanmış değil

Öneri → kimliği doğrulanmış yetkili insan onayı → kaynakta taze revizyon okuma → aynı property ve kapsam doğrulaması → compare-and-swap/revision önkoşulu → ayrı izinli sistemin sonucu şeklinde tasarlanmalıdır. Her geçiş sunucuda doğrulanır. Önceden işaretlenmiş bir UI kutusu, tarayıcı değişkeni veya AI çıktısındaki “approved” kelimesi onay değildir.

Yetkiler `read`, `recommend`, `prepare`, `approve` ve `execute` olarak ayrılır. Bu sürümde son ikisini sağlayan kimlik/komut hizmeti yoktur. İkinci asistanın “onaylaması” tek başına hiçbir kritik yetkiyi açmaz.

## Kalıcı audit, tekrar işlem ve yarış koruması — hedef mimari

Kalıcı kayıtta en az: `request_id`, tenant, kaynak olay/rezervasyon kimliği, kaynak revizyonu, policy sürümü, servis/insan aktörünün güvenilir ID'si, izin kapsamı, plan özeti, insan onayı bağı, beklenen revizyon, önceki/sonraki durum özeti, sonuç kodu, saat ve correlation/trace ID bulunmalıdır. Ham misafir notu, kimlik numarası, belge veya credential loglanmamalıdır. Salt append-only tasarım tek başına değiştirilemezlik kanıtı değildir; erişim kontrolü, saklama ve bütünlük denetimi gerekir.

Idempotency anahtarı tenant + kaynak kimliği + işlem türü + beklenen kaynak revizyonu kapsamında üretilir. Sunucuya ait HMAC anahtarı gerekiyorsa yalnızca korumalı sunucuda tutulur; frontend'e gönderilmez. Veritabanında benzersiz kısıt ve atomik işlem durumu gerekir. Aynı anahtarın farklı payload ile gelmesi çatışmadır; aynı sonucu yeniden yürütmek değildir.

Timeout sonucu belirsizse yeniden tahsilat/check-in denenmez. Durum `UNKNOWN` tutulur, kaynakla mutabakat yapılır, gerekirse insan devri gerekir. Lease/transaction lock, beklenen kaynak revizyonu ve rollback/compensation politikası ayrıca tasarlanmalıdır. Bu projede henüz kalıcı idempotency/audit deposu, dağıtık kilit, sunucu onayı veya canlı komut yürütücüsü bulunmaz. Tarayıcının kurgusal olay listesi bunların yerine geçmez.

## Gerçek bağlantı öncesi kabul kapıları

Otel ve sağlayıcının yazılı kapsam/yetkisi; ayrı servis kimlikleri/RBAC/MFA; tenant sınırı testleri; taze revizyon ve stale/replay testleri; PII/log minimizasyonu; idempotency/timeout mutabakatı; bağımsız güvenlik ve ilgili hukuk değerlendirmesi gerekir. KBS, kimlik belgesi ve ödeme süreçleri için ayrıca uzmanlık ve yetkili sağlayıcı gereklidir. Kurgusal testlerin başarılı olması üretim uygunluğu veya mevzuat sertifikası değildir.
