# Faz Kontrol Durumu

`docs/fazkontrol.md` karşı kod taraması. İşaret: ✅ tamam, 🟡 kısmi/planlı, ❌ yok.
Kaynak: `fazkontrol.md` düzenlenmedi, ayrı dosya.

## FAZ 1 — MVP Vitrin

- ✅ Ana sayfa — `index.html` tam.
- ✅ Kategori sayfaları çalışması — **[Uygulandı]** kök neden düşünülenden derindi: `fetchCategories()` her sayfada `/api/categories`'i çağırıyordu ama böyle bir public endpoint hiç yoktu (sadece admin-only `/admin/categories`), o yüzden sessizce 404 alıp site genelinde kategori adı/resmi boş kalıyordu. Eklendi: public `GET /api/auctions/categories` (`auctions.py`), frontend `api.js` bu URL'e çekildi. Ayrıca chip etiketleri (Cars/Real Estate/Marine/...) gerçek DB kategorileriyle (eskiden Vehicles/Equipment/Commercial Assets) hiç eşleşmiyordu — kullanıcı kararıyla **backend chip etiketlerine uyduruldu** (`category_seed.py` TOP_LEVEL yeniden yazıldı). Chip click artık `auctions.html`'de gerçek `category_id` ile filtreliyor (`api.js` `wireAuctionListings`).
- ✅ İletişim/hakkımızda — **[Uygulandı]** destek/iletişim (`support.html`) zaten ✅ idi. "About Us" artık `index.html#about` yeni bölümüne gidiyor (`build.py`), önceki `href="#"` boş link düzeltildi.
- ❌ TR/EN dil geçişi — footer `<select>` (`index.html:276`) var, JS bağlantısı yok, i18n string tablosu yok.
  **Plan:** `data-i18n` attribute + tek JSON dict + select `onchange` → `localStorage`. (Montenegro için tasarım gelene kadar ertele)
- ✅ Responsive — `style.css` 74 media query.
- ✅ Emergent/dış kaynak ibaresi — iz yok, temiz.

## FAZ 2 — Kayıt/Giriş/Rol

- ✅ E-posta/telefon kayıt — `auth.html:120-126`.
- ✅ Giriş/çıkış — JWT altyapı (CLAUDE.md doğrulanmış).
- ✅ Şifre sıfırlama — forgot-password endpoint (CLAUDE.md doğrulanmış).
- ✅ Profil sayfası — `account.html`.
- ✅ Rol yapısı — `buyer/seller/corporate_seller/admin/super_admin/support` (`domain.py:18-23`).
- 🟡 KVKK/GDPR onay — **[Kısmi uygulandı]** checkbox linkleri artık `/api/legal/{type}`'ı çeken bir modal açıyor (native `<dialog>`, `wireLegalModal()` `api.js`), footer'daki Terms/Privacy/Cookie linkleri de aynı modalı kullanıyor. İçerik hâlâ boş — `docs/proje-durum-raporu.md` §15 bunu zaten LITZOR'un avukatından gelecek hukuki metin olarak işaretlemiş, kodla çözülemez; modal 404'te "İçerik hazırlanıyor" gösteriyor. Admin zaten `POST /api/admin/legal` ile metni girebiliyor (yeni eklenmedi, mevcuttu) — kalan iş sadece gerçek metnin girilmesi.

## FAZ 3 — İlan Oluşturma

- ✅ Başlık/açıklama/kategori — `account.html:160-162`.
- ✅ Fiyat/min artış/bitiş — `account.html:163-165`.
- ✅ Fotoğraf yükleme — `uploads_router` bağlı (`main.py:131`).
- ✅ Araç alanları — brand/model/year/mileage/fuel_type/transmission/damage_status (`domain.py:135-141`), form alanları da var (`account.html:168-169`+).
- ✅ Ekipman alanları — equipment_brand/serial_number/condition/location (`domain.py:155-158`).
- ✅ Admin onay akışı — `AuctionStatus.under_review` + review_notes/reviewed_by.

## FAZ 4 — Canlı Teklif Motoru

- ✅ Teklif verme — `bids.py`.
- ✅ Anlık en yüksek teklif — WS broadcast (`ws.py`, CLAUDE.md).
- ✅ Geri sayım — `end_time` + `fmtEndsIn` (`api.js:285-286`).
- ✅ Kazanan belirleme — `finalize_auction()` (CLAUDE.md, scheduler + bid API ortak).
- ✅ Son dakika uzatma — anti-sniping wired (`bids.py:209-215`, `AuctionStatus.extended`).
- ✅ Teklif geçmişi — `Bid` tablosu.

## FAZ 5 — Admin Paneli

- ✅ Kullanıcı/rol yönetimi, ilan onay/red, kategori yönetimi (`api.js:1493+` adm-category-form), destek talepleri — `admin.py`/`admin.html` mevcut, yakın commit geçmişi bunu doğruluyor.
- ✅ Öne çıkan ilan yönetimi — `admin.py:683-706` toggle featured.
- 🟡 Temel raporlar — `admin_stats` (`admin.py:1029-1075`): kullanıcı/ilan/teklif/aktif/tamamlanan/bekleyen/kredi geliri ✅. "Satış" ve "komisyon" metriği yok — v1'de Sold/Paid state kasıtlı olarak yok (`domain.py` yorum: "no Sold/Paid states in v1").
  **Plan:** gerçek satış/ödeme akışı eklenmeden bu iki metrik tanımsız — mimari karar, şimdilik ertele.

