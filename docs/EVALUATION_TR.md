# Sentetik operasyon değerlendirmesi

Issue #50 için eklenen bu araç, mevcut Python motorunun küçük ve sürüm kontrollü bir sentetik senaryo kümesindeki sonuçlarını ölçer. **Üretim doğrulaması, gerçek otel pilotu, model doğruluğu veya operasyonel fayda ölçümü değildir.** Sonuçlar `DRY_RUN_ONLY` kalır; hiçbir hazır durumu insan onayının yerini almaz.

`konaklamaflow/evaluation.py`, mevcut `experience_engine.evaluate` işlevini çağırır. Rezervasyon kurallarını yeniden uygulamaz, motoru veya demo verisini değiştirmez. PR #49'un AI açıklama sözleşmesinden bağımsızdır; AI sağlayıcısı veya model çağrısı içermez. README çalışmasıyla da çakışmamak için bu belgeye bağlantı `docs/TESTING.md` üzerinden verilir.

## Kaynak ve etiketlerin durumu

`evaluation/benchmark.json`, `synthetic-benchmark.v1` sözleşmesini kullanır. Her vaka için kategori, kapsam, değerlendirme durumu, kaynak anlık görüntüsü ve rezervasyon bazında şu etiketler açıkça yazılır:

- `expected_reason_codes`: Beklenen neden kodlarının tam kümesi.
- `expected_classification`: `blocked`, `review_ready` veya `other`.
- `human_approval_required`: Her durumda `true`.

Beklentiler mevcut motor çıktısından otomatik üretilmedi; operasyon kurallarına göre elle tanımlandı, sonra çıktıyla karşılaştırıldı. Etiket kaynağı `manual_rule_spec` olarak belirtilir. **Bağımsız otel uzmanı incelemesi henüz yapılmadı:** `independent_hotel_expert_review: pending`. Bu küme uzman tarafından doğrulanmış gerçek veri veya bağımsız doğruluk sertifikası olarak sunulmamalıdır. Issue'daki uzman incelemesi şartının bu kısmı insan değerlendirmesini bekler.

Kaynaklar `EVAL_SYNTHETIC` tesis kodunu ve `EVAL_` kimliklerini kullanır. Bu adlandırma bir test sınırıdır; özel veriyi anonimleştirdiğine dair garanti değildir. Gerçek misafir, personel, otel, rezervasyon referansı veya kimlik belgesi eklenmemelidir.

## Senaryo kapsamı

| Kategori | Ölçülen kapsam | Açık sınır |
|---|---|---|
| `duplicate_ota_reference` | Aynı kanalda yinelenen dış referans; iki rezervasyonda doğru neden kodu | Canlı OTA eşleştirmesi yapılmaz. |
| `room_overlap` | Aynı odaya çakışan iki tahsis; temiz negatif kontrol; aynı gün çıkış/giriş | `[check_in, check_out)` aralığı kullanılır; genel otel kapasite optimizasyonu ölçülmez. |
| `maintenance_overlap` | Konaklama gecesiyle çakışan bakım aralığı | Bir etiketsiz kontrol ayrıca `not_evaluated` durumundadır. |
| `cancelled_assigned` | İptal edilmiş kaydın oda tahsisini koruması | İptal veya oda serbest bırakma işlemi yürütülmez. |
| `same_day_source_conflict` | Giriş günü anlık görüntüsünde iptal olayı ile onaylı rezervasyon arasındaki durum çelişkisi | Zaman damgalı revizyon sıralaması ve aynı gün değişiklik geçmişi `unsupported`. |
| `split_stay_partial_cancellation` | Ölçülmüyor | Bölünmüş konaklama/kısmi iptalin üst rezervasyonla uzlaştırılması `unsupported`. |

Toplam 10 vakanın 7'si ölçülür, 2'si desteklenmez, 1'i etiketsizdir. Altı kategorinin beşinde en az bir ölçülen vaka vardır; bu, kategorinin bütün alt durumlarının desteklendiği anlamına gelmez. Desteklenmeyen vakalarda sahte motor çıktısı veya beklenen başarı oluşturulmaz.

