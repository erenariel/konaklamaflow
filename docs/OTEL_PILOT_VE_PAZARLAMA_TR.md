# Pilot ve pazara giriş stratejisi

**Durum:** Bu belge plan ve araştırma hipotezidir. Gerçek otel pilotu, kullanıcı, ortaklık, zaman tasarrufu veya gelir sonucu bildirmez. Bu PR kapsamında yalnızca kurgusal veri ve izinli test ortamı kullanılır; gerçek kayıt işleme yetkisi verilmiş sayılmaz.

## Marka konumlandırması

**KonaklamaFlow — Misafire daha fazla zaman, operasyona daha fazla netlik.**

İlk ürün vaadi: Küçük ve butik otellerin mevcut PMS'lerini değiştirmeden rezervasyon çakışması, oda hazırlık statüsü, özel istek ve departman görevlerini görünür hale getiren açık kaynak **operasyon kontrol katmanı**.

**İddia edilmemesi gerekenler:** "Hatasız AI", "milisaniyede check-in", "tüm otellerle entegre", "ödemeyi ve KBS'yi otomatik gönderiyor", "onaylı Elektra/Sistem Otel/Sedna partneriyiz", "100 pilot işletme" vb.

## İlk değerlendirme personası (doğrulanmış müşteri değil)

- 10–80 odalı bağımsız/butik otel
- 7/24 resepsiyon; vardiyada 1–2 kişi, ayrı housekeeping sorumlusu
- Rezervasyon kaynağı: OTA, acente, direkt ve channel manager
- Sorun: Oda kategorisi uyuşmazlığı, iki ayrı yatak talebi, yanlış konfirmasyon, kirli oda, teknik blokaj, geç check-in, acente fiyatı ve görev devri
- Yönetici hedefi: Yüksek misafir memnuniyeti, düşük hata maliyeti, kolay personele eğitim ve izlenebilirlik

## Pilot yaklaşımı

1. **Yönetim onayı:** 1 sayfalık scope, veri koruma, görevler, riskler; izinsiz gerçek kayıt kullanılmaz.
2. **1. hafta / senaryo:** Kurgusal kayıtlarla 10 temel olay; gece vardiyası personeli iş akışını değerlendirir.
3. **2. hafta / shadow:** Sadece uygun şekilde anonimleştirilmiş snapshot; sonuçlar canlı PMS ile personel tarafından karşılaştırılır; KonaklamaFlow hiçbir işlem yazmaz.
4. **3. hafta / kalite:** Yanlış uyarılar, kaçırılan hatalar, anlaşılmayan öneriler ve mobil kullanılabilirlik tespit edilir.
5. **4. hafta / rapor:** Toplam senaryo, kontrol süresi, doğrulanan gerçek/yanlış uyarı, görev değişiklik talepleri ve alıntılanmasına izin verilen geri bildirimler. İzin yoksa işletme adı paylaşılmaz.

## Ölçümler

`manual_review_time_before`, `review_time_after`, `source_mapping_precision`, `room_assignment_conflict_count`, `guest_request_handovers`, `P50/P95_processing_latency`, `manual_overrides`, `false_alerts`, `missed_critical_events`, `pilot_user_satisfaction`. Sayısal kazanım iddiaları ancak gerçekten ölçülürse yayımlanır.

## Pazarlama kanal planı

- Açık kaynak GitHub dokümantasyonu ve test edilmiş kurgusal demo; yalnızca gerçekleşen geliştirmeleri anlat
- Kullanımı kolay **10 modüllü** otel kokpiti videosu / ekran kayıtları; "simülasyon" etiketi
- Türkçe/İngilizce belgelendirme; güvenlik sınırları şeffaf
- Küçük otel operasyon içerikleri (oda karışıklığı, HK, OTA iptal/modify) üzerinden teknik blog
- Karşılaştırılabilir, doğrulanabilir küçük pilot raporları; izinsiz marka veya müşteri logosu yok
- Bağımsız yazılım geliştiriciler için 'good first issue', data fixtures ve test katkısı

## Ticari model önerisi (araştırma hipotezi)

- **Açık kaynak çekirdek:** MIT/uyumlu lisans ile ücretsiz, yerel dry-run.
- **Opsiyonel kurumsal servis:** Yetkili PMS adaptörü, SLA, denetim raporlaması, eğitim, barındırma. Bu gelir modeli henüz yoktur; lisans ve telif uyumu ayrıca değerlendirilmeli.
- API'lere erişim için sağlayıcı lisans ve ücretleri otomatik olarak ücretsiz veya garanti edilmez.

## Misafir deneyimi

KonaklamaFlow'un misafir memnuniyetine etkisi ancak gerçek işletme süreçlerinde doğrulanabilir. Tasarımda misafirle yüz yüze karşılama, hassas talepler, problem çözümü, konuk şikâyetleri ve otelin kişisel dokunuşu insan ekibinde kalmalı; AI ise görünmez bir operasyon desteği olarak çalışmalıdır.

Büyük otel operasyonlarına genişleme ürün hedefidir. Demodaki 18 oda ve kurgusal ekranlar, büyük otelde yük, concurrency, erişilebilirlik veya gerçek operasyon başarısı ölçümü değildir. Pazarlama metni, tamamlanmış özellik ile mimari hedefi açıkça ayırmalı; kullanıcı görüşmesi veya pilot gerçekten yapılırsa tarih, yöntem, izin ve kanıtıyla raporlanmalıdır.
