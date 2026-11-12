# Codex devralma talimatı — **Git geçmişi temizliği bittikten sonra**

## Kesin ön koşul

Eren'in iki GitHub deposundaki kişisel e-posta metaverisini temizlemek için başlatılan `git-filter-repo` ve `--force-with-lease` işlemleri, yedekleme, PR #2 ve branch/tag bütünlüğü **tamamlanmadan herhangi bir git push / branch / PR / release / force-push başlatma**.

Bu paket, canlı depoya bilerek gönderilmeyen bağımsız bir v0.3 geliştirme prototipidir.

## İşlem sırası

1. Eski e-posta temizliğinin tamamlandığını, güncel `main`, `feat/front-desk-operations-rc1`, `v0.1.1` ref'lerini ve PR #2'nin durumunu doğrula.
2. Eski SHA'ları kullanma; yeni clone aç, `git config user.email` noreply ve `git config --global` ayarlarını doğrula. Gerçek e-posta adresini konsol veya PR'a yazma.
3. Yeni branch oluştur: `feat/hotel-operations-suite-v03`. `main` ve PR #2'yi otomatik birleştirme.
4. Bu paketten **ekleyerek** taşı: `demo/hotel-suite.html`, `examples/fictional-hotel.json`, `konaklamaflow/experience_engine.py`, `konaklamaflow/experience_cli.py`, `tests/test_experience_engine.py`, `tests/test_suite_browser.py`, `docs/*.md`. Mevcut `__init__.py`, `pyproject.toml`, `README.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, eski v0.2 modülleri ve testlerini **overwrite etme**.
5. Yeni dosyalar ile eski v0.2 operasyon motoru arasındaki farkları incele; iki ayrı kural motorunu kalıcı tutmak yerine tek sürümle uyumlu adaptör ve şema standardı geliştir.
6. Testleri çalıştır: `python -m unittest discover -s tests -v`; Playwright Chromium testleri. Browser testinin sabit `/usr/bin/chromium` yolu CI için ortam bağımsız yapılmalı.
7. Güvenlik: yeni gizli veri / PII taraması, CSP ve tarayıcı ağ istekleri, schema field allowlist, tarih/oda eşleme, prompt injection, idempotency, audit.
8. Github Actions'ta Python 3.11/3.12/3.13, tarayıcı/erişilebilirlik/syntax testlerini çalıştır. Browser testleri CI'da `playwright install chromium` ile erişilebilir olmalı.
9. Görev dalındaki geliştirmeleri PR olarak aç. **İnceleme tamamlanmadan, onaysız `main` merge veya live release yapma**.

## Değer açıklaması

Bu v0.3 paketi kullanıcıya demo gibi görünen 10 ekran sunar, ama gerçek işlemler yapmaz. Gerçek iki-AI entegrasyonu, OTA erişimi, CRM, PMS check-in ve KBS **yoktur**. Proje güvenliği ve gerçek kullanıcı benimsenmesi için safhalı yol haritası `OPERASYON_MIMARISI_TR.md` ve `GELISTIRME_YOL_HARITASI_TR.md` içindedir.

## Beklenen Codex raporu

- Eski e-posta temizliğinin sonucu ve güncel ref'ler
- Eklenen dosyalar, SHA'lar, test çıktısı
- Mimari tutarlılık ve güvenlik sorunları
- Gerçekliği aşan ürün/performans iddiaları varsa düzeltmeler
- Yeni PR bağlantısı ve açık teknik borçlar
