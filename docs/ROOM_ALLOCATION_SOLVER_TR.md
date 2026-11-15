# KonaklamaFlow — Sınırlı sentetik oda tahsis önerisi (#62)

**Durum:** Bağımsız Python araştırma prototipi. Bu modül mevcut
`experience_engine.evaluate()` kararlarını **değiştirmez**, otomatik oda
atamaz ve yayımlanmış HTML demosuna bağlanmaz. Gerçek tesis, PMS, KBS,
OTA, ödeme veya kullanıcı hesabı erişimi yoktur. Kaynak veride gerçek
misafir/kimlik bilgileri kullanılmamalıdır.

## Ne yapıyor?

`konaklamaflow.room_allocation_solver.propose_group(source)` en fazla
**4 konaklama / 18 aday oda / 100 mevcut hold** için deterministik,
bütçesi sınırlı bir **ortak öneri** üretir. Arama en fazla 20.000 durum
inceler; sınır aşılırsa kısmi plan vermek yerine
`manual_review_required` döner. Çıktı her durumda:

- `mode: DRY_RUN_ONLY`
- `human_approval_required: true`
- PMS, KBS, ödeme, mesaj ve oda durum değişikliği: **false**
- `status: proposed | no_solution | manual_review_required`
- `reason_codes` ve `search.states_explored` kanıtı

## Katı sentetik giriş sözleşmesi

`schema_version = allocation-synthetic.v1`,
`source_kind = fictional`. Başka üst seviye anahtar kabul edilmez.

- `rooms`: `id, category, capacity, bed, readiness, occupancy, maintenance`
  (bakım aralığı `start/end`).
- `stays`: `id, arrival, departure, category, persons, bed_request, status`.
- `holds`: `id, room_id, arrival, departure, status, release_confirmed`.

Oda kategorisi **birebir eşleşir**; otomatik upgrade yoktur. `bed_request`
(`none, twin, double, single`) zorunlu kısıttır. `flex` odaya `twin`
yerleşiminin yapılabileceği varsayılmaz. Fiziksel uygunluk için kaynak
`occupancy = verified_vacant` ve `readiness = inspected` demelidir.
Bu iki değer **canlı ve bağımsız doğrulanmış** anlamına gelmez.

Bakım ve oda tutma aralıkları giriş günü dahil, çıkış günü hariç
**[arrival, departure)** biçiminde değerlendirilir. `cancelled`,
`no_show` veya `checked_out` durumu tek başına odayı serbest bırakmaz:
`release_confirmed = true` açıkça sağlanmadıkça ilgili hold kalır.

## İşleme mantığı

1. Her konaklama için kategori, kapasite, yatak, bakım, hold ve
   hazır/boş sinyallerinden güvenli aday oda kümesi oluşturulur.
2. En az seçeneği bulunan konaklama önce çözülür. Aynı sayıda seçenek
   varsa zorunlu yatak talebine öncelik verilir.
3. Esnek konaklamada uygun double oda twin'e tercih edilir. Backtracking
   ile küçük gruba **birlikte uygulanabilir** plan aranır.
4. Bir odanın çakışmayan tarihlerde paylaşılması mümkündür, çakışan
   konaklamalarda mümkün değildir. Sınır aşılırsa kısmi öneri verilmez.

**Örnek:** T101 twin + D102 double; aynı tarihte esnek A ve kesin twin
isteyen B. Plan **A → D102, B → T101** şeklindedir. Bu, yüzeysel
açgözlü planlamanın twin odayı yanlışlıkla tüketmesi durumuna karşı
bir testtir. Her öneri **yetkili personel incelemesi** gerektirir.

Amaç fonksiyonu tanımlanmadığından **global optimum** iddiası yoktur.
Bu modül ayrıca gerçek konaklama, gelir, operasyon performansı veya
doğruluk düzeyi kanıtı sunmaz.

## Tekrar üretilebilir testler

```bash
python -m unittest discover -s tests -p 'test_room_allocation_solver.py' -v
python -m unittest discover -s tests -v
```

Bu geliştirmenin tamamlanması, gerçek PMS entegrasyonu veya otomatik
konaklama operasyonu için onay anlamına gelmez. İleride kanonik veri
modeline bağlanacaksa ayrı bir şema uyarlaması ve güvenlik incelemesi gerekir.
