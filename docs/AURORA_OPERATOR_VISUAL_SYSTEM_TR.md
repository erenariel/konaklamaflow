# KonaklamaFlow — Aurora Operator Workspace (özgün görsel katman)

> Durum: PR #38'de uygulanmış **CSS ve kaynak-bağlı demo görselleştirmesi**. Gerçek AI / PMS / finans entegrasyonu **eklenmedi**. Bu kılavuz, tek başına bir v1.0 vaat etmez.

## Tasarım ilkesi
Klasik PMS yazılımlarının yaygın operasyon ihtiyaçlarını — oda rack, tarih çizelgesi, misafir/rezervasyon görünümü, folyo, kasa ve doluluk — korurken **hiçbir sağlayıcının ekranını birebir çoğaltma**.

Aurora stili: kontrollü gece mavisi/indigo arka plan, özgün elektrik mavisi ve turkuaz vurgu, mor-pembe ikincil renkler, yumuşak çok katmanlı yüzeyler. Fütüristik ama okunabilir ekran; renkler salt dekorasyon değil, ayrıca *sözel durum/ikon/kanıt* ile desteklenir.

## Bu PR'da gerçekte yapılanlar
- `demo/ai-command-center.css`: AI merkezi ışık/ızgara ambiyansı, oda takvimi ve rezervasyon şeridinin kontrast/odak iyileştirmesi, temaya uygun renkler.
- `demo/hotel-ops-styles.css`: rezervasyon ve folyo tabloları, sabit başlık, durum satırları, form alanları, kart grupları.
- `demo/v04-integrated-preview.html`: aynı kaynak CSS'in üretim markers içinde yeniden gömülmesi; proje daha önce olduğu gibi çevrimdışı tek sayfadır.
- `tests/test_aurora_ui_contract.py`: kaynak-gömülü çıktı eşitliği, motion opt-out, odak ve tema sözleşmeleri.
- `docs/images/`: gerçek kurgusal demo üzerinden ekran görüntüsü ve kaynak karmasıyla doğrulanan GIF kayıtları.

## Hareket kuralı
- Tamamen görsel ve kurgusal senaryo odaklıdır; gerçek işlem ya da model çağrısı yapıyormuş izlenimi verme.
- `data-kf-motion="off"` ve `prefers-reduced-motion:reduce` seçeneklerinde animasyon devre dışı.
- Hover yalnızca erişilebilir olmayan bir bilgi taşımaz: klavye focus-visible ve açık durum metinleri öncelikli.
- Özellikle mobil viewport, 10 dil ve AR/HE RTL bozulmamalı.

## Kalan işler ve Codex'e devredilecek sınır
1. **Önce #35**: aynı sentetik `reservation_id` ile oda planı, rezervasyon, folyo, rapor ve AI değerlendirmesi tek veri kaynağına bağlanmalı.
2. **Sonra #37**: yeni grafik oda kartları, daha kapsamlı tarih aralığı timeline'ı, filtreler, forecast ve kasa ekranları gerçek şema üzerinde geliştirilmeli.
3. Gelecekte AI adaptörleri gerekiyorsa ayrıca **kaynak izinleri, güvenlik, durum doğruluğu ve insan onayı** ile ele alınmalı; bu PR'a karıştırılmamalı.
4. Eski `hotel-suite.html`, raporlar ve diğer rotalar silinmemeli. Parçalı iyileştirme, test ve geri alma olanağı korunmalı.

## Kamuya açık kaynak ve gizlilik
Operasyon ekran görüntüleri sadece yerleşik iş ihtiyacını anlamak için kullanıldı; fotoğraflar ve kişiye/otelin mali kaydına ait bilgiler GitHub'a aktarılmadı. Sağlayıcının marka görünümü, ikonları, kodu veya özgün ekran kompozisyonu kopyalanmadı. Yalnızca genel iş akışı kalıpları özgün ürün dilinde ele alındı.

## Teslim sınırı
Bu sürüm **kurgusal, offline, salt okunur demo**. Gerçek rezervasyon, KBS, kimlik, ödeme, fatura veya PMS bağlantısı yoktur.
