**BidMont performans denetimi — 6 Eylül 2026**

Proje kısmen optimize. Async veritabanı erişimi, temel ihale indeksleri ve hafif frontend tercihleri doğru. Ancak teklif sorguları, katılım listesi, bildirim sırası ve sınırsız yönetim listeleri veri/trafik büyüdükçe maliyeti artırıyor. Üretim kapasitesini doğrulayacak ölçüm yok; güvenilir bir “optimizasyon yüzdesi” veya eşzamanlı kullanıcı sayısı verilemez.

İncelenen commit: `0c6c2cc3389b51401777e9dccb892016b6cb179f`. Uygulama kodu değiştirilmedi. Denetim betiği ve sonuçlar bu klasörde.

**Ölçüm kapsamı**

Windows/Python 3.14.6 üzerinde, bellekte SQLite ve gerçek FastAPI endpoint'leri kullanıldı. 1.000 ihale, 100.000 teklif, 5.000 görsel kaydı; ihale başına 100 teklif ve 5 görsel. Görsellerin dosya içeriği yüklenmedi. Endpoint süreleri bir ısınma isteğinden sonraki beş ardışık isteğin medyanı. Kimlik gerektiren endpoint'lerde gerçek JWT doğrulaması ve kullanıcı sorgusu dahil.

Docker hedefi Python 3.11/PostgreSQL. Yerel ölçümler ağ, TLS, disk, ters vekil, gerçek SMTP, tarayıcı çizimi veya eşzamanlı yük içermiyor. Scheduler/lifespan çalıştırılmadı. SQL deneyinde yalnızca geçici bellek veritabanına indeks eklendi. Sonuçlar üretim gecikmesi veya kapasite tahmini değildir.

| Akış | SQL sorgusu | Medyan | Yanıt boyutu |
|---|---:|---:|---:|
| Genel liste, 24 ihale | 5 | 13,84 ms | 30.917 bayt |
| Teklif geçmişi, 50 kayıt | 3 | 22,59 ms | 14.045 bayt |
| Katılınan 1 ihale | 4 | 14,96 ms | 160 bayt |
| Katılınan 10 ihale | 13 | 101,04 ms | 1.591 bayt |
| Katılınan 100 ihale | 103 | 917,20 ms | 16.081 bayt |
| Yönetim listesi, tüm 1.000 ihale | 6 | 150,06 ms | 1.290.781 bayt |

**Öncelikli bulgular**

1. **Yüksek — Teklif erişiminde indeks eksik.** `backend/app/models/domain.py:198` içindeki Bid modelinde `auction_id` ve sıralama alanları için indeks yok; `backend/app/core/migrations.py` da bunları eklemiyor. Teklif geçmişi, önceki en yüksek teklif, katılım durumu ve ihale kapanışı aynı erişim desenini kullanıyor. 100.000 kayıtta temsilî sorgu planı `SCAN bids` ve geçici sıralama gösterdi. `(auction_id, invalidated, amount DESC, created_at ASC)` indeksiyle medyan **8,362 ms → 0,451 ms**, yaklaşık **18,5 kat** iyileşme ölçüldü. Bu tek sorgunun kazancı; tüm uygulamaya genellenemez. Önce bu indeksi gerçek PostgreSQL sorgu planıyla doğrulayıp model ve migration'a birlikte eklemek uygun. `auction_images.auction_id`, katılım listesinin `user_id` erişimi ve bildirimlerin `user_id/is_read` erişimi de indeks adayı; bunların kazancı ayrıca ölçülmedi.

2. **Yüksek — Katılım listesinde N+1 sorgu.** `backend/app/api/auctions.py:389` döngüsü her ihale için en yüksek teklifi yeniden sorguluyor. Ölçümde sorgu sayısı **N+3**: 100 katılımda 103 sorgu, yaklaşık 0,92 saniye. `joined_auctions` ayrıca sayfalamasız. Önce sayfalama, ardından yalnızca sayfadaki ihalelerin liderlerini tek toplu sorguda almak gerekir. İndeks tek sorguyu hızlandırır; N+1 kaynaklı ağ gidiş gelişlerini ortadan kaldırmaz.

