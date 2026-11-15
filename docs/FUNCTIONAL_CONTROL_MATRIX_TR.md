# KonaklamaFlow — 20 modülde tüm kontrollerin işlevselliği (#68)

## Ürün hedefi

Demo içinde görülen **her düğme, filtre, form ve menü anlamlı bir işe
yaramalı**. İşlemin sonucu sayfada görülebilmeli, geriye alınabilmeli
veya neden yapılamadığı açık şekilde açıklanmalı. Sırf tıklayınca toast
gösteren ama hiçbir değişiklik yapmayan sözde işlevler kabul edilmez.

Bu doküman, **tamamlandı** iddiası değil, işlevsellik için yürütülecek
kontrol envanterinin başlangıcıdır.

## Kapsam haritası

| Modüller | Beklenen temel davranış | Şu anki uygulama sınırı |
| --- | --- | --- |
| Genel bakış, gelişler, OTA | filtre, ayrıntı, eşleştirme incelemesi, senaryo | yalnız kurgusal veri |
| Oda planı, housekeeping, blokajlar | oda detayları, zaman aralıkları, durum kontrolü | doğrulanmamış boş oda satılamaz |
| Misafir deneyimi, misafirler | talepler, taslak metinler ve güvenli alan sınırları | gerçek kimlik girilmez |
| Görev merkezi, iş akışları, personel | simüle görev, adım, rol ve geriye alma | gerçek oturum/onay yok |
| Rezervasyonlar | çok odalı taslak ve doğrulama | gerçek rezervasyon oluşturulmaz |
| Folyo, acente, rapor, kurlar ve fatura | detay, kapsam ve filtre, kaynak/eksik veri açıklaması | gerçek tahsilat/fatura yok |
| Gelir, AI karar merkezi, entegrasyonlar | ölçüm, gerekçe, kurgusal zaman akışı, bağlantı sınırları | canlı model/API yok |
| Demirbaşlar | oda varlıkları ve bakım bağlamı | gerçek stok güncellemesi yok |

Ayrıca 20 sidebar düğmesi ve ortak araç çubuğunun tamamı; dil, tema,
sunum modu, hareketler, rapor indirme, sıfırlama; mobil/RTL/klavye
davranışları kapsam içindedir.

## Faz A — İlk somut düzeltme

- Kat hizmetlerinde **devre dışı duran "Teknik blokaj" düğmesi** artık
  ilgili kurgusal oda detayını açarak bakım/oda durumunu açıklıyor;
  bloke bir odayı serbest bırakmıyor veya oda durumunu değiştirmiyor.
- Rezervasyon taslakları artık form kapatıldıktan sonra aynı oturumun
  rezervasyon ekranında görünüyor; kullanıcı bu taslakları silebiliyor
  veya tüm demo durumunu sıfırlayabiliyor. Bu liste gerçek rezervasyon
  değil ve canonical/PMS verisini değiştirmiyor.
- "Oda ekle" artık formu baştan çizmek yerine yalnız yeni oda alanını
  ekliyor; yazılmış tarihler, taslak etiketi ve mevcut seçenekler
  kaybolmuyor. Hatalı tarih kontrolü de girilmiş değerleri silmeden
  uyarı veriyor.
- `tests/browser/test_functional_control_contract.py`, **20 modüle**
  gerçekten navigasyon yapıp içerik oluşmasını, etkin düğmelerin
  işlem adresi taşımasını, blokaj bilgisinin açılmasını ve temel
  filtre/form/iş akışı eylemlerini denetliyor.
- Python otoriter raporları, DOM navigasyonuyla sessizce değiştirilemez.
- Bu ilk aşama, **her alt kontrolde beklenen etkiyi henüz
  doğrulamıyor**; sonraki aşamalar sistematik olay/sonuç matrisi ve
  daha derin eylem regresyonları gerektirir.

## Kabul koşulları — Tüm hedefin tamamlanması

1. Her modüldeki **her etkin kontrol** için kaynağı, tetikleyicisi,
   beklenen sonuç, hata ve sıfırlama davranışı tanımlanmalı.
2. Playwright, gerçek düğme tıklamasıyla beklenen sonucu kontrol
   etmeli; yalnız `id` veya `data-*` bulunması yeterli kabul edilmez.
3. Kullanıcının yaptığını sandığı ama uygulamada yapılmayan işlem
   "başarılı" diye bildirilmez. Yetki/yasal veri/API gerekiyorsa
   açık engel ve mümkünse güvenli kurgusal önizleme sunulur.
4. Geçersiz kaynak, doluluk veya insan onayı gerektiren durumda
   sistem fail-closed davranır. Gerçek PMS/OTA/KBS/ödeme bağlantısı
   ve kimlik işleme yoktur.
5. 20 modülün tamamında kullanılabilir kontrollerin etkileri ve
   mobil/RTL/klavye/çevrimdışı sınırları test edilmeden
   **"bütün düğmeler çalışıyor" iddiası yapılmaz.**

Devam: [Issue #68](https://github.com/erenariel/konaklamaflow/issues/68).
