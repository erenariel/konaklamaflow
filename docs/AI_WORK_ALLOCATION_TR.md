# KonaklamaFlow — Codex kotasını koruyan görev paylaşımı

**Çalışma kuralı: 15 Kasım 2026.** Eren'in önceliği, hızlı tükenen Codex kotasını
yalnızca diğer mevcut geliştirme araçlarıyla güvenli ve verimli şekilde
yapılamayan **karmaşık yazılım mimarisi** işlerine ayırmaktır.

Bu dosya kalıcı proje çalışma rehberidir. Bir aracı otomatik olarak
başlatmaz, kullanıcının ChatGPT/Codex kota durumunu sorgulamaz ve bağlantı
olmayan iki ajan arasında canlı koordinasyon varmış gibi davranmaz.

## Görev sahipliği

| Görev | Varsayılan sorumlu | Not |
| --- | --- | --- |
| README, sürüm/yayın açıklaması, çeviri ve teknik doküman | ChatGPT + GitHub | Gerektiğinde küçük, incelemeye açık PR |
| Mevcut kural motorunda sınırlı hata düzeltmesi, test, fixture, CI triage | ChatGPT + GitHub | Erişilebilen dosyalar ve test çıktılarıyla doğrula |
| PR bağımlılık analizi, küçük diff, güvenli teknik inceleme | ChatGPT + GitHub | PR'ları otomatik birleştirme veya yayımlama |
| Erişilebilirlik, küçük arayüz ekleri, veriyle tutarlı metinler | ChatGPT + GitHub | Var olan otoriter Python raporunu kullan; JS'de ikinci karar motoru yaratma |
| Çok odalı kısıt çözücüsü, kaynak semantiği/şema göçü, büyük mimari refaktör | **Codex** | Dar kapsamlı Issue + ayrı branch + PR; kotayı koru |
| Tasarım referansları, GIF, tanıtım görselleri | ChatGPT ve uygun tasarım aracı | Gereksiz kod ajanı oturumu açma |
| Son birleştirme/dağıtım kararı | Proje sahibi ve repo koruma kuralları | Tam yeşil CI ve bağımlılık çözümü gerekir |

## Codex görevine başlamadan önce

1. **Önce ChatGPT aracılığıyla yapılabiliyor mu?** Evetse Codex çağırma.
2. Görev daha önce açık PR/Issue'da çözülmüş mü? Tamamlanan işi yeniden yaptırma.
3. **Bir Codex oturumu = bir dar kapsamlı konu.** İlk mesajda hedef,
   dosyalar, kabul testleri, dokunulmaması gereken dosyalar, stop koşulu ver.
4. Büyük tek HTML dosyasını, medya arşivini ve bütün repo geçmişini gereksiz
   okumaktan kaçın; yalnız ilgili Python modülleriyle başla.
5. Hedeflenen tekil testleri çalıştır; tam Python suite'i tamamlanan değişiklik
   üzerinde bir kez çalıştır. GitHub Actions browser paketleri ayrı çalışabilir.
6. Kapsamı aşan ve güvenli çözülemeyen noktada görevi durdur, yeni koda
   atlamadan teknik engeli raporla.
7. **Main'e otomatik merge/force-push/Pages deploy yok.**
   Gerçek rezervasyon, kimlik bilgisi, PMS/KBS/OTA/ödeme işlemi yok.

## Açık Codex adayı

- [#62 — sentetik, sınırlı global oda tahsis çözücüsü](https://github.com/erenariel/konaklamaflow/issues/62):
  kapsam daraltılmış birinci aşama, #11 / #1 ile ilişkili.
  **Codex oturumu kendiliğinden başlamaz.** Eren'in Codex ekranından
  #62'yi vererek başlatması gerekir.

## İkişer ikişer çalışma düzeni

ChatGPT uygun olduğunda iki bağımsız, küçük görevi aynı çalışma turunda
ele alabilir. Bağımlı PR'ların birleştirilmesi ise **sıralı** yapılır.
Örnek bağımlılıklar: #51 → #58 ve #53 → #59; #55 ve #61 arayüz/yayın
dosyalarıyla çakışma incelemesi gerekebilir. Görevlerin bir PR'da açık olması,
zaten yayımlandıkları veya canlı ürüne bağlandıkları anlamına gelmez.

## İlerleme raporu

Her iş için **Issue/PR URL'si, durum, test sonucu, kalan engel** verilir.
Teknik başarı ile saha doğruluğunu ayır:
kurgusal test, gerçek otel performansı değildir. Kod üretimi ve yorum tek
başına kullanıcı verisi işleme yetkisi değildir.

**Eren'in temel tercihi:** Codex kotasının çabuk tükenmesi yüzünden, onun
yapmasını gerektirmeyen hiçbir işi Codex'e yönlendirme.
