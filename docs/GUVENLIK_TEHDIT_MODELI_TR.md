# Güvenlik tehdit modeli — KonaklamaFlow v0.3

## Sınırlar

Bu sürüm kişisel veriler içeren gerçek bir sistem değil; kurgusal örnek veriyi gösteren çevrimdışı frontend ve mevcut çekirdeğe bağlanan Python inceleme adaptörüdür. Her iki bileşen de ağ isteği yapmaz ve kaynak sistemlere yazmaz. Bu, bütün potansiyel güvenlik kusurlarının giderildiğini kanıtlamaz.

## Tehditler / varsayılan engeller

| Tehdit | Bu pakette alınan önlem | Üretim öncesi gerekli |
|---|---|---|
| Kişisel veri paylaşımı | Girdi allowlist; isim, kimlik no, telefon, e-posta, doküman alanı yasak; serbest metin özel istek yok | Entegrasyon veri minimizasyonu, DLP, KVKK değerlendirmesi |
| Gerçek misafire yanlış mesaj | Sadece sabit kurgusal taslak, gönderim aracı yok | Yetkili mesaj API'si, dil/güvenlik kontrolü ve insan onayı |
| Oda çatışması | Tarih aralığı, oda, kategori, kapasite, HK kontrolü | Etkin envanter transaction lock, gerçek PMS taze versiyonu |
| Yetkisiz check-in / KBS | Hiçbir gerçek işlem yazma aracı yok | Ayrı policy engine, kullanıcı MFA, denetlenebilir yetki |
| Ödeme tekrar çekimi | Ödeme API'si yok | PSP token, idempotency, reconciliation, zero PII logs |
| Prompt injection | LLM veya e-posta girişi yok | Tool response sandbox, explicit role/tool policy, tainted content handling |
| Frontend XSS | Dinamik metinler escape edilir; harici içerik yüklenmez, CSP ağ bağlantısını engeller | Framework tabanlı otomatik SAST, güvenli server headers |
| Kaynak koduna e-posta gömülmesi | Bu pakette gerçek geliştirici e-postası tutulmaz | Git noreply, commit hook, CI secret scan ve geçmiş doğrulaması |
| Eşzamanlı ajan | Gerçek ajan/komut yürütücüsü yok; aynı salt okunur referansın tekrar incelenmesi işlem tekrarı değildir | ACL, least privilege, per-property tenant isolation, kalıcı olay idempotency ve revizyon kontrolü |

## Kullanım uyarısı

Ciddi bir sistem olarak yayınlamadan önce bağımsız güvenlik denetimi, real-data threat model, log/gizlilik yönetimi, KVKK ve ilgili kimlik bildirim yükümlülüklerine uyum zorunludur.

## Rapor güncelliği ve güven sınırı

- Rapor özeti, hash veya AI onayı kullanıcı/servis kimliği doğrulamaz. Kaynak, kontrol saati ve property bağlamı güvenilir çağırandan gelmelidir. AI kendi raporunu veya kendi saatini vererek yetki kazanamaz.
- Kurgusal tarayıcı değişikliği gerçek yetki veya taze kural motoru sonucu değildir. UI raporu eskiyse bunu açıkça belirtmeli ve hazır kararını yeniden üretilmiş gibi göstermemelidir.
- Oda önerileri aynı kalışta birbirinin stoklarını tüketmelidir; pending blokaj, iptal-durum çelişkisi, aynı gün devir ve bilinmeyen kaynak ilişkileri güvenli incelemeye gitmelidir.
- Console/CLI hata mesajı, dosya yolu veya JSON parse istisnasıyla ham kişisel veri geri yazılmamalıdır. Şema dışı alanlar ve serbest metin talimatları AI görevine taşınmamalıdır.
- Kimlik alanlarının alfanümerik olması anonimliğin kanıtı değildir. Gerçek rezervasyon kodları bile yeniden kişiye bağlanabilir; kaynakta minimizasyon/pseudonimleştirme gerekir.
- Demo içindeki olay listesi tarayıcı belleğindedir; değiştirilemez audit, gerçek kullanıcı yetkisi veya kalıcı idempotency kanıtı sayılmaz.

Üretim mimarisinin açık kalan katmanları [Entegrasyon Sözleşmesi](ENTEGRASYON_SOZLESMESI_TR.md) içinde ayrı işaretlenmiştir. Otomatik testler, gizli veri imza taraması ve erişilebilirlik kontrolleri yalnızca kendi tanımlı senaryoları için kanıttır; bağımsız kapsamlı pentest veya WCAG sertifikasyonu değildir.
