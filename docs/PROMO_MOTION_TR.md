# KonaklamaFlow — Tanıtım ve hareketli sunum yönergesi

Bu dosya, Codex'in uygulama geliştirmesiyle çakışmadan hazırlanmış özgün tanıtım hareket sistemini açıklar.

## Yayınlanan kaynak varlıklar
- `docs/images/ai-presentation-hero.svg`: README'nin yeni tanıtım görseli. CSS hareketleri ve **prefers-reduced-motion** desteği içerir; animasyon devre dışıysa ilk kare bilgi verir.
- `docs/images/ai-explanation-flow.svg`: Kaynak → kural → açıklama → personel akışını tanıtan kısa diyagram.
- Önceki `docs/images/operations-tour.gif` korunur, ancak README'nin üstündeki ilk görsel değildir.

## GitHub tanıtımına eklenen hareketli GIF'ler

Üç animasyon **doğrudan bu PR'ın `docs/images/` klasörüne** eklendi. README'deki hareketli tanıtım bölümünde her birinin altında Türkçe ve İngilizce kullanım açıklaması bulunur:

- `docs/images/ai-command-tour.gif` — kaynak incelemesi → kurallar → simüle AI açıklaması → personel değerlendirmesi
- `docs/images/roomplan-story.gif` — kurgusal rezervasyona bağlı oda planı vurguları
- `docs/images/overview-pulse.gif` — doluluk, kanallar ve AI destekli inceleme özetini tanıtan renkli döngü

İlk kareler ve hareketler gerçek kurgusal/çevrimdışı HTML'in Playwright/Chromium ekran görüntülerinden üretilmiştir. Görseller yalnızca **tanıtım README'sinde** kullanılır; çalışan demo HTML dosyalarında GIF oynatımı eklenmedi.

## Yeniden üretim

`scripts/build_promo_gifs.py` dosyası yerel HTML ekran görüntülerinden aynı üç medya türünü yeniden üretir. Örnek:

```bash
python -m pip install pillow playwright
python -m playwright install chromium
python scripts/build_promo_gifs.py --html demo/v04-integrated-preview.html --out docs/images
```

Not: Bu kayıtta AI operasyon panelini içeren `feat/ai-operations-dashboard-desktop-v052` dalındaki **sentetik HTML** kaynak alınmıştır. Codex demo tasarımını değiştirirse, tanıtım GIF'leri yeni sürümle tekrar eşleştirilmelidir.

## Hareket kuralları
1. Profesyonel palet: gece laciverti `#071426`, elektrik camgöbeği `#3EE2DF`, mint `#4FF1C4`, mor `#8873F9`, amber `#FFC45B`.
2. Ana kullanıcı akışı: kaynak verisi → deterministik engel → AI sunum açıklaması → yetkili personel incelemesi.
3. İşlevsel hareket yalnızca kullanıcı eylemiyle başlasın; arka plan dekoratif efektler düşük yoğunlukta olmalı, sonsuz parlamalar/kafa karıştıran titremeler kullanılmamalı.
4. Görsel parıltılar gerçek bağlantı veya tamamlanmış otel işlemi iddiası değildir. Her yerde **kurgusal/çevrimdışı** etiketi ve KBS/PMS/OTA sınırları görünür olsun.
5. Erişilebilirlik: `prefers-reduced-motion`, klavye ile durdurma/başlatma, ekran okuyucu için anlamlı başlık, 1366×768 ve 1440×900 masaüstü kontrolleri.
6. Tanıtım görsellerindeki sayılar yalnızca ilustratiftir; otel KPI'ları veya üretim performansı iddiası değildir.

## PMS araştırmasından özgün tasarım yönleri
- **ElektraWeb:** durum bazlı rezervasyon sekmeleri ve önbüro eylemleri — özgün etiketler/yerleşim.
- **Sistem Otel:** renk kodlu oda planı, housekeeping çizgileri, gelecek/gidecek/içeride filtreleri ve denetim görünürlüğü — sağlayıcı tasarımını kopyalamadan.
- **Sedna:** folyo/audit ve çok işlemli çalışma yaklaşımı — kullanıcıların güvenli, açıklanabilir AI karar yolunu izlemesi.

Düzenleme herhangi bir üreticiye bağlılık/ortaklık anlamına gelmez.