## Skor birimi ve paydalar

Neden kodu için tek skor birimi **`(case_id, reservation_id, reason_code)`** üçlüsüdür. Bir kodun vaka içinde herhangi bir rezervasyonda görünmesi yeterli sayılmaz. Yanlış rezervasyona yazılan kod bir yanlış pozitif ve ilgili doğru rezervasyonda bir kaçırma yaratabilir.

`reason_code_universe`, mevcut motorun 28 elemanlı `BLOCKER_CODES` kümesine tam eşit olmalıdır. Bir rezervasyonda aynı kod bir kez sayılır. Bilinmeyen veya tekrarlanan kodlar reddedilir. Motorun kod sözlüğü değişirse fixture ve inceleme birlikte güncellenmelidir; skor evreni sessizce genişlemez.

| Ölçüt | Tanım |
|---|---|
| TP | Beklenen ve üretilen kodların kesişimi. |
| FP | Üretilen fakat beklenmeyen kodlar. |
| FN | Beklenen fakat üretilmeyen kodlar. |
| TN | Sabit kod evreninde ne beklenen ne de üretilen kodlar. |
| `precision` | `TP / (TP + FP)` |
| `recall` | `TP / (TP + FN)` |
| `false_positive_rate` | `FP / (FP + TN)` |
| `false_negative_rate` | `FN / (FN + TP)` |
| `exact_reservation_match_rate` | Kod kümesi, sınıflandırması ve insan sınırı birlikte eşleşen rezervasyon / etiketli rezervasyon. |
| `classification_match_rate` | Sınıflandırması eşleşen rezervasyon / etiketli rezervasyon. |
| `case_coverage` | Ölçülen vaka / tüm vaka; dışlananlar bu kapsam paydasında kalır. |
| `category_coverage` | En az bir ölçülen vakası olan kategori / altı istenen kategori. |

Kod sayıları tüm etiketli rezervasyonlardan toplanır; vaka başına yüzdelerin ortalaması alınmaz. `unsupported` ve `not_evaluated` vakaları TP/FP/FN/TN, sınıflandırma ve eşleşme paydalarından tamamen çıkarılır; dışlanma nedeni raporda korunur. TN sayısı seçilen 28 koddan güçlü biçimde etkilenir. Bu nedenle çok sayıda TN, otel operasyonlarının çoğunun doğru yönetildiğine kanıt değildir.

Her oran JSON içinde `numerator`, `denominator`, `value`, `undefined_reason` alanlarını taşır. Payda sıfırsa `value: null` ve `undefined_reason: zero_denominator` üretilir; `0%` veya `100%` uydurulmaz. Değerler 0–1 aralığında, altı ondalığa yuvarlanır. Vaka ancak bütün etiketleri tam eşleşirse geçer; toplam `passed` yalnız ölçülen vakaların tamamı geçerse `true` olur. Dışlanmış vakaların `passed` alanı `null` kalır.

## Yeniden üretim

Depo kökünde Python 3.11 veya üzeriyle, ek çalışma zamanı bağımlılığı olmadan:

```bash
python -m konaklamaflow.evaluation evaluation/benchmark.json --json-output /tmp/synthetic-evaluation.json --markdown-output /tmp/synthetic-evaluation.md
python -m unittest discover -s tests -p 'test_evaluation.py' -v
python -m unittest discover -s tests -v
python -m unittest discover -s tests/browser -v
```

Tarayıcı testlerinin kurulumunu [TESTING.md](TESTING.md) açıklar. Değerlendirme komutu ağ isteği, PMS/OTA/KBS/ödeme bağlantısı, AI çağrısı veya operasyonel işlem yapmaz; yalnız yerel JSON/Markdown rapor dosyalarını yazar. Çıktıların girdiyi veya birbirlerini ezmesine izin verilmez. Hata mesajları girdi değerlerini ve özel dosya yollarını ekrana taşımaz.

