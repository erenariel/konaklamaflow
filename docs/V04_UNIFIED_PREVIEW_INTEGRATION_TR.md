# v0.4 Birleşik Otel Workbench Önizlemesi — Entegrasyon Notları

**Durum:** Çalışan **sentetik/çevrimdışı, ayrı taslak** ürün önizlemesi. GitHub Pages üretim demosu ve `main` üzerinde değişiklik yok. Görünen AI açıklaması bir modelden alınmaz; sabit kural etiketleridir. Kaynak PMS bağlantısı, ödeme, resmî KBS bildirimi, kimlik verisi veya gerçek rezervasyon işlemi yoktur.

## Nasıl açılır?

`demo/v04-integrated-preview.html` dosyasını yerel tarayıcıda aç. Hiçbir web sunucusu, API anahtarı, Codex veya paket kurulumu gerekmiyor. GitHub dosya görüntüleyicisi HTML'yi çalıştırmaz; dosyanın **ham hâlini indirip yerel olarak aç**.

## Gerçekten entegre edilenler

- PR #18'de doğrulanan **10 modüllü v0.3 çalışma arayüzü**, sunum modu, Light/Dark/Night Audit tema kontrolü, orijinal dört demo hikâyesi **aynen korunur**.
- Aynı sayfada ikinci bir **Küresel Karar Açıklama Merkezi** bölümü görünür. Bu bölüm **mevcut `INITIAL_EVALUATION` Python raporundan** rezervasyon durumlarını ve blocker kodlarını okur; yeni bir karar motoru çalıştırmaz.
- TR, EN, FR, EL, HE, AR, DE, RU, ES, UK dillerinde v0.3'ün **26 blocker kodunun tamamı** ve temel personel güvenlik uyarıları.
- Kanıt paneli `konaklamaflow/explainability.py` içindeki **allowlist kanıt alan adlarını** gösterir. Doğrudan gerçek/veri alanı **değerleri** veya doğrulanmış bir canlı PMS kanıtı göstermez.
- Açıklama metinleri `konaklamaflow/reason_i18n.py` çeviri kataloğundan alınmış, yerel statik bir kopyadır; yeni dil desteği uydurulmaz.
- OpenAI API, Anthropic API, Google Gemini API, Azure OpenAI ve yerel model sağlayıcıları sadece isim olarak görünür; **bağlı değil**. AI açıklaması ise blocker metinlerinden üretilmiş **deterministik offline açıklama**dır.
- Arapça/İbranice bölüm içinde RTL; kod ve alan adları bidi-safe soldan sağa. Çalışma uygulamasının geri kalanı henüz tamamen yerelleştirilmiş değildir.
- Orijinal oda temizliği/görev simülasyonu raporu geçersiz kıldığında, çok dilli paneldeki önceki kararlar da otomatik **kilitlenir**. Varsayılan “Demoyu sıfırla” akışı paneli yeniden kullanılabilir hâle getirir.
- Kontrollerin ayarları bellekte kalır; kalıcı kullanıcı takibi/telemetri yok.

## Neden ayrı dosya?

Mevcut `demo/hotel-suite.html` dosyası PR #18'de gerçek Chromium GIF'ine ve manifest hash'ine bağlıdır. O dosyayı burada değiştirip eski GIF hash'ini sahte biçimde güncellemek veya doğrulama testini devre dışı bırakmak güvenlik/ürün kalitesi açısından doğru olmaz. Bu nedenle v0.4 **ayrı bir HTML dosyasıdır**; orijinal demo, onun kayıtları, önceki tarayıcı testleri ve GitHub Pages tasarımı olduğu gibi kalır.

## Kaynak ve kapsam sınırları

- Rapora bağlılık: `INITIAL_EVALUATION.mode == DRY_RUN_ONLY`, `snapshot_sha256` kaydı, `human_approval_required` bayrakları, `reportStale` ve sabit blocker listesi üzerinden doğrulanır.
- Tarayıcıdaki SHA kaydı kimlik doğrulaması, canlı veri kökeni veya üretim güvenlik sınırı **değildir**. Gerçek PMS verileri için yetkili, server-side imzalı provenance ve operatör yetkisi ayrıca gereklidir.
- Paneldeki dil çevirileri **insan dil uzmanı onaylı değil**; başlıkta “Çeviri taslağı” ibaresi bilerek bulunur. 10 modüllü geri kalan ekran Türkçe kalır.
- Bu PR, #5/#19/#7/#8'in bütün işlerini kapatmaz; özellikle sürümlü API, tam i18n, WCAG 2.2 AA, native QA ve gerçek PMS yetkisi tamamlanmış sayılmaz.
- Preview, bir GitHub Pages deploy'u veya canlı uygulama sürümü değildir.

## Testler

```sh
python -m unittest discover -s tests/browser -v
python -m unittest discover -s tests -v
python scripts/generate_suite_demo.py --check
```

`tests/browser/test_v04_integrated_preview.py` şunları kontrol eder: 10 modül korunması, 10 dil × kural metni, Python raporu ve snapshot SHA eşitliği, tüm blokaj gerekçelerinin kaynak alanları, provider durumlarının bağlı değil olması, rapor invalidation/reset, tema/sunum ve mobil no-overflow, zero network.

Entegrasyon ilerletilirken bu ayrı sayfayı resmi ürüne birleştirmek, yeni medya kaydetmek veya `main`e merge etmek için insan incelemesi gerekir.
