# KonaklamaFlow — Global Presentation Mode / UX tasarım devri

**Durum:** Bağımsız etkileşimli tasarım prototipi; mevcut GitHub uygulamasına uygulanmış özellik değildir. Sadece kurgusal veri kullanır. Tarih: 13 Kasım 2026.

## 1. Tasarım vizyonu

KonaklamaFlow'un yeni sunum deneyimi, bir otel yöneticisinin veya jüri üyesinin 90 saniye içinde şu üç soruyu anlamasını sağlamalı:
1. Hangi operasyon sorunu oluştu?
2. Sistem bunu hangi somut ve denetlenebilir kanıta göre tespit etti?
3. İnsan hangi adımı atmalı; AI neyi yapamaz?

Temel prensip: **Rule engine decides → AI explains → Human approves.**

## 2. Görsel prototip dosyaları

- `KonaklamaFlow_Global_Presentation_Concept.html`: 10 dilde çevrimdışı, etkileşimli ve tek dosyalı örnek.
- `KonaklamaFlow_Presentation_Mode.png`: masaüstü sunum görünümü.
- `KonaklamaFlow_Desktop_Preview.png`: operatör görünümü.
- `KonaklamaFlow_Mobile_Preview.png`: 390px mobil düzen.
- `KonaklamaFlow_Arabic_RTL_Preview.png`: sağdan sola Arapça tasarım.
- `KonaklamaFlow_Multilingual_Presentation_Tour.gif`: tarayıcıdan 12 karelik değişen dil/senaryo/tema tanıtımı.

## 3. Bileşenlerin işlevi

- **Koyu sol navigasyon:** genel bakış, oda planı, gelişler, OTA kontrolü ve AI açıklamaları. Sunum modunda alan açmak için gizlenir.
- **Üst kontrol çubuğu:** 10 dil, Light/Dark/Night Audit temaları, Operator/Presentation geçişi; kalıcı izleme veya depolama yok.
- **Sahne kahraman alanı:** tek ve anlaşılır sorun anlatımı, DRY_RUN_ONLY uyarısı ve personel onay sınırı.
- **Dört KPI kartı:** kurgusal oda/varış/uyarı sayısı ve kararın otoritesi (kural motoru).
- **Yedi günlük room rack:** oda blokajları, bakım ve tartışmalı durumlar; örnek veridir, gerçek müsaitlik garantisi değildir.
- **Kanıt tablosu:** rezervasyon referansı, oda, reason code, durum ve kaynak güvenilirliği. Teknik referanslar bidi izolasyonuyla LTR okunur.
- **Beş adımlı hikâye:** sinyal → kontrol → kanıt → AI açıklaması → yetkili personel. Play/pause, adım adım gezinme, reset; tercih edilen reduced motion desteklenir.
- **Açıklanabilirlik rayı:** neden, kanıt, güvenli sonraki adım ve insan onayı sınırı. AI metni önceden hazırlanmış mock'tur, gerçek model çağrısı değil.
- **AI sağlayıcı vitrini:** OpenAI API, Claude API, Gemini API, Azure OpenAI, Local models; hiçbiri bağlı olarak gösterilmez. Marka logosu kullanılmaz.

## 4. Dil mimarisi

İlk hedef: `tr-TR`, `en`, `fr`, `el`, `he`, `ar`, `de`, `ru`, `es`, `uk`. Prototipin görsel çevirileri insan tarafından kalite onayı almamıştır. Üründe tam destek ilan etmeden önce iki dilli/yerel uzman incelemesi gerekir.

Canlı uygulamaya geçerken **BCP-47 locale + mesaj kataloğu + stabil key** mimarisi kur. `Intl.DateTimeFormat` ve `Intl.NumberFormat` ile tarih/sayı/para/çoğul kurallarını yerelleştir. JSON schema, reason code, snapshot SHA ve karar yetkisi çevrilmez. Dil geçişi sunucu verisini veya export parity'yi değiştirmemeli.

