# KonaklamaFlow sunum ve motion tasarım sözleşmesi

> 13 Kasım 2026 için tasarlanmış ürün planıdır. Bu doküman yeni animasyonların veya gerçek AI sağlayıcı bağlantısının kurulu olduğu iddiası değildir.

## Temel ilkeler
- Birincil marka KonaklamaFlow. Sağlayıcı logoları üründen büyük görünmez; izin yoksa metinli kart.
- Bir sahnede **tek ana karar**: kullanıcı önce sorunu, sonra kaynağı, sonra çözüm sınırını görür.
- Renk = tek sinyal değil: Blocked → simge + “İnceleme gerekli”; Ready → “Personel ön kontrolüne hazır”; Unknown → “Canlı kaynak doğrulanmadı”.
- Operator Mode: sakin, hızlı, okunabilir, hızlı klavye gezinimi. Presentation Mode: 16:9 anlatım alanı, sahne bölüm başlığı, altyazı ve geçiş ilerlemesi.
- Temalar: Light (gündüz), Dark (kurumsal), Night Audit (yüksek kontrastlı gece vardiyası). Tüm temalarda odak göstergesi ve kontrast korunur. Kullanıcı tercihi bellek içi; public offline demo yerel kalıcı depolama yapmaz.
- Motion: kısa easing geçişler, sahne odak vurgusu, ölçülü grafik yükselişi; yanıp sönme, gereksiz parallax yok. Sistem reduced-motion isteği varsayılan olarak öncelikli.

## Üç sunum formatı

### 90 saniyelik “elevator demo”
0–10sn ürün vaadi + kurgusal demo etiketi.
10–25sn 7 günlük room rack ve oda takvimi.
25–40sn twin scarce / overbooking uyarısı.
40–55sn engine evidence / why blocked.
55–70sn AI mock explanation + no-write boundary.
70–85sn personel onayı ve sıradaki güvenli adım.
85–90sn entegrasyon yol haritası ve proje CTA.

### 3 dakikalık rehberli tur
0–30 dashboard / bir bakışta vardiya.
30–60 room rack + maintenance.
60–100 OTA kaynak uyuşmazlığı.
100–130 housekeeping ve güncel olmayan veri.
130–155 iki asistanın sadece read-only devir protokolü.
155–180 güvenlik sınırı + read-only pilot yol haritası.

### 7 dakikalık teknik tur
- Her modülün canlı olmayan işlev sınırı.
- Python engine kuralları, input validation / fail-closed, reason + evidence.
- Snapshot parity, stale report, policy checks.
- Gelişmiş OTA ve sınırlı çok odalı planlama, açık Issue #1.
- AI provider port, mock-vs-real ayrımı, auth, data minimization, cost budget.
- Testler/CI ve production gates; prototip ile production arasında net çizgi.

## Kayıt ve gösterim
- GIF A: 12–20 sn gerçek desktop room timeline + filtre + drawer.
- GIF B: 12–20 sn gerçek housekeeping/OTA collision + why/evidence.
- GIF C: 12–20 sn gerçek mock-AI explanatory rail; ekranda “simülasyon” yazısı.
- PNG desktop 1440, mobil 390, opsiyonel 768; küçük dosya, alt metin ve video seçeneği.
- “Play” kullanıcıya bırakılır; GIF için statik poster/low-motion alternatif.
- Build script kullanıcı eylemleriyle tarayıcıdan kayıt eder; AI tarafından üretilen dekoratif görüntü gerçek ürün ekranı gibi sunulmaz.

## İnceleme senaryoları
1. Twin odanın başka rezervasyona gereksiz tahsisi: alternatifler ve kısıt nedenleri.
2. Oda 303 temiz değil: öneri gösterme, personel kontrolü, stale rapor.
3. OTA/PMS kaynak kodu uyuşmazlığı: otomatik eşleştirme yok, inceleme kuyruğu.
4. Başarılı pre-review: gerçek check-in değil, yetkili personel incelemesine hazır.

## Sunum kabul kontrolü
[ ] Desktop/mobile gerçek preview.
[ ] Tab/Escape focus, VoiceOver/NVDA anlamlı kontroller.
[ ] Reduced-motion / animasyonsuz statik anlatım.
[ ] Tema/mod değişimi kural kararını, hash'i veya export'u değiştirmiyor.
[ ] Tüm senaryolar izlenebilir gerçek ekran kaydı ve doğrulanan artefakt.
[ ] TR/EN iyi okunur; 320px yatay body overflow yok.
[ ] Marka/telif/ortaklık beyanı doğrulanmış.