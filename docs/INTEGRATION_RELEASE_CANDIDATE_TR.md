# KonaklamaFlow — Birleşik çevrimdışı sürüm adayı (#66)

Bu çalışma, bağımsız pull request'lerde test edilmiş modülleri tek
**inceleme ve sürüm adayı** dalında birleştirir. Ana dal ve GitHub Pages
yalnız bu PR açıldığı için güncellenmez.

## Bu sürüm adayında bulunanlar

- **PR #51 + #58:** Proje içinde etiketlenmiş 10 sentetik vakadan 7'sini
  ölçen tekrar üretilebilir doğruluk ölçümü ve görsel scorecard. Kapsam
  dışı üç vakanın ikisi desteklenmez; birinin bağımsız etiketi yoktur.
- **PR #53 + #59:** Python kaynak/raporuna bağlı, üç *kurgusal* inceleme
  olayını gösteren hash zinciri ve statik HTML. Gerçek denetim veya
  personel faaliyetini kanıtlamaz; güvenilir haricî hash dayanağı yok.
- **PR #55:** Python kural nedenleri ve alan isimleriyle eşleşen görsel
  karar kanıt yolu; kaynak veya rapor tutarsızsa güvenli biçimde kapanır.
- **PR #61:** Mevcut yayımlanmış v0.5.2 ekran görüntüsünü içeren tanıtım
  sayfası ve yeni modüller için bağlantılar.
- **PR #63:** Codex kotasını koruyan çalışma görev dağılımı.
- **PR #65:** En fazla dört kurgusal konaklama için, yalnızca personel
  onayına sunulan bağımsız oda tahsis çözücüsü. **Mevcut demo UI'sına
  veya gerçek PMS'e bağlanmış değildir.**

## Çakışma çözümü

Elle uzlaştırılan dosyalar:
`.github/workflows/tests.yml`,
`demo/v04-integrated-preview.html`,
`scripts/stage_demo_site.py`,
`tests/test_demo_site.py`.

Ana demo artık üç ayrı okumalık sayfaya bağlantı içerir:
`project-overview.html`, `synthetic-scorecard.html`,
`fictional-trace.html`. Son iki sayfa yerel Python modüllerinin
doğrulanmış kurgusal çıktılarını kullanarak hazırlanır, özel dosyalar
ve kimlik/ödeme bilgileri kopyalanmaz.

## Bilinçli olarak dahil edilmeyen PR

**PR #64** aynı `evaluation.py` ve `evaluation/benchmark.json`
dosyalarında **#51'den farklı benchmark şeması** kullanır. Ayrı
uyarlama ve etiketleme/ölçüm paydası incelemesi olmadan #51 üstüne
yazılması #58'i bozabileceğinden aday dışındadır.

## Gerekli doğrulama

```sh
python -m unittest discover -s tests -v
python -m unittest discover -s tests/browser -v
python scripts/generate_canonical_demo.py --check
python scripts/stage_demo_site.py --output /tmp/integrated-kf-release
python -m scripts.verify_release_readiness --site /tmp/integrated-kf-release
```

Başarı kriteri: 3 Python sürümü, Chromium, üreticinin `--check`
kontrolleri, offline artefaktların bir arada oluşması ve repo kaynakları,
özel loglar ile `.git` klasörünün yayın dizininde bulunmaması.

**Yayın açıklamaları:** `demo/project-overview.html` ve README metinleri
artık bir sürüm adayı ile canlı dağıtım arasındaki farkı zamana dayanıklı
biçimde anlatır. Görsel tarihsel v0.5.2 demo ekranına aittir; PR durumları
statik sayfada canlı takip edilmez. `scripts.verify_release_readiness`
sunulan tüm dosyaları ve bağlantıları yayından önce denetler.
Canlı Pages deploy tamamlandıktan sonra gerçek ağ üzerinden smoke test
yapmak gerekir (ayrıntı: `docs/RELEASE_GATE_TR.md`).

Bu sürüm **gerçek PMS/KBS/OTA/ödeme sistemi, canlı AI çağrısı, gerçek
personel onayı, otomatik check-in veya değiştirilemez audit** içermez.
Gerçek otel doğruluğu iddia edilmez. CI başarısı tek başına üretime
hazırlık sertifikası veya merge/deploy izni değildir.
