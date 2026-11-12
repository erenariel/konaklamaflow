# Kamuya açık ürünlerden iş akışı araştırması (12 Kasım 2026)

Kamuya açık tanıtım, yardım ve ürün sayfaları incelendi. Bu çalışma erişim izni gerektiren özel arayüzler, kodlar, logolar veya ticari sırlar üzerine kurulmamıştır. Ürünlerin tamamını test etmiş olduğumuz anlamına gelmez. KonaklamaFlow bağımsız bir projedir, adı geçen markalarla bağlantılı değildir.

## ElektraWeb

**İncelenen iş akışları:** Ön büro, Check-in listesi, Room Rack, dijital kat hizmetleri, görev yönetimi, oda durumu kontrolü ve online check-in'de personel onayı. Kullanıcı deneyimi açısından **gelişler → oda durumu → kontroller → check-in eylemi** zinciri önemli. Mevcut uygulamada bu zincirin sadece *öneri / kontrol* tarafı oluşturuldu.

Kaynaklar:
- https://www.elektraotel.com/tr/elektraweb-nedir/index.html
- https://support.elektraweb.com/faq/mod-1-front-office/elektra-faq-1822
- https://yardim.elektraweb.com/crm/online-check-in-listesi
- https://www.elektraweb.com/wp-content/uploads/2025/06/katalog.pdf

## Sedna HOTEL

**İncelenen iş akışları:** PMS ve bulut/yerel çalışma, rezervasyon entegrasyonu, ön check-in/ön check-out bilgileri, misafir talep takibi, kapı kilidiyle entegre olabilen konaklama süreçleri. Ön check-in belgesinin personel tarafından son kontrolü önemli; bu nedenle sırf misafir veriyi girdi diye otomatik giriş tamamlanmış sayılmıyor.

Kaynaklar:
- https://kod.com.tr/Product/SednaHotel
- https://play.google.com/store/apps/details?id=com.kod.sednahotel&hl=tr

## Sistem Otel

**İncelenen iş akışları:** Rezervasyon ve kanal akışı, oda ve blokaj, rapor/denetim, kullanıcı yetkileri, gün sonu, AI resepsiyonist, KBS/e-Fatura/KVKK gibi Türkiye'ye özgü modüller. Bu özelliklerin kamuya açık ürün açıklamasında bulunması bize bir **entegrasyon vaadi** sağlamaz. İzinli API ve üretici anlaşması olmadan Sistem Otel hesabına müdahale yapılmayacaktır.

Kaynaklar:
- https://www.sistemotel.com/
- https://www.sistemotel.com/otel-programi
- https://www.sistemotel.com/sik-sorulan-sorular

## KonaklamaFlow'a aktarılan tasarım ilkeleri

1. Bir ekranda geliş kuyruğu, oda hazırlığı ve uyarı sıralaması.
2. Temizlik/teknik bloke/oda kategorisi rezervasyonun tek anlık görüntüsünde birlikte kontrol edilmeli.
3. İş akışı geçmişi ve son kullanıcı onayı tasarımda merkezi konumda olmalı; bugün sadece read-only rapor uygulanıyor.
4. Misafire erken check-in / yatak tipi gibi bir vaat otomatik verilmemeli.
5. Başka ürünlerin ekran görüntüleri, ikonları, metinleri, ticari kimliği veya kodları kopyalanmaz. Yeni kokpit özgün bir görsel dildir.
