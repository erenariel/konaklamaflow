# KonaklamaFlow — Ürün tasarımı ve resepsiyon operasyonları

**Durum:** v0.2 geliştirme adayı. **Canlı otel işlemi yapmaz.** Tüm örnekler kurgusal ve kimliksizdir.

## Kimin için?

Türkiye'de yaklaşık 10–80 odalı butik oteller, pansiyonlar ve bağımsız işletmelerin ön büro personeli, kat hizmetleri ve operasyon yöneticileri. Bu bir rakip PMS klonu değil; mevcut sistemlerin üzerine takılabilecek bir **operasyon kontrol / karar destek katmanı** olarak konumlanır.

## Tipik bir vardiyada kullanıcı akışı

1. Yetkili PMS'den *kurallara uygun, en aza indirilmiş/pseudonimleştirilmiş* rezervasyon ve oda durum özetini hazırla. Kullanıcı adı, pasaport, telefon, TC kimlik, e-posta ve ödeme kartını dışa aktarma.
2. KonaklamaFlow çekirdeği çakışma, oda kategorisi ve temel fiyat farklarını değerlendirir.
3. Resepsiyon kontrol katmanı oda temizlik durumu, teknik blokaj, kimlik kontrol durumu (yalnızca yetkili sistemce doğrulanmış sinyal), ödeme incelemesi ve giriş saatini kontrol eder.
4. Kuyruk kayıtları üç gruba ayrılır: personel kontrolüne hazır, engeli olan ve önceki girişin incelenmesi gereken.
5. İkinci AI asistanı yalnızca açıklama/önceliklendirme ve görev özeti üretebilir; yazma yetkisi yoktur.
6. Gerçek oda ataması, misafirin check-in işlemi, KBS bildirimi, ödeme ve misafir mesajı yalnızca yetkili sistemin kendi güvenli akışı üzerinden ve gerekli yetkili onaylarıyla yapılır.
7. Sistem beklenmeyen durumlarda güvenli biçimde *durur*: hatayı sessizce yutmak yerine işin insan incelemesine girmesini sağlar.

## V0.2 kapsamı (bu paket)

- `operations.py`: deterministik, kimliksiz veriyle ön check-in *inceleme* listesi.
- `agent_protocol.py`: kısa ömürlü, hash kontrollü, **salt okunur** ikinci asistan görev sözleşmesi.
- `demo/operations.html`: internet gerektirmeyen, arama ve filtre özellikli görsel kokpit. Dosya içe alma da yereldir.
- `tests/test_operations.py`: çekirdek kontroller, hatalı inputlar, değişmeyen karar çıktısı.
- `tests/browser/test_operations_ui.py`: tarayıcıda kontroller, XSS dayanımı örneği, mobil taşma, çevrimdışı olma.
- Oda önerileri: çift yataklı odaları uygun olduğu sürece önce kullanarak sınırlı twin kaynaklarını koruma yönergesi.

## V0.3+ için **yapılacaklar**, yapılmış özellik değil

- Kullanıcı rol ve erişim modeli (resepsiyon/kat hizmetleri/operasyon), SSO/MFA.
- PMS ürünlerinden gelen **resmen izin verilmiş, tercihen salt-okunur API adaptörleri**; kopya ekran / DOM otomasyonu değil.
- Envanter değişiminde yeniden doğrulama ve optimistic concurrency / revision token.
- Değiştirilemez audit kaydı ve olay tekrarında idempotency garantisi.
- Oda atamada tüm konaklama aralığını değerlendiren optimizasyon ve çoklu tesis izolasyonu.
- Gerçek personel pilotları, erişilebilirlik testleri, masaüstü ve mobil kullanım araştırması.
- Yetkili kimlik doğrulama, ödeme ve resmî bildirim sağlayıcıları için ayrı güvenlik ve hukuki inceleme.

## Risk ve denetim katmanları

| Risk | İzin verilen davranış | Yasak / canlıda bloke |
|---|---|---|
| Çift rezervasyon | Kritik uyarı, kanıt ve yeniden inceleme | Otomatik rezervasyon silme |
| Kirli / teknik kapalı oda | Check-in hazırlığına engel | Oda temizmiş gibi işaretleme |
| Yatak talebi | Uyumsuz oda önerme, açık uyarı | Uygun olmayan iki yataklı oda garantisi verme |
| Kimlik | Yetkili personel doğrulama durumunu kontrol | Kimliği AI üzerinden doğrulama / gerçek belgeyi açık kaynağa gönderme |
| KBS | Entegrasyon dışı, yalnızca durum takibine yer verme | Alanları manipüle etme, sahte kimlik veya bildirim |
| Ödeme | İnceleme bayrağı | Yetkisiz çekim/iade |
| Misafire mesaj | Gönderim öncesi taslak ve kontrol | AI'nın doğrulanmamış garantiler vermesi |

## Hız hedefleri ile gerçeklik

Yerel kural motoru milisaniyeler içinde örnek raporu işleyebilir, ama uçtan uca check-in süresi; ağ, PMS API'si, kişinin kimlik kontrolü, ödeme, oda hazırlığı ve onaylara bağlıdır. **AI hatasız değildir.** Hız optimizasyonu doğrulama adımlarını atlayamaz. Sürüm başına gecikme ve hata ölçümleri ancak gerçek izinli pilotta kaydedilebilir.
