# AI provider — görsel durum, teknik sözleşme ve sınırlar

## Durum modelinin tek doğrusu
- not_integrated: yalnızca planlandı; ağ çağrısı veya kimlik bilgisi yok.
- mock_demo: sabit örnek / deterministik açıklama; kamuya açık demoda tek etkin görsel “AI”.
- configured: yetkili özel backend yapılandırması var, ama bağlantı doğrulanmadı.
- connected_verified: yalnızca gerçek health/auth testi geçmiş ve yetkili ayrı ortamda bağlantı aktif.
- disabled: tenant veya politika tarafından kapalı.

Kamuya açık demoda configured/connected_verified gösterilmez. “Connected” kelimesi sırf marka/logoyu yerleştirmekle kazanılmaz.

## Sağlayıcı vitrini
- OpenAI API; Anthropic API; Google Gemini API; Azure OpenAI; Local/OpenAI-compatible self-hosted.
- Yan panelde sade metin adı + desteklenmesi hedeflenen yetenekler. Gerçek servis veya model, auth erişimi doğrulanmadıysa “Bağlı değil”.
- ChatGPT Business aboneliği OpenAI API organizasyonu değildir; kullanıcıya ayrı API faturalaması/ayrı izin, olası kredi avantajı ve kullanım limitleri açıklanır.
- Marka görselleri sadece lisans ve resmi kılavuza uygun doğrudan ilgili servis için gösterilebilir; partnerlik/endorsement ve yanıltıcı co-branding yok.
- Referans: https://openai.com/brand/ ; https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform ; https://www.anthropic.com/legal .

## Read-only çağrı portu
Girdi: canonical snapshot/report için güvenilir runtime tarafından verildiği doğrulanmış, minimize edilmiş reason codes ve sentetik görev özeti. Ham misafir adı, telefon, e-posta, belge numarası, ödeme kartı, özel serbest metin veya API token yok.
Çıktı: JSON Schema/strict typed model; request_id, provider_id, model_id, created_at, explanation, next_staff_step, no_execution=true, source_report_hash; string boyut sınırları ve redaction.
Dört yetenek: explain_decision, summarize_shift, draft_guest_message (gönderilmez), prepare_handoff_summary. Durum / karar / oda atama / ödeme / KBS / kimlik doğrulama değiştiren hiçbir fonksiyon yok.

## Örnek backend güvenlik iş akışı
1. İnsan/servis kimliğini backend doğrular. Modelden kimlik veya zaman alınmaz.
2. Yetki ve tesis kapsamı doğrulanır; girdi allowlist + upstream pseudonymization.
3. Trusted report güncellik kontrolü, version/correlation ve event invalidation.
4. Model çağrısı ancak ayrı opt-in env flag ve secrets vault ile; kısa timeout, bütçe, rate limiter, egress allowlist.
5. Yanıtı metin olarak escape et; aşırı iddia/hallucination guard, output schema reject; yetki verilmez.
6. Hata, timeout, stale report veya kota aşımında deterministik kural açıklaması fallback; hiçbir canlı işlem yok.
7. Loglara guest-data, prompt, API key veya rezervasyon referansı koyma; sadece anonim hata/metric.

## Yasak iddialar
- “Powered by ChatGPT Business” sadece Business üyeliği bulunmasıyla yazılamaz.
- OpenAI, Anthropic, Microsoft veya Google resmi ortağı gibi görünme.
- Gerçek API yoksa marka logolu “Live AI” göstergesi gösterme.
- “AI check-in yaptı”, “KBS tamamlandı”, “ödeme çekildi” gibi beyanlar demo için yasaktır.

## Test planı
- Provider mock vs disabled vs not_integrated görünüm.
- Provider outage, timeout, budget exceed, invalid structured output, stale source, prompt injection, XSS.
- Public demo uçtan uca zero network / zero secrets / zero PII.
- Hash/TTL yalnızca bütünlük/güncellik sinyalidir; auth olarak kabul edilmez.
- API erişimi ayrı onay ve gerçek maliyet sınırıyla değerlendirilir.