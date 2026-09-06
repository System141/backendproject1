**Uygulama sonucu**

Dokuz bulgu için yerel değişiklikler uygulandı. Çalışma dalında bırakıldı; commit, push veya canlı deployment yapılmadı.

| Ölçüm | Önce | Sonra |
|---|---:|---:|
| Genel liste, 24 ihale | 13,84 ms / 5 SQL | 9,70 ms / 4 SQL |
| Teklif geçmişi, 50 kayıt | 22,59 ms | 6,59 ms |
| Katılınan 100 ihale | 917,20 ms / 103 SQL | 8,05 ms / 3 SQL |
| İki yapay 100 ms SMTP gönderimli teklif | 248,16 ms | 29,84 ms; e-postalar worker'da |
| 20 yapay 10 ms sokete yayın | 306,24 ms | 24,89 ms |
| Yönetim ihale listesi yanıtı | 1.290.781 bayt / 1.000 kayıt | 64.533 bayt / 50 kayıt |

SQLite bellek DB, 1.000 ihale / 100.000 teklif / 5.000 görsel kaydı; endpoint medyanları ısınma sonrası beş isteğe dayanır. SMTP ve soket ölçümleri birer sentetik deneydir. Yönetim karşılaştırması sayfalamanın ilk yanıtı küçültmesini gösterir; aynı miktarda veri döndürülmüyor. Boyutlar HTTP istemcisinin açtığı yanıt boyutlarıdır. Yerel makine yükü süreleri etkiler; bu sonuçlar üretim SLA'sı veya kullanıcı kapasitesi değildir. Ham sonuçlar: results.json ve after-results.json.

**Değişen davranış**

- İhale lideri, indeks destekli ilişkili alt sorguyla aynı SQL içinde alınıyor; uygulama seviyesindeki N+1 kaldırıldı. Eşit miktar/tarihte kayıt ID'si son sıralama anahtarı. Liste sorgularından kullanılmayan görseller çıkarıldı.
- Beş yeni erişim indeksi model ve migration'a birlikte eklendi. Migration mevcut kolon/enumları inceliyor; atlanan bir DDL hatası sonraki işlemlerin transaction'ını bozmuyor. Ham session yolu aynı migration işlevini kullanıyor.
- SMTP yapılandırılmışsa bildirim ve e-posta işi birlikte kaydediliyor. `notification_emails` tablosu başlangıçta oluşturuluyor. Worker 2 saniyede bir en fazla 25 iş alıyor; SMTP socket timeout 10 saniye, en fazla 5 deneme. Hatalar loglanıyor. Doğrulama e-postalarının mevcut doğrudan gönderim yolu korunuyor.
- Kapanan ihaleler hatırlatmalardan önce işleniyor. Scheduler iş süresini 30 saniyelik periyottan düşüyor. WebSocket gönderimleri en fazla 32 eşzamanlı işlem ve bağlantı başına 2 saniyelik timeout kullanıyor.
- Yönetim kullanıcı/satıcı/ihale/teklif/destek/audit listeleri ve hesap ihale/katılım/teklif/watchlist listeleri varsayılan 50, en fazla 100 kayıt döndürüyor. Dizi yanıt biçimi korundu; toplam `X-Total-Count` başlığında, sonraki sayfa `offset` ile. API'yi kullanan başka istemciler de sayfalama yapmalı.
- Yönetim sekmeleri ilk açılışta yükleniyor. Kullanıcı araması sunucuda, teklif filtresi ihale başlığı/Lot ID/ihale ID'siyle çalışıyor. İsimler sayfa yanıtında geliyor; tüm kullanıcı/ihale listelerini önceden yükleme kaldırıldı. Genel listede sabit 24 kayıt ve offset; eski kartlar tekrar indirilmeden ekleme.
- Galeride URL başına aynı istek/blob paylaşılıyor, görsel listesi/oturum değişiminde ve sayfadan çıkışta temizleniyor. Görünür küçük resimler için yetki kontrollü `?thumbnail=true` kullanılıyor. 320×240 WebP önbelleği upload dizinindeki `.thumbnails` altında; asıl dosya korunuyor. 20 megapiksel üzerindeki kaynaklar küçük resim işlemi için reddediliyor; asıl indirme yolu devam ediyor.
- Gzip varsayılan açık; medya yolları yeniden sıkıştırılmıyor. Proxy zaten sıkıştırıyorsa `HTTP_COMPRESSION=false` kullanılmalı. HTML yeniden doğrulaması ve özel dosyalardaki `private, no-store` korunuyor; sürümsüz JS'ye uzun süreli cache eklenmedi.

Yeni tek bağımlılık: [Pillow 12.3.0](https://pypi.org/project/pillow/12.3.0/). JPEG/PNG/WebP küçük resim üretimi standart kütüphanede bulunmadığı için eklendi; diğer değişiklikler mevcut bağımlılıklarla yapıldı.

**Doğrulama**

- Tüm mevcut 293 test ilk geçişte başarılı. Yeni dört test: sabit sorgu sayısı/sayfalama/lider seçimi; e-posta tekrar deneme/idempotency; küçük resim boyutu/önbellek/yetki; yavaş WebSocket alıcısı.
- Birleşik test çalışması: **297 geçti, 18 uyarı, 90,71 saniye**. JavaScript dosyaları `node --check`, diff `git diff --check` ile kontrol edildi. Sonrasında tek e-posta işinin beklenmeyen istisnasına karşı koruma eklenip ilgili bildirim/performance testleri tekrar çalıştırıldı.
- Gerçek tarayıcı, izole bellek DB: 24/48/72/96/120/125 kart; 125 farklı ihale bağlantısı. Yönetim filtresinde 1–50, 51–100, 101–125; son sayfada ileri düğmesi kapalı. Console hata/uyarı listesi boş. Ekran düzeni görsel olarak kontrol edildi.

**Yayın öncesi**

1. Docker engine başlatıldıktan sonra izole staging PostgreSQL'de migration'ı iki kez ve gerçek sorgularla EXPLAIN çalıştır. Mevcut indeks kurulumu startup sırasında normal CREATE INDEX kullanır; büyük tabloda kilit/başlangıç süresi ölçülmeli.
2. Container'ı güncel requirements ile yeniden oluştur; DB ve uploads volume yedekleriyle mevcut yayın prosedürünü uygula. Yeni indeksler ve ek outbox tablosu eski kodla birlikte bulunabilir. Geri dönüşte outbox teslimi durur; bekleyen işler silinmemeli.
3. SMTP gönderimini ve başarısız denemeleri staging'de doğrula. Worker tek süreç varsayar; çoklu worker için iş sahiplenme gerekir. SMTP kabulünden sonra süreç çökerse aynı e-posta tekrar gönderilebilir. Beş başarısız denemeden sonra iş loglanır ve otomatik tekrar durur.
4. Gerçek proxy sıkıştırmasını, mobil galeri yükünü ve eşzamanlı tekliflerde p95/p99, hata oranı, CPU/RAM, DB kilit/baglanti beklemelerini ölç. Canlı ortam bu çalışmada değiştirilmedi.

Tekrar üretme: kökte `rtk proxy python docs/performance-audit-2026-09-06/probe.py`; sonuç after-results.json'a yazılır. UI için `ui_fixture.py` yalnızca localhost:8765 üzerinde sentetik veri sağlar; gerçek DB/SMTP kullanmaz.
