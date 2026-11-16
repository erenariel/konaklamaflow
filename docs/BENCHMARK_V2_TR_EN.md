# Benchmark v2: sentetik ölçüm ve metodoloji / Measurement methodology

**Durum:** yalnızca kurgusal veri, proje geliştiricisinin etiketleri.
Gerçek bir otelden ölçüm veya bağımsız doğrulama değildir.

## Tam paydalar

- 43 kayıt: **40 etiketli gözlem**, 2 unsupported, 1 unlabelled.
- **23 farklı sentetik senaryo** 40 gözlemi üretir. Bir senaryo birden
  fazla (rezervasyon, gerekçe kodu) gözlemi üretir. Bu nedenle
  40 bağımsız rezervasyon veya 40 farklı otel ölçümü değildir.
- Ölçüm birimi: belirli senaryoda tek rezervasyon için tek gerekçe kodunun
  var/yok (bool) etiketi. Tüm rezervasyon süreci veya tüm uyarıların
  birlikte doğruluğunu ölçmez.
- Etiketler metinsel gerekçeyle **proje tarafından yazılmıştır**; rapordan
  türetilmez. Bağımsız bir otel uzmanı etiketleri doğrulamadı.
- Motor, orijinal kurgusal fixture'dan her senaryoyu yeniden üretir ve
  her etikete karşılık gerçek deterministic evaluate() çıktısını karşılaştırır.
  Manifest rastgele JSON patch veya Python kodu çalıştıramaz.

## Çalıştırma

Depo kökünde Python 3.11+:

~~~bash
python -m unittest discover -s tests -v
python -m konaklamaflow.evaluation_v2
python -m konaklamaflow.evaluation_v2 --json /tmp/kf-v2.json --markdown /tmp/kf-v2.md
python -m konaklamaflow.evaluation_v2 --strict
~~~

## Skorun anlamı

- **TP:** beklenen ve görülen uyarı, **TN:** beklenmeyen ve görülmeyen.
- **FP:** beklenmediği hâlde görülen uyarı, **FN:** beklenip görülmeyen uyarı.
- Kapsam = 40/43. Etiket eşleşmesi = (TP+TN)/40.
- Precision/recall ve FP/FN oranları kendi gerçek paydalarıyla hesaplanır.
  Sıfır payda için oran 0 veya %100 değil, JSON null olur.
- Yanlış eşleşmeler (FP/FN) listeden çıkarılmaz; JSON'da expected,
  predicted, outcome ve rationale, Markdown'da ayrıntıları bulunur.
  Toplam rapor da fail durumunu açıkça gösterir.
- Normal diagnostic CLI, FP/FN olsa da tüm raporu üretip 0 döndürebilir;
  **--strict** herhangi bir eşleşmezlikte 1 döndürür. Geçersiz manifest
  ve dosya hatası 2 döndürür. CI normal değerlendirmeyi arşivleyip
  raporu özetler; güvenlik/yapı testleri ayrıca hata ile durur.

## Dışlanan senaryolar

- reordered_same_day_revisions: unsupported, NO_EVENT_REVISION_MODEL.
- partial_cancellation: unsupported, NO_PARTIAL_CANCELLATION_MODEL.
- split_stay_truth_unreviewed: unlabelled, SPLIT_STAY_TRUTH_UNREVIEWED.

Bunlar başarı veya başarısızlık diye puanlanmaz. Ölçülen vakayı
sonradan desteklenmeyen olarak işaretleyerek gizlemek manifest
doğrulamasında engellenir.

## Sınırlar

Gerçek otel doğruluğu, kullanıcı benimsemesi, bağımsız etiket,
pilot çalışma, PMS/OTA/KBS, ödeme, anlık oda tahsisi, KVKK uygunluğu,
şifreleme sertifikası, işlem süresi ve insan override ölçümü
**yapılmamaktadır**. Veriler tamamen sentetiktir.
Orijinal 10 vakalık v1 raporu değişmeden korunur.

## English summary

43 total case records: 40 author-labeled binary observations from 23
distinct fictional scenarios, 2 unsupported and 1 unlabelled. Several
observations can share a scenario. Each scored unit checks one
(scenario, reservation, reason code) against actual rule-engine output.
All FP and FN mismatches are preserved and explained. No independent
expert labels, real hotel data or field accuracy claims are made.
The optional --strict switch returns exit code 1 on a measured mismatch.
