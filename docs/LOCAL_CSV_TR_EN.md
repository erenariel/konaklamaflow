# Yerel CSV içe aktarma / Local CSV review (candidate)

**Durum / Status:** v0.2.0rc2 adayı. Gerçek müşteri veya otel dışa aktarımlarında
güvenli kullanım henüz bağımsız olarak doğrulanmadı. İlk testler için yalnızca
examples/csv/ altındaki **tamamen kurgusal** verileri kullan.

## 60 saniyede dene

Python 3.11+ kurulu terminalde, depo dizininden:

~~~bash
python -m pip install .
konaklamaflow demo
konaklamaflow review-csv \
  --rooms examples/csv/rooms.csv \
  --reservations examples/csv/reservations.csv \
  --as-of 2026-11-12
~~~

konaklamaflow demo, kurulu pakette gelen 5 odalı kurgusal örneği çalıştırır.
review-csv iki yerel CSV okur, Python'da geçici olarak asgari alanlara
indirger ve var olan rezervasyon inceleme kurallarını çalıştırır.
Girdi dosyalarını değiştirmez veya geçici JSON dosyası yazmaz.
Çıktı varsayılan olarak terminale yazılır. Paylaşılabilir rapor olarak
değerlendirme. --output review.json kullanırsan raporu yerel diske yazar;
POSIX sistemlerde izinler 0600 olur. Girdi dosyasının üzerine yazmayı reddeder.

## Sütun sözleşmesi / CSV schema

UTF-8, virgülle ayrılmış dosya; UTF-8 BOM kabul edilir. Alan adları aşağıdaki
gibi **tam ve küçük harfli** olmalı. Excel .xlsx dosyası doğrudan desteklenmez.
Başlıklar benzersiz olmalı. İki dosyanın her biri en fazla 2 MB.
Oda sınırı 500; rezervasyon sınırı 5.000.

| Dosya | Gerekli sütunlar | İsteğe bağlı |
|---|---|---|
| rooms.csv | room_id,category,beds | active |
| reservations.csv | reservation_ref,checkin,checkout,category,status | room_id,twin_requested |

Desteklenen category değerleri: economy, basement, standard, superior, deluxe,
triple, family, suite. beds: double, twin, flex. status: confirmed, pending,
cancelled. checkin/checkout: YYYY-MM-DD (checkout gelişten sonra).
active/twin_requested: true/false, TRUE/FALSE, 1/0, yes/no; boşsa sırasıyla
true ve false. Oda adı veya rezervasyon referansı boş bırakılamaz.
Tutar, özel istek, çok odalı ebeveyn rezervasyonu, kaynak revizyonu ve
saat dilimi **henüz** desteklenmez. Kaynak sabit LOCAL_CSV olarak yazılır.

## Asgari veri / Data minimization

Program, aşağıdaki **tam adlandırılmış** özel sütunları kabul eder ama tüm
değerlerini atar: guest_name, first_name, last_name, full_name, name, surname,
guest_first_name, guest_last_name, guest_email, email, guest_phone, phone,
phone_number, mobile_phone, guest_address, address, passport, passport_number,
id_number, national_id, date_of_birth, dob, guest_notes, notes, remarks,
special_requests, payment_card, credit_card, card_number, card_expiry, cvv,
payment_token, guest_id, guest_identifier.

Tanımsız sütun **reddedilir**; otomatik olarak korunmaz. Oda kimlikleri
R_... ve rezervasyon referansları B_... biçimine dönüştürülür.
Bellekte rastgele üretilen gizli anahtarla HMAC kodu kullanılır; aynı
çalıştırmada oda/rezervasyon ilişkisi korunur, başka çalıştırmada kodlar
değişir. Anahtar veya eşleme tablosu diske yazılmaz.

**Bu işlem hukuken veya teknik olarak kesin anonimleştirme değildir.**
Konaklama tarihleri, kategori, oda planı ve çıktıdaki örüntülerden
yeniden kimlik belirleme mümkün olabilir. Önceki kaynak CSV hâlâ diskte
bulunur. Özellikle kamuya açık GitHub issues, e-posta, ekran görüntüsü,
Pages, çevrimdışı ZIP ve CI artefaktlarına gerçek otel verisi koyma.
Gerçek dışa aktarımlarda geçerli işletme izni, veri minimizasyonu, yerel
güvenlik ve KVKK incelemesi gerekir.

## English summary

Strict local CSV mapping for fictional trials. Explicit allowlisted business
fields only; named sensitive columns are dropped, unknown headers are rejected.
Room and booking IDs receive per-run HMAC pseudonyms. Reports are advisory,
offline and read-only. **Pseudonymization is not irreversible anonymization.**
Dates and booking patterns may remain personal data. No arbitrary OTA vendor
export schema is supported yet. Do not upload real guest files to GitHub or
test with live hotel data without authorization and privacy review.
