# Etkileşimli otel demosu ve hareketli tanıtım

`demo/hotel-suite.html` tek başına çalışan kurgusal bir otel operasyon ekranıdır. Bir görsel galeri değildir: modüller, rezervasyon/oda detayları, görev ve housekeeping simülasyonu, filtreler ve rapor indirme önceki prototiple birlikte çalışır.

İlk ekran; kompakt operasyon çubuğu, yedi günlük rezervasyon/oda blokaj çizelgesi ve iki-asistan inceleme paneli sunar. Bu, otel yazılımlarında alışılmış operasyon kavramlarından yararlanan özgün bir arayüzdür. Sedna, ElektraWeb veya Sistem Otel'in ekran görüntüsü, HTML/CSS'i, ikonu, logosu veya özel kodu kullanılmaz. Kamuya açık işlev araştırmasının kaynakları [RESEARCH_MATRIX_TR.md](RESEARCH_MATRIX_TR.md) içindedir.

Senaryo seçiciden örneği seçip **Oynat**, **Duraklat**, **Sonraki** veya **Başa dön** kontrolleri kullanılabilir. Twin oda kıtlığı, housekeeping engeli, OTA eşleşmesi ve insan ön incelemesine hazır bir kayıt gösterilir. Her adım, Python kural motorunun aynı kurgusal snapshot için ürettiği sonuç ve kanıtlardan oluşturulur. Engelli bir kayıt gösterim sırasında hazır veya tamamlanmış check-in'e çevrilmez.

AI-1 kaynakları/incelenecek işi, kural motoru sayısal/tarihsel kontrolleri, AI-2 açıklama/devir özetini, personel ise son insan kontrol noktasını temsil eder. Bu akış **senaryolu bir görselleştirmedir**; gerçek model çağrısı, canlı PMS/OTA erişimi veya otomatik işlem değildir. Gerçek model bağlanırken kullanılabilecek salt okunur sözleşme `suite_agent_protocol.py` içindedir. Kimlik, ödeme, KBS ve kaynak sistemi değiştirme kapalıdır.

Gezinti, sıfırlama veya bir yerel veri değişikliği eski oynatma zamanlayıcılarını iptal eder. Housekeeping/görev/OTA simülasyonu yine rapor güncelliğini geçersiz kılar; rehber oynatımı bunu aşamaz. Hareket azaltma tercihi olan tarayıcılarda otomatik ilerleme yerine elle adımlama kullanılır. Duraklatma/sıfırlama ve klavye kontrolleri erişilebilir kalır.

Tanıtım GIF'i gerçek Chromium ekranından kaydedilir:

```sh
# Optional browser extra, Playwright Chromium and ffmpeg gerekir.
python scripts/generate_suite_demo.py --check
python scripts/record_demo_tour.py
```

Çıktı `docs/images/operations-tour.gif`, kayıt kanıtı `operations-tour.json` dosyasıdır. Kanıt kaynak HTML, snapshot, rapor ve GIF hash'lerini; görülen aşamaları, tarayıcı hata/ağ isteği sayısını içerir. Bu bir performans ölçümü, otel kullanım kanıtı veya gerçek AI ajanının üretim kaydı değildir. GIF yalnızca kurgusal uygulamanın oynatımını tanıtır.

GitHub Pages staging yalnızca incelenmiş halka açık dosyaları kopyalar. Suite `index.html` ve `hotel-suite.html`, önceki rapor panelleri `reviewer.html` ve `operations.html` olarak hazırlanır. Dolu çıktı dizini kabul edilmez; `.git`, kaynak export'u veya özel raporlar yayıma taşınmaz. Bu staging kodu kendi başına deploy yapmaz. Pages dağıtımı yalnızca aynı depodaki başarılı main push testlerinin incelenmiş SHA'sından yapılır; PR dalı kendiliğinden yayımlanmaz.
