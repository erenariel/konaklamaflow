# Codex for Open Source — Gerçekçi başvuru stratejisi

**Hazırlanma tarihi: 12 Kasım 2026**

## Hedef

Türkiye'deki küçük ve bağımsız konaklama işletmelerinin anlaşılır, incelenebilir ve veri minimizasyonuna öncelik veren açık kaynak operasyon araçlarına erişimini kolaylaştırmak. Altı aylık ChatGPT Pro, nihai ürün değil: açık kaynak bakım sorumluluğu oluştuğunda başvurulabilecek olası bir destek.

OpenAI'ın yayımladığı koşullar: https://openai.com/tr-TR/form/codex-for-oss/

> Program aktif açık kaynak proje bakım sorumlularını değerlendiriyor; kullanım, ekosistem önemi ve somut bakım faaliyeti sinyallerini inceliyor. Yeni oluşturulan bir depo, çok sayıda yapay commit ya da şık bir README tek başına kabul güvencesi değildir.

## Konumlandırma

**KonaklamaFlow** tek bir otelin kopyası değildir. Pseudonimleştirilmiş verilerle çalışan, marka bağımsız, açık kaynaklı rezervasyon analizi motorudur. Küçük otellerin otel yazılımındaki verileri kopyalamadan önce veri minimizasyonuyla kontrol etmeleri gerekir. Özellikle pahalı/bakımı zor yetkisiz web otomasyonları yerine; açık şema, test edilebilir kurallar, raporlar ve zamanla izinli API adaptörlerine odaklanılır.

**Yan projeler:** Hospitality Tip Ledger (kuruş bazında bahşiş dağıtımı; ayrı, sınırlı kapsam) ve privacy-first AI workflow dokümantasyonu. Bu yardımcı projeler yalnızca gerçek kullanıcı faydası gösterdikleri takdirde ayrı depolara dönüşmeli.

## Başvuru kanıt tablosu — dürüstçe toplanacak

| Kriter | Elde olan (v0.1 hazırlık) | Geliştirilmesi gereken |
|---|---|---|
| Açık kaynak kod | MIT lisansı, 23 test, örnekler ve belgeler | GitHub'da gerçekten yayımlanması |
| Aktif bakım | Yerel 0.1 değişiklik günlüğü ve issue şablonları | Gerçek GitHub issues, gerçek PR incelemeleri, sürüm yayımlama ve geri bildirim |
| Kullanım | Henüz kanıt yok | Gönüllü otel pilotları, izinli referanslar ve doğrulanabilir kullanım |
| Ekosistem önemi | Vendor-neutral, doğrulanabilir otel operasyon kuralları | Başka açık kaynak PMS projeleriyle uyumluluk ve katkı |
| Güvenlik | Sentetik örnekler ve dar şema | Bağımsız inceleme, tehdit modeli, sürdürülebilir güvenlik yanıtı |

## İlk pilot için ölçülebilir sorular

- Her gece manuel kaç rezervasyon kontrolü yapılıyor? (ham kişisel verileri toplamadan, yalnızca sayım)
- Mevcut yöntemde kaç işlem yanlış oda kategorisine atanma riski taşıyor?
- Kontrol için harcanan dakika, prototipten önce ve sonra nasıl değişiyor?
- Hatalı pozitif veya hatalı negatif kontrol örnekleri **sentetik test** haline dönüştürülebilir mi?
- Operatör yazılımın raporunu anlıyor mu; hangi uyarı daha faydalı?

Sayıları ölçmeden hiçbir başarı yüzdesi ya da tasarruf iddiası yapılmamalı.

## Geniş benimsenme için iki paralel kanal

1. **Kendi açık kaynak projemizin bakımı:** v0.1'in yayınlanması, dokümantasyon, issue triage, iyileştirmeler, sürüm notları ve topluluk desteği.
2. **Mevcut açık kaynak PMS ekosistemine katkı:** Özellikle [QloApps](https://github.com/Qloapps/QloApps) veya [Kamra PMS](https://github.com/Kamra-PMS/kamra-pms/) gibi projelerin gerçek sorunlarını ve katkı rehberlerini inceleyip izinli, küçük ama değerli test/dokümantasyon/yamaları önermek. Dış projeye bir pull request göndermek **tek başına o projenin çekirdek bakım sorumlusu olduğumuzu göstermez**.

## İlk 90 gün — örnek çalışma ritmi

- Gün 1–7: kodu PUBLIC depoya koy, CI'nin gerçekten geçtiğini gör, v0.1 etiketini ancak testten sonra yayımla.
- Gün 8–30: sentetik veri setleriyle en az üç gerçek operasyon senaryosu ekle; rapor arayüzü ve CLI'yi iyileştir, herkese açık katkı belgelerini koru.
- Gün 31–60: 2–3 gönüllü otel veya geliştiriciden izinli kullanım geri bildirimi iste; gerçek veri toplamadan bu geri bildirimlerle somut issue oluştur.
- Gün 61–90: izinli adaptör sözleşmesi, kural konfigürasyonu, log tasarımı ve üçüncü taraf kod inceleme önerilerini değerlendir; aktif bakım ve geri bildirim kanıtlarını doğrula.

Bu süreler **OpenAI'ın resmî zorunluluğu değildir**. Hiçbir yıldız, indirme, kabul ya da Pro erişimi garanti edilmez.

## Başvuru metni hazırlanırken

Resmî formda 500 karakterlik iki açıklama bulunur. Gerçek yayımlanma, bakım ve kullanım verileri toplanmadan başarı iddiası içeren bir metin gönderilmemelidir. OpenAI Organization ID ve başvuru e-postası kullanıcı tarafından güvenli biçimde belirlenmelidir; bunlar açık GitHub depolarına yazılmamalıdır.
