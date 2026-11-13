# KonaklamaFlow — gerçek ekran kayıtları ve konsept görselleri

v0.5.2 adayının ana görseli çalışan entegre uygulamanın gerçek ekran görüntüsüdür.
Eski SVG konseptleri ayrı korunur; gerçek PMS ekranı veya çalışan bir AI modelinin
çıktısı olarak sunulmaz. Yeni kayıtlar ana dala/yayına kendiliğinden alınmaz.

## Üç gerçek tarayıcı kaydı

- `docs/images/ai-command-tour.gif`: kaynak → kurallar → senaryolu açıklama → personel.
- `docs/images/roomplan-story.gif`: kurgusal oda planı, oda detayı ve teknik blokaj.
- `docs/images/overview-pulse.gif`: genel görünüm ve kaynak veriye bağlı grafikler.

Her dosya aynı adlı JSON manifesti ve `-poster.png` statik alternatifiyle birlikte
üretilir. Manifest güncel HTML/rapor/GIF/poster hash'lerini, görülen aşamaları,
gerçek kullanıcı kontrollerini ve sıfır istek/hata sonucunu bağlar. Testler gerçek
GIF karelerini ayrıca sayar; hash veya manifest sahte olarak güncellenmez.

```sh
python scripts/record_demo_tour.py --showcase all
python scripts/capture_previews.py
python -m unittest discover -s tests -p test_showcase_media.py -v
```

Gereksinimler: isteğe bağlı Playwright Chromium ve FFmpeg. Eski
`python scripts/build_promo_gifs.py --html demo/v04-integrated-preview.html --out docs/images`
komutu da artık aynı kanonik kayıt aracına yönlenir: kaynakla eşleşmeyen GIF veya
boyanmış sayaç katmanı üretemez, manifestleri birlikte kaydeder. Pillow gerekmez.

## Konsept varlıkları ve sınırlar

`ai-presentation-hero.svg` ile `ai-explanation-flow.svg` özgün illüstrasyonlardır.
README'de gerçek ekran kayıtlarından ayrı etiketlenir. Statik posterler hareket
istemeyen izleyiciler için ilk seçenektir. Uygulamada OS reduced-motion ve kullanıcı
hareket tercihi; klavye, duraklatma ve elle adımlama korunur.

Canlı gibi görünen hareketler bir bağlantı iddiası değildir. AI bölümü mock_demo;
PMS/OTA/ödeme/KBS/kimlik/misafir mesajı ve gerçek AI API kapalıdır. Grafik sayıları
sentetik snapshot tahsislerini gösterir; fiziksel doluluk, tahsilat veya forecast
olarak yorumlanmaz. Çeviriler insan incelemesi bekleyen taslaklardır.

Otelcilikteki durum sekmeleri, renkli oda planı ve audit/report kavramlarından
özgün tasarım amacıyla yararlanılır; ElektraWeb, Sistem Otel veya Sedna özel kodu,
arayüzü veya marka varlığı kopyalanmaz. Ortaklık iddiası yoktur.
Ayrıntılı doğrulama: [V052_MOTION_SHOWCASE_TR.md](V052_MOTION_SHOWCASE_TR.md).
