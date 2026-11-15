# KonaklamaFlow — Yayın kapısı ve geri dönüş planı

Bu belge birleşik çevrimdışı sürüm adayı [PR #67](https://github.com/erenariel/konaklamaflow/pull/67)
için son doğrulama rehberidir. **Bu dosyadaki komutlar yayına alma yapmaz.**

## Yayın öncesi kalite kapıları

1. PR'ın en güncel commit'i için GitHub Actions'ta Python **3.11, 3.12,
   3.13** ve tam Chromium paketinin **success** olduğunu doğrula.
2. `python scripts/generate_canonical_demo.py --check` komutuyla
   gömülü Python karar raporlarının güncel olduğunu doğrula.
3. Çevrimdışı çıktıyı yeni, boş bir klasöre hazırla ve yayın öncesi
   doğrulamayı çalıştır:

   ```bash
   python scripts/stage_demo_site.py --output /tmp/konaklamaflow-rc
   python -m scripts.verify_release_readiness --site /tmp/konaklamaflow-rc
   ```

4. `index.html`, `project-overview.html`, `synthetic-scorecard.html`,
   `fictional-trace.html` sayfalarını kontrol et. Tanıtımda gerçek
   tarihsel v0.5.2 ekran görüntüsü bulunmalı; canlı otel verisi veya
   personel işlemi olduğuna dair iddia bulunmamalı.
5. **#64 benchmark'ı dahil edilmedi.** #51'in ayrı sentetik sözleşmesi
   ve #58'in rapor uyumu korunur. #65 yalnız bağımsız Python öneri modülüdür;
   otel/demoya canlı bağlantı eklenmedi.
6. PR'ı birleştirme kararı proje sahibi tarafından ayrıca verilir.
   Başarılı test, Pages'in güncellendiği anlamına gelmez.

## Canlı yayın sonrası kontrol (ayrı adım)

GitHub Pages yayın görevinin başarılı tamamlandığını kontrol et; daha sonra
`https://erenariel.github.io/konaklamaflow/` ve
`/project-overview.html`, `/synthetic-scorecard.html`,
`/fictional-trace.html` adreslerini gerçek ağ üzerinden açıp 200 yanıtını,
görselleri, mobil düzeni ve bağlantıları incele. Çevrimdışı ön kontrol
canlı CDN veya Pages durumunu kanıtlamaz.

## Geri dönüş

Beklenmeyen yayın sorunu varsa yeni kodun gerçek otel uygulamalarına
erişimi olmadığını doğrula. GitHub'da başarılı eski `main` commit'ini
ve önceki başarılı Pages dağıtımını belirle; proje sahibinin onayı ve
repo kurallarıyla **geri alma commit'i** ya da önceki başarılı sürümün
yeniden dağıtımını değerlendir. Önceki commit'i zorla taşımak yerine
izlenebilir, gözden geçirilebilir yöntem kullan. Özel veri içeren
çıktıyı veya yerel rapor dosyalarını site staging alanına koyma.

## Sınır ve kanıt

Çıktılar tamamen kurgusaldır. 7/10 yalnız proje etiketli sentetik
vakaların kapsamıdır; gerçek otel doğruluğu değildir. Hash-zinciri
gerçek personel kimliği veya değiştirilemez denetim kanıtı değildir.
Oda atama çözücüsü personel onayı olmadan işlem yapmaz ve kurgusal
girdi dışında kullanılmamalıdır.
