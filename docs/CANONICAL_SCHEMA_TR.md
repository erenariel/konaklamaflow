# Ortak kurgusal rezervasyon modeli — Issue #35

Birleşik demonun tek kaynağı `examples/canonical-hotel.json` dosyasıdır
(`canonical-hotel.v1`). Bu, açıkça yazılmış yeni bir **kurgusal senaryodur**;
eski KFD finans kayıtlarının KF kayıtlarına taşındığı veya PMS'den alındığı
iddia edilmez. Kimlik/iletişim alanları yalnız `null` kabul edilir. Görüntü
etiketleri kurgusaldır; doğrulayıcı anonimleştirme aracı değildir.

## Kimlikler ve ilişkiler

| Varlık | Bağlantı |
| --- | --- |
| Tesis / senaryo | `property_id`, `scenario_id`, `as_of`, `at_time` |
| Rezervasyon | Sabit `id`; açık `room_stay_ids`, `guest_ids`, `agency_id` |
| Oda konaklaması | Kendi kimliği; `reservation_id`, `room_id`, tarih, kişi, yatak, fiyat |
| Misafir | Kurgusal kimlik ve etiket; kimlik/iletişim alanları `null` |
| OTA / PMS referansı | Tür + sağlayıcı + tesis + dış kimlik; canlı bağlantı değildir |
| Folyo | `reservation_id` + `room_stay_id` + `room_id` + para birimi |
| Hareket | Açık posting/payment kimliği, Decimal tutar, tarih ve kaynak folyo |
| Oda blokajı | Kimlik, oda, başlangıç/bitiş, tür ve durum |
| Görev | Oda ve/veya rezervasyon ilişkisi; birlikte verilirse uyumlu olmalı |
| Rapor | 32 sabit kod; kaynak kapsamı, durum ve kanonik SHA-256 |

Sıra, benzer numara veya isim üzerinden eşleştirme yapılmaz. Kopuk ilişkiler,
yinelenen kimlikler ve yanlış folyo/oda/para birimi bağları üretimi engeller.
Operasyonel hatalar (çakışma, temizlik, twin, iptal sonrası fiziksel hold)
saklanmaz; mevcut Python motoruna inceleme için iletilir. Kaynak rezervasyon
durumları aynen korunur; `pending` veya `no_show` başka duruma çevrilmez.

## Üretim ve doğrulama

`canonical.py` şema ve projeksiyonları, `canonical_reporting.py` mevcut Decimal
hesaplayıcısına bağlı raporları, `canonical_presentation.py` kimlik bağlarını
ve sunum verisini üretir. JavaScript sonuçları gösterir; ikinci karar motoru
veya yetkili muhasebe sistemi değildir.

```bash
python scripts/generate_canonical_demo.py
python scripts/generate_canonical_demo.py --check
python scripts/generate_suite_demo.py --screenshots
python scripts/capture_previews.py
python scripts/record_demo_tour.py
python scripts/record_demo_tour.py --showcase all
python -m unittest discover -s tests -v
python -m unittest discover -s tests/browser -v
```

Dört `examples/canonical-*.json` projeksiyonu, birleşik HTML, oda workbench'i
ve global sunum aynı kaynağa bağlıdır. Eski `fictional-hotel.json` ve
`hotel-operations-fictional.json` bağımsız API örnekleri olarak korunur;
birleşik demonun ikinci kaynağı olmaz. Özgün CLI/report viewer örnekleri de
ayrı tarihsel örneklerdir.

## Finans ve gezinme

Senaryo 12 KF rezervasyonu, 18 oda, 27 kurgusal misafir ve yalnız üç açık
folyo içerir: KF1001, KF1004, KF1007. Açık oda hareketlerinin toplamı
316.50 EUR'dur; ödeme kaydı yoktur. Teklif tutarı tahsilat, kazanılmış gelir
veya mali fatura değildir. Diğer dokuz kaydın finans durumu `not_applicable`
olarak gösterilir; ilgisiz ilk folyo veya sıfır bakiye üretilmez. Kaynağı eksik
11 rapor `not_implemented` kalır.

Dashboard/oda planı ayrıntısından ilgili PMS kaydına, varsa açık folyo
kimliğine ve rezervasyon kapsamlı rapora geçilir. Toplu rapor tek rezervasyona
ayrıştırılamıyorsa bu sınır gösterilir. Housekeeping simülasyonu sonrası
donmuş folyo/rapor kaynağı eski olarak işaretlenir; yeni hareket uydurulmaz.

## Çok odalı rezervasyonların sınırı

Bir üst kayda birden fazla açık oda konaklaması bağlanabilir. Her konaklama
mevcut Python motorunda ayrı vaka olur; üst kayıt korunur. İlk oda tüm
rezervasyon yerine geçirilmez. Paylaşılan OTA referansı tek başına duplicate
kanıtı değildir. Muhafazakâr sonuç ve `requires_multiroom_review` sınırı
açıktır. Küresel çok odalı optimizasyon bu görevde tamamlanmış değildir.
Mevcut dört tek odalı AI hikâyesinden birinin kaydı çok odalı yapılırsa ilgili
hikâye güvenli biçimde atlanır; çok odalı hikâye üretimi ayrıca geliştirilmelidir.

## Güvenlik ve yayın sınırı

Tüm kaynaklar sentetik ve çevrimdışıdır. Atanmış oda çizgileri doğrulanmış
fiziksel doluluk veya satılabilir envanter değildir. PMS/OTA/AI API, ödeme,
KBS, kimlik işleme ve gerçek mesaj gönderimi kapalıdır. On dil ve RTL korunur;
çeviriler insan incelemesi bekleyen taslaktır. Ayrı taslak PR insan incelemesi
bekler; bu çalışma main'i, sürümü veya canlı demoyu yayımlamaz.