Çıkış kodları: `0` ölçülen etiketler eşleşti; `1` geçerli değerlendirmede etiket/sınıflandırma uyuşmazlığı; `2` bozuk girdi, güvenli olmayan çıktı yolu veya geçersiz motor sözleşmesi. Eksik rezervasyon etiketleri, bilinmeyen kodlar, yinelenen JSON alanları, bozuk kaynak veya değiştirilmiş insan onayı politikası başarı raporuna dönüştürülmez. Regresyon testlerinde kasıtlı yanlış tahminlerle FP/FN ve başarısızlık yolu da sınanır; temiz negatif vaka ise tek başına başarısızlık demek değildir.

İki rapor yazılmadan hazırlanır ve her dosya ayrı atomik değiştirilir; iki dosyayı kapsayan bir dosya sistemi işlemi garantisi yoktur. Son değiştirme sırasında disk hatası olursa yalnız bir dosya yenilenmiş olabilir. Bu durumda `2` çıkış kodunu esas alın ve komutu sorunu giderdikten sonra yeniden çalıştırın.

## Gerçek komut çıktısından örnek

Yukarıdaki değerlendirme komutunun mevcut fixture ile ürettiği örnek:

```text
SYNTHETIC BENCHMARK PASS: not production validation
evaluated_cases=7 / total_cases=10; labelled_reservations=10
reason_decisions=280; TP=12; FP=0; FN=0; TN=268
precision=12/12=1.0; recall=12/12=1.0
false_positive_rate=0/268=0.0; false_negative_rate=0/12=0.0
exact_reservation_match_rate=10/10=1.0
classification_match_rate=10/10=1.0
case_coverage=7/10=0.7; category_coverage=5/6=0.833333
human_override_rate=not_measured; processing_time=not_measured
```

Bu örnek yalnız küçük, elle tanımlanmış sentetik kümedeki eşleşmeyi gösterir; gerçek rezervasyon doğruluğu veya AI model performansı değildir. Yeni fixture veya motor değişikliklerinde komutu yeniden çalıştırın; bu metni güncel CI sonucu yerine kullanmayın.

## Rapor sözleşmesi, süre ve CI

JSON raporu `synthetic-evaluation-report.v1` sürümündedir. `counts`, `metrics`, `categories`, `cases`, `label_provenance`, `approval_policy` ve `fixture_sha256` birlikte izlenmelidir. Her rezervasyonda beklenen/gerçek kodlar, eksik/fazla kodlar, sınıflandırma eşleşmesi ve insan sınırı bulunur. Kaynak anlık görüntülerinin tamamı rapora kopyalanmaz.

`fixture_sha256`, anahtarları sıralanmış JSON içeriğini bağlar; boşluklardan etkilenmez, dizi sıralamasından etkilenir. Vaka/etiket ve kaynak koleksiyonlarının sırası değişse de skorlar eşdeğer kalmalıdır. Kaynak özeti farklıysa iki raporun tüm baytlarının aynı olması beklenmez.

`human_override_rate` gerçek onay olayı olmadığı için her zaman `not_measured` ve `null` kalır. Varsayılan çalıştırma süre iddiası üretmez. Komuta `--measure-time` eklenirse `perf_counter` ile yalnız yerel motor çağrılarının toplam saniyesi ölçülür; dosya okuma/yazma, ağ, PMS gecikmesi, insan incelemesi veya misafir bekleme süresi bu sayıya dahil değildir. Bu seçenek açıkken sürelerin tekrarlarda değişmesi normaldir.

GitHub Actions, Python 3.11/3.12/3.13 işlerinde aynı komutu çalıştırır. O çalıştırmada üretilen JSON ve Markdown dosyaları `synthetic-evaluation-<python>-<sha>` artifact'ine alınır; Markdown iş özetine de eklenir. Başarı ölçümü sabit bir örnek dosyadan okunmaz. İncelenen commit'in gerçek CI sonucu ve artifact'i esas alınmalıdır.

Bağımsız uzman etiket incelemesi, daha çeşitli negatif/kenar vakalar, sürümlü kaynak uzlaştırması ve gerçek izinli pilot ölçümü hâlâ ayrı işlerdir. Bu araç bu eksikleri kapatmış sayılmaz; `main` birleştirmesi, sürüm veya Pages yayını gerçekleştirmez.
