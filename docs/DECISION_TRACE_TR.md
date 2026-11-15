# KonaklamaFlow — Sentetik karar izi gösterimi (Issue #52)

Bu çalışma `#5` açıklama sözleşmesini kullanarak kurallardan gelen **neden kodlarını**, `evidence_field_paths` alan yolu kanıtlarını, kaynak/rapor SHA-256 değerlerini ve **uydurma demo adımlarını** opak görev kimliklerine bağlar.

## Kullanım

Depo kökünde, Python 3.11+ ile:

```bash
python -m unittest discover -s tests -v
python -m konaklamaflow.trace_cli --output /tmp/trace.json
python -m konaklamaflow.trace_cli --verify /tmp/trace.json
```

Örnek kaynak `examples/fictional-hotel.json` dosyasındaki 18 odalı kurgusal tesistir. Komutların gerçek PMS/OTA/KBS/ödeme bağlantısı veya LLM çağrısı **yoktur**. Üretilen iz `DRY_RUN_ONLY` ve `SIMULATED_ONLY_NO_AUTHORIZATION_OR_WRITE` olarak işaretlidir. İşlem adları `review_queued`, `evidence_viewed` ve `handoff_suggested` olup hiçbirisi rezervasyon onaylamak veya yazma işlemi yapmak değildir.

## Nasıl çalışır?

1. Her başlatma sırasında gerçek `experience_engine.evaluate` kural motoru çalışır.
2. `build_explanations` kaynak ve raporun **tam olarak eşit** olduğunu doğrular.
3. Açıklama katmanındaki opak `task_id` ve tam gerekçe listesi kullanılır; gerçek misafir/oda/rezervasyon kimliği taşınmaz.
4. Her olay bir önceki olayın `event_hash` değerini `previous_hash` içinde saklar. JSON alanları deterministik biçimde hashlenir.
5. `verify_trace` sıra, hash, reason code, alan kanıtları, kaynak/rapor hashleri ve izinli demo rol/adım kombinasyonlarını kontrol eder. Tek olay silmek, değiştirmek veya başka göreve taşımak reddedilir.

## Güvenlik ve dürüstlük sınırları

**Bu bir gerçek audit trail / immutable log değildir.** Hashler bağımsız bir güven köküne bağlanmıyor. İz içeriğinin tamamını değiştirebilen bir saldırgan zincirin tamamını yeniden hesaplayabilir; güvenli haricî anchor, kurumsal imza, WORM saklama, sunucu tarafı erişim kontrolü ve kimlik doğrulama burada **yoktur**.

`simulated_role` bir kullanıcı hesabı, personel doğrulaması veya yetkilendirme değildir. `simulated_at` gerçek olay zamanı değildir; 12 Kasım 2026 tarihli kurgusal senaryo zamanıdır. Hashler de gerçek kaynak doğruluğunu veya üçüncü taraf verisinin güvenilirliğini kanıtlamaz.

Gerçek otellerde yasal/veri sorumluluğu, KVKK, RBAC/MFA, tenant ayrımı, idempotency, değiştirilemez kayıt altyapısı, haricî güvenilir zaman damgası ve bağımsız güvenlik incelemesi ayrı çalışmalar olarak **Issue #14** kapsamındadır. Canlı pilot, çalışan/onay kanıtı veya gerçek otel operasyon başarısı iddia edilmez.

Bu aşama sadece hatanın görünür hâle gelmesini ve bir kararın dayandığı **kural kanıtlarını** gösterir. İnsan onayı gerçek, yetkili PMS üzerinde ayrıca gerekecektir.
