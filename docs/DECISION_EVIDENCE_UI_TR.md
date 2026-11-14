# Karar kanıt yolu — çevrimdışı UI (Issue #54)

Bu modül `demo/v04-integrated-preview.html` dosyasındaki mevcut kurgusal
`INITIAL_EVALUATION` Python raporunu ve Python `explainability.EVIDENCE` alan yolu
sözlüğünü kullanarak seçili rezervasyon için dört aşamayı gösterir:

1. Kurgusal kaynak anlık görüntüsünün SHA-256 referansı.
2. Yetkili kurallar motorunun ürettiği opak görev kimliği ve **tam** neden kodları.
3. Nedenlerle eşleşen güvenli **alan isimleri** (misafir değerleri değil).
4. Gerçek işlem yapılmadığını ve personel onayı sınırını belirten uyarı.

Bu görünüm **PR #53'ün hash-zincirli olay/audit günlüğünü göstermiyor**.
Çevrimdışı HTML, geçmişte gerçekten işlem yapıldığını ya da personelin
kanıtı görüntülediğini ispatlamaz. Kaynak zaman damgası ve üçüncü taraf
gerçekliği bağımsız doğrulanmadı. `source_bound` yalnızca HTML'de gömülü
rapor/sözlük bağının mevcut SHA işaretiyle eşleştiği anlamına gelir;
kimlik doğrulama veya kriptografik tarayıcı doğrulaması değildir.

`reportStale` işaretlendiğinde, seçili görev artık yoksa, izinli neden/kanıt
sözlüğü eksikse veya otomatik onay sınırı değiştirilmişse detaylar gösterilmez.
Yeni işlem oluşturulmaz. DOM metni `textContent` ile yazılır; istek, veri
yüklemesi, kayıt depolaması ve canlı API yoktur.

## Test
```bash
python scripts/generate_canonical_demo.py --check
python -m unittest discover -s tests -v
python -m unittest discover -s tests/browser -v
node --check demo/decision-evidence-ui.js
```

UI 10 dilde **taslak** arayüz metni gösterir; profesyonel çeviri kontrolü
yapılmamıştır. Basit bakım ve karar görüntüleme işlevi sunar; gerçek PMS
audit/approval iş akışı sağlamaz.
