# Devam notu (WIP) — 20 Kasım 2026

> Geçici dosya. İş bitince silinecek. Dal: `claude/trusting-allen-gv4p12`.
> Kullanıcı isteği: incelemede bulunan **bütün eksikleri tamamlamak**. Kullanıcı
> 20 Kasım'da işi durdurup kaydetmeyi istedi; kaldığımız yer aşağıda.

## Tamamlananlar (test edildi)

1. **`konaklamaflow/core.py`, girdi şeması 1.1.** 1.0 girdileri aynen geçerli; yeni alanların hepsi opsiyonel.
   - Durumlar: `checked_in`, `checked_out`, `no_show`.
   - Yeni girdi alanları: `nightly_rates`, `discount_base`, `adults`, `children`,
     `board` (RO/BB/HB/FB/AI/UAI), `guest_key`, `block_id`, `segments` (oda değişimi),
     `arrival_time`, `departure_time`.
   - Oda alanları: `max_occupancy`, `max_adults`. Üst seviye alanlar: `blocks` (allotment/grup, `release_days` veya `cutoff`), `policy`.
   - Para birimleri genişledi (RUB, CHF, AED, …).
   - Yeni kodlar: `IN_HOUSE_WITHOUT_ROOM`, `CHECKOUT_OVERDUE`, `STATUS_DATE_CONFLICT`,
     `NO_SHOW_HOLD_REVIEW`, `PENDING_ARRIVAL_DECISION`, `PENDING_EXCEEDS_CAPACITY`,
     `POSSIBLE_DUPLICATE_BOOKING`, `OCCUPANCY_EXCEEDS_ROOM`, `SAME_DAY_TURNOVER_RISK`,
     `ROOM_MOVE_OPTION`, `BLOCK_NOT_FOUND`, `BLOCK_MISMATCH`, `BLOCK_OVERBOOKED`.
   - Çıktı şeması 1.1: önceki bütün alanlar değişmedi. Eklenenler: `split_stay_proposals`,
     `today_departures`, `room_moves`, `availability` (kategori × gece, satılan oda bazında),
     `meal_forecast`, `blocks`, ayrıca özette 3 yeni sayaç.
   - `_Planner`: odası kayıtsız konaklayan misafirler ve henüz release edilmemiş blok
     odaları için kapasite ayırır. Bunlar yoksa öneri davranışı eskisiyle birebir aynı.
   - **Bilinçli karar:** farklı kanallarda aynı referans numarası mükerrer kayıt sayılmaz
     (`tests/test_v02_audit.py` kanal bağımsızlığını sabitliyor). Mükerrer tespiti yalnızca
     aynı `guest_key` + aynı tarihler + farklı kaynak koşuluyla yapılır.
2. **`konaklamaflow/report_contract.py`:** yeni kodlar `REASONS` listesine eklendi (ön büro modülü çekirdek kodlarını taşıyor).
3. **`tests/test_core_schema11.py`:** 44 yeni test.

**Doğrulama:** Mevcut 382 test ve 44 yeni test geçiyor. Benchmark v1/v2, ön büro (ops) ve suite
çıktıları değişiklik öncesiyle bayt bayt aynı. `generate_*_demo.py --check` geçiyor.
Performans: 500 oda / 5.000 rezervasyon yaklaşık 0,4 sn.

## Yarım kalan: CSV içe aktarma

`wip/local_csv_draft.py` **test edilmemiş taslak**, hiçbir yerden import edilmiyor. İçeriği:

- Ayraç (`, ; tab |`) ve cp1254/UTF-8 otomatik algılama, `GG.AA.YYYY` tarih, `1.234,56` tutar.
- Türkçe başlık eşanlamlıları; Türkçe kişisel veri sütunları okunup atılıyor.
- Kapalı sözlükler: kategori, durum, yatak, pansiyon, kaynak, döviz.
- Eşleme JSON'u: `columns`, `ignore`, `values`, `defaults`, `policy`.
- Çalıştırma başına HMAC takma adları ve sadece bellekte tutulan etiketler (personel gerçek numaraları yerelde görebilsin diye).
- Opsiyonel blok CSV'si, opsiyonel misafir eşleme (`link_guests`), sütun konumuna göre `inspect_csv`.