*(Not: doc'ta FAZ 6 yok, 5'ten 7'ye atlıyor — olduğu gibi bırakıldı.)*

## FAZ 7 — Bildirim/Destek

- ✅ Teklif/tekliften düşme/bitiş hatırlatma/sonuç bildirimleri — `NotificationType` (outbid, bid_received, auction_ending_soon, auction_won/lost, auction_approved/rejected/completed).
- 🟡 Kazanana e-posta/SMS/WhatsApp — e-posta SMTP altyapısı var, env-gated (`notifications.py`, `smtplib`). SMS/WhatsApp yok — doc zaten bunu "opsiyonel" sayıyor, e-posta yeterli.
- ✅ Destek talep formu — `support.html` + `support_router`.

## FAZ 8 — B2B Kurumsal Panel

- ✅ Kurumsal satıcı hesabı — `corporate_seller` rolü + `SellerProfile.account_type="company"`.
- ✅ Toplu ilan yükleme / Excel-CSV aktarma — **[Uygulandı]** `POST /api/auctions/bulk-import` (CSV, stdlib `csv`), her satır aynı `create_auction()`'dan geçiyor (validasyon/ücret/lot-kodu tek yerde kalıyor), satır bazlı başarı/hata raporu dönüyor. `account.html`'de "My listings" sekmesinde CSV upload input'u.
- ✅ Kurumsal satış raporu / satıcı performans ekranı — **[Denetim hatası düzeltildi, kod zaten vardı]** `GET /api/users/me/seller-stats` (`users.py:74`) zaten mevcuttu — ilk taramada `sellers.py`'ye bakılmış, `users.py` atlanmış. `account.html`'in `acct-seller-stats` paneli bunu zaten gösteriyor. Yeni kod yazılmadı, sadece rapor düzeltildi.
- ✅ Kurumsal doğrulama belgeleri — **[Uygulandı]** `SellerProfile.verification_document` kolonu (`MISSING_COLUMNS`'a eklendi), `POST /api/sellers/me/verification-document` (upload) + `GET /api/sellers/{profile_id}/verification-document` (owner/staff-only indirme, `private_uploads/` — public mount'ta değil). Seller apply formuna dosya input'u eklendi.
- ❌ Balkanlar/İngilizce pazar genişleme altyapısı — i18n olmadan (FAZ 1 gap) bu da yok, aynı kökten.

## Uygulama sonrası özet (bu oturumda kapatılan maddeler)

Kapatıldı: FAZ 1 kategori filtresi (kök neden dahil), FAZ 1 hakkımızda linki, FAZ 8 toplu CSV yükleme, FAZ 8 kurumsal rapor (zaten vardı), FAZ 8 doğrulama belgesi upload. FAZ 2 KVKK linkleri plumbing olarak bağlandı (içerik hâlâ LITZOR'dan bekleniyor). 263 backend testi geçiyor (yeni eklenen testler dahil).

Ertelendi (kullanıcı notu / mimari karar, bu oturumda dokunulmadı): FAZ 1 TR/EN dil geçişi (Montenegro tasarımı gelene kadar), FAZ 5 satış/komisyon metriği (v1'de Sold/Paid state yok), FAZ 7 SMS/WhatsApp (doc zaten opsiyonel sayıyor), FAZ 8 Balkan/İngilizce pazar genişleme altyapısı (i18n'e bağlı, aynı erteleme).

### ⚠️ İki önemli uyarı

1. **Mevcut DB'ler için kategori geçişi yarım kalır.** `category_seed.py` sadece ekler, hiç silmez/yeniden adlandırmaz — zaten seed edilmiş bir DB (yerel `bidmont.db`, canlı Postgres) eski `Vehicles/Equipment/Commercial Assets` + 9 alt kategoriyi YENİ 8 kategoriyle birlikte taşımaya devam eder. Eski kategorilere bağlı mevcut ilanlar hiçbir chip filtresiyle eşleşmeyecek, ilan formunun kategori dropdown'ı da ~20 seçenek gösterecek. Temizlik için admin panelden (`PUT /admin/categories/{id}`, status=inactive) manuel müdahale gerekir — otomatik migration/silme yazılmadı (`category_seed.py`'de `ponytail:` notu var).
2. ~~`docs/proje-durum-raporu.md` ile çelişki~~ — çözüldü: o dosyanın 01.08.2026'ya kadarki durumu izlediği, yani 09.08.2026'daki site yeniden inşasından (eski tek-dosya SPA → şu anki çok sayfalı site) ÖNCEye ait olduğu ortaya çıktı. `docs/legacy/proje-durum-raporu.md`'ye taşındı ve başına arşiv notu eklendi.

### Dokunulmayan küçük eksikler (kapsam dışı, tek satır not)

- `auctions.html`'deki filtre `<select>` (satır ~75, "All categories/Cars/Heavy equipment/...") hâlâ dekoratif — chip'ler çalışıyor ama bu ayrı dropdown bağlanmadı, etiketleri de eski/küçük harfli.
- `admin.html`'de satıcı doğrulama belgesini indirmek için UI linki yok — backend endpoint (`GET /api/sellers/{profile_id}/verification-document`) staff-gated ve çalışıyor, admin paneline buton eklenmedi.
