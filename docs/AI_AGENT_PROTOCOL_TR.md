# İki AI asistanı için güvenli görev devri

Bu paket yalnızca salt okunur inceleme referansı üretir. Gerçek AI sağlayıcısı, yetkilendirme sunucusu, imzalı onay veya işlem yürütücüsü yoktur. İkinci AI'nın verdiği metin, kimlik/check-in/ödeme/KBS yetkisi sayılmaz.

1. Güvenilir çağıran, kaynaktan tutarlı ve önceden pseudonimleştirilmiş anlık görüntü alır; `plan_operations` ile rapor üretir.
2. `make_handoff(report, issued_at, 300)` doğrulanmış rapordan 30–600 saniyelik manifest oluşturur. Manifestte yalnızca opak görev ID'si, durum ve izinli neden kodları bulunur; tesis, rezervasyon/kanal/oda referansları ve serbest metin diğer AI'ya gönderilmez.
3. AI yanıtı yalnızca `task_id`, `intent`, `snapshot_sha256`, `report_sha256` içerebilir. Tek amaç `SUGGEST_RECEPTION_REVIEW` olur; bilinmeyen alan, araç çağrısı veya yazma amacı reddedilir.
4. Güvenilir çağıran kaynak durumunu tekrar okuyup güncel raporu hesaplar. `verify_suggestion(manifest, suggestion, checked_at, current_review=fresh_report)` hem manifesti hem yanıtı bu raporla karşılaştırır. Kaynak, tesis, değerlendirme saati veya görev kapsamı değişirse eski referans reddedilir.
5. Saat, güncel rapor ve saklanan manifest AI'dan veya istemcinin serbest alanlarından alınamaz. Hash ve TTL kimlik doğrulama değildir; gerçek kaynak erişimi ve operatör yetkisi bu pakette doğrulanmaz.

```python
from konaklamaflow.operations import plan_operations
from konaklamaflow.agent_protocol import make_handoff, verify_suggestion

report = plan_operations(trusted_snapshot, "2026-11-12", "14:01")
manifest = make_handoff(report, "2026-11-12T11:01:00Z")
# trusted_snapshot/fresh_snapshot örnekte yer tutucudur; gerçek veri/kimlik içermez.
fresh_report = plan_operations(fresh_snapshot, "2026-11-12", "14:01")
valid_reference = verify_suggestion(
    manifest, ai_suggestion, "2026-11-12T11:02:00Z", current_review=fresh_report
)
# True yalnızca açıklama referansının geçerli olduğunu belirtir; işlem onayı değildir.
```

Aynı geçerli açıklama tekrar doğrulanabilir. İşlem yürütülmediğinden kalıcı idempotency kaydı, imzalı işlem günlüğü veya ödeme tekrar koruması uygulandığı iddia edilmez. Gelecekteki izinli entegrasyon ayrıca sunucu tarafı RBAC/MFA, property/tenant izolasyonu, kaynak revizyonu ile compare-and-swap, benzersiz idempotency kaydı, yetkili insan onayı, korumalı audit ve belirsiz sonuç prosedürü gerektirir. Misafir notu, sağlayıcı alanı ve model yanıtları güvenilmeyen veridir; talimat veya yetki kaynağı değildir.
