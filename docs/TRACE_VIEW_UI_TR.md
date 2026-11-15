# Kurgusal karar geçmişi görünümü (Issue #57, PR #53 üzerine)

`scripts.render_trace_view` sayfası, `decision_trace.fictional_walkthrough`
üzerinden kurgusal adımlar oluşturur ve yayımlamadan önce
`verify_trace` ile **tam kaynak/rapor/hash/alan gerekçesi eşleşmesini**
doğrular. İstemci iş mantığı çalıştırmaz; HTML salt okunur ve çevrimdışıdır.

Yalnızca üç **simüle edilmiş** olayın zamanını, rol *etiketini*, opak
görev kimliğini, karar gerekçelerini, güvenli alan yollarını ve hash
bağlantılarını gösterir. Gerçek personel eylemi veya onay kaydı değildir.
Bir saldırgan tüm zinciri yeniden hesaplayabileceğinden bağımsız imza,
haricî hash dayanağı ve üretim immutable log garantisi bulunmamaktadır.

`scripts.stage_demo_site` sayfayı `fictional-trace.html` adıyla sentetik
örnekten oluşturur; ana demoda link vardır.

Doğrulama:
```sh
python -m unittest discover -s tests -v
python -m unittest discover -s tests/browser -p test_trace_view_ui.py -v
python -m scripts.render_trace_view --output /tmp/trace-view.html
python -m scripts.render_trace_view --check /tmp/trace-view.html
```

Gerçek misafir verisi, şifre, KBS, PMS, OTA, ödeme entegrasyonu veya
personel yetkilendirme katmanı içermez. İleride PR #55 ile birleştirilecek
olursa ayrı entegrasyon testi gerekir.
