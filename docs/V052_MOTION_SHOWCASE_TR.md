# v0.5.2 — sunum ve hareketli görsel çalışma

Bu, PR #31 üzerindeki sentetik/çevrimdışı görsel adaydır. Paket sürümü, canlı
AI entegrasyonu veya otel kullanımına hazır PMS olarak sunulmaz. Main'e merge,
release ve Pages yayını bu çalışma için yapılmaz.

## Görsel yaklaşım

Özgün indigo/violet ve aqua renkli AI sahnesi; kaynak → Python kural motoru →
senaryolu AI açıklaması → yetkili personel akışını görünür kılar. Kanıt sayısı,
aktif adım ve oda vurgusu anlatımla değişebilir; gerçek envanter, tahsilat,
güven yüzdesi veya başarı sonucu uydurulmaz. Doluluk benzeri grafik sentetik
tahsis sayısını gösterir; fiziksel doluluk, gelir veya satış tahmini değildir.

Pulse, shimmer, glow, counter-pop, slide-in ve orbit hareketleri kısa ve
dekoratiftir. İşletim sistemi reduced-motion ve kullanıcı hareket kapatma
seçimi önceliklidir. Statik içerik, elle adımlama ve klavye erişimi korunur.
Görsel yenileme vendor ekranı, logosu, fotoğrafı veya özel kodunu kopyalamaz.

Eski rapor viewer'ının tanıtım paneli de güncellenir; rapor yükleme/doğrulama
ve son geçerli raporu koruma davranışı değiştirilmez. Global sunumun süre,
dil ve RTL kontrolleri korunur. Yeni metinlerin bulunması bütün uygulamanın
on dilde uzman incelemesinden geçtiği anlamına gelmez.

## Gerçek tarayıcı medyası

```sh
python scripts/generate_hotel_ops_demo.py --check
python scripts/capture_previews.py
python scripts/record_demo_tour.py --showcase all
python -m unittest discover -s tests -v
python -m unittest discover -s tests/browser -v
```

İsteğe bağlı Playwright Chromium ve FFmpeg gerekir. Sistem Chromium'u için
`KONAKLAMAFLOW_CHROMIUM` yürütülebilir dosya yoluna ayarlanabilir.

- `docs/images/ai-command-tour.gif`: gerçek ilk hikâyenin beş aşaması.
- `docs/images/roomplan-story.gif`: oda planı, oda detayı ve teknik blokaj.
- `docs/images/overview-pulse.gif`: genel görünüm, kanıt akışı ve grafikler.
- Her kaydın aynı adlı JSON manifesti ve `-poster.png` statik alternatifi vardır.
- `v052-previews.json`, on gerçek ekran görüntüsünü kaynak hash'lerine bağlar.

Kayıt aracı yalnız kullanıcıya açık kontrolleri çalıştırır. Kaynak ve rapor
değişmezliği, sıfır dış istek/tarayıcı hatası ve GIF başına 5 MB bütçe kontrol
edilir. CI, manifestteki kare sayısını gerçek GIF bloklarından yeniden sayar;
güncel HTML, GIF, poster ve PNG hash'leri eşleşmeden test geçmez. Eski legacy
`operations-tour.gif` ve doğrulaması ayrıca korunur; yeni arayüz diye sunulmaz.

## Güvenlik ve kabul sınırı

Gerçek PMS/OTA, ödeme, KBS, kimlik belgesi, misafire mesaj ve AI sağlayıcı
çağrıları kapalı kalır. CSP `connect-src 'none'` ve unsafe-eval yasağı korunur.
Misafir adları mevcut sentetik fixture'a bağlı kurgusal gösterim adlarıdır.
Anlatım kaynak veriyi değiştirmez; yerel operasyon simülasyonu raporu stale
yaparsa eski hazırlık ve export engelleri aşılmaz.

1366×768, 1440×900 ve 1600×900 masaüstü; dar mobil, dil/RTL, üç tema,
reduced-motion, görsel durum geçişleri ve kaynak parity testleri uygulanır.
Son yerel doğrulama: **206 Python ve 119 Chromium testi başarılı**.
Arapça/İbranice ilerleme oranları bütün olarak LTR bidi izolasyonu kullanır;
oranın ekranda ters görünmesi için regresyon kontrolü eklenmiştir.
Bu otomatik kontroller tam WCAG uygunluğu veya yerel konuşur çeviri onayı
değildir. İnceleme için test sayıları, commit SHA ve gerçek CI bağlantıları
PR #31 açıklamasında tutulur; kullanıcı adına otomatik merge/release yoktur.