Arapça (`ar`) ve İbranice (`he`) için `dir=rtl`, logical CSS özellikleri, `bdi`/Unicode bidi isolation, LTR oda kodları, yönlü navigasyon ve RTL ikon testleri gerekir.

## 5. Sunum hareketi

- Yumuşak kart ortaya çıkışı, kritik oda vurgusu, ilerleme çizgisi ve adım geçişleri.
- Parlak, sürekli veya agresif animasyon yok; kullanıcı oyun sırasında kontrolü elinde tutar.
- `prefers-reduced-motion`, manuel adım ve klavye erişilebilirliği korunmalı.
- Hedef formatlar: 90 saniye ürün tanıtımı, 3 dakika rehberli tur, 7 dakika teknik sunum.
- GIF'ler gerçek çalışan uygulamadan kaydedilmeli, kaynağı/commit SHA'sı/manuel incelemesi ve alt yazılı video alternatifi olmalı.

## 6. Codex uygulama sırası

1. Mevcut açık #19 (i18n), #4 (tema/sunum), #5 (açıklanabilirlik), #6 (story), #9 (a11y) işlerini oku; yeni tekrarlı issue açma.
2. Bu HTML'yi ürün kodu olarak doğrudan `main`'e kopyalama. İskelet, tasarım tokenları, locale mimarisi ve state sınırlarını mevcut v0.3 ile **uyumlu ayrı feature branch/draft PR** üzerinde port et.
3. Açıklamalar yalnız Python report reason/evidence alanlarıyla beslensin. `READY` kararını browser/AI üretmesin.
4. Demo kurgusal ve offline: zero network, zero secrets, zero real PII; PMS/OTA/KBS/ödeme/kimlik/mesaj işlemleri kapalı.
5. Doğrulanabilir Playwright matrisi: 10 locale × 3 tema × 2 mod, en az 320/375/768/1440 viewport; RTL ve 200% zoom. Klavye focus, reduced motion, source parity, no-network ve XSS.
6. Çeviri kapsamı %100, insan dil kalite onayı ve gerçek tarayıcı ekran kanıtı olmadan “10 dilde tam destek” duyurma.
7. PR inceleme ve CI başarılı olmadan merge, Pages release, production entegrasyonu yapma.

## 7. Henüz yapılmamış, gerçek ürüne aktarılması gerekenler

- Mevcut GitHub projesine entegrasyon ve bağımsız PR testleri.
- İnsan onaylı profesyonel çeviri; hukuki uyarıların yerel anlam doğrulaması.
- Screen-reader/contrast/zoom ve erişilebilirlik kabulü.
- Gerçek zamanlı AI provider API köprüsü ve yetkilendirmesi (ayrı özel backend, açık onay, maliyet limiti).
- Gerçek PMS adaptörü ve güvenlik/uyumluluk denetimi (ayrı pilot).
- Çok dilli kayıt dosyalarının izlenen commit ile tekrarlanabilir build süreci.

## Güncel sunum kontrol geliştirmeleri

- Kullanıcı sunum adımlarını **1× / 1,5× / 2×** hızlarda oynatabilir. Hız değiştiğinde mevcut zamanlayıcı kapatılıp yalnız kullanıcı daha önce oynatmayı başlattıysa güvenli şekilde yeniden başlatılır.
- On dilde hareketi kapat/aç kontrolü ve ekrandaki kontrol düğmelerinin erişilebilir etiketleri bulunur.
- İşletim sisteminin `prefers-reduced-motion: reduce` ayarı önceliklidir. Bu durumda animasyon ve otomatik zamanlayıcı çalışmaz; kullanıcı isteğiyle yalnız tek adım ilerlenir.
- Animasyon ve hız ayarları **yalnızca anlatımı** etkiler; hikâyenin kurgu nedenlerini, rezervasyon karar kodlarını veya gerçek sistem durumunu değiştirmez.
- Mevcut konsept, gerçek Python otel karar motoru ve on modüllü üretim demosu ile henüz birleştirilmemiştir. Yayınlanan tamamlanmış özellik gibi gösterilmemelidir.
