# Kamuya açık ürün araştırması — 12 Kasım 2026

Bu belge, erişilebilir resmî ürün açıklamaları ve yardım/kullanım kılavuzlarında **belgelenen** iş akışlarını değerlendirir. Ürünlere giriş yapılmadı; API, güvenlik, erişilebilirlik veya üretim davranışı test edilmiş sayılmaz. Ekran görüntüsü, marka varlığı, HTML/CSS, özel kod veya kılavuz metni kopyalanmadı. KonaklamaFlow bağımsızdır; üreticilerle ortaklık, sertifikasyon veya hazır entegrasyon iddiası yoktur.

## Doğrulanan ürün işlevleri ve çıkarım

| Kaynak | Resmî belgede görülen iş akışı | KonaklamaFlow için tasarım çıkarımı |
|---|---|---|
| ElektraWeb [Online Check-in Listesi](https://yardim.elektraweb.com/crm/online-check-in-listesi) | Online doldurulan girişin ön büro onayıyla tamamlanması | Girdi sinyali, yetkili personel işleminin yerine geçmemeli; ön hazırlık ile tamamlanmış giriş ayrı olmalı. |
| ElektraWeb [HK Oda İşlemleri](https://yardim.elektraweb.com/kat-hizmetleri/hk-oda-islemleri) | Temizlik/onay ve OOO/OOS durumları, teknik servis bekleme, oda durum uyuşmazlıkları | “Temiz” ve “kontrol edilmiş” farklı statüler olmalı; teknik bloke veya belirsiz oda teslim için hazır sayılmamalı. |
| Sistem Otel [Ön Büro kılavuzu](https://sistemotel.gitbook.io/sistem-otel-kullanim-klavuzu/sistem_otel_programi_folyo_islemleri) | Oda planı, folyo borç/ödeme, checkout/fatura ve kasa başlıkları | Görsel plan ile finans incelemesi ayrılmalı; örnek fiyat toplamı gerçek tahsilat veya muhasebe sonucu diye sunulmamalı. |
| Sistem Otel [Oda Bakım kılavuzu](https://sistemotel.gitbook.io/sistem-otel-kullanim-klavuzu/sistem_otel_programi_oda_bakim) | HK başlangıç/bitiş bildirimi, housekeeper uyuşmazlık raporu, teknik OOO/OOS iş emri | Departman görevleriyle oda hazırlığı birlikte gösterilmeli; bir görev tamamlandı diye envanter kendiliğinden açılmamalı. |
| Sistem Otel [resmî ürün açıklaması](https://www.sistemotel.com/otel-programi) | Kaynak akışı, oda blokajı, rol yetkileri, hareket logu ve gün sonu | Kaynak revizyonu, izlenebilirlik ve yetki sınırı gelecekteki adaptör sözleşmesinin parçası olmalı. |
| Sedna HOTEL [Kod Yazılım ürün sayfası](https://kod.com.tr/Product/SednaHotel) | Ön büro yetkilendirmesi/log takibi, folyo/oda blokajı ve mobil housekeeping iş takibi | Ortak bir operasyon kuyruğu oluşturulmalı; işlemi kimin, hangi kaynak revizyonunda değerlendirdiği görünür olmalı. |

Tablonun son sütunu bağımsız tasarım yorumudur; üreticilerin KonaklamaFlow'u desteklediği anlamına gelmez. Sedna için bu incelemede eksiksiz ve güncel bir açık kullanım kılavuzu doğrulanmadı. Ürün sayfasındaki güvenlik, hız veya müşteri başarı ifadeleri bağımsız kanıt olarak alınmadı.

## Mevcut uygulama ile boşluklar

| Alan | v0.3 entegrasyonunun kapsamı | Sonraki geliştirme / üretim öncesi açık |
|---|---|---|
| Rezervasyon eşleştirme | Kurgusal Booking.com, Expedia, Trip.com/Ctrip ve diğer kanal etiketleri; kimlik ve alan tutarlılığı incelemesi | Yetkili kaynak adaptörü, imzalı olay, revizyon sıralama, rate-plan/çoklu oda sözleşmesi |
| Check-in hazırlığı | v0.2 deterministik çekirdeğe bağlanan şema adaptörü; blokaj ve insan incelemesi | Gerçek kaynakta kimlik, ödeme ve resmî durum doğrulaması; ön hazırlık giriş tamamlamak değildir |
| Oda önerisi | Kategori, kapasite, yatak, hazırlık ve kalış aralığına göre güvenli öneri | Global optimizasyon, çoklu oda/grup, çocuk kapasitesi, sözleşmeli yükseltme ve tesis politikaları |
| Housekeeping / teknik servis | Kurgusal oda ve iş listesi; yerel görsel simülasyon | Personel yetkisi, atama, gerçek oda revizyonu, denetlenebilir tamamlanma ve taze rapor |
| Misafir iletişimi | Sabit kurallı, gönderilmeyen örnek mesaj taslağı | Gönderim izni, dil/vaat kontrolü, yetkili mesaj sağlayıcısı |
| Gelir / folyo / gece audit | Kurgusal tutarların sınırlı incelemesi ve açık sınırları | Gerçek folyo kalemleri, tahsilat mutabakatı, günlük gelir tanımı ve ayrı finans yetkileri |
| İki AI asistanı | Salt okunur açıklama sözleşmesi; gerçek model çağrısı yok | Güvenilir sunucu kimliği, tool policy, yetkili insan onayı, idempotency ve kalıcı audit |

Bu boşluklar tamamlanmış özellik olarak pazarlanmaz. Demodaki ekran sayısı, büyük otel ölçeği veya gerçek operasyon yararı için ölçüm değildir.

## OTA erişimi hakkında doğrulanan sınırlar

[Booking.com Connectivity belgeleri](https://developers.booking.com/connectivity/docs), bağlantı partnerleri için rezervasyon, fiyat ve müsaitlik işlevlerini ve onboarding gerekliliklerini açıklar. Belgenin açık olması erişim anahtarı veya bağlantı hakkı vermez. Bu projede bu API'lere bağlantı bulunmaz; yeni partner kabulünün durumu hakkında doğrulanmamış bir iddia yapılmaz.

[Expedia Group Connectivity Hub](https://developers.expediagroup.com/supply/lodging), bağlantı sürecinde başvuru, lisans/PCI değerlendirmesi ve test aşamalarını anlatır. İnceleme tarihinde tekil tesislerden doğrudan API bağlantısı kabul etmediğini belirtir. Bu durum gelecekte değişebilir; gerçek adaptör öncesinde sağlayıcıyla yeniden doğrulanmalıdır.

[Trip.com Open Platform](https://connect.trip.com/) gelecekte başvurulabilecek resmî bağlantı noktasıdır. Bu çalışma, Trip.com/Ctrip API yetkisi, sertifikasyonu veya doküman uyumluluğunu doğrulamış değildir; mevcut `trip` kanalı yalnızca kurgusal örnek veri etiketidir.

Gerçek rezervasyon değiştirme, check-in, tahsilat, KBS veya kimlik belgesi işleme etkinleştirilmez. Olası gelecek bağlantı için hem otel hem sağlayıcı yetkisi, veri minimizasyonu, güvenlik ve hukuk değerlendirmesi gerekir. Bu belge hukuki uygunluk görüşü veya sertifika değildir.