3. **Yüksek — E-postalar teklif yanıtını ve kapanış işini bekletiyor.** `backend/app/api/bids.py:241` ve `:254` iki bildirimi sırayla bekliyor; WebSocket yayını `:281`'de, bunlardan sonra. `backend/app/services/notifications.py:174` thread kullanıyor: event loop serbest kalıyor, fakat çağıran istek e-postanın bitmesini hâlâ bekliyor. Her e-postaya kontrollü 100 ms gecikme verildiğinde iki e-postalı teklif isteği **248,16 ms** sürdü; bu gerçek SMTP ölçümü değildir. Ayrıca `smtplib.SMTP` çağrısında açık timeout yok (`:68`). Scheduler, kapanmış ihalelere geçmeden önce bitiş hatırlatmalarını sırayla gönderiyor (`backend/app/core/scheduler.py:52–85`); döngü bittikten sonra 30 saniye uyuyor (`:129`). Dolayısıyla gerçek tur aralığı iş süresi + 30 saniye. E-posta teslimini yanıt/kapanış yolundan ayırmak, timeout koymak ve süresi dolmuş ihaleleri önce işlemek gerekir. Teslim garantisi gerekiyorsa kalıcı gönderim kaydı ve yeniden deneme tasarlanmalı. Aynı AsyncSession paralel görevler arasında paylaşılmamalı.

4. **Orta — Yönetim ve hesap listeleri sınırsız.** `backend/app/api/admin.py:678` tüm ihaleleri ve ilişkilerini yüklüyor. 1.000 kayıtla yanıt **1,29 MB**, yerel medyan 150 ms. Kullanıcılar, teklifler, audit kayıtları; ayrıca `my_auctions`, `joined_auctions` ve watchlist de büyüyen koleksiyonları sınırsız döndürüyor. `assets/js/api.js:1494` kullanıcı/ihale listelerini önceden indiriyor; ilgili sekmeler `:1583` ve `:1698`'de tekrar istiyor. Liste endpoint'lerine limit/offset ve kullanıcı arayüzüne sayfalama; sekmelere ilk açılışta yükleme eklenmeli. Büyük koleksiyonların tarayıcı bellek/DOM etkisi ölçülmedi.

5. **Orta — WebSocket yayını yavaş alıcıları sırayla bekliyor.** `backend/app/api/ws.py:128` her bağlantıda `await send_text` çalıştırıyor; gönderim timeout'u yok. 20 yapay sokete ayrı ayrı 10 ms bekleme verildiğinde yayın **306,24 ms** sürdü; Windows zamanlayıcı çözünürlüğü de bu değere dahil. Bu bir ağ kapasite testi değil, seri beklemenin gösterimi. Sınırlı eşzamanlı gönderim ve yavaş bağlantı timeout'u yeterli ilk adım. Docker şu anda tek Uvicorn süreci çalıştırıyor; WebSocket odaları ve scheduler süreç içinde. Worker sayısını doğrudan artırmak yerine önce yayın ve scheduler koordinasyonu ele alınmalı.

6. **Orta — Gerçek galeri görselleri küçültülmeden ve tekrar blob olarak alınıyor.** `backend/app/api/uploads.py:103` yüklenen dosyayı boyut sınırıyla kopyalıyor, küçük görsel üretmiyor. `assets/js/api.js:590` her kullanımda fetch/blob/object URL oluşturuyor; `:674` tüm küçük resimler için de tam görseli çekiyor. Görsel değiştirme ve lightbox açma aynı yolu kullanıyor. Object URL'ler galeri yeniden kurulduğunda temizleniyor (`:667`); uzun gezinmede listede birikebilir. HTTP önbelleği bazı ağ indirmelerini karşılayabilir, ancak blob/object URL tekrarını kaldırmaz. Medya kimliği başına tekrar kullanım, küçük resim varyantı ve görünür küçük resimleri yükleme önerilir. Yetkili medya erişimi korunmalı. Gerçek tarayıcı bellek tüketimi ölçülmedi.

