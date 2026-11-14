# Sentetik doğruluk paneli (Issue #56, PR #51 üzerine)

`scripts.render_scorecard`, her üretimde `evaluation/benchmark.json`
ile `examples/fictional-hotel.json` dosyalarını okuyup **doğrudan**
`run_evaluation` motorunu çalıştırır. Oranlar ve durumlar HTML içinde elle
yazılmaz. İstemcide tekrar sınıflandırma veya AI çağrısı yapılmaz.

`scripts.stage_demo_site` yalnız güvenli olarak izinlenmiş sayfaları
kopyalar ve `synthetic-scorecard.html` sayfasını bu Python sonucundan oluşturur.
Panel mevcut birleşik kurgusal demoda bir bağlantıdan açılır.

Yerel kontrol:
```sh
python -m unittest discover -s tests -v
python -m unittest discover -s tests/browser -p test_scorecard_ui.py -v
python -m scripts.render_scorecard --output /tmp/scorecard.html
python -m scripts.render_scorecard --check /tmp/scorecard.html
```

Göstergeler: coverage, 5 TP / 2 TN, FP/FN, precision/recall/FPR/FNR
ve her gösterge için payda. **Yedi ölçülebilir sentetik etiket ve üç kapsam
dışı vaka** açıkça ayrılır. Denominator sıfırsa "undefined" gösterilir.
Gerçek operasyon doğruluğu, üretim güvenilirliği, insan override oranı
ve gerçek işlem süresi iddia edilmez.

Bu sayfa yalnız kurgusal test raporunu sunar. KVKK, otel entegrasyonu,
canlı AI/PMS/KBS/OTA/ödeme veya insan yetkilendirmesi içermez.
