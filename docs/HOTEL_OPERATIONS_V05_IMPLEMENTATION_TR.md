# KonaklamaFlow v0.5 — rezervasyon, misafir, folyo ve rapor çalışma alanı

**Gerçek proje kodu:** `konaklamaflow/hotel_ops.py` (veri doğrulama, rezervasyon taslağı, folyo/rapor hesaplama), `demo/hotel-ops-module.js` (mevcut 10-modüllü uygulamaya eklenen sekiz operasyon sayfası), `demo/v04-integrated-preview.html` (aynı projedeki bütünleşik gerçek arayüz), `scripts/generate_hotel_ops_demo.py` (Python rapor-fixture eşitliği), ve ilgili testler.

Bu gerçek otel kullanımı için **yetkilendirilmiş PMS, kimlik veri tabanı, ödeme işlemcisi veya muhasebe yazılımı DEĞİLDİR**. Bu kod üretimde kullanılacak iş modellerini tasarlayan, yalnızca kurgusal veriyle çalışan uygulama katmanıdır. `main` henüz değiştirilmedi; PR insan incelemesi ve CI ile korunur.

## Navigasyon ve erişilebilirlik

- Küresel dil seçici, görülebilir **üst araç çubuğunda**. TR / EN / FR / EL / HE / AR / DE / RU / ES / UK sunum açıklamalarını ve yeni modüllerdeki temel eylem başlıklarını değiştirir. Türkçe kalmış eski modüller için “tümü eksiksiz çevrildi” iddiası **yoktur**.
- Başlangıç modülü **Oda Planı**. Önceki 10 modül korunur; sekiz yeni modül eklenir: Rezervasyonlar, Misafirler, Aktif Folyolar, Acente Alacakları, Rapor Merkezi, Kurlar ve Fatura, Blokajlar, Demirbaşlar.
- Yeni oda envanteri ana `examples/fictional-hotel.json` kaynağındaki **18 oda** ve oda kategorileri/kapasiteleriyle hizalanmıştır.
- Oda kategori kataloğunda ekonomi, standart, superior, deluxe, triple, family bulunur. Bir tesiste başka kategoriye (suite, studio, accessible, connected rooms) geçiş, tesisin gerçek katalog ve kapasite sözleşmesiyle gerçekleştirilmelidir. Otel yetkisi olmadan ek oda uydurulmaz.

## Rezervasyon oluşturma: çalışma sözleşmesi

- Sıra numarası `KFD-YYYY-NNNN` demo tahsisi; gerçek sisteme yazılmaz. Formda grup/konaklama adı, giriş/çıkış, acente ve kanal ref, BB/HB/RO/FB, self payment / City Ledger, net/komisyon/komisyonsuz, confirmed/option/waitlist, opsiyon tarihi, birden fazla oda ve kişi sayısı bulunur.
- **1–12 oda** içeren taslak desteklenir. `hotel_ops.draft_new_reservation` kategoriye göre kişi kapasitesini, tarih aralığını, acenteyi ve pansiyon tipini doğrular. Her durumda `STAFF_REVIEW_REQUIRED_NOT_SAVED` döner. Bir tarayıcı taslağının oda blokajını veya muhasebeyi değiştirme hakkı yoktur.
- Günlük farklı oda ücretleri ve oda/rezervasyon ilişkisi **kurgusal kayıtlar** üzerinde görüntülenebilir. Yeni ücret/kredi tipi/folyo posting işlemi yalnızca yetkili PMS ve muhasebe rolüyle daha sonra eklenecek sunucu üzerinden mümkün olabilir.

## Misafir ve kimlik alanları

Alan şeması: `customer_id`, `surname`, `given_name`, `identity_type` (pasaport, AB kimliği, ulusal kimlik, ehliyet, diğer), `country` (ISO 3166 alpha-2 kodu), `preferred_language`, `title`, `gender`, `identity_number`, `turkish_national_id`, `birth_place`, `date_of_birth`, `address`, `telephone`, `email`.

- Demo profilleri sentetik; pasaport, TC kimlik, doğum tarihi, telefon, adres, e-posta **boş** ve gerçek girişe kapalı. Türkiye ülke seçildiğinde TC kimlik alanının *gelecekte yetkili sistemde açılacağı* belirtilir; bu demoda gerçek numara saklanmaz ve girilmez. Diğer ülkelerde kapalı kalır.
- KBS veya sınır ötesi veri transferi **yok**. İleride Türkiye KVKK ve GDPR için hukuki dayanak, aydınlatma, amacı aşmama, erişim rolleri, şifreleme, saklama süresi, olay kaydı, silme ve yetkili veri işleyen sözleşmeleri gerekir. Referanslar:
  - https://www.kvkk.gov.tr/Icerik/6649/Personal-Data-Protection-Law
  - https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/principles-gdpr_en
- Alan listesi, doğum/cinsiyet/unvan dahil, her otel/ülke için otomatik zorunlu değildir. Amaç ve mevzuat bazında gerekli olanlar seçilir.

## Folyo ve acente alacakları

