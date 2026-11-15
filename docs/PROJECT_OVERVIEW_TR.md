# KonaklamaFlow — Tanıtım sayfası ve yayın doğruluğu (Issue #60)

Bu belge `demo/project-overview.html` tanıtım sayfasının içerik sınırlarını açıklar.

## Neler var?

- **Yayımlanmış v0.5.2**: Birleşik çevrimdışı operasyon demosu, 18 odalı
  kurgusal kaynak, oda planı, önceden hesaplanmış kural açıklamaları.
- **Gerçek ekran görüntüsü**: `docs/images/ai-command-tour-poster.png`,
  yayınlanan v0.5.2 deneyimine aittir. Henüz yayımlanmamış PR ekranları gibi
  gösterilmez.
- **Kavramsal akış şeması**: Kaynak → kural motoru → kanıt alanları → insan sınırı.
  Bunun bir UX şeması olduğu, canlı bir iş akışından alınmadığı belirtilir.
- **Sentetik ölçüm**: PR #51'deki yedi etiket/10 vaka kapsamının paydaları açık;
  5 TP, 2 TN, 0 FP, 0 FN yalnız değerlendirilen sentetik etiketler içindir.
  Gerçek otel doğruluğu veya bağımsız doğrulama değildir.
- **İnceleme adayları**: PR #51, #53, #55, #58, #59 için ayrı kartlar.
  Kodu/testi bulunan fakat `main` dalına alınmamış durumdadırlar.
- **TR + EN**: Türkçe detay, kısa İngilizce özet. Tam çeviri yapılmış izlenimi
  verilmez.

## Güncelleme düzeni

Bu sayfa **14 Kasım 2026 tarihli bir durum özeti** sunar; GitHub API'sine bağlanıp
PR durumlarını canlı okumaz. Yeni bir PR birleştirildiğinde veya canlı demo
değiştiğinde, bu metni ve README'yi gözden geçirip güncellemek gerekir.
Yayımlanmış/kurgusal/incelemede ayrımı korunmalıdır.

Sayfa `scripts/stage_demo_site.py` ile kontrollü dağıtım klasörüne
`project-overview.html` olarak kopyalanır. Bu işlem kendi başına Pages'e
deploy etmez. Canlı bağlantı ancak PR merge, CI onayı ve Pages yayınından
sonra kullanılabilir. Çevrimdışı CSS ve yerel poster görseli kullanılır;
haricî script, izleme veya model API çağrısı içermez.

## Tekrar üretilebilir kontrol

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s tests/browser -p 'test_project_overview.py' -v
python scripts/generate_canonical_demo.py --check
python scripts/stage_demo_site.py --output /tmp/new-overview-site
```

Tanıtımda gerçek misafir veri seti, ödeme kaydı, KBS bildirimi, kimlik
doğrulama, canlı OTA/PMS veya doğrulanmamış üretim başarı iddiaları bulunmaz.