7. **Orta — Uygulama katmanında metin sıkıştırması yok.** `Accept-Encoding: gzip, br` ile uygulamaya yapılan isteklerde HTML ve `api.js` için `Content-Encoding` gelmedi. Ana sayfanın HTML/CSS/üç JS toplamı **243.172 bayt**; dosyalar ayrı ayrı gzip ile **59.246 bayt**, **%75,6** küçülebiliyor. Bu hesap görselleri ve API yanıtlarını içermez. Ters vekil/CDN üretimde zaten sıkıştırıyor olabilir; dağıtım katmanı incelenmedi. Önce canlı yanıt başlıkları doğrulanmalı, gerekiyorsa tek katmanda sıkıştırma açılmalı. Statik JS için ETag var fakat açık Cache-Control yok. Uzun cache süresi ancak dosya sürümleme ile birlikte düşünülmeli; güncelleme sonrası eski JS sunulmamalı.

8. **Düşük — Liste için kullanılmayan görsel kayıtları yükleniyor.** `backend/app/api/auctions.py:247` tüm görselleri eager-load ediyor; `backend/app/services/auctions.py:285` liste yanıtında bunları kullanmıyor. Deneyde 24 ihale için 120 görsel kaydı gereksiz taşınıyor ve beş sorgudan biri bu yükleme. Aynı desen yönetim, satıcı ve watchlist listelerinde var. Detay endpoint'inde görseller gerekli; yalnızca liste sorgularından kaldırılmalı.

9. **Düşük — “Daha fazla” önceki kayıtları yeniden indiriyor.** `assets/js/api.js:523` limit'i 24 → 48 → 72 → 96 → 100 artırıp listeyi baştan çiziyor. Sonunda 100 ayrı ihale göstermek için toplam **340 kayıt** taşınıyor; 100'ün ötesine geçilemiyor. Sabit sayfa boyutu, offset ve yalnızca yeni kartların eklenmesi yeterli.

**İyi uygulananlar**

- Genel ihale listesi en fazla 100, teklif geçmişi en fazla 200, bildirim listesi en fazla 50 kayıt döndürüyor; bazı sayımlar SQL COUNT kullanıyor.
- Genel listede satıcı ilişkileri toplu yükleniyor; bu yol satıcı başına N+1 üretmiyor. Temel ihale filtre/sıralama indeksleri hem modelde hem migration'da var.
- Parola hash/doğrulama ve dosya kopyalama ana event loop dışına alınmış. Dosyalar sınırlı parçalarla kopyalanıyor; istek ve dosya boyutu sınırları var.
- Statik vitrin framework bağımlılığı taşımıyor; WebP, srcset, görsel ölçüleri, bazı lazy görseller, hero preload ve defer script kullanılıyor. Dosya başına ETag mevcut. Güncel kök frontend, AGENTS.md'deki SPA tanımından farklı olarak birden çok statik HTML sayfasından oluşuyor.
- Teklif yazımında satır kilidi ve idempotency kontrolü var. Performans için bunlar kaldırılmamalı; SQLite ölçümü PostgreSQL kilit rekabetini doğrulamıyor.

**Doğrulama ve uygulama sırası**

Mevcut test paketi: **293 geçti, 18 uyarı, 89,79 saniye**. Komut: backend dizininde `rtk proxy python -m pytest -q --disable-warnings --durations=5`. Bu testler işlevsel kontrol; yük veya PostgreSQL eşzamanlılık testi değil.

Önce teklif indeksi ve katılım listesindeki N+1; ardından e-posta/kapanış sırası ve sınırsız listeler. Sonra galeri, WebSocket gönderimi ve dağıtım sıkıştırması. Havuz büyütme, Redis veya yeni altyapı için bu incelemede ölçülmüş zorunluluk yok.

Üretim kapasitesi için sonraki ölçüm, Docker/Python 3.11/PostgreSQL ile üretime benzeyen veri dağılımında yapılmalı: arama, genel liste, aynı ihaleye eşzamanlı teklif, farklı ihalelere teklif ve yavaş WebSocket alıcıları. p50/p95/p99, hata oranı, CPU/RAM, DB bağlantı bekleme ve kilit bekleme süreleri birlikte izlenmeli. Bu denetimde Lighthouse/LCP/INP veya canlı sunucu yük testi yapılmadı.

Tekrar üretme: proje kökünde `rtk proxy python docs/performance-audit-2026-09-06/probe.py`. Betik gerçek DB/SMTP yapılandırmasını kendi sürecinde geçersiz kılar, yalnızca bellek DB'sine sentetik veri yazar ve JSON sonucu stdout'a basar. Kaydedilmiş sonuçlar `results.json` içinde. Süreler makine yüküne göre değişir.
