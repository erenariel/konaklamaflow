# Issue #35 — yerel doğrulama kaydı

Tarih: 13 Kasım 2026. Bu kayıt yeni ortak kurgusal kaynak modelinin **taslak
PR adayı** içindir. Main'e birleştiği, canlıya alındığı veya gerçek otelde
doğrulandığı anlamına gelmez. Kaynak kodu ve medya üretim tabanı:
`a940b4131d928d50f03c197c24e64224a8e99905`.

| Kontrol | Sonuç |
| --- | --- |
| Python regresyonları | 266 test geçti |
| Chromium regresyonları | 145 test geçti |
| Kanonik model/rapor/üretim kontrolleri | 52 Python testi, tam koşuya dahil |
| Oda/rezervasyon/folyo/rapor gezinmesi | Açık kimliklerle doğrulandı; finanssız kayıt ayrı durum |
| 32 rapor seçimi | Her raporun Python kaynak durumu doğrulandı |
| PR #34 | 320/375/390 px dil seçimi, 10 dilde hareket kontrolleri, RTL korunuyor |
| PR #36 | Varsayılan çok nedenli Python kanıt paneli ve kaynak açıklaması korunuyor |
| PR #38 | Aurora görsel sistemi güncel main'den korunuyor |
| Görsel doğrulama | 25 gerçek ekran görüntüsü; tema/mod/boyut matrisi, klavye, %200 zoom, reduced motion |
| Güncel tanıtım görselleri | 10 ekran görüntüsü + workbench önizlemeleri yeniden üretildi |
| GIF kayıtları | `operations-tour`, `ai-command-tour`, `roomplan-story`, `overview-pulse`; her biri <5 MB |
| Çevrimdışı kayıt | Medya manifestlerinde 0 ağ isteği ve 0 tarayıcı hatası |
| Gizlilik | Erişilebilir geçmiş ve çalışma ağacında kişisel e-posta eşleşmesi 0; owner noreply doğrulandı |
| Gizli değer taraması | Gitleaks geçmiş ve kaynak taramasında 0 bulgu; gerçek değerler raporlanmadı |
| Üretim kontrolü | Üç `--check` komutu, Python derleme, JS sözdizimi ve statik staging geçti |

Görsel kontrol temsili metin kontrastını ölçer; bağımsız tam WCAG denetimi
veya ekran okuyucu onayı değildir. Gizlilik taraması tüm olası kişisel
verileri bulma garantisi vermez; negatif test adresleri sentetiktir. Özel
tarama kayıtları/yedekler depoya eklenmez. GitHub CI sonucu PR'ın **Checks**
sekmesinden ayrıca doğrulanmalıdır; bu dosya CI başarısını varsaymaz.

## Kaynak gerçekliği

Tüm yeni görünümler `examples/canonical-hotel.json` dosyasından üretilir:
12 üst rezervasyon, 12 oda konaklaması, 18 oda, 27 kurgusal misafir ve üç
açık folyo. Kaynak sırası değiştirilse de kimlik bağları korunur. Eski KFD
kayıtları yeniden adlandırılmaz veya sırayla eşleştirilmez. Olmayan ödeme,
folyo, muhasebe veya mali fatura üretilmez.

İki denetim bulgusu testle düzeltildi: tutarsız oda/rezervasyon görev bağının
sessizce kaybolması ve iş akışı inceleme düğmesinin başka ekrana yönlenmesi.
Çok odalı kayıtlar oda konaklamaları halinde korunur; global optimizasyon ve
çok odalı otomatik AI hikâyesi üretimi tamamlanmış değildir. Ayrıntı:
[ortak şema ve sınırlar](CANONICAL_SCHEMA_TR.md).

Canlı PMS/OTA/AI API, ödeme, KBS, kimlik işleme, gerçek mesaj ve mali
faturalama kapalıdır. İnsan incelemesi olmadan merge/release/deploy yapılmaz.

## Yeniden üretme

```bash
python scripts/generate_canonical_demo.py --check
python scripts/generate_suite_demo.py --check
python scripts/generate_hotel_ops_demo.py --check
python -m unittest discover -s tests -v
python -m unittest discover -s tests/browser -v
python scripts/verify_commit_privacy.py
python scripts/verify_demo_experience.py --output /tmp/issue35-visual-check
```

Medya yeniden üretimi için [şema belgesindeki komutları](CANONICAL_SCHEMA_TR.md)
kullanın. HTML hash'i değişirse GIF ve manifest gerçek tarayıcıdan birlikte
yeniden üretilmelidir; hash güncelleyerek test atlanmamalıdır.
