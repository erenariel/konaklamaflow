# KonaklamaFlow v0.5.1 — PMS kaynak araştırması, bütünleşik simülasyon ve dil onarımı

**Kapsam:** Kamuya açık kaynaklardan alınan operasyon kalıplarıyla geliştirilen **özgün**, ücretsiz/kurgusal ve çevrimdışı bir otel işletim önizlemesi. Vendor kodları, ekran görselleri, kullanıcı el kitaplarının metinleri veya kapalı API'leri kopyalanmadı. Mevcut `main` için ayrı PR üzerinden doğrulanacaktır.

## Kaynak araştırması ve kanıt sınırlamaları

| Sağlayıcı | Bulunan kamusal kaynak | İşlev tasarımına alınan genel fikir |
|---|---|---|
| ElektraWeb | [Resmî ön büro kontrol paneli](https://yardim.elektraweb.com/detayli-anlatim/onburo-kontrol-paneli), [resmî rezervasyon rehberi](https://yardim.elektraweb.com/ozet-kilavuz/rezervasyon-olusturma), [resmî eğitim materyali](https://kilavuz.elektraweb.com/) | Durum bazlı bekleyen/gelen/konaklayan/ayrılan rezervasyon görünümleri; rezervasyon kartı, oda uygunluğu, folyo, blokaj ve rol bazlı kontrol |
| Sistem Otel | [Kullanım kılavuzu](https://sistemotel.gitbook.io/sistem-otel-kullanim-klavuzu), [rezervasyon/grup/depozito](https://sistemotel.gitbook.io/sistem-otel-kullanim-klavuzu/sistem_otel_programi_rezervasyon/31_rezervasyon_olusturma), [ön büro/folyo](https://sistemotel.gitbook.io/sistem-otel-kullanim-klavuzu/sistem_otel_programi_folyo_islemleri/43_folyo_islemleri), [raporlar](https://sistemotel.gitbook.io/sistem-otel-kullanim-klavuzu/sistem_otel_programi_raporlar) | Oda planı ve blokaj, grup rezervasyonu, tarih bazlı fiyatlar, housekeeping ve iş emirleri, ödemelerden ayrı City Ledger, folyo ve audit ön kontrolleri |
| Sedna / Kod Yazılım | [Üreticinin kamusal ürün açıklaması](https://kod.com.tr/Product/SednaHotel) | Kullanıcı yetkisi ve LOG tasarımı, çoklu işlem akışı, ön büro + gelir/forecast/bütçe + görev ve CRM alanları |

**Sedna notu:** Üreticinin kamuya açık ürün açıklaması bulundu. Bütün ekranları kapsayan güncel ve açık erişimli eksiksiz bir Sedna kullanım kılavuzunu doğrulayamadık. Dolayısıyla hiçbir işlev için gizli/kapalı Sedna kılavuzuna erişildiği veya tüm vendor işlevlerinin birebir uygulandığı iddia edilmemektedir.

## Yapılan gerçek proje değişiklikleri

1. **Sol menü**: 20 modül için masaüstünde bağımsız düşey kaydırma alanı; küçük ekranda yatay modül kaydırma. En alttaki Blokajlar, Demirbaşlar, İş Akışları ve Personel/Oturum alanlarına erişim.
2. **10 dil tek merkez**: TR/EN/FR/EL/HE/AR/DE/RU/ES/UK seçimleri ana 20 modül menüsünü, sayfa başlıklarını, ortak eylemleri, karar açıklamasını ve RTL temel yönünü günceller. HTML `lang`/`dir` değiştirilir. Temel operasyon terimlerinin 58'i on dilde, 119 ilave iş terimi gerektiğinde **açık İngilizce taslak fallback** ile eşleştirilmiştir; bütün eski metinler henüz dil uzmanı tarafından onaylanmış değildir.
3. **Otel iş akışı kataloğu**: 14 özgün işlem paketi: rezervasyon/grup, oda blokajı, check-in ön kontrolü, checkout bakiye, folyo, acente alacağı, night audit, housekeeping, fiyat/kontrat, misafir gizliliği, fatura, analiz, personel devri, entegrasyon izinleri.
4. **Beş farklı vaka simülasyonu**: oda çakışması; ödeme/folyo; kimlik ve giriş; OTA kaynak uyuşmazlığı; bakım ve temizlik. Üstteki “AI senaryosunu keşfet” eylemi artık mevcut tek ekrandaki senaryoyu başlatmak yerine ilgili senaryo merkezine açar ve vaka dizisini sırayla oynatır. Hareketi azalt tercihi korunur. Çıktı **AI çağrısı veya kesin PMS kararı değildir**.
5. **Personel ve oturum (kurgusal)**: beş örnek personel `DEMO-REC-001` vb., login ID, departman, erişim kapsamları, görüntüleme izni ve oturum içi işlem izi. Rol değiştirerek kurgusal yetki görünürlüğü gösterilebilir. Bu, gerçek kimlik doğrulaması / oturum açma / RBAC backend değildir. Şifre, personel gerçek adı, telefon veya gerçek kullanıcı verisi yoktur.
6. **AI güvenliği**: modül planı `AI-1 kaynak okur → deterministik Python kural motoru → AI-2 açıklama → yetkili insan karar verir`. Kural kodları ayrı, eylem durumu `STAFF_REVIEW`/`MISSING_TRUSTED_SOURCE`/`AUTHORIZATION_REQUIRED`; provider durumları `NOT_CONNECTED`. Gerçek kullanıcıya ait rezervasyon, kimlik, ödeme, PMS, OTA, KBS, fatura veya e-posta işlemi açılmadı.

## Bu sürümde *henüz yok*

- **Üç PMS’in tam fonksiyonel kopyaları** veya o ürünlerin API istemcisi/sertifikasyonu.
- Gerçek hesabın login/SSO/MFA, sunucu taraflı RBAC, tenant izolasyonu, şifreleme veya kalıcı audit.
- Gerçek veriyi okuyup yazan AI ajanı, onaylı API ve uygulayıcı erişim katmanı. AI destekli otomatik icra iddiası yok.
- Gerçek ödeme, şehir hesabı aktarımı, e-fatura, vergi fişi, polis/KBS bildirimi veya canlı misafir kaydı.
- **10 dilde her eski paragrafın profesyonel, hukukî ve yerel terminoloji onayından geçmiş çevirisi.** Bir sonraki ayrı aşama eksiksiz key-by-key katalog ve native speaker QA/WCAG/RTL ekran okuyucu testidir.

## Kod / regresyon

- `konaklamaflow/workflow_catalog.py` güvenli simülasyon/personel hakları veri modeli
- `demo/hotel-workflow-ui.js` özgün iş akışları ve beş adımlı vaka turları
- `demo/full-ui-i18n.js`, `demo/full-ui-lexicon.js` tek dil yönetimi ve çok dilli metin kataloğu
- `demo/v04-integrated-preview.html` ana uygulamaya inlined kaynaktan bağlanmış ekran ve kayan menü
- `tests/test_workflow_catalog.py`, `tests/browser/test_full_ui_localization.py` güvenlik ve arayüz regresyonları

```sh
python -m unittest discover -s tests -v
python -m unittest discover -s tests/browser -v
node --check demo/hotel-workflow-ui.js
node --check demo/full-ui-i18n.js
node --check demo/full-ui-lexicon.js
python scripts/generate_hotel_ops_demo.py --check
```

**Üretim kuralı:** Sözleşme, yasal dayanak, veri minimizasyonu, yetkili rol ve gerçek kaynak sürümü olmadan hiçbir yazma işlemi devreye alınamaz.
