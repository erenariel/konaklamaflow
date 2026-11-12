# PR #18 — v0.4 görünüm başlangıcı ve kayıt doğrulaması

Bu belge v0.4'ün tamamlandığı veya üretim kullanımına hazır olduğu iddiası değildir.
Çalışma, mevcut taslak PR #18 / Issue #4 kapsamındadır. Main'e birleştirme,
Pages yayını ve paket sürümü bu çalışma için yetkilendirilmemiştir.

## Başlangıç ve kaynaklar

- Kontrol edilen main: `1d91daf21d455f04c81c1fa96aaf3e444b6a9fe5`.
- PR #18 başlangıç head'i: `4d1713f37346383a561170d9af7e8eb3e44c67f7`.
- Güncel uzak depodan temiz klon kullanılır; eski gizlilik temizliği öncesindeki
  klonlar, geçmiş yeniden yazma ve force-push kullanılmaz.
- [Ana uygulama planı](CODEX_V04_UYGULAMA_PLANI_TR.md),
  [storyboard](SUNUM_STORYBOARD_V04_TR.md),
  [AI sözleşmesi](AI_PROVIDER_V04_TR.md) ve mevcut #1 / #4–#17 okunmuştur.
  Yeni issue oluşturulmamıştır.
- Başlangıç main doğrulaması: 147 Python ve 56 Chromium testi geçti.
- Başlangıç PR doğrulaması: 147 Python testinde yalnızca eski kayıt manifestinin
  güncel HTML ile uyuşmaması başarısızdı. Güncel uzak CI'da browser işi başarılıydı;
  reduced-motion testi CSP'yi gevşetmeden locator polling kullanıyordu.

## Bu aşamanın düzeltmeleri

- Açık, koyu ve gece temalarında iç içe kartlar, etiketler, oda çizelgesi, düğmeler
  ve açıklama paneli için tutarlı renkler ve ölçülen metin kontrastı.
- Kullanıcının hareketi kapatması hem dekoratif animasyonları hem otomatik hikâye
  ilerlemesini durdurur. İşletim sisteminin reduced-motion tercihi önceliklidir;
  elle adımlama çalışır. Tekrar açmak kendi başına oynatmayı başlatmaz.
- Sunumda erişilebilir modül seçici, görünür odağa dönüş ve yeterli genişlikte
  16:9 anlatım alanı; dar ekranda yeniden akış.
- Kaynak snapshot ve Python raporu, tema/mod/hareket değişiminden etkilenmez.
  Housekeeping/görev değişiklikleri eski raporu geçersiz kılmaya devam eder.
- GIF ve manifest birlikte gerçek Chromium oynatımından yeniden üretilir.
  Hash kontrolü ve beklenen hikâye aşamaları testi korunur.

## Tekrarlanabilir doğrulama

Gereksinimler: Python 3.11+, isteğe bağlı `.[browser]` bağımlılığı,
Playwright Chromium ve GIF için FFmpeg. Sistem Chromium'u kullanılacaksa
`KONAKLAMAFLOW_CHROMIUM` ortam değişkeni yürütülebilir dosyaya işaret edebilir.

```sh
python scripts/generate_suite_demo.py --screenshots
python scripts/record_demo_tour.py
python scripts/generate_suite_demo.py --check
python -m unittest discover -s tests -v
python -m unittest discover -s tests/browser -v
python scripts/verify_demo_experience.py --output /tmp/demo-experience
python scripts/verify_commit_privacy.py
python -m compileall -q konaklamaflow scripts
```

Kayıt çıktıları: `docs/images/operations-tour.gif` ve `.json`.
Önizlemeler: `demo/desktop-preview.png` ve `demo/mobile-preview.png`.
Kayıt manifesti güncel HTML/GIF/snapshot/rapor hash'lerini, görülen hikâye
aşamalarını ve sıfır istek/hata koşulunu bağlar; hash tek başına yetki değildir.
GIF bütçesi 5 MB'dır.

Son yerel doğrulama: **147 Python, 66 Chromium testi başarılı**. Yeni kayıt
321.766 bayt, 21 gerçek tarayıcı karesi ve beş hikâye aşaması içerir; istek ve
tarayıcı hata sayısı sıfırdır. İncelenen normal metin örneklerinin en düşük
kontrastı açık temada 5,375:1, koyuda 6,43:1, gece temasında 8,72:1'dir.
Bu sayılar üretim performansı veya kullanıcı araştırması sonucu değildir.

`verify_demo_experience.py` üç tema × iki mod × 320/375/768/1440 genişlik için
24 gerçek ekran görüntüsü, yakınlaştırma kontrolü ve JSON kanıtı üretir.
Ölçümler bu sentetik demo ve test ortamıyla sınırlıdır. Ekran görüntüleri CI
artefaktıdır; farklı platformlarda piksel eşitliği garantisi veya #9'un tam
görsel regresyon altyapısı sayılmaz. CI bağlantısı, nihai commit SHA'sı ve test
sayıları PR açıklamasında güncel tutulur.

## Korunan sınırlar ve kalan işler

Kamu demosunda gerçek AI/PMS/OTA bağlantısı, kimlik işleme, ödeme, KBS,
gerçek misafire mesaj veya kalıcı operasyon yazması yoktur. Sentetik anlatım
model yanıtı veya insan yetkilendirmesi sayılmaz. CSP'nin `connect-src 'none'`
ve `unsafe-eval` yasağı korunur. Özel yedekler ve eski SHA Support yazışmaları
halka açık depoya taşınmaz; yeni geçmiş temizliği yapılmaz.

Bu aşamadaki otomatik kontrast, klavye, reflow ve reduced-motion kontrolleri
tam WCAG 2.2 AA uygunluğu veya ekran okuyucu kabulü değildir. Bağımsız insan
incelemesi, #9'un kapsamlı a11y/görsel/performance kapıları ve #6'nın 90 saniye /
3 dakika / 7 dakika anlatımı, hızlar, üç ayrı GIF ve video seti açık kalır.

Sonraki ayrı taslak PR: #5 için sürümlü `reason_code`, kanıt alanı, kaynak
geçerliliği, güvenli personel adımı ve insan onay sınırı. Ardından #9 → #6 →
#7 → #8 → #10 → #17 → #1/#11 → #12 → #13 → #14 → #15 → #16 bağımlılık sırası
izlenir. Gerçek API, PMS pilotu ve üretim kabulü ayrıca yetki ve dış inceleme
gerektirir; plan veya mock sözleşme olarak bulunmaları uygulanmış canlı
güvenlik kontrolü oldukları anlamına gelmez. Issue'lar kabul kanıtı ve review
olmadan kapatılmaz.
