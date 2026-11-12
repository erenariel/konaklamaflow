# Yayın öncesi kalite kapıları — v0.2.0rc1

Bu geliştirme **henüz GitHub'a yüklenmiş değildir**. Kaynak paketi, canlı `erenariel/konaklamaflow` v0.1.1 üzerinde incelenerek bir feature branch / PR aracılığıyla birleştirilmelidir.

## Kapsam ve test

- [ ] Yeni modüller ve testler mevcut `main` üzerinde çatışmasız eklendi.
- [ ] `tools/apply_to_existing_repo.py` yalnızca beklenen hedefleri değiştirdi.
- [ ] `python -m unittest discover -s tests -v` tüm mevcut ve yeni testleri başarıyla geçti.
- [ ] `python -m pip install -e '.[browser]'` (mevcut optional browser bağımlılıkları) ardından Playwright tarayıcı testleri başarıyla geçti.
- [ ] `python -m konaklamaflow.ops_cli examples/operations-demo.json --as-of 2026-11-12 --at-time 14:01` tutarlı rapor verdi.
- [ ] Eski rezervasyon CLI `python -m konaklamaflow examples/demo.json --as-of 2026-11-12` çalışıyor.
- [ ] `demo/operations.html` hem masaüstü hem mobil açılıyor ve yerel dosya yükleme güvenli.
- [ ] `examples` içinde yalnızca kurgusal kimliksiz veriler var; özel hesap, otel personeli, rezervasyon referansı, misafir verisi veya token yok.
- [ ] `git diff`, otomatik testler ve istenirse bağımsız kod gözden geçirmesi tamamlandı.
- [ ] `SECURITY.md` sürüm durumu güncellendi.
- [ ] `README.md` durum açıklaması ve Pages linki doğru.
- [ ] GitHub Actions `tests` ve `demo` iş akışları bu commit için yeşil.
- [ ] Artık yanlış olan eski sürüm/dokümantasyon bilgileri güncellendi.
- [ ] Gerçek pilot ve benimsenme sayıları olmadıkları sürece yazılmadı.

## Kritik sınırlamalar

- `READY_FOR_HUMAN_CHECKIN_REVIEW`: sadece insanın işlem **öncesi kontrolüne hazır**, gerçek check-in tamamlanmış değil.
- `identity_status`: girdi içindeki durum kurgusal veya yetkili sistemce sağlanmış olmalıdır; bu prototip durumu gerçek kaynakta doğrulamıyor.
- `registration_status`: bir durum sinyali; KBS'ye hiçbir bildirim yapılmıyor.
- `make_handoff`: read-only AI görev açıklaması; gerçek yetkilendirme veya çağrı yapmıyor.
- İzin verilmiş üretici API bağlantısı, RBAC ve audit yok. Canlı otelde kullanılmamalı.

## Bilinen teknik borç

- Oda seçiminde sadece heuristik geliştirme var, global optimizasyon yok.
- Anlık durum değişikliği / optimistic concurrency henüz yok.
- Pseudonimleştirme kullanıcı tarafından *önceden* yapılmalı; yalnızca regex ile kimliksiz hale gelmiş sayılmaz.
- Web panelinin dosya yüklemesi kimliksiz rapor için; 2MB sınırı bir güvenlik denetimi değil.
- Gerçek ücretlendirme, çoklu oda/kategori yükseltmeleri, erken/ geç çıkış politikaları, OTA yazma, KBS, e-Fatura, ödemeler kapsam dışı.

## Sürüm mantığı

`0.2.0rc1`: test edilebilir geliştirme adayı. İlk gerçek, tekrarlanabilir dış test ve kod incelemesinden sonra `0.2.0` yayımlanabilir. Ana dalı onaysız force-push yapma. Eski etiketleri değiştirme.