- Folyo: tesis / rezervasyon / oda / müşteri veya acente alacaklısı / şirketin ticari unvanı / due date (vade) / para birimi / oda, restoran, minibar, transfer, ekstra yatak, ekstra konaklama, kur farkı veya düzeltme posting kodu.
- **City Ledger ödeme şekli değildir**: otelden acenteye devredilmiş, henüz tahsil edilmemiş alacaktır. Nakit, kredi kartı, mail order, banka havalesi örnek ödeme yöntemleridir. Gerçek tahsilat/charge/post yetkisi kapalıdır.
- `Decimal` (Python) ile posting toplamı – tahsilat = folyo bakiyesi; EUR ve TRY ayrı sütunlarda tutulur, birbirine karıştırılmaz. İade, fatura iptali, chargeback, otomatik döviz muhasebesi ve vergi uygulanmamıştır.

## Rapor kataloğu (32 tür)

### Hesabı mevcut kurgusal örnekten üretilen raporlar (21)

- Aktif Folyolar (`active_folios`)
- Aylık Detaylı Gelir (`monthly_revenue`)
- Detaylı Gelir (`detailed_revenue`)
- Folyo Analiz (`folio_analysis`)
- Günlük Denge (`daily_balance`)
- Hareketler (`transactions`)
- Gruplu Hareketler (`grouped_transactions`)
- Oda Listesi (`room_list`)
- Oda Fiyat Kontrol (`room_rate_control`)
- Acente Aylık Performans (`agency_monthly`)
- Acente Satış Detayı (`agency_sales`)
- Acente Yıllık Kümülatif Performans (`agency_annual`)
- Blokaj (`blockage_report`)
- Ekstra Yatak (`extra_bed`)
- Erken Ödeme (`advance_payment`)
- Fatura Posting Detay (`posting_invoice`)
- Doluluk (`occupancy`)
- City Ledger Acente Alacakları (`city_ledger`)
- Kur Takibi (`exchange_rates`)
- Rezervasyon Listesi (`reservation_list`)
- Misafirler (`guest_list`)

### Yalnız kayıt / entegrasyon sözleşmesi, **gerçek hesaplama yok** (11)

- Günlük Mizan (`trial_balance`; `requires_accounting`)
- Maliye Listesi (`fiscal_list`; `requires_fiscal`)
- Check-in İptal (`checkin_cancellations`; `requires_audit`)
- Çarşaf Listesi (`linen_list`; `requires_housekeeping`)
- Bütçe Analiz (`budget_analysis`; `requires_budget`)
- Bilgi İşlem (`it_report`; `requires_system_logs`)
- E-posta Gönderim (`email_report`; `requires_mail_permissions`)
- Emanet Kasa (`safe_deposit`; `requires_safe_ledger`)
- Fatura Listesi (`invoice_register`; `requires_invoicing`)
- Gelir Gider (`income_expense`; `requires_expense_ledger`)
- Gelir Yönetimi (`revenue_management`; `requires_rm_data`)

Bu durumlardaki ekran boş raporu sahte değerlerle doldurmaz: gerekli kaynak veya yetki eksikliğini görünür kılar. Gerçek mali mizan, e-fatura, vergi listesi, erken ödeme ve muhasebe uygunluğu ayrıca incelenmelidir.

## Para birimi ve fatura sınırlamaları

ISO 4217 kodları para birimi seçiminde kullanılmalıdır. 10 dil, 10 sabit para birimi anlamına **gelmez**; bir ülkede birden çok para birimi ve farklı vergi şartları olabilir. Demo kuru açıkça `FICTIONAL_DEMO_RATE` etiketli, tarihli ve **gerçek piyasa fiyatı değildir**. Faturanın yasal para birimi, e-fatura gereksinimi, kur tarih/saat politikası ve vergi numarası şirket ve ülke mevzuatına göre ayrı sağlayıcı/pilot incelemesi gerektirir. Kaynak: https://www.iso.org/standard/64758.html

## Kapanış için gerekli sonraki teslimatlar

1. Full-stack yetkili sunucu ve gerçek veri depolama/erişim rolü tasarımı (RBAC+MFA, tenant isolation, audit, consent/legal basis).
2. Doğrulanmış oda/rezervasyon içe alma, bir rezervasyonun birden çok odaya ve birden çok folyo hesabına dağıtılması.
3. Günlük fiyat, komisyon, acente alacağı, cash/bank/card/mail-order posting için çift kayıt muhasebesi ve idempotency.
4. İlgili mevzuata uygun e-fatura/e-arşiv ve resmi bildirim API'leri; bu demo gerçek işlem yapamaz.
5. Bütün 18 navigasyon ekranı ve form etiketlerinde 10 dil için native-speaker doğrulama, RTL/WCAG kullanıcı testi.
6. Veri yetkilendirmesi ve denetlenebilir pilot tamamlanmadan canlı PMS veya kişisel veri kullanılmamalı.

## Test / oluşturma

```sh
python -m unittest discover -s tests -v
python -m unittest discover -s tests/browser -v
python scripts/generate_suite_demo.py --check
python scripts/generate_hotel_ops_demo.py --check
python scripts/stage_demo_site.py --output /tmp/konaklamaflow-site
```
