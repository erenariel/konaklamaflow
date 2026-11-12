# KonaklamaFlow — Açık kaynak pazarlama ve topluluk stratejisi

**Ürün konumu:** Küçük oteller için *rezervasyon ön kontrolü ve resepsiyon operasyon kontrol listesi*. Şu anda tam PMS, canlı check-in, otomatik KBS veya yapay zeka rezervasyon asistanı değildir.

## Kimin problemine çözüm arıyoruz?

- **Gece resepsiyonu:** Son dakika değişiklikleri, kirli oda, hatalı blokaj, çift rezervasyon ve ertesi gün giriş bilgilerini hızlıca kontrol etmek ister.
- **Operasyon sorumlusu:** Sabah kontrolünün aynı standartla yapılmasını, kritik işlerin gözden kaçmamasını ister.
- **Kat hizmetleri:** Hangi odanın öncelikli olduğunu ve girişe uygunluğunu net görmek ister.
- **Küçük otel sahibi:** Lisans bağımlılığına girmeden, mevcut PMS'ini değiştirmeden bir kontrol katmanı denemek ister.

## Mesajlaşma / farklılaştırma

**Ana başlık:** "Oda hazır mı? Rezervasyon çakışıyor mu? Resepsiyon bunu tek ekranda görsün."

**Alt metin:** "KonaklamaFlow, butik oteller için açık kaynaklı ve mahremiyet öncelikli bir operasyon kontrol aracıdır. İlk prototip kurgusal verilerle çalışır; gerçek PMS işlemleri ve resmi bildirimler yapmaz."

**Üç somut vaat:** Görünür uyarılar, doğrulanabilir kural raporları, insan kontrolü. Hız veya doğruluk yüzdesi konusunda ölçülmemiş iddialar kullanma.

**Yanlış vaatler (yasak):** "AI asla hata yapmaz", "milisaniyede tüm check-in biter", "KBS otomatik tamamlandı", "tüm otellerde çalışır", "yüzlerce otel kullanıyor" gibi doğrulanmamış ifadeler.

## Dağıtım kanalları

1. **GitHub:** İki dilli kısa başlangıç belgesi, demo, örnek JSON, katkı rehberi, düşük seviyeli bug ve enhancement issue'ları.
2. **Landing page / GitHub Pages:** İnteraktif *kurgusal* kokpit ve açık sınırlar. `demo/operations.html` yayınlanmadan önce CI tarayıcı testleri geçmeli.
3. **Gönüllü otel pilotları:** 2–3 tesiste yalnızca sentetik verilerle kullanıcı akışı testi; gerçek veri için hukuki değerlendirme ve güvenli entegrasyon gerekir.
4. **Topluluk:** Python / hotel-tech / turizm yazılımı topluluklarında dürüst demo; katkı çağrısı ve Türkçe dokümantasyon.
5. **İçerik:** "Overbooking nasıl önlenir?", "Kirli oda check-in kontrol listesi", "Açık kaynakta kişisel veri nasıl korunur?" teknik makaleleri.

## 30/60/90 günlük doğrulanabilir hedefler — HEDEF, GERÇEKLEŞMİŞ SONUÇ DEĞİL

| Süre | Hedef | Kanıt |
|---|---|---|
| İlk 30 gün | En az 3 bağımsız geliştirme geri bildirimi, 2 ön büro kullanıcı görüşmesi | Halka açık issue / tarihlendirilmiş, izinli anonim görüşme notları |
| 60 gün | 1 onaylı sentetik pilot, 1 dış katkı PR'si (varsa) | Test raporu, gerçek PR bağlantısı |
| 90 gün | Kullanıcıların gerçek ihtiyaçlarıyla önceliklendirilmiş v0.3 ve tekrar üretilebilir sürüm | Release, changelog, yeşil test, kullanım örnekleri |

Sayılar **hedef** olduğu için başvuruya sonuç olarak yazılmaz. Pilot reddedilebilir veya daha uzun sürebilir.

## Ölçüm planı

- Sentetik olaylarda kritik çakışma kaçırma oranı (test verisine karşı), yanlış alarm sayısı, P95 yerel işlem süresi.
- İnsan pilotta görev başına geçen süre (kontrol grubu ile), engellerin çözülme süresi, kullanıcı hatası ve düzeltme ihtiyacı.
- GitHub Issues/PR, sürümler, bağımsız kullanıcı/katkı ve yalnızca gerçek olarak doğrulanabilen kullanım bilgileri.

## Açık kaynak ve sürdürülebilirlik

Çekirdek MIT lisanslı ve ücretsiz kalabilir. İleride opsiyonel kurulum, profesyonel destek ve yetkili entegrasyon hizmetleri ayrı değerlendirilebilir. Bu gelir modeli henüz yoktur; open-source katkı ve güvenlik önce gelir.

## Codex for Open Source başvurusu için gerçek kanıtlar

Kayıtlı sürümler, gerçek sorun triage'ı, bakım sorumluluğu, test ve güvenlik süreci, doğrulanabilir kullanımlar. Suni commit, fake star, sahte PR ve hayalî müşteri referansı oluşturma.
