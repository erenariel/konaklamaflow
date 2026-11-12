# v0.3 snapshot ve rapor kullanımı

Bu dosya şeması yalnızca kurgusal veya kaynağında önceden en aza indirilmiş test verisi içindir. Ham otel export'u, misafir adı, iletişim bilgisi, belge veya credential kabul eden bir içe aktarıcı değildir. Alan biçimi kişisel veri olmadığını tek başına kanıtlamaz.

Örnek girdi [`examples/fictional-hotel.json`](../examples/fictional-hotel.json), üretilmiş rapor [`examples/operations-evaluation.json`](../examples/operations-evaluation.json) içindedir. Mevcut v0.2 girdi biçimi değiştirilmez; 0.3 adaptörü ona bağlanır.

```sh
python -m konaklamaflow.experience_cli examples/fictional-hotel.json /tmp/fictional-suite-report.json
```

Çıktı karar desteğidir. Gerçek oda ataması, check-in, tahsilat veya resmi kayıt oluşturmaz.

## Kaynak alanları

- `schema_version`: `0.3`; `property_id`: opak tesis pseudonimi; `as_of`: kanonik takvim tarihi. İsteğe bağlı `at_time`, tesisin değerlendirme yerel saatidir; verilmezse `14:00`. Kaynağın ne zaman toplandığını veya güncel PMS revizyonunu kanıtlamaz.
- `rooms`: kategori, kişi kapasitesi, yatak, housekeeping, kat ve izinli olanak bayrakları. Üst sınır 500 oda; kapasite 1–20. İsteğe bağlı `maintenance`, en fazla 100 adet `{start, end}` bakım aralığı taşır; bitiş tarihi hariçtir ve bütün konaklama aralığı ortak motor tarafından denetlenir. Oda statüsünün “inspected” olması gerçek personel kimliğini doğrulamaz.
- `reservations`: opak iç/kaynak/PMS kodları, kanal, durum, geliş/ayrılış, kategori/kişi/yatak, oda bağlantısı, kimlik/ödeme **sinyalleri**, izinli özel talep bayrakları ve fiyat. Serbest metin misafir notu kullanılmaz. Rezervasyon üst sınırı 5000.
- `arrival_state`: `expected`, `arrived`, `checked_in` veya `checked_out`; yoksa `expected` kabul edilir. Confirmed rezervasyon, PMS kodu veya kimlik sinyali misafirin geldiği anlamına gelmez. Sinyaller yalnızca kurgusal/izinli kaynak girdisidir; paket bu olayları gerçekleştirmez. İptal/no-show gibi durumlarla çelişen `checked_in` sinyali fiziksel oda blokajını ortadan kaldırmaz; insan incelemesi gerekir.
- `price_total`: tüm kalışa ait **ondalık metin**; örneğin `"280.00"`. Float kullanılmaz. Desteklenen para birimiyle birlikte taşınır. Vergi, komisyon, kur, tahsilat veya gecelik gelir bilgisi içerdiği varsayılmaz.
- `channel_events`: kanal, dış kod ve belirtilen rezervasyon ilişkisiyle örnek olaylar; üst sınır 5000. `trip`/`ctrip` ilişkisi aynı sağlayıcı etiketinin kanonikleştirilmesidir; diğer kanallarla bulanık eşleştirme değildir.
- `tasks`: izinli departman türü, durum, öncelik ve var olan oda/rezervasyon bağlantısı; üst sınır 5000. Açık housekeeping/maintenance görevi hazırlığı veya öneriyi engelleyebilir. Görev durumu, kalıcı atama veya yetkili personel onayı değildir.

Bilinmeyen alan, geçersiz tür/tarih, bozuk ilişki veya yinelenen kimlik sessizce ileri taşınmamalıdır. Nullable bağlantı alanları da zorunludur: rezervasyonda `pms_ref`/`room_id`, olayda `reservation_id`, görevde `room_id`/`reservation_id` yok sayılmaz; bağlantı yoksa açıkça `null` kullanılır. Görev en az bir mevcut hedefe bağlanmalıdır. İzinli alan ve enum listeleri uygulanmış `experience_engine.py` doğrulamasıdır; bu belge API'nin tümünü donduran bir uyumluluk garantisi değildir.

