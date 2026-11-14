# KonaklamaFlow — AI-ready altyapı (1. aşama)

**Durum: Sağlayıcı bağımsız, çevrimdışı altyapı. Henüz gerçek yapay zekâ, PMS entegrasyonu, kimlik doğrulama veya canlı otomasyon yoktur.**

## Ne yaptık?

KonaklamaFlow'da rezervasyon çakışması, oda uygunluğu, teknik blokaj, temizlik ve personel inceleme koşullarını **Python deterministik kural motoru** kontrol eder. Görseldeki "AI Senaryosunu Oynat" bölümü gerçek bir yapay zekâ çağrısı değildir; önceden hazırlanmış örnek verilerin **animasyonlu simülasyonudur**.

Yeni ai_explanation.py modülü ileride Grok, Claude, OpenAI veya yerel bir dil modelinin güvenli şekilde eklenebilmesi için **dar bir açıklama sözleşmesi** sağlar. Bu modül hiçbir sağlayıcıya bağlanmaz.

**Güven sınırı:**
1. Yetkili yerel ortam, önceden kurgulanmış veya uygun şekilde asgariye indirilmiş rezervasyon snapshot'ını değerlendirir.
2. suite_agent_protocol yalnız **opak görev referansı, durum ve motor neden kodları** üretir.
3. prepare_explanation_request tek bir görev için minimum bilgileri içeren isteği hazırlar. **Orijinal snapshot ve güvenilir manifest modele gönderilmez.**
4. Bir model daha sonra bağlanırsa yalnız kontrol edilebilir biçimde bir açıklama metni ve izinli kontrol listesi kodları önerebilir.
5. validate_explanation_response aynı kaynağı güvenilir yerel çalışma ortamında yeniden değerlendirir; eski/bozulmuş snapshot, değiştirilmiş neden kodu, fazladan eylem ve onay alanlarını reddeder.
6. Dönen çıktı MODEL_TEXT_UNVERIFIED statüsündedir. Kural motorunun sonucu ve yetkili personel kontrolü üstün tutulur.

## Yalnızca kurgusal veri ile örnek

~~~python
import json
from konaklamaflow.ai_explanation import (
    prepare_explanation_request,
    validate_explanation_response,
)

with open("examples/fictional-hotel.json", encoding="utf-8") as source:
    snapshot = json.load(source)

# Bu zamanlar demo örneğidir; canlı erişim yetkisi değildir.
manifest, request = prepare_explanation_request(
    snapshot, "2026-11-12T11:00:00Z"
)

# Gerçek sağlayıcı çağrısı yok: yanıt yerel test için elle yazılır.
example_response = {
    key: request[key]
    for key in (
        "task_id", "intent", "snapshot_sha256", "report_sha256", "reason_codes"
    )
}
example_response["summary"] = "Kurgusal kayıt personel incelemesi gerektirir."
example_response["checklist"] = [
    "VERIFY_SOURCE_RECORD",
    "ESCALATE_TO_AUTHORIZED_STAFF",
]

result = validate_explanation_response(
    manifest,
    example_response,
    "2026-11-12T11:01:00Z",
    current_snapshot=snapshot,
)
assert result["operational_authorization"] is False
~~~

Modelden gelen özet **doğrulanmış gerçek bilgi değildir**. İleride arayüzde sabit bir güvenlik uyarısı ile ve yalnız düz metin olarak (HTML innerHTML değil, textContent) gösterilmelidir. Bu doğrulama semantik doğruluk garantisi vermez.

## Kademeli geliştirme planı

**1 — Bu aşama (kod ve test):** Sınırlı açıklama kontratı; süre ve içerik bütünlüğü kontrolü; şema dışı alan ve yazma komutlarını reddetme; model çağrısı yok.

**2 — Yerel kurgusal veri girişi:** Bağımsız masaüstü test ortamında sahte PHOBS/PMS örnekleri için JSON şema sürümü, tekrar eden kayıt kontrolü ve kaynak güncelliği. GitHub Pages'te canlı misafir verisi kullanılmaz.

**3 — İsteğe bağlı model adaptörü:** Yalnız kurgusal test verisiyle, kapalı varsayılanlı ve açıkça yetkilendirilmiş bir sağlayıcı veya yerel model. API anahtarı frontend, GitHub deposu veya loglara konmaz. Maliyet, kota, gizlilik, hız ve hata senaryoları sınanır.

**4 — Gerçek pilot için ön koşullar:** Tesisin yazılı izni, tedarikçi şartları, KVKK ve erişim/gizlilik değerlendirmesi; veri minimizasyonu; yerel veya korumalı sunucu ortamı; operatör hesapları ve audit. Grokbot'un PMS ekranlarını görebilmesi tek başına aktarma izni değildir. Gerçek PMS, ödeme ve KBS işlemleri yine bu modülün kapsamı dışındadır.

İlgili belgeler: AI_AGENT_PROTOCOL_TR.md, ARCHITECTURE.md, GUVENLIK_TEHDIT_MODELI_TR.md.
