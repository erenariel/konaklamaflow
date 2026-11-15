# KonaklamaFlow — Sentetik doğruluk değerlendirmesi (Issue #50)

Bu katman, **üretim ortamı / gerçek otel / canlı AI / PMS performansı ölçmez**.
Açık, elle yazılmış proje içi beklentiler ile mevcut deterministik `experience_engine.evaluate`
çıktılarını karşılaştırır; bağımsız otel uzmanı henüz etiketleri onaylamadı.

## Tekrar üretim

Depo kökünde, Python 3.11+ ile:

```bash
python -m unittest discover -s tests -v
python -m konaklamaflow.evaluation
python -m konaklamaflow.evaluation --json /tmp/evaluation.json --markdown /tmp/evaluation.md
```

Kaynak: `examples/fictional-hotel.json` (18 odalı kurgusal snapshot).
Etiketler: `evaluation/benchmark.json` (10 vaka).
Yalnız allowlist ile tanımlanmış değişimler uygulanır; mevcut Python kuralları
aynen kullanılır. Kurgusal senaryolarda her çalışma bağımsız değerlendirilir.

## Ölçüm birimi ve kapsam

**Birim:** (vaka, rezervasyon ID, reason code) üçlüsü için ikili 
'uyarı var / yok' etiketidir. Bir vakanın **tüm uyarıları** için doğruluk
veya tüm otel işlemlerinin başarısı ölçülmez. Diğer yan uyarılar bu metriğe
dahil değildir. Beklenen etiketler motordan alınmadı, proje geliştiricisi
tarafından elle tanımlandı; bağımsız uzman kontrolü yok.

10 vakanın 7'si etiketli ve ölçülür:
- OTA referans çoğalması, çakışan oda, açık bakım görevi, oda bağlı kalan
  iptal, OTA statü çelişkisi (5 pozitif);
- çakışmasız oda ve oda bağlantısı kaldırılmış iptal (2 negatif).

İki vaka **unsupported**: sırasız güncelleme/revizyon geçmişi ve kısmi iptal.
Bir vaka **unlabelled**: bağlantılı split-stay segmentleri. Bunların hiçbiri
paydalara alınmaz, başarı olarak sayılmaz. Kapsam = ölçülen / tüm vakalar.

## Metrikler

- TP: beklenen ve gözlenen uyarı; FN: beklenen ama görünmeyen uyarı.
- FP: beklenmeyen ama gözlenen uyarı; TN: beklenmeyen ve görünmeyen uyarı.
- Precision = TP/(TP+FP); recall = TP/(TP+FN).
- False-positive rate = FP/(FP+TN); false-negative rate = FN/(FN+TP).
- Payda sıfırsa sayı **null**; raporda açıkça undefined.
- `human_override_rate` ve `processing_time_ms` = **not_measured**:
  bir karar onaylama olayı veya gerçek süre ölçümü kaydedilmez.

İlk örneklerin beklenen sınıflandırması: 5 TP / 2 TN / 0 FP / 0 FN.
Bu değerler **ancak komutlar çalıştırılıp testler başarılı olduğunda**
gerçek test sonucu sayılabilir. Küçük sentetik kümede %100 skor,
üretimde doğruluk, güvenlik sertifikası veya pilot kanıtı değildir.

## Güvenlik ve kabul

Her vaka için gerçek `evaluate` motoru yeniden çalışır. Sahte/eksik rapor,
yanlış rezervasyon eşlemesi, bilinmeyen reason code, insan onayı sınırının
kaldırılması, bozuk/ek alanlı fixture reddedilir. Hatalı beklenti değişikliği
skoru **fail** yapar ve CLI çıkışı 1 olur. Geçersiz veri çıkışı 2 olur.
Testler CI'da Python sürümleri boyunca çalışır; gerçek sonuçlar artefakt
olarak saklanır.

`DRY_RUN_ONLY` korunur. Misafir/personel kimlik bilgisi, gizli bilgi,
gerçek otel kaydı, haricî API, KBS, ödeme, check-in yazımı **yoktur**.
Üretim geçişi için bağımsız güvenlik incelemesi, otel ve tedarikçi yetkisi,
KVKK uygunluk değerlendirmesi ve gözetimli pilot ayrıca gerekir.
