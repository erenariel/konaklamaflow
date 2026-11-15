# Akıllı Oda Tahsis Merkezi — Kurgusal etkileşimli önizleme

Bu modül çevrimdışı KonaklamaFlow demosuna `allocation-lab.html`
adlı yeni bir sayfa ekler. **Henüz gerçek rezervasyona oda atamaz**,
dış servise bağlanmaz ve Python'ı tarayıcıda çalıştırmaz.

## Nasıl çalışır?

- `konaklamaflow.room_allocation_solver.propose_group` tek karar kaynağıdır.
- `scripts/render_allocation_lab.py` altı **önceden tanımlanmış, yalnız
  kurgusal** girdiyle modülü çalıştırır. Her çıktının durumunu, güvenlik
  sınırını ve yan etki bayraklarını kontrol edip sayfanın içinde sunar.
- `demo/allocation-lab.js` bu önceden hesaplanmış sonuçları gösterir.
  Yalnız senaryo seçme, **Önerileri göster**, **Kararın nedenlerini göster /
  gizle** ve **Sıfırla** kontrolleri vardır. Sonuç yeniden hesaplanmaz.
- Kaynak, oda/rezervasyon kartları ve sonuç gerekçeleri salt okunurdur.
  Bilinmeyen doluluk, bakımdaki oda ve iptal edilmiş ancak serbestliği
  teyit edilmemiş tutmalar **doğrulanmış müsaitlik sayılmaz**.
- İki örtüşmeyen tarihin aynı odayı kullanabildiği örnek de vardır.
  Önceki çıkış günü eski konaklamaya dahil değildir.

## Altı örnek
1. Twin yatak kıtlığı: A esnek → double, B zorunlu twin → twin.
2. Bakım: o tarihte uygun twin bulunamaz.
3. Doluluk bilinmiyor: personel incelemesi gerektirir.
4. İptal blokajı teyitsiz: personel incelemesi gerektirir.
5. Aynı oda için çakışan konaklamalar: ortak çözüm yoktur.
6. Çıkış günü tekrar kullanım: iki çakışmayan konaklamaya aynı oda önerilir.

## Sınırlar

Bu, gerçek otel verisinin simülasyonu değildir: oda kimlikleri T101/D102
gibi yapay örneklerdir. Kullanıcı kendi tarih/oda/misafir kombinasyonunu
girip Python algoritmasına yeni hesap yaptırmaz. HTML içinde yalnız
Python'dan *önceden hesaplanmış kurgusal* sonuç vardır. Tarayıcıda fetch,
canlı AI, veri kaydı veya servis bağlantısı yoktur. `DRY_RUN_ONLY` ve
`human_approval_required` korunur.

Önceki ana demo ve kaynak-bazlı karar paneli değişmeden kalır;
bu modüle ana demodan ve proje tanıtımından bağlantı verilir.
Açık PR incelemesi, tüm Python ve Playwright CI başarıları ve proje
sahibi onayı olmadan `main`'e alınmaz.

## Kontrol komutları

```sh
python -m unittest discover -s tests -p 'test_allocation_lab.py' -v
python -m unittest discover -s tests/browser -p 'test_allocation_lab.py' -v
python -m scripts.render_allocation_lab --output /tmp/kf-allocation.html
python -m scripts.render_allocation_lab --check /tmp/kf-allocation.html
python scripts/stage_demo_site.py --output /tmp/kf-allocation-site
python -m scripts.verify_release_readiness --site /tmp/kf-allocation-site
```