**Sıradaki adım:** taslağı `konaklamaflow/local_csv.py` yerine koy (import yolları göreli
`.core` / `.io_safety` olmalı), `tests/test_local_csv.py`'yi geçir. Korunması gerekenler:
`R_`/`B_` token biçimi (26 karakter), kaynak sütunu yoksa `LOCAL_CSV`, tanınmayan sütunun
reddi, `active` yoksa odaların pasif sayılması. Ardından yeni özellikler için test yaz ve
`examples/csv/` altına kurgusal bir Türk PMS dışa aktarımı ile örnek eşleme dosyası ekle.

## Kalan işler (sırayla)

1. **CLI (`cli.py`):** `review-csv` için `--blocks`, `--mapping`, `--link-guests`, `--rooms-active`
   ve `--labels-output` (0600) bayrakları; `inspect-csv` ve `ui` komutları.
2. **Yerel arayüz (`konaklamaflow ui`):**
   - stdlib `http.server`, yalnızca 127.0.0.1, Host başlığı kontrolü, çalıştırma başına token, boyut sınırları, diske hiçbir şey yazılmaz.
   - multipart için `email.parser` (`cgi` Python 3.13'te yok).
   - Sunucu tarafında üretilen TR/EN sayfa; gerçek rezervasyon/oda numaraları bellekteki etiketlerden gösterilir.
3. **Görüntüleyiciler:**
   - `demo/viewer.html` hem 1.0 hem 1.1 raporlarını doğrulasın ve yeni bölümleri göstersin.
   - 13 yeni kod için `issueCopy` metinleri yazılsın; `BASE_PRICE_MISMATCH` regex'indeki para birimleri güncellensin.
   - `demo/operations.html` yeni kod etiketlerini alsın.
   - `examples/demo-report.json` ve gömülü örnek yeniden üretilsin; tarayıcı testleri çalıştırılsın.
4. **Dokümanlar:**
   - `docs/INPUT_SPEC.md` (şema 1.1), `docs/LOCAL_CSV_TR_EN.md`, `docs/LIMITATIONS.md`, `README.md`, `CHANGELOG.md` güncellensin.
   - `SECURITY.md`, `docs/MAINTAINER_PLAN.md` ve `docs/RELEASE_CHANNELS_TR_EN.md` içindeki rc1 ifadeleri rc2 yapılsın.
   - İç çalışma notları (`CODEX_*`, `AI_WORK_ALLOCATION_TR`, `PR18_DOGRULAMA_TR`, `ISSUE35_VALIDATION_TR`, …) bağlantıları güncellenerek `docs/internal/` altına taşınsın.
5. **CI:** minimal kurallı ruff ve coverage eklensin; `.github/dependabot.yml` oluşturulsun (github-actions, pip).
6. **Kapanış:**
   - Tüm birim ve tarayıcı testleri çalıştırılıp push edilsin; bu dosya ve `wip/` silinsin.
   - Issue/PR/dal temizliği için kanıtlı bir liste hazırlanıp **kullanıcı onayına** sunulsun. Onaysız kapatma veya silme yapılmayacak.
   - Adaylar: #50, #52, #54, #56, #57, #62 ve #70 kodda karşılığı olan issue'lar; #71 muhtemelen #90 ile geçersiz; 66 dal.
   - PR yalnızca kullanıcı isterse açılacak.

## Doğrulama tarifi

Değişiklikten sonra şunları çalıştırıp çıktıları önceki sürümle karşılaştır:

- `python -m unittest discover -s tests`
- `python -m konaklamaflow.evaluation` ve `python -m konaklamaflow.evaluation_v2` (`--json` ile)
- `python -m konaklamaflow.ops_cli examples/operations-demo.json --as-of 2026-11-12 --at-time 14:01`
- `python -m konaklamaflow.experience_cli examples/fictional-hotel.json OUT.json`
- `python scripts/generate_suite_demo.py --check` (ve diğer iki generator)