## Eşleştirme ve karar raporu

Kanal eşleştirmesinde olayın kanal/dış kod/belirtilen rezervasyon kimliği ve `mapped` statüsü beraber değerlendirilir. Kaynak ilişkisini doğrulayacak veri yoksa otomatik eşleşme uydurulmaz. `direct`/`agency` içindeki dolu PMS kodu da doğrulanmış canlı PMS sonucu değil, sınırlı bir girdi sinyalidir. Farklı sağlayıcıdaki aynı dış kod rezervasyon birleştirme nedeni değildir.

Raporun `arrivals` kayıtları suite incelemesinin sonucudur: durum, engeller, kontrol listesi, öneri ve insan incelemesi sınırını taşır. `event_reviews` / `unmatched_channel_events` kaynak ilişki sorunlarını, `tasks` öncelik sırasındaki kurgusal görevleri belirtir. İç içe `engine_report`, ortak v0.2 motorunun tanı çıktısıdır; nihai suite sonucunun üstüne bir onay katmanı gibi kullanılmaz.

`room_plan`, güncel günün pending/confirmed blokajlarını, fiziksel konaklamayı, doğrulanmamış çıkışı, bakım ve departman işlerini ortak motor verisinden üretir. `reservation_ids_all_holds`, ileri tarihli blokajları da içerir. `REQUIRES_LIVE_REVALIDATION` gerçek oda boşluğu veya teslim garantisi değildir. Tarayıcı bu rapor alanlarını gösterir; kendi ayrı oda müsaitliği veya kanal eşleştirme kararını üretmez.

`financial_review`, para birimi bazında bütün kalışa ait kurgusal rezervasyon tutarlarını toplar; gelecekteki ve devam eden confirmed/in-house kayıtlar bulunabilir. Bu, günlük gerçekleşmiş gelir, ADR/RevPAR, tahsilat, banka mutabakatı veya muhasebe bakiyesi değildir. Folyo satırları/ödeme kalemleri olmadığı için gerçek folyo/gece-audit mutabakatı uygulanmış sayılmaz. Para birimleri birbirine çevrilmez.

`review_ready`, yalnızca belirtilen snapshot ve değerlendirme anındaki insan ön incelemesine uygunluk anlamına gelir. Kaynak değişirse rapor yeniden üretilmelidir. Aynı gün önceki konaklamanın çıkışı, pending blokaj, teknik/temizlik işi ve kritik özel talepler ayrıca incelenir. Öneriler kısıtları koruyan sezgisel seçimdir; bütün otel için en iyi plan garantisi değildir.

Tarayıcı Python çıktısını gösterir. Housekeeping, görev veya kanal olayı simülasyonunda veri değiştiğinde rapor eski sayılır; sıfırlamaya kadar hazır kararı ve rapor dışa aktarımı geçersizleştirilir. Bu, tarayıcıda aynı kararların yeniden hesaplandığı anlamına gelmez. Tarayıcı logu ve rapor hash'i sunucu audit'i, kimlik doğrulama veya insanın gerçek işlem onayı değildir. Salt okunur AI devri ve gelecekteki güven sınırları için [Entegrasyon Sözleşmesi](ENTEGRASYON_SOZLESMESI_TR.md) okunmalıdır.

## Salt okunur suite AI devri

`make_suite_handoff(trusted_snapshot, issued_at, validity_seconds=300)` son suite kararlarını temel alır; içteki v0.2 tanı raporunu nihai sonuç yerine kullanmaz. `verify_suite_suggestion(retained_manifest, suggestion, checked_at, *, current_snapshot)` güvenilir güncel snapshot ile tekrar değerlendirme ister. Zaman, saklanan manifest ve güncel snapshot AI tarafından kontrol edilen girdi olamaz. Yalnızca opak görev kimliği, son durum/engel kodları ve snapshot/rapor hash'leri aktarılır; rezervasyon/kanal/oda kodu, serbest metin veya kimlik belgesi gönderilmez. Hash/TTL kimlik doğrulama, kalıcı tekrar işlem koruması veya herhangi bir yazma yetkisi değildir.
