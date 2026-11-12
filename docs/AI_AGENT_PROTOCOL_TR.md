# İki AI asistanı için güvenli görev devri

**Güven sınırı:** Bu sürüm yalnızca rapor oluşturur. `agent_protocol.py` gerçek yetkilendirme, imzalı onay veya işlem yürütme sistemi değildir.

## Roller

- **Operasyon Hazırlama Asistanı (AI-1):** İzinli veri kaynağından kimliksiz operasyon özetini çıkarmak üzere ileride geliştirilecek adaptörü yönlendirir. Gerçek belgeleri diğer modellere iletmez.
- **İkinci İnceleme Asistanı (AI-2):** Kural motoru çıktısındaki engelleri açıklar, yapılacakları önceliklendirir, insan için Türkçe/İngilizce taslak oluşturur. *Check-in, ödeme, kayıt veya mesaj göndermez.*
- **Deterministik Kural Motoru:** Tarih, statü, rezervasyon çakışması, oda tipi, temizlik ve benzeri kontrol kararlarını tekrar üretilebilir biçimde hesaplar. AI'nın yalnızca serbest metin yanıtına güvenilmez.
- **Yetkili Personel / PMS:** Son onay, misafir kimliği, folyo/ödeme ve resmî bildirimlerin tek gerçek kaynağı.

## Protokol akışı

1. `plan_operations(...)` raporunu oluştur. `snapshot_sha256` mevcut girdi anlık görüntüsünü tanımlar.
2. `make_handoff(report, issued_at, 300)` yalnızca pseudonim rezervasyon kodu ve sebepleri içeren manifest üretir.
3. AI-2, `SUGGEST_RECEPTION_REVIEW` amacı dışında bir işlem önerirse `verify_suggestion` reddeder.
4. Kaynak değiştiğinde veya beş dakika geçtiğinde görev devri geçersizdir. Yeni anlık görüntü alınmalıdır.
5. Üretim ortamında ayrıca RBAC, MFA, sunucu imzaları, idempotency storage, denetlenebilir audit ve PMS tarafında işlem öncesi yeniden doğrulama şarttır; bu pakette bunlar **henüz yoktur**.

## İdempotency ve denetim tasarımı (gelecek sürüm)

`(property_id, source, reservation_ref, operation_kind, canonical_snapshot_hash)` tuple'ından kararlı talep kimliği üret. Üretim veri tabanında benzersiz constraint uygula. Aynı işlem tekrar gelirse önceki sonucu dön; sonradan tekrar ödeme/check-in yapma. Dış sisteme yazılamayan başarısız işlemler için güvenli durum, yeniden deneme ve olay günlüğü kullan. Olası race condition için güncel PMS revizyonu ile compare-and-swap gerektir.

## Önemli: Bu kodun *yapmadıkları*

- Şifre, erişim anahtarı, TCKN/pasaport, guest profile veya ödeme bilgisi almaz.
- Web sayfasına giriş yapmaz, rezervasyonu yeşile almaz, folyo veya KBS kaydı oluşturmaz.
- İkinci asistanı gerçekte çağırmaz; yalnızca görev sözleşmesi verir. Uygun AI sağlayıcısının bağlantısı ileride isteğe bağlı yapılabilir.
- Yetkili personelin varlığını veya KBS sonucunu kriptografik biçimde doğrulamaz.

Örnek Python:

```python
from konaklamaflow.operations import plan_operations
from konaklamaflow.agent_protocol import make_handoff
import json

source = json.load(open("examples/operations-demo.json", encoding="utf-8"))
report = plan_operations(source, "2026-11-12", "14:01")
manifest = make_handoff(report, "2026-11-12T11:01:00Z")
print(manifest["mode"])  # NO_EXECUTION_READ_ONLY
```
