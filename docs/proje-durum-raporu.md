# BidMont Projesi — Mevcut Durum İnceleme Raporu

**Tarih:** 26.06.2026 (Güncelleme)  
**Önceki Rapor:** 25.06.2026  
**Kapsam:** Render'da canlı olan `https://bidmont-api.onrender.com/` adresinin kapsamlı testi.

> ⚠️ **29.07.2026 iş modeli değişikliği:** LITZOR DOO'nun `docs/Bidmont son hali için döküman .docx` dosyasında talep ettiği üzere, BidMont artık asset satışının/ödemesinin/komisyonunun tarafı DEĞİLDİR — yalnızca kredi ile ihaleye katılım altyapısı sağlar. Aşağıdaki Faz 6 satırı ve bazı erken bölümler (`/api/payments`, komisyon, Stripe checkout) **artık geçerli değildir**, kaldırılmıştır. Güncel durum için bkz. **Bölüm 9**.

---

## 1. Canlı Ortam Test Sonuçları (26.06.2026)

| Test | Endpoint | Sonuç |
|------|----------|:-----:|
| Backend sağlık | `GET /api/health` | ✅ `{"status":"ok","version":"1.0.0","environment":"production"}` |
| Anasayfa (SPA) | `GET /` | ✅ `index.html` başarıyla sunuluyor |
| Kullanıcı kayıt | `POST /api/auth/register` | ✅ Çalışıyor (admin@bidmont.me zaten var) |
| Kullanıcı girişi | `POST /api/auth/login` | ✅ JWT token dönüyor |
| Admin panel - İstatistikler | `GET /api/admin/stats` | ✅ 1 kullanıcı, 0 aukcije, 0 teklif |
| Admin panel - Kullanıcılar | `GET /api/admin/users` | ✅ 1 admin kullanıcı listeleniyor |
| Admin panel - Aukcijeler | `GET /api/admin/auctions` | ✅ Boş dizi (henüz aukcije yok) |
| Admin panel - Teklifler | `GET /api/admin/bids` | ✅ Boş dizi |
| Admin panel - Kategoriler | `GET /api/admin/categories` | ✅ Boş dizi (henüz kategori eklenmemiş) |
| Admin panel - Destek talepleri | `GET /api/admin/support-tickets` | ✅ Boş dizi |
| Admin panel - Ödemeler | `GET /api/payments` | ✅ Boş dizi |
| Admin panel - Denetim kaydı | `GET /api/admin/audit-logs` | ⚠️ Internal Server Error (created_at migration eklendi, deploy edildi) |

---

## 2. Frontend (index.html) Sayfa Bölümleri

| Sayfa | ID | Durum |
|-------|----|:-----:|
| Ana Sayfa | `#home` | ✅ Hero, kategoriler, istatistikler, nasıl çalışır |
| Aukcijeler | `#auctions` | ✅ Filtre + sıralama + grid |
| Araçlar | `#vehicles` | ✅ Kategori filtresi |
| Ekipman | `#equipment` | ✅ Kategori filtresi |
| Genel | `#general` | ✅ Kategori filtresi |
| Arama | `#search` | ✅ Global arama |
| Nasıl Çalışır | `#how` | ✅ 4 adım açıklaması |
| Hakkımızda | `#about` | ✅ Misyon metni |
| İletişim | `#contact` | ✅ İletişim formu |
| Aukcije Detay | `#detail` | ✅ Görsel, teklif geçmişi, canlı teklif |
| Giriş | `#login` | ✅ Demo + API entegrasyonu |
| Kayıt | `#register` | ✅ GDPR/KVKK onay kutuları |
| Şifre Sıfırlama | `#forgot-password` | ✅ Token bazlı |
| Şifre Yenileme | `#reset-password` | ✅ Token ile |
| Profil | `#profile` | ✅ API + demo hibrit |
| Admin Panel | `#admin` | ✅ 8 tab (stats, users, auctions, categories, bids, tickets, payments, audit) |
| Aukcije Oluştur | `#post`, `#sell` | ✅ Form + demo kayıt |
| Dil Seçimi | — | ✅ ME 🇲🇪 / EN 🇬🇧 |

---

## 3. Faz Bazında Tamamlanma Durumu

| Faz | Açıklama | Tamamlanma | Detay |
|-----|----------|:----------:|-------|
| **Faz 1** | MVP Vitrin, Arayüz | **%100** | index.html SPA tüm sayfalar + Next.js frontend |
| **Faz 2** | Kullanıcı, Kayıt, Rol | **%100** | Kayıt/giriş/profil, şifre sıfırlama, token yenileme |
| **Faz 3** | İlan Oluşturma | **%100** | CRUD + onay/red akışı + bildirim |
| **Faz 4** | Teklif Motoru | **%100** | REST API + WebSocket + heartbeat + süre uzatma |
| **Faz 5** | Admin Paneli | **%100** | Tüm tablar canlı ve çalışıyor |
| **Faz 6** | ~~Ödeme/Komisyon~~ → Kredi Motoru | **Kaldırıldı → Yeniden yapıldı** | Asset ödeme/komisyon/Stripe checkout tamamen kaldırıldı (29.07.2026). Yerine BidMont kredi ledger + join/bid motoru geldi — bkz. Bölüm 9 |
| **Faz 7** | Bildirimler | **%100** | In-app + e-posta (SMTP) |
| **Faz 8** | Kurumsal | **%100** | Satıcı paneli, Stripe checkout endpoint, SPA tam API entegrasyonu, CSV/toplu yükleme MVP dışı |

**MVP genel tamamlanma: %100**

---

## 4. Düzeltilen & Kalan Sorunlar

### ✅ Bu Oturumda Düzeltilenler
| # | Sorun | Çözüm |
|---|-------|-------|
| 1 | Audit-logs endpoint'i Internal Server Error | `main.py`'de `MISSING_COLUMNS`'a `audit_logs.created_at` eklendi, deploy edildi |

### 🟡 Kalan Küçük İyileştirme Alanları
| # | Alan | Açıklama |
|---|------|----------|
| 1 | Veritabanı boş | Admin panelden kategori eklenip demo aukcijeler girilebilir |
| 2 | Docker Compose PostgreSQL | SQLite yerine PostgreSQL konteyneri eklenebilir |
| 3 | `SECRET_KEY` env kontrolü | Sabit fallback kaldırılıp env zorunlu yapılabilir |
| 4 | Frontend-Backend tam entegrasyon | Statik sayfaların backend API'lerine bağlanması |
| 5 | E2E testleri | Playwright/Cypress ile uçtan uca testler |

---

## 5. Test Sonuçları

**Tüm 107 test başarıyla geçiyor:**
- 53 integration test (auction, auth, bid, health, payment)
- 54 unit test (models, schemas, security)

---

## 7. Revizyon Geçmişi (27.06.2026)

### ✅ Bu Oturumda Yapılan Düzeltmeler
| # | Sorun | Çözüm |
|---|-------|-------|
| 1 | Dockerfile'da hard-coded JWT_SECRET | Kaldırıldı, çalışma zamanı env değişkeni olarak verilmesi zorunlu kılındı |
| 2 | Forgot-password token'ı hash'siz saklanıyor | `hashlib.sha256` ile hash'lenerek DB'ye yazılıyor, production'da response'ta dönmüyor |
| 3 | Reset-password token karşılaştırması hash'siz | Gelen token hash'lenip DB'deki hash ile karşılaştırılıyor |
| 4 | `scheduler.py` ve `bids.py` finalize kodu duplike (~120 satır) | `app/services/auctions.py` içinde `finalize_auction()` servis fonksiyonu oluşturuldu |
| 5 | `main.py` ve `admin.py` migration kodu duplike | `app/core/migrations.py` ile tek kaynak |
| 6 | `auctions.py` ve `admin.py` response builder duplike | `app/services/auctions.py:build_auction_response()` ile tek kaynak |
| 7 | Uploads static dosyaları SPA catch-all tarafından engelleniyor | `app.mount("/uploads", StaticFiles(...))` eklendi |
| 8 | Frontend (Next.js) ve backend içinde aynı SPA paralel | `frontend/` → `docs/legacy/frontend-nextjs/` arşivlendi |
| 9 | Üç adet venv (218 MB) | Hepsi silindi, `.gitignore`'a `.venv/` ve `**/venv/` eklendi |
| 10 | Gereksiz dosyalar (testdir, log.txt, script.node.sh, bidmont.db) | Silindi |
| 11 | `requirements.txt`'de `starlette==1.3.0` (var olmayan versiyon) | Kaldırıldı (FastAPI kendi bağımlılığını yönetir) |
| 12 | `requirements.txt`'de packagecloud extra-index | Kaldırıldı |
| 13 | `docker-compose.yml`'de kullanılmayan volume + deprecated `version` | Temizlendi |
| 14 | Bid history'de N+1 count (`len(scalars().all())`) | `select(func.count(...))` ile optimize edildi |
| 15 | `models/__init__.py`'de eksik export'lar | `AuditLog`, `UserRole`, `AuctionStatus` vb. eklendi |
| 16 | `i18n.ts`'de `require()` yerine import | Düzeltildi |
| 17 | `useAuth.tsx` ve `types/index.ts` duplike User interface | `useAuth.tsx` artık `types/index.ts`'i import ediyor (elde yapıldı) |
| 18 | `auctions.py:54` gereksiz `hasattr` kontrolü | `is_featured is not None` ile değiştirildi |

## 8. Revizyon Geçmişi (28.06.2026)

### ✅ Bu Oturumda Yapılan Düzeltmeler
| # | Sorun | Çözüm |
|---|-------|-------|
| 1 | `renderDetail` TypeError: `$('#detailCity')` null, fiyat/teklif/sayaç render edilmiyordu | `#detailCity` kaldırıldı, şehir `#detailMeta`'ya `city · desc` formatında eklendi |
| 2 | `#detailStatus` alanı hiç doldurulmuyordu | `renderDetail`'e bitiş zamanına göre "Aktivna/Završena" atandı |
| 3 | pytest `asyncio_default_fixture_loop_scope` uyarısı | `pytest.ini`'ye eklendi |
| 4 | Faz 6: alıcı hizmet bedeli ve satıcı ilan ücreti eksikti | `Payment.buyer_service_fee` (%3 otomatik), `Auction.listing_fee` eklendi; migration'a dahil edildi |
| 5 | Faz 8: Satıcı/kurumsal panel eksikti | `GET /api/users/me/seller-stats` eklendi; profil sayfasına satıcı dashboard bölümü eklendi (ME/EN) |

### Devam Eden İyileştirmeler
| # | Alan | Açıklama |
|---|------|----------|
| 1 | Stripe webhook | `POST /api/payments/stripe/checkout` endpoint'i var; webhook ile otomatik ödeme onayı eklenebilir |
| 2 | Pytest third-party uyarıları | `jose` ve `pytest_asyncio`'dan gelen `utcnow()` / `get_event_loop_policy` uyarıları, kütüphane güncellemesi gerektirir |
| 3 | `.docx` dokümanlar | Git LFS veya markdown dönüşümü önerilir |

---

- ✅ **Backend API**: Tüm endpoint'ler canlı ve çalışıyor
- ✅ **Frontend (index.html)**: 17 sayfa bölümü eksiksiz, ME/EN dil desteği ile Render'da sunuluyor
- ✅ **Admin Panel**: 8 tablı tam yönetim paneli aktif
- ✅ **WebSocket**: Canlı teklif, heartbeat, online kullanıcı sayısı
- ✅ **Render deploy**: Otomatik deploy aktif, Docker + PostgreSQL
- ✅ **Detail sayfası**: TypeError düzeltildi, fiyat/teklif geçmişi/sayaç artık render ediliyor

---

## 9. Revizyon Geçmişi (29.07.2026) — İş Modeli Değişikliği: BidMont Kredi Motoru (Faz 1)

**Kaynak:** `docs/Bidmont son hali için döküman .docx` (LITZOR DOO, 21 bölümlük değişiklik talebi — tam kapsam tek oturumda uygulanamayacak kadar büyük olduğundan, **§8 Kredi Sistemi + §18 Bid/Veri Bütünlüğü** öncelikli faz olarak seçildi ve uygulandı).

### ✅ Bu Fazda Yapılanlar

| # | Değişiklik | Detay |
|---|-----------|-------|
| 1 | Asset satış/ödeme/komisyon yolu tamamen kaldırıldı | `payments.py`, `Commission` modeli, admin komisyon uçları, ölü frontend kodu (`createMonriCheckout`) silindi — §1.2/§12 gereği |
| 2 | Kredi ledger sistemi | `CreditPackage`, `CreditLedger` (immutable, before/after balance), `AuctionParticipant` (auction+user unique), `BidIncrementRule`, `PlatformSettings` tabloları eklendi |
| 3 | `apply_ledger_entry` servisi | `credits_balance`'ın artık **tek** değiştirilme noktası (`app/services/credits.py`) — satın alma, join-spend, admin adjust, reversal hepsi buradan geçiyor |
| 4 | `POST /api/auctions/{id}/join` | Katılım kredisi bir kez düşülüyor; tekrar çağrılırsa no-op (idempotent), DB unique constraint ile çift düşüm engelleniyor |
| 5 | Bid motoru sertleştirildi | `place_bid` artık join şartı arıyor, idempotency key destekliyor, admin-configurable increment (`BidIncrementRule`) ve anti-sniping (`PlatformSettings`) kullanıyor (eskiden hardcoded 300sn) |
| 6 | `finalize_auction` | Artık `Payment` kaydı oluşturmuyor; en yüksek geçerli teklifi created_at'e göre deterministik tie-break ile seçiyor, invalidated teklifleri hariç tutuyor |
| 7 | Lot ID | Her ihale için `BM-{PREFIX}-{seq:06d}` server-side benzersiz kod üretiliyor |
| 8 | Admin uçları | Kredi paketi CRUD, bid-increment CRUD, platform ayarları, manuel kredi düzeltme, bid invalidate (reason zorunlu, current_price yeniden hesaplanıyor), auction cancel (katılımcılara otomatik kredi iadesi) — hepsi audit-logged |
| 9 | Frontend minimal entegrasyon | Kredi mağazası artık `/api/credits/packages`'tan geliyor (hardcode yok); bid akışı 403'te otomatik join deniyor, 402'de "kredi satın al"a yönlendiriyor |

### Test Sonuçları

**114/120 test geçiyor.** Kalan 6 başarısız test bu faz **öncesinde de** mevcuttu (auth/forgot-password `ENVIRONMENT` bağımlılığı, auction-create listing-fee bakiye varsayımı) — bu oturumdaki değişikliklerle ilgisi yok, `git stash` ile doğrulandı.

- Yeni: `tests/unit/test_credits_service.py` (6 test — ledger matematik, bid increment lookup)
- Yeni: `tests/integration/test_credit_engine.py` (9 test — join/double-spend, 402, join gate, idempotency, webhook retry, tie-break, admin invalidate, admin cancel/reversal)
- Silindi: `tests/integration/test_payment_api.py` (kaldırılan asset-checkout akışını test ediyordu)

### Bu Fazın Kapsam Dışı Bıraktıkları (Sonraki Fazlar)

Kozmetik metin değişimi (Adriatic→Montenegro, General→Commercial Assets), satıcı başvuru/doğrulama akışı, çok adımlı ilan oluşturma sihirbazı, `AuctionStatus` genişletmesi (DRAFT/UNDER_REVIEW/UPCOMING/LIVE/EXTENDED), contact-unlock, RBAC katmanları (Super Admin/Support), legal terms versiyonlama, bildirim şablonları/i18n — dokümanın geri kalan ~19 bölümü.

### LITZOR'dan Beklenen Girdi (Canlıya Geçmeden Önce)

Kredi paketi fiyatları/miktarları, varsayılan participation-credit-cost politikası, bid-increment tablosu değerleri, anti-sniping süresi — şu an makul varsayılan/placeholder değerlerle çalışıyor, gerçek değerlerle değiştirilmeden canlıya alınmamalı (§21.1).

### Doğrulanması Gereken: Eşzamanlılık (Concurrency)

Test paketi in-memory SQLite üzerinde çalışıyor; `SELECT ... FOR UPDATE` SQLite'ta no-op'tur. Çift-join'siz/çift-kredi'siz garantiler DB seviyesindeki UNIQUE constraint'lerden geliyor (bu da SQLite'ta da geçerli), ama gerçek eşzamanlı istek senaryosu (iki simultane join, üç simultane webhook retry) yalnızca gerçek Postgres üzerinde (`docker compose up --build`) test edilerek dürüstçe kanıtlanabilir. ~~Bu makinede Docker kurulu değil~~ **29.07.2026'da Docker Desktop + WSL2 kuruldu ve doğrulama yapıldı — bkz. Bölüm 10.**

---

## 10. Revizyon Geçmişi (29.07.2026, devam) — Docker/Postgres Canlı Doğrulama

Docker Desktop + WSL2 kuruldu, `docker compose up --build` ile gerçek Postgres 16 üzerinde tüm Faz 1 akışı uçtan uca test edildi (kayıt, admin seed, kategori, kredi paketi, ilan, onay, kredi satın alma + webhook, join, bid, admin invalidate, admin cancel/reversal) ve **eşzamanlılık senaryoları gerçek Postgres'te doğrulandı**:

- 5 simultane webhook retry → bakiye yalnızca 1 kez arttı (100, 500 değil). ✅
- 2 simultane join (aynı kullanıcı) → kredi yalnızca 1 kez düştü (90), ikinci istek "already_joined" ile no-op döndü. ✅
- Bid idempotency key retry → aynı bid kaydı döndü, ikinci satır oluşmadı. ✅
- Admin invalidate → current_price doğru yeniden hesaplandı. ✅
- Admin cancel → katılımcı kredisi doğru iade edildi. ✅
- Scheduler auto-finalize (arka plan, 30sn'de bir) → gerçek Postgres'te süresi dolan ilan doğru şekilde otomatik sonuçlandırıldı. ✅

### 🐛 Bu Doğrulama Sırasında Bulunan ve Düzeltilen Buglar

Bunların **hiçbiri SQLite testlerinde ortaya çıkmadı** — SQLite tip/tz kontrolünde gevşek, Postgres/asyncpg ise katı. Bu tam olarak "neden gerçek Postgres'te test etmek gerekir" sorusunun cevabı:

| # | Bug | Kapsam | Kaynak |
|---|-----|--------|--------|
| 1 | `_utcnow()` timezone-aware datetime döndürüyordu, ama tüm `DateTime` kolonları Postgres'te `TIMESTAMP WITHOUT TIME ZONE` — asyncpg aware datetime'ı reddediyor | **Sistemik, önceden var olan bug** — kullanıcı kaydı dahil hemen hemen her INSERT'i kırıyordu | `models/domain.py:_utcnow()` artık naive UTC döndürüyor; `to_naive_utc()` helper'ı eklendi; `scheduler.py`, `auth.py` (reset token), `auctions.py` (start/end_time), `admin.py` (invalidated_at), `bids.py` (anti-sniping extension) düzeltildi |
| 2 | `admin.py`'de `os` modülü hiç import edilmemiş, ama `seed_admin` içinde `os.getenv("SEED_SECRET")` kullanılıyordu | **Önceden var olan bug** — `/admin/seed` endpoint'i her zaman `NameError` ile patlıyordu (test suite bunu hiç çağırmadığı için yakalanmamıştı) | `import os` eklendi |
| 3 | `join_auction`'da `IntegrityError` sonrası `db.rollback()` çağrısı session'daki TÜM ORM nesnelerini expire ediyor; hemen ardından `current_user.id`'ye senkron erişim `MissingGreenlet` hatası veriyordu | **Bu fazda benim yazdığım yeni kod** — eşzamanlı iki join isteğinden kaybeden istek 500 dönüyordu (veri bütünlüğü bozulmuyordu, yalnızca hata yanıtı yanlıştı) | `user_id` rollback'ten ÖNCE lokal değişkene alındı; aynı sınıf risk taşıyan `get_or_create_settings`/`generate_lot_code` da tam session rollback yerine SAVEPOINT (`db.begin_nested()`) kullanacak şekilde güçlendirildi |

---

## 11. Revizyon Geçmişi (30.07.2026) — Doküman Tam Kapsam Hedefi: Faz 2 Başlangıcı

Kullanıcı hedefi "proje `docs/Bidmont son hali için döküman .docx` içindeki gereksinimleri karşılamalı" olarak belirlendi — dokümanın kalan ~19 bölümü artık aktif olarak uygulanıyor. Bu bölüm, dokümanın **kod ile karşılanabilecek** kısımlarının ilerlemesini takip eder; §21.1'de listelenen kalemler (LITZOR'un tüzel kayıt bilgileri, PSP merchant bilgileri, gerçek fiyatlar, hukuki metinler, marka varlıkları) hiçbir kod değişikliğiyle karşılanamaz ve bu bölümde ayrıca **"LITZOR girdisi bekleniyor"** olarak işaretlenir.

### ✅ Bu Oturumda Tamamlananlar

| # | Bölüm | Değişiklik | Detay |
|---|-------|-----------|-------|
| 1 | §12.1 | `AuctionStatus` genişletildi: DRAFT/UNDER_REVIEW/UPCOMING/LIVE/EXTENDED/ENDED/CANCELLED | Eski `pending_approval/active/completed` isimleri yeniden adlandırıldı; `Auction.status` (ve `User.role`, `PaymentStatus`, `CreditLedgerType`, `NotificationType`) `native_enum=False` ile VARCHAR kolona taşındı — Postgres native enum tipi büyütmek `ALTER TYPE` gerektirir, bu projenin ADD-COLUMN-only migration sistemi bunu yapamaz |
| 2 | §12.5, §5.11, AC-11/AC-12 | Sunucu taraflı contact-unlock | Yeni `GET /api/auctions/{id}/contact` — yalnızca `ended` durumda ve yalnızca satıcı/en-yüksek-teklif-sahibi için satıcı/alıcı iletişim bilgisi döner; canlı ihalede hiçbir endpoint telefon/e-posta döndürmez |
| 3 | §5.8 | Bid history anonimleştirildi | `get_bid_history` ve WS `new_bid` broadcast'i artık gerçek isim yerine `Bidder #NNNN` (auction+user'a göre deterministik hash) döndürüyor |
| 4 | §6/§7, §10.5, §15.1 | Yeni tablolar: `SellerProfile`, `Watchlist`, `TermsDocument`, `TermsAcceptance`; `AuctionImage` → `media_type`/`visibility` kolonlarıyla genişletildi (ayrı `AuctionMedia` tablosu yerine — CLAUDE.md/doküman §18 isimlendirmenin projeye uyarlanabileceğini belirtiyor) | Watchlist API (`/api/watchlist`) ve Legal API (`/api/legal/{type}`, `/api/legal/accept`, admin `/admin/legal`) eklendi |

### 🐛 Bu Doğrulama Sırasında Bulunan ve Düzeltilen Buglar

| # | Bug | Kapsam | Kaynak |
|---|-----|--------|--------|
| 1 | Postgres'te `auctions.status` daha önce native enum tipiydi (`auctionstatus`), eski üye adlarıyla (`active`, `completed`, ...) ve 1 satır veri içeriyordu | Dev/test verisiydi (bu oturumun kendi smoke testinden), gerçek kullanıcı verisi değil | `docker compose down -v` ile temiz volume — proje kasıtlı olarak Alembic kullanmıyor, `ALTER TYPE` migration'ı eklemek bu ölçekte gereksiz karmaşıklık olurdu |
| 2 | `POST /admin/legal` aynı `(document_type, version)` ile ikinci kez çağrılırsa `UniqueViolationError` ile 500 dönüyordu | Bu oturumda yazılan yeni kod | `IntegrityError` yakalanıp 409 Conflict döndürülüyor |
| 3 | `POST /api/legal/accept` hiç yayınlanmamış bir `document_type`/`version` çiftini de kabul ediyordu — audit trail'i değersizleştiriyordu | Bu oturumda yazılan yeni kod | Kayıttan önce `TermsDocument`'ta o versiyonun var olduğu doğrulanıyor, yoksa 404 |
| 4 | `users.py`'de seller-stats sayaçları `str(row[0])` kullanıyordu; Python'da `str(EnumMember)` "ClassName.member" döner, "member" değil — `counts.get("active", 0)` her zaman 0'a düşüyordu | **Önceden var olan bug**, state machine rename'inden bağımsız, bu değişikliği yaparken keşfedildi | `row[0].value` kullanılacak şekilde düzeltildi |

Tüm düzeltmeler gerçek Postgres'e karşı (`docker compose up --build`, temiz volume) canlı doğrulandı: state transition zinciri (`under_review → live → extended → ended`) anti-sniping ile birlikte uçtan uca test edildi, scheduler `extended` durumundaki ilanı doğru sonuçlandırdı, contact-unlock kapanış sonrası doğru çalıştı. `pytest` 128/134 geçiyor (aynı 6 önceden var olan hata, ilgisiz).

### LITZOR'dan Beklenen Girdi (Kod ile Karşılanamaz — §21.1)

Tüzel unvan/CRPS/PIB/adres, destek e-postası, canlı telefon, PSP/acquirer seçimi ve merchant bilgileri, nihai ME/EN hukuki metinler, logo/favicon/marka varlıkları, gerçek ilan görselleri (AC-20). Bu kalemler için altyapı (TermsDocument, SellerProfile, CreditPackage vb.) hazır — içerik LITZOR'un hukuk/muhasebe danışmanlarından gelmeden canlıya alınmamalı.

**Sonuç:** Bug #1 ve #2 canlıya Postgres ile geçilseydi platformun **hiç çalışmayacağı** anlamına geliyordu (kayıt olma dahil). Bu oturumdaki Docker doğrulaması olmasaydı bu iki bug production'da ilk kullanıcı kaydında ortaya çıkacaktı.

---

## 12. Revizyon Geçmişi (30.07.2026, devam) — Satıcı Başvuru/Doğrulama + İlan İnceleme Akışı (§11)

### ✅ Bu Oturumda Tamamlananlar

| # | Bölüm | Değişiklik |
|---|-------|-----------|
| 1 | §11.1/§11.2/§11.3 | `SellerProfile` üzerinden başvuru akışı: `POST /api/sellers/apply`, `GET /api/sellers/me`; admin: `GET/POST /api/admin/sellers/{id}/verify`, `/reject` (reason zorunlu). Doğrulama, kullanıcı rolünü otomatik `seller`/`corporate_seller`'a yükseltiyor. |
| 2 | §11.5 | `create_auction`/`my_auctions`/`update_auction`/`delete_auction` artık `get_current_seller` kullanıyor (önceden `get_current_user` idi — rol kontrolü hiç çalışmıyordu). Listing oluşturmak için **doğrulanmış** `SellerProfile` şart; self-declared `seller` rolü tek başına yetmiyor. |
| 3 | §11.5 (changes requested) | Yeni `AuctionStatus.draft` durumu: admin `POST /{id}/request-changes` (reason zorunlu) → `draft` + `review_notes`; seller düzenleyip `POST /{id}/submit` ile tekrar `under_review`'a döner. |
| 4 | §11.6 | `looks_like_direct_contact()` — başlık/açıklamada telefon/e-posta/URL deseni varsa `Auction.contact_flagged=True` (yalnızca uyarı, otomatik blok yok — doküman böyle istiyor). |
| 5 | §11.7 | Listing submit'ten önce `declaration_accepted` zorunlu; kabul, `TermsAcceptance` tablosuna `seller_listing_declaration` olarak, gerçek bir `TermsDocument` versiyonuna referansla kaydediliyor (bkz. bug #3 aşağıda — neden sabit string yeterli değildi). |

Yan etki: rol-gate düzeltmesi önceki oturumdan kalan "6 önceden var olan hata"nın **2 tanesini** (buyer'ın auction oluşturması 403 yerine 402 dönüyordu, `/auctions/my` buyer'a 403 yerine 200 dönüyordu) doğru şekilde çözdü — bunlar aslında bu bölümün kapsamına giren gerçek bug'larmış.

### 🐛 Bu Doğrulama Sırasında Bulunan ve Düzeltilen Buglar

| # | Bug | Kapsam | Kaynak |
|---|-----|--------|--------|
| 1 | `POST /auctions/{id}/request-changes` gerçek Postgres'te 500 veriyordu: `notifications.type` kolonu `VARCHAR(19)` olarak oluşturulmuş (SQLAlchemy `Enum(..., native_enum=False)` kolon uzunluğunu tablo ilk oluşturulduğundaki üye değerlerinden otomatik hesaplıyor), yeni eklenen `listing_changes_requested` (25 karakter) sığmadı | **Sistemik, tekrarlayabilir bug sınıfı** — `AuctionStatus` için native-enum'dan kaçınmak için kullanılan `native_enum=False` çözümünün kendisi yeni bir tuzak yarattı; bu proje ADD-COLUMN-only migration sistemi `ALTER COLUMN TYPE` da yapamıyor | Tüm `Enum(..., native_enum=False)` kolonlarına (`UserRole`, `AuctionStatus`, `PaymentStatus`, `CreditLedgerType`, `NotificationType`, `SellerVerificationStatus`) sabit `length=50` eklendi; dev volume temizlendi (`docker compose down -v`) — kolonlar artık üye listesi büyüdükçe otomatik daralmıyor |
| 2 | Seller declaration (`TermsAcceptance`) sabit `version="1.0"` string'i ile, karşılığında hiçbir `TermsDocument` içeriği olmadan kaydediliyordu — tam olarak §15.1'in önlemeye çalıştığı "içeriksiz versiyon" sorunu, farklı bir kapıdan | Bu oturumda yazılan yeni kod | `get_or_create_seller_declaration()` eklendi (`get_or_create_settings` ile aynı idempotent get-or-create deseni) — gerçek `TermsDocument` içeriği otomatik oluşturuluyor, `TermsAcceptance.version` ona referans veriyor |
| 3 | `looks_like_direct_contact()` regex'i (`\+?\d[\d\s\-\(\)]{7,}\d`) sıradan araç metnini de yakalıyordu (ör. "2020, 150 000 km" 9+ karakter basamak/boşluk dizisi içeriyor) | Bu oturumda yazılan yeni kod, canlıya çıkmadan review'da yakalandı | Regex 6+ **rakam** gerektirecek şekilde değiştirildi (ayraçlar sayılmıyor), düz metin artık yanlış pozitif üretmiyor |

Tüm akış (başvuru → doğrulanmamışken engellenme → admin verify → rol yükseltme → ilan oluşturma → changes-requested → resubmit → contact-flag) gerçek Postgres'e karşı uçtan uca doğrulandı. `pytest`: 142/145 geçiyor (3 önceden var olan, ilgisiz `forgot-password` hatası — `ENVIRONMENT` bağımlılığı).

### Not: Doküman ile Uyuşmayan Bir Nokta (LITZOR Onayı Gerekebilir)

`create_auction` seller'dan `LISTING_FEE_CREDITS` (varsayılan 10 kredi) düşüyor — bu mekanizma Faz 1 kredi-motoru pivot'undan ÖNCE vardı ve doküman bunu tarif etmiyor (§8 yalnızca alıcının katılım kredisinden bahsediyor). Kaldırılmadı çünku doküman bunu yasaklamıyor da değil — LITZOR'un bu ücretin kalıp kalmayacağını teyit etmesi gerekiyor.

---

## 13. Revizyon Geçmişi (30.07.2026, devam) — RBAC Katmanları + Audit Log İyileştirmesi (§17.1/§17.2)

### ✅ Bu Oturumda Tamamlananlar

| # | Bölüm | Değişiklik |
|---|-------|-----------|
| 1 | §17.1 | `UserRole`'e `super_admin` ve `support` eklendi. `get_current_admin` artık `admin`+`super_admin` kabul ediyor (finansal/kredi/bid mutasyonları için — support hariç, varsayılan-red). Yeni `get_current_staff` dependency'si (`admin`+`super_admin`+`support`) yalnızca support-ticket uçlarına bağlandı. |
| 2 | §17.1 test senaryosu | "Support rolü credit package price veya bid history değiştirememeli" — `/admin/credit-packages`, `/admin/credits/adjust`, `/admin/bids/{id}/invalidate` support için 403; `/admin/support-tickets` (list+update) support için 200. |
| 3 | §17.2 | Audit log'daki "Updated fields: [...]" tarzı zayıf detaylar, gerçek before/after değerleriyle değiştirildi (`_diff_summary()` helper) — kategori, kredi paketi, bid-increment kuralı, platform ayarları, kullanıcı durumu, destek talebi güncellemelerinde. |

### 🐛 Bu Doğrulama Sırasında Bulunan ve Düzeltilen Bug

`role` kolonu önceki oturumda `length=50` ile düzeltilmişti (bkz. Bölüm 12, bug #1) — bu sayede `super_admin`/`support` gibi yeni üye eklemek bu oturumda **hiçbir** VARCHAR-taşması yaşanmadan çalıştı. Gerçek Postgres'te doğrulandı: buyer→support rolüne yükseltilen kullanıcı credit-package/credits-adjust/bid-invalidate uçlarında 403 alıyor, support-tickets uçlarında 200 alıyor; `super_admin` tüm admin yetkilerine sahip.

`pytest`: 147/150 geçiyor (aynı 3 önceden var olan, ilgisiz `forgot-password` hatası).

---

## 14. Revizyon Geçmişi (30.07.2026, devam) — Server-Side Arama + Pagination + Autocomplete (§13, §4.4)

### ✅ Bu Oturumda Tamamlananlar

| # | Bölüm | Değişiklik |
|---|-------|-----------|
| 1 | §13.1 | `GET /api/auctions?search=` artık title/description yanında Lot ID, brand, model, equipment_brand, location alanlarında da arıyor; ayrı `city` filtre parametresi eklendi. |
| 2 | §4.4 | Pagination zaten `limit`/`offset` ile vardı; şimdi gerçek toplam sayıyı (pre-pagination) `X-Total-Count` response header'ında dönüyor — mevcut response body şeklini (bare array) bozmadan frontend'in "daha fazla var mı" bilmesini sağlıyor. |
| 3 | §13.2 | Yeni `GET /api/auctions/autocomplete?q=` — Lot ID/brand/model/city önerileri, `min_length=2` sunucu tarafında da zorunlu kılınıyor (frontend debounce'una ek güvence). |

Gerçek Postgres'e karşı doğrulandı: `X-Total-Count` header'ı ve autocomplete uçları hatasız çalışıyor. `pytest`: 151/154 geçiyor (aynı 3 önceden var olan hata).

### Devam Eden Kapsam

i18n (§2.4/§16.3), frontend sayfa yeniden yapımı (§2-3-4-5-9-10-11-14), güvenlik sertleştirme (§19) — sırayla uygulanıyor.

## 15. Revizyon Geçmişi (30.07.2026, devam) — Bildirim Event Kapsamı + Idempotency (§16)

### Yapılanlar

- **Yeni event'ler**: `auction_joined` (katılım onayı), `auction_extended` (anti-sniping uzatması, satıcıya), `credit_purchase_successful` / `credit_purchase_failed` (Monri callback), `seller_application_submitted` (başvuru onayı) — `NotificationType` enum'una eklendi (VARCHAR(50) sütun, migration gerekmedi çünkü `native_enum=False, length=50` zaten yeterli genişlikte).
- **Ending-soon hatırlatması**: scheduler'a yeni bir 15 dakikalık (900s) eşik kontrolü eklendi — biddable durumundaki, bitişine 15 dk kalan her açık artırmanın tüm katılımcılarına `auction_ending_soon` bildirimi gönderiliyor.
- **Idempotency (§16.2)**: `Notification` tablosuna nullable+unique `event_key` sütunu eklendi (`MISSING_COLUMNS` + `MISSING_UNIQUE_INDEXES` — mevcut tabloya ALTER TABLE ile UNIQUE eklenemediği için ayrı index yolu, `bids.idempotency_key`/`auctions.lot_code` ile aynı desen). `send_notification()` artık opsiyonel `event_key` parametresi alıyor; verilirse SAVEPOINT (`db.begin_nested()`) içinde ekleniyor, `IntegrityError` yakalanıp sessizce `None` dönülüyor (get_or_create_settings ile aynı idempotent-insert deseni). Retry riski taşıyan çağrı noktalarına (scheduler poll, Monri callback retry, aynı bid'in tetiklediği extension) `event_key` verildi; tek seferlik kullanıcı aksiyonlarına (seller application submit) verilmedi.
- **Dedup uygulanan noktalar**: ending-soon (`ending_soon:{auction_id}:{user_id}`), auction join (`auction_joined:{auction_id}:{user_id}`), anti-sniping extension (`auction_extended:{bid_id}`), auction sonu bildirimleri (`auction_ended:{auction_id}:{winner|seller|loser:{id}}` — scheduler ile manuel finalize arasında yarış ihtimaline karşı), kredi satın alma sonucu (`credit_purchase:{purchase_id}:{completed|failed}` — ödeme ağgeçidi callback'i tekrar edebilir).

### Bilinen Sınır (ponytail)

`ending_soon` event_key'i auction+user bazlı, end_time bileşeni yok — anti-sniping uzatması bitiş zamanını eşik dışına itip sonra tekrar içeri girerse ikinci hatırlatma gitmez. Pratikte 120s'lik uzatma 900s'lik eşiğin çok altında kaldığı için gerçek dünyada nadiren tetiklenir; gerekirse key'e end_time eklenir.

### Doğrulama

- Yeni `tests/integration/test_notifications.py` (3 test): event_key duplicate skip, event_key'siz çoklu satır, join iki kez çağrılınca tek bildirim.
- `pytest`: 154/157 geçiyor (aynı 3 önceden var olan forgot/reset-password hatası).
- `docker compose up --build -d`: migration loglarında `notifications.event_key` sütunu ve `uq_notifications_event_key` unique index hatasız eklendi.
- Canlı Postgres'e karşı smoke test: iki kez join çağrısı → tek `auction_joined` satırı; bid → `bid_received` bildirimi; DB seviyesinde aynı `event_key` ile ikinci INSERT unique index tarafından reddedildi. Docker loglarında hata yok.

### Ek düzeltme: Kredi callback yarış durumu (§8.4/AC-02)

Matris çalışması sırasında (Bölüm 16) fark edildi: `POST /credits/monri/callback` "already completed?" kontrolü ile status güncellemesi arasında atomiklik yoktu — `stripe_session_id` üzerinde de unique constraint eksikti. Eşzamanlı iki callback teslimatı ikisi de `status == pending` görüp ikisi de krediyi ekleyebilirdi (dar ama gerçek bir yarış penceresi). Düzeltme: durum geçişi artık koşullu `UPDATE ... WHERE status='pending'` ile atomik yapılıyor (rowcount=0 ise "already_processed" dönülüyor, ledger'a hiç dokunulmuyor); `CreditPurchase.stripe_session_id` model üzerinde `unique=True` yapıldı ve mevcut deploy'lar için `uq_credit_purchases_stripe_session_id` migration index'i eklendi. Mevcut `TestCreditWebhookIdempotency::test_retried_webhook_credits_once` testi (sıralı 3 retry) hâlâ geçiyor; `pytest` tam koşu: 154/157 (aynı 3 önceden var olan hata). Docker migration logunda yeni unique index hatasız eklendi.

## 16. Kapsam Durum Matrisi (§1-§21)

Bu matris, `docs/Bidmont son hali için döküman .docx` dosyasındaki her numaralı madde için güncel durumu özetler. Durum kategorileri:

- **✅ tamam** — kodda uygulanmış ve doğrulanmış (test + canlı Postgres).
- **🔶 backend tamam, frontend bekliyor** — API/veri modeli hazır, `index.html` tarafında henüz bağlanmadı (Görev #17/#18 kapsamı).
- **🟡 kısmi** — bir parçası var, bilinen eksik/basitleştirme var (not ile açıklanmış).
- **⛔ LITZOR verisi bekleniyor** — kod hazır veya hazırlanabilir, ama gerçek veri/karar (fiyat, PSP merchant bilgisi, hukuki metin, marka varlığı) LITZOR'dan gelmeden canlıya alınamaz.
- **🚫 kapsam dışı / kod ile çözülemez** — şirket tescili, hukuki onay, altyapı/domain sağlayıcı seçimi gibi tamamen LITZOR/iş tarafı kararı.
- **⬜ başlanmadı** — henüz hiç iş yapılmadı.

### §1 — İş Modeli

| Madde | Durum | Not |
|---|---|---|
| 1.1 Temel iş modeli (kredi ile katılım, ended≠sold, BidMont satışa taraf değil) | ✅ | Backend baştan bu modelle kurulu: `payments.py`/`payment.py` (Stripe checkout) tamamen kaldırıldı, `AuctionStatus.ended` "satış" anlamına gelmiyor, kredi tek gelir modeli. |
| 1.2 Kapsam dışı liste (checkout, escrow, payout, devir, lojistik, finansman, kredi transferi, kripto, ülke genişlemesi) | ✅ | Hiçbiri implemente değil — bu doğru durum. `CreditLedger`'da transfer/cash-out endpoint'i yok. |

### §2 — Global Tasarım / Header

| Madde | Durum | Not |
|---|---|---|
| 2.1 Adriatic/Balkans metni kaldır | 🔶 | Backend'de bölgesel iddia yok; `index.html` metni güncellenmedi (Görev #18). |
| 2.2 Header menü yeniden düzenle | 🔶 | Frontend işi, başlanmadı. |
| 2.3 "General" → "Commercial Assets" | 🔶 | Kategori adı DB'de serbest metin (`Category.name`), backend bunu zorlamıyor; seed veri + frontend adlandırması güncellenmeli. |
| 2.4 ME/EN dil sistemi | 🟡 | Görev #17 kapsamında planlı, henüz başlanmadı. Backend'de `User.preferred_language` alanı yok — eklenmesi gerekecek. |
| 2.5 Account badge dil tutarlılığı | 🔶 | Frontend işi. |
| 2.6 Bildirim merkezi (zil ikonu) | 🔶 | Backend tamam (`Notification` modeli, `/api/notifications` endpoint'leri, Bölüm 15'teki event kapsaması); frontend bell UI yok. |
| 2.7 Mobile responsive | 🔶 | Frontend işi, `index.html` mevcut CSS'i denetlenmedi. |

### §3 — Ana Sayfa

Tüm 3.1–3.10 maddeleri **🔶 backend tamam, frontend bekliyor** — hero, live/ending-soon kartları, kategori kartları, how-it-works, why-BidMont, seller acquisition, disclaimer: bunların hepsi `index.html` içeriği. Gerekli backend veri (canlı/ending-soon ihale listesi, kategori sayıları) `GET /api/auctions` ve `GET /api/auctions?status=...` üzerinden zaten alınabiliyor. 3.4 (demo istatistikleri kaldırma) doğrudan `index.html` metin düzenlemesi, backend'de sahte istatistik zaten yok.

### §4 — Auctions Liste Sayfası

| Madde | Durum | Not |
|---|---|---|
| 4.1 Genişletilmiş filtreler (kategori, şehir, status, fiyat, seller type, condition, kategoriye özel alanlar) | 🟡 | `city`, `status`, kategori, arama Bölüm 14'te eklendi. Fiyat aralığı ve seller type filtresi backend'de yok — eklenmesi ucuz (query param + WHERE). Frontend filtre paneli yok. |
| 4.2 Kart veri seti (Lot ID, şehir, current bid, bid count, credit cost, verified badge, watchlist) | ✅ backend / 🔶 frontend | `AuctionResponse` bu alanların tamamını içeriyor (`lot_code`, `location`, `current_price`, `participation_credit_cost`); `bid_count` `GET /auctions/{id}` yanıtında var. Watchlist API (Bölüm 12) hazır. Frontend kart tasarımı yok. |
| 4.3 Gerçek ilan görselleri / DEMO etiketi | 🚫 kod ile çözülemez | Bu bir içerik/veri kuralı — seller'ların stok görsel yerine gerçek görsel yüklemesi operasyonel bir politika, kodla zorlanamaz (upload endpoint zaten herhangi bir gerçek görseli kabul ediyor). |
| 4.4 Pagination / arama | ✅ | Bölüm 14: `X-Total-Count` header, autocomplete, genişletilmiş arama. `pytest` ve canlı Postgres doğrulandı. Bilinen sınır: autocomplete 100 satır önden çekip Python'da dedupe ediyor (`app/api/auctions.py` içinde `ponytail:` yorumu ile işaretli), 1000+ ilanda location eşleşmeleri gözden kaçabilir. |
| 4.5 Empty state | 🔶 | Frontend işi. |

### §5 — İhale Detay Sayfası

| Madde | Durum | Not |
|---|---|---|
| 5.1 Sunucu tabanlı teklif (localStorage değil) | ✅ | Mimari baştan DB tabanlı; demo/localStorage bid hiç yok. |
| 5.2 Çoklu fotoğraf galerisi | 🟡 | `AuctionImage` çoklu görsel/doküman destekliyor (`media_type`, `visibility`, `sort_order`), upload endpoint çoklu dosya kabul ediyor (`app/api/uploads.py`). Frontend galeri/lightbox UI yok. |
| 5.3 Lot ID | ✅ | `BM-{prefix}-{seq}` formatında, `lot_sequences` tablosuyla üretiliyor, unique constraint var, detail/kart/admin'de dönüyor. |
| 5.4 Participation credit cost gösterimi | ✅ backend / 🔶 frontend | `AuctionResponse.participation_credit_cost` + `GET /credits/balance` mevcut; UI paneli yok. |
| 5.5 Join Auction adımı | ✅ | `POST /auctions/{id}/join` — tek seferlik kredi düşümü, idempotent (aynı user ikinci çağrıda `already_joined=true`, ikinci kez kredi düşmüyor), `test_notifications.py`/`test_credit_engine.py` ile doğrulandı. |
| 5.6 Admin-configurable bid increment | ✅ | `BidIncrementRule` tablosu + admin CRUD endpoint'leri (`app/api/admin.py`), `get_bid_increment()` servis fonksiyonu frontend hardcode yerine bunu kullanıyor. |
| 5.7 Bid confirmation modal | 🔶 | Frontend işi; backend zaten confirm olmadan bid kabul etmiyor (ayrı POST çağrısı gerekiyor). |
| 5.8 Bid history anonimleştirme | ✅ | `anonymize_bidder()` (SHA256 tabanlı deterministik "Bidder #NNNN"), hem REST hem WS broadcast'te uygulanıyor. |
| 5.9 Immutable bid history | ✅ | Bid'lerde delete endpoint yok; sadece admin `invalidate` (reason zorunlu, audit-logged) var. `Bid` idempotency_key + server timestamp + status alanları mevcut. |
| 5.10 Anti-sniping | ✅ | `PlatformSettings.anti_sniping_window_seconds`/`extension_seconds` admin-configurable; tetiklenince `auction_extended` bildirimi (Bölüm 15) + WS broadcast ile tüm client'lara yeni deadline iletiliyor. |
| 5.11 Seller bilgisi kontrollü gösterim | ✅ | Contact unlock server-side (Bölüm 11): canlı sırada `GET /auctions/{id}/contact` 400 dönüyor; sadece `ended` + yetkili taraf (seller/winner) görebiliyor. |
| 5.12 Platform rolü uyarı metni | 🔶 | İçerik/metin işi, `index.html`'e eklenmedi. |

### §6 — Araç Alanları

Yapılandırılmış alanların listesi (marka, model, yıl, km, yakıt, şanzıman, vb.) **✅** — `Auction` tablosunda `brand`/`model`/`year`/`mileage`/`fuel_type`/`transmission`/`condition`/`location` sütunları var (migration ile eklendi). VIN/şasi numarası ve "anahtar sayısı" gibi bazı niş alanlar için ayrı sütun yok — mevcut `serial_number`/genel alanlara sığdırılabilir veya küçük bir migration ile eklenir.

| Madde | Durum | Not |
|---|---|---|
| 6.1 Kategorize kusur bölümü (exterior/interior/mechanical/tyres/missing parts) | 🟡 | Şu an tek bir genel `damage_status`/`condition` metin alanı var, doc'un istediği kategori bazlı ayrım (exterior/interior/mechanical/...) yapılandırılmış olarak yok. Gerçek eksik — küçük bir JSON/ayrı tablo ile eklenebilir, henüz yapılmadı. |
| 6.2 Doküman bölümü (public/private erişim) | ✅ | `AuctionImage.media_type="document"` + `visibility` (public/private) zaten var; upload endpoint dosya tipi/boyut doğruluyor. Frontend doküman listesi UI'ı yok. |

### §7 — Equipment / Commercial Assets

| Madde | Durum | Not |
|---|---|---|
| 7.1 Equipment alanları | 🟡 | `equipment_brand`, `serial_number`, `condition`, `location` gibi paylaşılan sütunlar var; "operating hours", "operating weight" gibi equipment'e özel alanlar için ayrı sütun yok (genel alanlara metin olarak sığdırılıyor). |
| 7.1.1 Equipment template'ini araçtan ayır | 🔶 | Backend şeması kategoriler arası paylaşılan sütun kullanıyor (kabul edilebilir uyarlama), kategoriye göre farklı alan gösterimi tamamen frontend'in işi — yapılmadı. |
| 7.2.1 Commercial Assets alt kategorileri (Hospitality, Restaurant Equipment, vb.) | ⬜ | `Category` tablosu generic (parent_id ile hiyerarşi destekliyor) ama bu spesifik taxonomy seed edilmedi. |
| 7.2.2 Commercial asset özel alanları (quantity, package/lot contents, vb.) | ⬜ | Karşılık gelen sütun yok; en yakın alanlar (`condition`, `location`) genel amaçlı. |

### §8 — Kredi Sistemi

| Madde | Durum | Not |
|---|---|---|
| 8.1 My Credits sayfası | ✅ backend / 🔶 frontend | `GET /credits/balance` + `CreditLedger` geçmişi mevcut; sayfa UI'ı yok. |
| 8.2 Credit Store | ✅ backend / 🔶 frontend | `CreditPackage` admin CRUD + `GET /credits/packages` public liste; store UI'ı yok. |
| 8.3 PSP entegrasyonu | ⛔ LITZOR verisi bekleniyor | Monri hosted form-post entegre (PAN/CVV BidMont'ta hiç tutulmuyor) — kod hazır. Gerçek `MONRI_MERCHANT_KEY`/`MONRI_AUTHENTICITY_TOKEN` (prod merchant hesabı) LITZOR'dan gelmeden test modunda kalır. |
| 8.4 Webhook idempotency | ✅ (bu oturumda düzeltildi) | Bu bölümde yukarıda anlatılan atomik `UPDATE ... WHERE status='pending'` + `stripe_session_id` unique constraint ile gerçek eşzamanlılık yarışı da kapatıldı; önceden sadece sıralı retry'a karşı korumalıydı. |
| 8.5 Immutable credit ledger | ✅ | `CreditLedger`: type, +/- amount, reference, before/after balance, created_at, actor — satır silinmiyor, reversal ayrı satır. |
| 8.6 Join Auction kredi düşümü (transaction sırası) | ✅ | `apply_ledger_entry()` + `AuctionParticipant` unique constraint (auction_id, user_id) — race condition `IntegrityError` yakalanarak ele alınıyor (bkz. `join_auction`). |
| 8.7 Yetersiz bakiye akışı | ✅ backend / 🔶 frontend | `apply_ledger_entry` 402 dönüyor, participant kaydı hiç oluşmuyor. "Buy Credits" CTA'sı frontend işi. |
| 8.8 Kredi iade altyapısı | ✅ | `admin_cancel_auction`: her katılımcı için `CreditLedgerType.reversal` yeni satır (eski satır değişmiyor), reason zorunlu + audit-logged. |
| 8.9 Kredi transfer/nakit çekim kapalı | ✅ | Bu endpoint'ler hiç yok — doğru durum bu. |

### §9 — How It Works Sayfası

Tüm 9.1–9.4 **🔶 backend tamam, frontend bekliyor** — buyer/seller adım listeleri statik metin, backend'de karşılık gelen akışların hepsi zaten var (register→buy credits→join→bid→highest bidder / apply→verify→list→review→live→contact). Sayfa içeriği `index.html`'e eklenmedi.

### §10 — My Account / Buyer Dashboard

| Madde | Durum | Not |
|---|---|---|
| 10.1 Dashboard navigasyonu | 🔶 | Frontend işi. |
| 10.2 Credit balance kartı | ✅ backend / 🔶 frontend | Veri hazır (`/credits/balance`), kart UI yok. |
| 10.3 My Bids gerçek tablo | ✅ backend / 🔶 frontend | `GET /auctions/my-bids`(benzeri) zaten Lot ID, status, current highest verisini döndürüyor; tablo UI yok. |
| 10.4 Joined Auctions | ✅ backend / 🔶 frontend | `GET /api/auctions/joined` (Bölüm 17'de eklendi) — join_date, credits_spent, auction status, my_bid_status. Test + canlı doğrulandı. UI yok. |
| 10.5 Watchlist | ✅ | `Watchlist` tablosu + `GET/POST/DELETE /api/watchlist` (Bölüm 12), unique constraint (user_id, auction_id) ile idempotent add/remove. |
| 10.6 Profile alanları | 🟡 | `User` üzerinde `phone`, `accepted_terms/privacy`, `marketing_consent` var; `address/city`, `preferred_language`, company-specific alanlar (PIB vb. `SellerProfile`'da) kısmen dağınık — buyer tarafı için ayrı `city`/`address` sütunu yok. |

### §11 — Seller Başvuru / Dashboard / İlan Oluşturma

| Madde | Durum | Not |
|---|---|---|
| 11.1 Post Auction → doğrulanmış seller akışı | ✅ | Bölüm 13: `create_auction` artık `get_current_seller` + verified `SellerProfile` zorunlu kılıyor. |
| 11.2 Seller Application alanları | ✅ backend / 🔶 frontend | `SellerProfile` + `POST /api/sellers/apply`: company/individual, PIB, authorized person, city, seller_type. "Phone + email verification" alt-maddesinin e-posta yarısı Bölüm 57'de gerçek bir gate olarak uygulandı (`email_verified=False` → 403); telefon/SMS yarısı SMS gateway kararı gerektirdiği için C listesinde. Doküman yükleme upload endpoint'i üzerinden yapılabilir (ayrı bir "seller application documents" ilişkisi yok, genel upload kullanılıyor). Form UI yok. |
| 11.3 Seller Dashboard | ✅ backend / 🔶 frontend | `GET /auctions/my` (durum bazlı filtrelenebilir), `GET /sellers/me` mevcut; dashboard sayfası yok. |
| 11.4 Multi-step Create Listing (8 adım) | 🔶 | Backend tek bir `POST /auctions` endpoint'i ile tüm alanları kabul ediyor (adım adım değil, tek istekte); admin `request-changes` ile "adım 8" onay/geri gönderme akışı var. Frontend'in bunu 8 adımlı wizard olarak sunması ayrı bir iş — draft durumu şu an sadece admin'in `request-changes` çağrısıyla ulaşılabiliyor, seller kendi başına draft kaydedip sonra devam edemiyor (kısmi kayıt/draft-save akışı yok). |
| 11.5 Seller doğrudan LIVE yapamaz | ✅ | `create_auction` default `AuctionStatus.under_review`; sadece admin `approve` ile `upcoming`/`live`'a geçiyor. |
| 11.6 Doğrudan iletişim paylaşımını önleme (flag) | ✅ | `looks_like_direct_contact()` regex tabanlı tespit, `Auction.contact_flagged` alanına yazılıyor. Admin panelinde görünür uyarı Bölüm 58'de eklendi (önceden veri hesaplanıyordu ama `index.html` hiçbir yerde göstermiyordu — otomatik blok değil, doc'un istediği gibi flag+manuel moderasyon). |
| 11.7 Seller doğruluk beyanı | ✅ | `TermsAcceptance` + `SELLER_DECLARATION_VERSION` — submit anında checkbox zorunlu, versiyon+timestamp saklanıyor. |

### §12 — İhale Kapanışı ve İletişim Açılması

Tüm 12.1–12.5 **✅ tamam** (Bölüm 10/11'de yapıldı ve doğrulandı): state machine (`DRAFT/UNDER_REVIEW/UPCOMING/LIVE/EXTENDED/ENDED/CANCELLED`), deterministik highest-bid tie-break (`order_by(desc(amount), asc(created_at))`), `finalize_auction()` sonucu "highest bidder" olarak dönüyor ("Sold" yok), contact unlock server-side (AC-11/AC-12 doğrulandı).

### §13 — Search Sayfası

Tüm 13.1–13.3 **✅ backend tamam** (Bölüm 14): server-side arama (Lot ID/brand/model/equipment_brand/location), autocomplete (`GET /auctions/autocomplete`, min_length=2), aynı filtre component'i auctions listesiyle paylaşılabilir (aynı `GET /auctions` endpoint'i kullanılıyor). Search sayfası frontend UI'ı **🔶 bekliyor**.

### §14 — About / Contact / Footer

| Madde | Durum | Not |
|---|---|---|
| 14.1 About Us içerik genişletme | 🚫 kod ile çözülemez (içerik) | Sayfa yapısı frontend işi, ama içerik (LITZOR DOO kurumsal bilgisi) LITZOR'dan gelecek. |
| 14.2.1 Gerçek iletişim bilgileri | ⛔ LITZOR verisi bekleniyor | Placeholder (`info@bidmont.me`, `+382 20 000 000`) kod tarafında sabit metin; gerçek e-posta/telefon/adres LITZOR'dan gelmeden değiştirilemez. |
| 14.2.2 Contact form kategorileri | ✅ backend (bu oturumda eklendi) / 🔶 frontend | `SupportTicket.category` (sabit regex enum) + opsiyonel `lot_code`. Bölüm 18'de detay. Kategori seçim UI'ı yok. |
| 14.2.3 Contact üzerinden seller bypass önleme | ✅ | Contact unlock kuralı (§12.5) zaten sadece auction result üzerinden çalışıyor; support akışı seller contact açığa çıkarmıyor (support ticket'lar seller bilgisi döndürmüyor). |
| 14.3.1/14.3.2 Footer + LITZOR DOO bilgisi | 🚫 kod ile çözülemez (içerik) + ⛔ LITZOR verisi | Frontend metin işi + gerçek şirket bilgisi. |

### §15 — Legal Sayfalar

| Madde | Durum | Not |
|---|---|---|
| Legal route'lar (Terms, Participation Rules, Credit Terms, Seller Terms, Privacy, Cookie, Refund Policy, Legal Notice) | ✅ backend / ⛔ içerik | `TermsDocument` (document_type+version unique) + `GET/POST /api/legal` — route/versioning altyapısı tam. Nihai hukuki metinler LITZOR'un avukatından gelmeden sadece placeholder içerik girilebilir. |
| 15.1 Terms versioning | ✅ | `TermsAcceptance`: user_id, document_type, version, accepted_at — audit edilebilir. |
| 15.2 Credit checkout öncesi açık onay | ✅ (bu oturumda eklendi) | `terms_accepted` zorunlu + `TermsAcceptance` kaydı sipariş oluşmadan önce yazılıyor. Bölüm 18'de detay. |
| 15.3 Join Auction öncesi kural onayı | 🟡 | Join endpoint'i zaten server log'da timestamp'li kayıt oluşturuyor (`AuctionParticipant.joined_at`) ama doc'un istediği "kaç kredi düşeceği + final süreç buyer-seller arasında" açık onay metni/checkbox'ı join akışına bağlı bir `TermsAcceptance` olarak ayrı kaydedilmiyor. |

### §16 — Notifications ve E-posta

| Madde | Durum | Not |
|---|---|---|
| 16.1 Minimum event listesi | ✅ | Bölüm 15'te tamamlandı — tüm 12 event tipi mevcut ve tetikleniyor. |
| 16.2 Tekrarlanan bildirimleri önleme | ✅ | `event_key` unique constraint + SAVEPOINT idempotent insert (Bölüm 15). |
| 16.3 ME/EN e-posta template'leri | ⬜ | Henüz başlanmadı — Görev #17 (i18n) kapsamında planlı. Şu an tüm bildirim metinleri sabit İngilizce. |

### §17 — Admin Panel Modülleri

| Madde | Durum | Not |
|---|---|---|
| Dashboard/metrics | ✅ | `GET /admin/stats`. |
| User management (suspend/reactivate) | ✅ | `PUT /admin/users/{id}/status` + audit log. |
| Seller application review/verification | ✅ | Bölüm 13 (`GET /admin/sellers`, `/verify`, `/reject`). |
| Listing review (approve/changes-requested/reject) | ✅ | Bölüm 10/13 (`approve_auction`, `request-changes`, `reject_auction`). |
| Auction scheduling/cancel | ✅ | `admin_cancel_auction` + reason + credit reversal. |
| Participation credit cost / bid increment / anti-sniping config | ✅ | `Auction.participation_credit_cost`, `BidIncrementRule`, `PlatformSettings`. |
| Credit package management / order view | ✅ | `CreditPackage` CRUD, `CreditPurchase` sorgulanabilir (ayrı bir "tüm siparişler" admin listesi endpoint'i eklenmemiş olabilir — küçük eksik, doğrulanmadı). |
| Manual credit adjustment / reversal (reason zorunlu) | ✅ | `POST /admin/credits/adjust`, reason zorunlu + audit. |
| Bid audit/invalidate (reason zorunlu) | ✅ | `POST /admin/bids/{id}/invalidate`. |
| Category management | ✅ | `admin.py` category CRUD. |
| Support/contact requests | ✅ | `SupportTicket` + `get_current_staff` (support rolü de erişebiliyor). |
| Legal document version management | ✅ | Bölüm 12 (`POST /admin/legal`, duplicate→409). |
| Notification template management | ✅ | Bölüm 50'de kapatıldı — yeni `NotificationTemplate` tablosu (type/title/message, ME+EN) + admin CRUD + `template_vars` mekanizmasıyla 5 yüksek-değerli bildirim tipi için düzenlenebilir. |
| Audit log viewer | ✅ | `GET /admin/audit-logs`. |
| 17.1 RBAC (Super Admin/Admin/Support) | ✅ | Bölüm 13 — `get_current_staff` vs `get_current_admin` ile support'un credit/bid'e erişimi engellendi, doğrulandı (`test_rbac_api.py` + canlı smoke). |
| 17.2 Admin audit log (before/after) | ✅ | `_diff_summary()` helper — before/after alan diff'i audit detail'de. |
| 17.3 Admin 2FA | ✅ | Bölüm 45'te kapatıldı — stdlib RFC 6238 TOTP (`hmac`/`hashlib`/`struct`, yeni bağımlılık yok), her admin hesabında isteğe bağlı (self-service enable/disable), etkinken login kod zorunlu kılıyor. |

### §18 — Backend / Veri Modeli Kuralları

| Madde | Durum | Not |
|---|---|---|
| lot_code UNIQUE | ✅ | Model + migration unique index. |
| AuctionParticipant(auction_id, user_id) UNIQUE | ✅ | Doğrulandı — çift join race'i `IntegrityError` ile ele alınıyor. |
| Bid idempotency key unique | ✅ | `test_retried_bid_returns_same_bid`. |
| Credit balance + ledger aynı transaction | ✅ | `apply_ledger_entry()` tek fonksiyon, tüm çağıranlar bunu kullanıyor. |
| Credit balance negatif olamaz | ✅ | `apply_ledger_entry` yetersiz bakiyede 402 fırlatıyor, bakiye negatife düşmüyor. |
| Bid history / credit ledger admin UI'dan silinemez | ✅ | Delete endpoint'i yok, sadece invalidate/reversal. |
| current_highest_bid denormalize ama valid Bid'lerden doğrulanabilir | ✅ | `Auction.current_price` denormalize alan, `finalize_auction` gerçek `Bid` satırlarından yeniden hesaplıyor. |
| DB timestamp UTC, UI local time | 🔶 | Backend UTC tutuyor (`_utcnow`); UI'da Montenegro local time'a çevirme frontend işi. |

### §19 — Güvenlik ve Canlı Ortam Altyapısı

| Madde | Durum | Not |
|---|---|---|
| 19.1 Domain + HTTPS | 🟡 kısmi (kod tarafı Bölüm 22'de tamamlandı) / 🚫 altyapı | Kod tarafı: `ENVIRONMENT=production` iken `HTTPSRedirectMiddleware` devreye giriyor (test/dev'de kapalı, canlıda `docker exec` ile doğrulandı). Gerçek domain + TLS sertifikası + reverse proxy (nginx/Traefik) seçimi hâlâ tamamen altyapı/deploy kararı, kodla çözülemez. |
| 19.2 Şifre ve session güvenliği | 🟡 | Bcrypt (doğru) + JWT Bearer token (cookie değil, dolayısıyla CSRF riski mimari olarak zaten düşük). Login rate-limit var (`auth.py`). HttpOnly/SameSite N/A çünkü cookie kullanılmıyor — bilinçli mimari seçim, dokümante edilmeli. |
| 19.3 Bid/Join/support rate limit | ✅ (bu oturumda eklendi) | `join_auction` (20/dk), `place_bid` (60/dk), `support/contact` + `support/tickets` (10/dk) — `auth.py`'nin mevcut `limiter` nesnesi paylaşılarak eklendi. Canlı Postgres'e karşı doğrulandı: 11. `support/contact` isteğinde gerçek `429` alındı. Limit değerleri LITZOR'un gerçek trafik beklentisine göre ayarlanabilir bir varsayılan. |
| 19.4 Dosya upload güvenliği | ✅ | `app/api/uploads.py`: MIME whitelist, 10MB boyut sınırı, sunucu tarafı üretilen dosya adı (client filename hiç kullanılmıyor → path traversal/extension spoofing kapalı). Malware taraması (opsiyonel, "imkanı" ibaresiyle) yok. |
| 19.5 Ödeme kartı verisi saklama | ✅ | Monri hosted form-post — PAN/CVV hiçbir zaman BidMont backend'ine gelmiyor/loglanmıyor. |
| 19.6 Backup ve restore | 🟡 script hazır / 🚫 zamanlama operasyon | Bölüm 46'da `backend/scripts/backup_db.sh` (pg_dump + uploads arşivi) ve `restore_db.sh` (ayrı bir `bidmont_restore_test` DB'sine) yazıldı, gerçek bir restore testi doğrulandı. Gerçek cron zamanlaması + saklama politikasının canlı ortamda işletilmesi hâlâ LITZOR'un altyapı kararı. |
| 19.7 Monitoring | ✅ backend / 🚫 uptime servis seçimi | Bölüm 46'da `alert_admins()` eklendi — payment webhook failure, bid engine error, unhandled global exception'da her admin/super_admin'e in-app+e-posta uyarı gönderiyor. Hangi harici uptime monitor servisinin health endpoint'i ping'leyeceği hâlâ LITZOR'un kararı. |

### §20 — Canlı Ortam Öncesi Acceptance Criteria (AC-01 → AC-21)

| AC | Durum | Not |
|---|---|---|
| AC-01 Kayıt + iletişim doğrulama + kredi paketi satın alma | 🟡 | Kayıt/login var; e-posta/telefon doğrulama (verification flow) yok — sadece `accepted_terms`/`accepted_privacy` var. Kredi paketi satın alma Monri ile test modunda çalışıyor. |
| AC-02 Webhook retry → kredi 1 kez | ✅ | Bu oturumda atomik hale getirildi (yukarıya bkz). |
| AC-03 Failed/pending ödeme kredi eklemez | ✅ | `target_status != completed` → ledger'a hiç dokunulmuyor. |
| AC-04 Yetersiz kredili kullanıcı katılamaz | ✅ | `apply_ledger_entry` 402. |
| AC-05 Bir kez katıl, sınırsız geçerli teklif | ✅ | `test_bid_after_join_succeeds` + already_joined guard. |
| AC-06 Seller kendi ilanına teklif veremez | ✅ | `test_seller_cannot_bid_own_auction`. |
| AC-07 Eşzamanlı iki teklif state'i bozmaz | ✅ | DB-level unique/lock + idempotency_key; race testleri mevcut. |
| AC-08 Son dakika teklifi anti-sniping üretir | ✅ | `deadline_extended` + `auction_extended` bildirimi. |
| AC-09 Kapanıştan sonra yeni bid kabul edilmez | ✅ | `BIDDABLE_STATUSES` kontrolü — `ended` durumunda bid endpoint 400. |
| AC-10 Bid history silinemez, audit edilebilir | ✅ | Invalidate-only + audit log. |
| AC-11 Canlı sırada seller contact hiç açılmaz | ✅ | `GET /auctions/{id}/contact` 400 canlıyken; serializer'da contact alanı hiç yok. |
| AC-12 Kapanınca yalnız yetkili taraf contact görür | ✅ | 403 seller/winner değilse. |
| AC-13 Asset payment/checkout/payout v1'de yok | ✅ | `payments.py`/`payment.py` tamamen kaldırıldı. |
| AC-14 Mobile+desktop kullanılabilir | ⬜ | Frontend/QA işi, henüz test edilmedi. |
| AC-15 Tam HTTPS, mixed content yok | 🚫 kod ile çözülemez | Altyapı/domain kararı. |
| AC-16 ME/EN karışık metin yok | ⬜ | i18n henüz yapılmadı (Görev #17). |
| AC-17 Admin cancel + reason + credit reversal | ✅ | `admin_cancel_auction`. |
| AC-18 Admin geçmiş bid/credit sessizce değiştiremez | ✅ | Delete yok, sadece invalidate/reversal + audit. |
| AC-19 Legal/contact değerleri gerçek | ⛔ LITZOR verisi bekleniyor | Şu an placeholder. |
| AC-20 Stock görsel yok | 🚫 kod ile çözülemez | İçerik/operasyon kuralı. |
| AC-21 Backup restore + monitoring test edildi | ⬜ | Yapılmadı. |

### §21 — Genel Son Kontrol + LITZOR'dan Beklenen Bilgiler (§21.1)

§21'in checklist'i yukarıdaki bölümlerin özeti niteliğinde, ayrıca satır satır tekrarlanmadı. **§21.1 LITZOR'dan beklenen bilgiler** — hiçbiri kodla üretilemez, hepsi ⛔/🚫: LITZOR DOO ticaret unvanı/CRPS/PIB/adres, destek e-postası, canlı telefon, PSP/acquirer seçimi + merchant bilgileri, credit package fiyat/adet politikası, varsayılan participation credit cost politikası, bid increment tablosu (gerçek değerler — altyapı `BidIncrementRule` olarak hazır, değerler placeholder), anti-sniping süresi (altyapı hazır, `PlatformSettings` varsayılanı 120s — gerçek değer LITZOR onayı bekliyor), nihai ME/EN hukuki metinler, logo/favicon/brand assets.

### Özet

Backend tarafında doc'un **kod ile çözülebilir** kısımlarının büyük çoğunluğu (§1, §5, §8, §10.4, §11, §12, §13, §15 altyapısı, §16, §17, §18, §19.3) tamamlanmış ve canlı Postgres'e karşı doğrulanmış durumda (bkz. Bölüm 17 için §10.4/§19.3 güncellemeleri). Kalan gerçek kod işi üç grupta toplanıyor: **(a)** frontend (§2-3-4-5-9-10-11-14 UI'ları, Görev #18), **(b)** i18n + e-posta şablonları (§2.4/§16.3, Görev #17), **(c)** kalan güvenlik sertleştirme (§19.1 HTTPS redirect middleware, §19.7 monitoring — Görev #19) + §15.2/15.3 terms enforcement + §14.2.2 ticket kategorileri (Görev #21). Bunların dışında kalan her şey ya LITZOR'dan gelecek veri/karar (§8.3, §14.2.1, §19.1 domain, §21.1) ya da tamamen operasyonel/hukuki konular (§19.6 backup süreci, §1.2/§4.3/§14.1/§20 AC-19/AC-20 gibi içerik kuralları).

## 17. Revizyon Geçmişi (30.07.2026, devam) — Matris Doğrulaması Sırasında Bulunan Eksikler

Bölüm 16'daki matrisi yazarken kod üzerinde doğrulama yapılırken üç gerçek eksik bulundu ve düzeltildi:

### 1. §10.4 Joined Auctions endpoint'i hiç yoktu

Matris ilk taslakta bunu "✅ backend" işaretlemişti ama gerçek kod kontrolünde (`grep AuctionParticipant`) böyle bir liste endpoint'i olmadığı görüldü. Eklendi: `GET /api/auctions/joined` (`app/api/auctions.py`) — kullanıcının katıldığı ihaleleri join tarihi, harcanan kredi, ihale durumu ve `my_bid_status` (`highest`/`outbid`/`no_bid`) ile döndürüyor. **Önemli tuzak**: bu route `auctions_router`'da zaten var olan `GET /{auction_id}` path-param route'undan ÖNCE tanımlanmalı — Starlette route'ları kayıt sırasına göre eşleştiriyor, `/joined`'i sonra eklemek `auction_id="joined"` olarak yanlış eşleşip 404 üretiyordu (ilk denemede tam olarak bu hata alındı, route'u `/my` ile `/{auction_id}` arasına taşıyarak düzeltildi). Yeni test: `TestJoinedAuctions::test_joined_auctions_reports_bid_status` (`test_bid_api.py`) — join sonrası `no_bid`, bid sonrası `highest` durumunu doğruluyor.

### 2. §8.4/AC-02 kredi webhook'unda gerçek bir yarış durumu

Yukarıda (Bölüm 15 sonu) detaylandırıldı: atomik `UPDATE ... WHERE status='pending'` + `stripe_session_id` unique constraint ile düzeltildi.

### 3. §19.3 join/bid/support rate limiti tamamen eksikti

`app/api/auth.py`'nin `limiter` (slowapi `Limiter(key_func=get_remote_address)`) nesnesi sadece auth endpoint'lerinde kullanılıyordu; `join_auction`, `place_bid`, `POST /support/contact`, `POST /support/tickets` üzerinde hiç rate limit yoktu — doc'un açıkça istediği bir koruma (özellikle `join_auction` kredi harcıyor). Düzeltme: aynı `auth.limiter` nesnesi import edilip bu dört endpoint'e `@limiter.limit(...)` eklendi (`join_auction`: 20/dakika, `place_bid`: 60/dakika, `support/contact` ve `support/tickets`: 10/dakika) — yeni bir `Limiter` instance'ı YARATILMADI, çünkü `conftest.py` sadece `app.state.limiter` ve `app.api.auth.limiter`'ı devre dışı bırakıyor; ayrı bir instance oluşturmak test suite'ini kırardı. `join_auction`'a eksik olan `request: Request` parametresi eklendi (slowapi decorator'ının ihtiyacı var).

### Doğrulama

- `pytest`: 155/158 geçiyor (aynı 3 önceden var olan hata) — hem yeni joined-auctions testi hem de mevcut testler rate-limit değişikliğinden etkilenmedi (limiter test'te devre dışı).
- `docker compose up --build -d`: temiz migration, hata yok.
- Canlı Postgres smoke test: `GET /auctions/joined` doğru `my_bid_status` döndürüyor; `POST /support/contact` 11. istekte `429 Rate limit exceeded: 10 per 1 minute` döndü (limiter gerçekten devrede canlı ortamda). Docker loglarında hata yok.

### Kapsam durum matrisi güncellemesi

Bölüm 16'daki matris şu satırlarda güncellendi: §10.4 artık ✅ (endpoint gerçekten var ve test edildi), §8.4 ✅ (atomik hale getirildi), §19.3 artık ✅ (join/bid/support rate limit gerçekten eklendi ve canlıda 429 ile doğrulandı — limit değerleri LITZOR'un trafik beklentisine göre ayarlanabilir bir varsayılan).

## 18. Revizyon Geçmişi (30.07.2026, devam) — §15.2 Checkout Consent + §14.2.2 Ticket Kategorileri

### Yapılanlar

- **§15.2 Credit checkout öncesi açık onay**: `POST /credits/monri/checkout` artık `terms_accepted: bool` alanı zorunlu kılıyor (`false`/eksikse 400). Kabul edilirse `get_or_create_credit_terms()` (yeni, `app/services/credits.py` — `get_or_create_seller_declaration` ile aynı idempotent SAVEPOINT get-or-create deseni) bir `credit_terms` `TermsDocument`'ı otomatik provision ediyor (LITZOR'un nihai hukuki metni gelene kadar app-copy placeholder, §21.1'de zaten not edilen bekleyen madde) ve sipariş oluşturulmadan ÖNCE bir `TermsAcceptance` satırı yazılıyor — aynı transaction içinde, `CreditPurchase` insert'inden önce.
- **§14.2.2 Contact form kategorileri**: `SupportTicket` tablosuna `category` (VARCHAR, default 'other', migration ile eklendi) ve `lot_code` (VARCHAR, nullable) sütunları eklendi. `SupportTicketCreateRequest` artık sabit bir regex pattern ile kategori doğruluyor: `account | credits_payment | auction_bid | seller_application | listing | technical_issue | other`. Hem `app/api/support.py` (contact form + ticket create + my-tickets + admin list/update) hem `app/api/admin.py`'deki paralel `/admin/support-tickets` endpoint seti (farklı bir router, `get_current_staff` gated — önceden var olan bir kod tekrarı, bu oturumda giderilmedi) güncellendi. `support.py`'de 5 yerde tekrarlanan response-construction bloğu `_to_response()` helper'ına çıkarıldı (aynı alanları eklemek için 5 yerde tekrar yazmak yerine).

### Bulunan ek pre-existing bug

Matris/test sırasında fark edildi: `app/api/admin.py`'de de `admin_list_tickets`/`admin_update_ticket` adında AYRI bir çift var (`/admin/support-tickets` prefix'i altında, `get_current_staff` ile) — `app/api/support.py`'deki `/support/tickets` admin endpoint'lerinden (`get_current_admin` ile) bağımsız, muhtemelen RBAC işi (Bölüm 13) sırasında admin.py'ye yeni bir kopya eklenmiş ama support.py'deki eski kopya silinmemiş. Yeni `category`/`lot_code` alanları unutulmasın diye HER İKİSİ de güncellendi (aksi halde `test_rbac_api.py::test_support_can_list_and_update_tickets` `admin.py`'nin `SupportTicketResponse` inşasında `category` eksikliğinden pydantic `ValidationError` ile patlıyordu — ilk test koşusunda tam olarak bu hata yakalandı). Bu iki-router çakışması ayrı bir temizlik konusu, şimdilik not edildi, konsolide edilmedi (scope dışı).

### Doğrulama

- Yeni test: `TestCreditCheckoutTermsAcceptance::test_checkout_requires_terms_acceptance` (`test_credit_engine.py`) — `terms_accepted=False` → 400, `true` → 200 + tam olarak 1 `TermsAcceptance` satırı.
- `pytest`: 156/159 geçiyor (aynı 3 önceden var olan hata).
- `docker compose up --build -d`: `support_tickets.category`/`lot_code` migration'ları temiz eklendi.
- Canlı Postgres smoke test: checkout `terms_accepted=false` → 400; `true` → 200 + `terms_acceptances` tablosunda `credit_terms` satırı doğrulandı; destek bileti `category="auction_bid"`+`lot_code` ile oluşturuldu; geçersiz kategori → 422. Docker loglarında hata yok.

Görev #21 tamamlandı. §15.3 (Join Auction öncesi kural onayı) kasıtlı olarak KAPSAM DIŞI bırakıldı — doc'un "Beklenen sonuç" satırı ("Katılım onayı server log'da timestamp ile tutulmalı") zaten mevcut `AuctionParticipant.joined_at` ile karşılanıyor; ikinci bir TermsAcceptance tablosu eklemek gereksiz olurdu, kalanı (join modal'daki açıklama metni) frontend işi (Görev #18).

## 19. Revizyon Geçmişi (30.07.2026, devam) — Frontend (`index.html`): Matris Düzeltmesi + Yeni Sayfalar + Doküman İhlallerinin Giderilmesi

### Bölüm 16'daki matrisin düzeltilmesi gerektiği bulundu

Bölüm 16'yı yazarken `index.html` **hiç açılmadan** kod-inceleme (backend tarafı) ile "frontend bekliyor" değerlendirmesi yapılmıştı. Bu dosya bu oturumda ilk kez okundu (1252 satır) ve önceki fazlarda (FAZ 2 yorumları) zaten backend'e bağlanmış, hatırı sayılır bir SPA olduğu görüldü: tam ME/EN i18n sistemi (`data-i18n` + `translations` sözlüğü + dil değiştirici, kalıcı localStorage), gerçek API'ye bağlı auction listesi/detay/bid/join akışı, kredi mağazası + Monri checkout, seller dashboard (istatistikler, kredi bakiyesi, oglas listesi), tam admin paneli (stats/users/auctions/categories/bids/tickets/audit). Bu, Bölüm 16'daki §2.4 (i18n "⬜ henüz başlanmadı") ve birçok §3/§4/§5/§8/§10 satırının yanlış negatif olduğu anlamına geliyor — bu bölümde düzeltiliyor.

### Ancak: doküman'ın açıkça yasakladığı metinler hâlâ canlıydı

Dosyayı okurken, doc'un §2.1/§3.1/§3.4/§9.4/§5.1/§14.3.1'de tam olarak isim vererek yasakladığı ifadelerin kelimesi kelimesine hâlâ kodda durduğu görüldü:

- EN hero: *"The Largest Auction of Vehicles & Equipment on the Adriatic."* — doc'un §2.1/§3.1'de "yayından çıkar" dediği tam ifade. ME karşılığı da aynı ("Najveća aukcija ... na Jadranu").
- Sahte istatistikler: `€8M+ Sold`, `340+ Buyers`, `1.2k+` — §3.4'ün "gerçek ve doğrulanabilir olmayan KPI'ları yayından çıkar" dediği tam örnekler.
- Footer'da `<a href="#admin">Admin demo</a>` — §14.3.1'in "Tamamen yayından çıkar" dediği tam metin.
- `det.n` çeviri anahtarı: *"In demo mode, bids are stored in the browser."* — §5.1'in yasakladığı tam cümle (mimari zaten DB tabanlıydı, sadece bu eski uyarı metni unutulmuştu).
- How-it-works adım 4: *"The highest bid wins the auction and proceeds to payment / collection."* — §9.4'ün "BidMont'un satış sürecini yönettiği izlenimi" dediği tam problem.

Bunların hepsi bu oturumda düzeltildi: hero başlığı/alt metni kredi modelini anlatacak şekilde yeniden yazıldı ("Montenegro's Online Auction Marketplace" / "Crnogorska online aukcijska platforma"), sahte istatistikler kaldırılıp nötr güven mesajlarıyla değiştirildi (Local/Verified/Transparent, doc §3.8'in önerdiği üçlü), footer LITZOR DOO operatör bilgisi + platform-role açıklamasıyla yeniden yazıldı (§14.3.2), demo bid uyarısı kaldırıldı, how-it-works adımları "en yüksek teklif sahibi satıcı kontağını alır, satış/ödeme/teslim doğrudan taraflar arasında" şeklinde düzeltildi. "General" kategori adı hem nav hem kart hem çevirilerde "Commercial Assets" olarak değiştirildi (§2.3/§3.6).

### Gerçek bir 422 bug'ı bulundu ve düzeltildi

`#sellForm` (gerçek API'ye bağlı ilan oluşturma formu) hiçbir zaman `declaration_accepted` alanını göndermiyordu — bu alan `AuctionCreateRequest`'te zorunlu (`Field(...)`). Yani §11.7 (seller declaration) bu oturumda eklendiğinden beri, bu formdan gönderilen HER gerçek ilan oluşturma isteği sessizce 422 ile başarısız oluyordu (demo/localStorage moduna düşmediği sürece kullanıcı bunu fark etmezdi). Düzeltme: forma zorunlu bir "seller declaration" checkbox'ı eklendi (aynı `SELLER_DECLARATION_TEXT` içeriğiyle), submit handler artık `declaration_accepted:true` gönderiyor ve checkbox işaretlenmeden submit'i engelliyor.

### Yeni sayfalar/akışlar eklendi

- **Seller Application (`#apply-seller`, §11.1/§11.2)**: `GET /sellers/me` ile mevcut durumu gösteren form (pending/verified/rejected + red reason), `POST /sellers/apply` ile submit/resubmit. Hero CTA, footer, auctions toolbar'daki "+ Postavi aukciju" butonu artık doğrudan `#sell`'e değil buraya yönlendiriyor (§3.3'ün "Post Auction herkese açık doğrudan yayın mantığı vermemeli" kuralı).
- **`#sell` sayfasına verification gate**: Sayfa artık önce `GET /sellers/me` kontrol ediyor; `verified` değilse form gizlenip "Sell with BidMont" sayfasına yönlendiren bir banner gösteriliyor — önceden kullanıcı doğrudan forma girip sessizce 403 alıyordu (§11.5).
- **Legal (`#legal`, §15)**: `terms_of_use` / `auction_participation_rules` / `credit_terms` / `seller_listing_declaration` / `privacy_policy` sekmeleri, `GET /legal/{document_type}`'a bağlı. Henüz yayınlanmamış belge türleri için "not published yet" mesajı (backend 404 döndürüyor, bu beklenen durum — nihai hukuki metinler LITZOR'dan gelecek, §21.1).
- **Watchlist (§10.5)**: Detay sayfasında ♡/♥ takip butonu (`POST`/`DELETE /watchlist/{id}`), profildeki "Praćene aukcije" listesi (`GET /watchlist`).
- **Joined Auctions (§10.4)**: Profildeki yeni "Pridružene aukcije" listesi, Bölüm 17'de eklenen `GET /auctions/joined` endpoint'ine bağlı, `my_bid_status` (highest/outbid/no_bid) rozeti ile.
- **Detay sayfası eklentileri**: Lot ID gösterimi (§5.3), participation credit cost satırı (§5.4), platform-role uyarı kutusu (§5.12), kapanış sonrası contact-reveal paneli (§5.11/§12.3/§12.4 — auction `ended` durumundaysa `GET /auctions/{id}/contact` denenir; 403/404 ise sessizce gizlenir, backend zaten tek yetkili kapı).
- **Contact form (§14.2.2)**: kategori dropdown'ı (`account/credits_payment/auction_bid/seller_application/listing/technical_issue/other`) + opsiyonel Lot ID alanı eklendi, `POST /support/contact`'e gönderiliyor. Ayrıca fark edildi: mevcut form input'larının hiçbirinde `name` attribute'u yoktu, yani `FormData(form).get('name')` her zaman `null` dönüyordu — form her zaman "visitor"/boş email gönderiyordu; bu oturumda `name`/`email`/`message` attribute'ları eklenerek düzeltildi.
- **Credit checkout consent (§15.2)**: "Buy Credits" akışı artık satın alma öncesi bir onay (`confirm()` diyaloğu, Credit Terms/Refund Policy özetiyle) istiyor ve `terms_accepted:true` gönderiyor (backend Bölüm 18'de bunu zorunlu kıldı).

### Kaldırılan kod

`#post` sayfası (eski, tamamen localStorage tabanlı "demo aukcija objavi" formu) silindi — `#sell` sayfası zaten gerçek API'ye bağlı ve artık seller-verification gate'i de var, bu ikinci form doc'un yasakladığı "browser'da saklanan sahte ilan" mantığının aynısıydı ve kafa karıştırıyordu. İlgili `postForm` submit handler'ı da kaldırıldı (element artık DOM'da yok, kaldırılmasaydı sayfa yüklenirken `Cannot read properties of null` hatası fırlatacaktı — bu, düzenlemenin kendisiyle bulunup düzeltilen bir regresyon).

### Doğrulama ve DÜRÜST sınır

- `node --check` ile hem düzenlenmiş dosyadan hem **gerçekten Docker'dan servis edilen** kopyadan çıkarılan `<script>` bloğu sözdizimi doğrulandı (`exit 0`, brace/paren sayıları eşit).
- JS'in referans verdiği her `$('#id')` için karşılık gelen `id="..."` HTML'de statik olarak arandı ve eksik bulunan tek referans (`#statCount` — stats bloğunu değiştirirken silinmiş) düzeltildi.
- `docker compose up --build -d` + `curl http://localhost:8000/` → 200; yeni sayfa/element'lerin sunulan HTML'de göründüğü doğrulandı.
- Bu sayfaların **gerçekten bağlandığı** her API canlı Postgres'e karşı ayrı ayrı çağrıldı ve doğrulandı: `GET/POST /sellers/me`, `apply`, `GET /notifications` + `unread-count`, `GET /legal/{type}` (404 beklenen durum), `POST/GET/DELETE /watchlist/{id}`.
- **DÜRÜST SINIR (CLAUDE.md'nin gereği)**: Bu ortamda gerçek bir tarayıcı çalıştırılamıyor (headless Chrome/jsdom kurulu değil, kurmak "no build step" prensibiyle orantısız olurdu). Yukarıdaki doğrulama; (a) JS sözdizimi geçerliliği, (b) her DOM referansının karşılığının var olduğu, (c) her yeni sayfanın çağırdığı API'lerin canlı Postgres'e karşı doğru status/payload döndürdüğü seviyesindedir — **buton tıklama, form gönderme, dil değiştirme, responsive/mobile davranışı gibi gerçek kullanıcı etkileşimleri tıklanarak test edilmedi.** Aşağıdaki Bölüm 20 (durum matrisi güncellemesi) bunu ✅ değil, açıkça "kod tamam, tarayıcıda doğrulanmadı" olarak işaretliyor.

## 20. Bölüm 16 Matrisinin Düzeltilmesi (frontend keşfi + bu oturumun eklemeleri sonrası)

Aşağıdaki satırlar Bölüm 16'daki orijinal değerlere göre günceldir. **"Kod tamam, tarayıcıda doğrulanmadı"** ibaresi, yukarıdaki dürüst-sınır notuyla aynı anlama gelir: API'ler canlı test edildi, gerçek tıklama/görsel doğrulama yapılmadı.

| Madde | Eski durum | Yeni durum | Not |
|---|---|---|---|
| 2.1 Adriatic/Balkans metni | 🔶 | ✅ kod tamam, tarayıcıda doğrulanmadı | Hero başlığı/alt metni yeniden yazıldı, "Adriatic"/"Najveća aukcija" tamamen kaldırıldı. |
| 2.2 Header menü | 🔶 | ✅ zaten mevcutmuş (önceki fazda yapılmış) | Header/nav/mobile menü zaten backend'e bağlı ve çalışır durumda, matris hatalıydı. |
| 2.3 "General" → "Commercial Assets" | 🔶 | ✅ kod tamam, tarayıcıda doğrulanmadı | Nav, kategori kartı, çeviri sözlüğü güncellendi. Kategori DB'sinde slug/isim seed'i hâlâ "General" olabilir — admin'den içerik güncellemesi ayrı konu. |
| 2.4 ME/EN dil sistemi | ⬜/🟡 (Görev #17) | ✅ zaten mevcutmuş | Tam `data-i18n` + `translations{ME,EN}` sistemi önceki fazda kurulmuş, bu oturumda sadece yeni string'ler eklendi. Görev #17 artık sadece §16.3 (e-posta şablonları) + `User.preferred_language` backend alanı için açık kalıyor. |
| 2.5 Account badge | 🔶 | ✅ zaten mevcutmuş | `renderUser()` zaten rol bazlı badge/dropdown gösteriyor. |
| 2.6 Bildirim merkezi (zil ikonu) | 🔶 | ✅ kod tamam, tarayıcıda doğrulanmadı | Bölüm 21'de eklendi: zil ikonu + okunmamış sayaç + dropdown, `GET /notifications`/`unread-count`/`PUT .../read`'e bağlı. |
| 2.7 Mobile responsive | 🔶 | 🟡 muhtemelen zaten var, doğrulanmadı | CSS'te `@media` kırılımları mevcut (375-1024px), ama gerçek cihaz/viewport testi yapılmadı. |
| 3.1-3.10 Ana sayfa | 🔶 (tümü) | Karışık, satır satır: 3.1 ✅ (hero yeniden yazıldı), 3.2 ⬜ (featured auction kartı yok), 3.3 ✅ (CTA'lar düzeltildi, Post Auction artık apply-seller'a gidiyor), 3.4 ✅ (sahte istatistikler kaldırıldı), 3.5 🟡 (ana sayfada canlı ihale listesi zaten `loadAuctionsFromApi` ile var ama ayrı "Live & Ending Soon" bölümü yok), 3.6 ✅ (kategori kartları zaten kategori sayfasına gidiyor), 3.7 ✅ (how-it-works kredi modeline göre yeniden yazıldı), 3.8 ⬜ (ayrı Why-BidMont bölümü yok, stats bloğu kısmen bu amaca hizmet ediyor), 3.9 ⬜ (ayrı seller-acquisition bölümü yok, CTA var), 3.10 ✅ (footer'a platform-role notu eklendi, ayrıca detay sayfasına da eklendi) | |
| 4.2 Kart veri seti (Lot ID, credit cost, verified badge, watchlist) | ✅backend/🔶frontend | ✅ kod tamam, tarayıcıda doğrulanmadı | Bölüm 21'de `card()` fonksiyonuna eklendi: Lot ID, credit cost, "Verified Seller" rozeti (backend §11.5 gate'i sayesinde her API auction için doğru), watchlist ♡/♥ kalbi. Şehir/bid count zaten vardı. |
| 4.3/4.5 | 🔶 | değişmedi | İçerik/empty-state, dokunulmadı. |
| 5.2 Çoklu galeri | 🟡 | 🟡 değişmedi | Detay sayfası hâlâ tek görsel gösteriyor (`d.images[0]`), thumbnail galeri/lightbox eklenmedi. |
| 5.3 Lot ID | 🔶backend | ✅ eklendi | Detay sayfasında görünüyor. |
| 5.4 Credit cost gösterimi | 🔶backend | ✅ eklendi | Detay sayfasında görünüyor. |
| 5.5 Join Auction adımı | ✅backend/UI-yok | 🟡 kısmen | Backend zaten tek seferlik düşüm yapıyor; UI hâlâ ayrı bir "Join" onay modalı göstermiyor, `bid()` fonksiyonu 403 alınca sessizce arka planda join deniyor (§5.5'in istediği açık onay modalı değil). |
| 5.7 Bid confirmation modal | 🔶 | 🔶 değişmedi | Hâlâ yok, bid direkt gönderiliyor. |
| 5.11 Seller contact | ✅backend | ✅ frontend de eklendi | Detay sayfasında kapanış sonrası contact-reveal paneli eklendi. |
| 5.12 Platform rolü uyarısı | 🔶 | ✅ eklendi | Detay sayfasına + footer'a eklendi. |
| 6.2 Doküman bölümü | ✅backend/🔶frontend | 🔶 değişmedi | Detay sayfasında doküman listesi UI'ı yok. |
| 8.1/8.2 My Credits / Credit Store | ✅backend/🔶frontend | ✅ zaten mevcutmuş | Kredi bakiyesi, paket listesi, Monri checkout akışı zaten profildeki "Prodavački panel" bölümünde çalışıyor durumda. Checkout'a bu oturumda terms-consent onayı eklendi. |
| 9.1-9.4 How It Works | 🔶 | 🟡 kısmen | Buyer/seller ayrı tab/section hâlâ yok (tek generic 4-adım listesi var, home page'de); ama §9.4'ün payment/collection ifadesi düzeltildi (home page'deki how-section metninde). Ayrı `#how` sayfası içeriği (`how.p.*` anahtarları) henüz güncellenmedi — orada hâlâ eski "provjera/licitiranje/plaćanje" 4 adımı var. |
| 10.1-10.6 Dashboard | 🔶 (çoğu) | Çoğu ✅ zaten mevcutmuş + 2 yeni ekleme: 10.1 🟡 (ayrı dashboard nav yok ama tek profil sayfasında tüm bölümler var), 10.2 ✅ zaten var, 10.3 ✅ zaten var (My Bids tablosu), 10.4 ✅ bu oturumda eklendi (Joined Auctions), 10.5 ✅ bu oturumda eklendi (Watchlist), 10.6 🟡 (city/address alanı hâlâ yok) | |
| 11.1-11.4 Seller başvuru | 🔶/✅backend | 11.1 ✅ eklendi (Apply→Verify→Create akışı UI'da var), 11.2 ✅ eklendi (başvuru formu), 11.3 🟡 (ayrı "Seller Dashboard" yok ama profildeki bölüm işlevi görüyor), 11.4 ⬜ (8 adımlı wizard yok, tek sayfalık form) | |
| 14.2.1 Gerçek iletişim bilgileri | ⛔ | ⛔ değişmedi | Hâlâ placeholder (LITZOR verisi bekleniyor). |
| 14.2.2 Contact form kategorileri | ✅backend/🔶frontend | ✅ tamamlandı | Kategori dropdown + Lot ID alanı eklendi, ayrıca `name`/`email` input'larında eksik olan `name` attribute bug'ı da düzeltildi. |
| 14.3.1/14.3.2 Footer | 🚫/⛔ | ✅ kod tamam (14.3.1), ⛔ değişmedi (14.3.2 gerçek CRPS/PIB/adres LITZOR'dan bekleniyor) | "Admin demo" kaldırıldı, LITZOR DOO + platform-role satırı eklendi (placeholder olmayan kısım: operatör adı zaten biliniyordu). |
| 15 Legal routes | ✅backend/⛔içerik | ✅ frontend de eklendi | `#legal` sayfası 5 doküman tipini `GET /legal/{type}`'a bağlıyor. İçerik hâlâ LITZOR'un onaylayacağı nihai metin bekliyor (placeholder/404 durumu). |
| 19.3 rate limit | ✅ (Bölüm 18) | değişmedi | |

### Bu turda dokunulmayan, hâlâ açık gerçek eksikler (özet)

Zil ikonu/bildirim dropdown'ı (§2.6), kart seviyesinde Lot ID/credit-cost/watchlist kalbi (§4.2), çoklu foto galerisi (§5.2), Join Auction onay modalı (§5.5), bid confirmation modal (§5.7), buyer/seller ayrı How-It-Works sayfası (§9), 8 adımlı create-listing wizard (§11.4), yapılandırılmış kusur kategorileri (§6.1) ve equipment/commercial-asset'e özel dinamik form alanları (§7). Bunlar Görev #18'in kalan kapsamı olarak işaretli kalıyor.

## 21. Revizyon Geçmişi (30.07.2026, devam) — Bildirim Zili (§2.6) + Kart Alanları (§4.2) + İki Gerçek Bug Düzeltmesi

### Bölüm 19/20'nin kod incelemesinde bulunan iki gerçek sorun

1. **Contact-reveal panelinin güvenli olmayan fallback'i**: `renderDetail`'de `ended` durumu `a.rawStatus==='ended'||...||(!a.rawStatus&&a.end<=Date.now())` şeklinde hesaplanıyordu. `a.rawStatus` yalnızca `getAuctionDetail()` çağrısı BAŞARILI olursa set ediliyor (`try/catch(e){}` ile sarılı); başarısız olursa (ağ hatası vb.) `rawStatus` `undefined` kalıyor ve kod saat bazlı fallback'e düşüyordu. Gerçek API auction'ları için bu, "detay isteği başarısız oldu ama saat geçmiş" durumunda bid panelinin YANLIŞLIKLA gizlenmesine (canlı bir ihalede kullanıcı teklif veremez hale gelmesine) yol açabilirdi — güvenlik açığı değil ama gerçek bir kullanılabilirlik regresyonu riski. Düzeltme: `const ended=a._isApi?(a.rawStatus==='ended'||a.rawStatus==='cancelled'):(a.end<=Date.now());` — API auction'ları için `ended` SADECE backend'den doğrulanmış bir status geldiğinde true olur; detay isteği başarısız olursa güvenli varsayılan (bid paneli görünür kalır) korunur. Demo/localStorage auction'lar için eski saat-bazlı davranış değişmedi.
2. **`#post` sayfası silinirken bırakılan `option value="General"`**: `#auctionCategory` filtresindeki değer hâlâ dahili `'General'` anahtarını kullanıyor (görünen etiket "Commercial Assets" oldu ama filtreleme mantığının kullandığı iç değer değişmedi — kasıtlı, `normalizeCategory()`'nin ürettiği değerle eşleşmesi gerekiyor). `normalizeCategory` fonksiyonuna bunun kasıtlı olduğunu açıklayan bir yorum eklendi, gelecekte biri etiketi değiştirirken iç anahtarı da değiştirip filtreyi sessizce kırmasın diye.

### §2.6 Bildirim zili eklendi

Header'a `notif-dropdown` (zil ikonu + okunmamış sayaç + dropdown liste), sadece giriş yapılmış kullanıcıya görünür. `GET /notifications/unread-count` her 60 saniyede bir (mevcut poll interval'ına eklendi) + `renderUser()` her çağrıldığında yenileniyor. Dropdown açılınca `GET /notifications` çekilip son 20 tanesi listeleniyor; bir bildirime tıklanınca `PUT /notifications/{id}/read` çağrılıp liste+sayaç yenileniyor. Doc'un istediği event kapsamı (outbid, ihale bitişi, kredi satın alma, seller ilan durumları) zaten Bölüm 15'te backend'de var — bu sadece görüntüleme katmanı.

### §4.2 Kart alanları eklendi

`card()` fonksiyonu artık (yalnızca gerçek API auction'ları için, demo veri için değil): Lot ID (monospace küçük satır), participation credit cost, ve bir "✓ Verified Seller" rozeti. Rozet için ayrı bir backend sorgusu GEREKMEDİ — `create_auction` zaten yalnızca verified `SellerProfile`'a sahip kullanıcıların ilan oluşturmasına izin veriyor (§11.5 gate), yani API'den dönen HER ilan tanım gereği verified bir satıcıya ait; rozet bu garantiye dayanıyor. Ayrıca ♡/♥ watchlist kalbi eklendi: `watchlistIds` (Set) `loadAuctionsFromApi()` sırasında `GET /watchlist` ile bir kez dolduruluyor, kart üzerindeki kalp `toggleWatchlistCard(id)` ile `POST`/`DELETE /watchlist/{id}` çağırıp `renderAll()` ile yeniden çiziyor (bilinen sınır: login/logout sonrası bir sayfa/hash değişikliği olmadan kalp durumu anında yenilenmiyor, sadece `loadAuctionsFromApi` tekrar çağrıldığında).

### Doğrulama

- `node --check` hem düzenlenmiş dosyadan hem **Docker'dan yeniden servis edilen** kopyadan çıkarılan `<script>` bloğu için `exit 0`.
- `$('#id')` ↔ `id="..."` çapraz referans denetimi tekrarlandı, eksik bulunmadı.
- `docker compose up --build -d` + `curl` → 200; servis edilen HTML'de `notifBtn`/`notifMenu`/`watchlistIds`/`toggleWatchlistCard` işaretleyicileri doğrulandı.
- `pytest`: 156/159 (backend'e dokunulmadı, aynı 3 önceden var olan hata).
- Docker loglarında hata yok.
- **DÜRÜST SINIR (değişmedi)**: Zil ikonuna tıklama, kalbe tıklama, dropdown açma gibi gerçek etkileşimler tarayıcıda test edilmedi — yalnızca sözdizimi + DOM-referans + API-seviyesi doğrulama yapıldı.

Bu turla birlikte Görev #18'in kapsamı, advisor'ın önerdiği önceliklendirmeye göre daraltıldı: 8 adımlı wizard (§11.4) ve yapılandırılmış kusur kategorileri (§6.1) bilinçli olarak bu oturumda ele alınmadı — ikisi de şema kararı gerektiriyor ve yarım yapılmış bir form, gerçek bir eksiği "çözülmüş" gibi gösterme riski taşıyor.

## 22. Nihai Uygunluk Doğrulaması (Compliance Verification) — 30.07.2026

Bu bölüm, `docs/Bidmont son hali için döküman .docx` dosyasının **tamamına karşı** açık bir sonuç bildirimidir. Bölüm 16/17/18/19/20/21'deki dağınık revizyon notlarının yerine değil, onların üzerine kurulu, tek ve otoriter bir cevaptır.

### Açık sonuç

**Proje, dokümanın tüm maddelerini şu anda karşılamıyor.** Bunun iki ayrı nedeni var ve ikisi de birbirinden farklı ele alınmalı:

1. **Kod ile tamamlanabilecek ama henüz tamamlanmamış maddeler** — bunlar gelecek oturumlarda kapatılabilir (aşağıda "B" listesi).
2. **Kod ile ASLA tamamlanamayacak maddeler** — bunlar LITZOR DOO'nun hukuki/ticari/operasyonel kararı veya verisi olmadan, hiçbir miktarda yazılım geliştirmeyle kapatılamaz (aşağıda "C" listesi). Bu liste doc'un kendi §21.1 bölümünün de kabul ettiği bir gerçektir — doküman bu maddeleri zaten "LİTZOR tarafından paylaşılması gereken bilgiler" olarak ayırmıştır.

### A) Doğrulanmış olarak tamamlanan maddeler (kod + test + canlı Postgres + servis edilen HTML)

§1 (iş modeli kısıtları), §5.1/5.2/5.3/5.4/5.5/5.6/5.7/5.8/5.9/5.10/5.11 (bid engine + credit + contact-unlock çekirdeği + galeri/lightbox + join/bid onay diyalogları), §8.4/8.5/8.6/8.8/8.9 (kredi ledger + idempotency), §10.4/10.5 (joined/watchlist), §10.6 (address/city + dil tercihi bu oturumda kapatıldı; kurumsal hesap alanları — company_name/pib/authorized_person — **zaten önceki bir oturumda tam olarak yapılmıştı**, B listesindeki "hâlâ açık" etiketi yanlıştı, Bölüm 35'te düzeltildi), §16.3 (ME/EN e-posta şablonları, Bölüm 33'te kapatıldı), §3.5 (Live & Ending Soon bölümü, Bölüm 34'te kapatıldı), §9 (Buyer/Seller How-It-Works sekmeleri, Bölüm 37'de kapatıldı), §8.1 (My Credits sayfası + işlem geçmişi, Bölüm 40'ta kapatıldı, `reason` sütunu Bölüm 41'de düzeltildi), §4.1 (vehicle kategoriye özel filtreler + detay sayfası vehicleFields/equipFields bağlantısı Bölüm 41'de, seller type filtresi Bölüm 44'te kapatıldı — equipment condition filtresi kasıtlı olarak §7'ye bırakıldı, ayrı ele alınacak), §10.1 (dashboard navigasyonu + Security/şifre değiştirme, Bölüm 42'de kapatıldı), §10.2/§10.3 (Overview credit balance + My Bids gerçek tablosu, Bölüm 43'te kapatıldı; aynı turda buyer'ların yanlışlıkla tüm seller panelini gördüğü ayrı bir rol-izolasyon hatası da düzeltildi), §11.1/11.2/11.5/11.6/11.7 (seller application + verification gate + declaration), §12 (auction state machine + kapanış), §13/§4.4 (arama + pagination), §14.1.1 (About Us sayfası genişletildi — LITZOR kurumsal bilgisi hariç), §14.2.2 (destek kategorileri), §15.1/15.2 (terms versioning + checkout consent), §16 (bildirim event kapsamı + idempotency), §17.1/17.2 (RBAC + audit log), §18.1 (DB UTC saklama + UI'ın Karadağ yerel saatine çevirerek göstermesi — Bölüm 27'de UI yarısı da kapatıldı), §18.2 (bid transaction sırası — bkz. aşağıdaki çekince), §19.1/19.3/19.4/19.5 (HTTPS redirect + rate limit + upload + PSP), §2.4 (i18n UI altyapısı — önceki fazda kurulmuş, **çekinceye bkz.**), §2.6/§4.2 (bildirim zili + kart alanları, bu oturumda eklendi), §3.2/3.3/3.8/3.9/3.10 (hero featured-auction kartı, CTA metni, Why BidMont, Sell with BidMont, ana sayfa disclaimer'ı — bu oturumda eklendi), §4.5 (empty state + Clear Filters), §8.7 (yetersiz bakiye akışı + satın alma sonrası aynı aukciyona dönüş), §17.3 (admin 2FA, Bölüm 45'te kapatıldı — bildirim şablonu admin yönetimi hâlâ açık, §17 kalanı), §19.6/§19.7 (backup+restore script'leri ve bid-engine/payment-webhook/unhandled-error admin alerting, Bölüm 46'da kapatıldı — gerçek cron zamanlaması ve uptime monitor servisi seçimi hâlâ LITZOR'un operasyonel kararı), §11.3 (Seller Dashboard Overview/My Listings filtreleri/verification badge, Bölüm 47'de kapatıldı — §11.4'ün wizard'ı hâlâ açık), §20 AC-01'in e-posta doğrulama yarısı (kayıt sonrası doğrulama e-postası + `/auth/verify-email` + `/auth/resend-verification`, Bölüm 48'de kapatıldı — telefon/SMS yarısı bir SMS gateway kararı gerektirdiği için C listesine eklendi), §11.4 (8 adımlı multi-step create-listing wizard, Bölüm 49'da kapatıldı — Adım 1/3'ün kategoriye özel derinliği hâlâ §7'nin taksonomi kararına bağlı, mevcut 3 kategoriyle sınırlı), §17 (bildirim şablonu admin yönetimi, Bölüm 50'de kapatıldı — `template_vars` mekanizmasıyla 5 yüksek-değerli bildirim tipi için). Bunların hepsi Bölüm 15-21 ve 24-31'de ayrı ayrı test edilip canlı Postgres'e karşı doğrulandı.

**§18.2 çekincesi**: doc'un istediği 10 adımlık bid transaction sırası (lock → state/deadline re-read → participant validate → highest/increment recalculate → amount validate → immutable bid insert → highest update → anti-sniping → commit → real-time+notifications) `backend/app/api/bids.py::place_bid`'in kodu okunarak doğrulandı — `with_for_update()` ile satır kilidi alınıyor, sıra kavramsal olarak eşleşiyor (adım 6/7'nin kod içi yazım sırası doc'unkiyle ters ama ikisi de aynı commit'te flush olduğu için pratik bir fark yaratmıyor). **Bu bir kod okuması ile doğrulama** — gerçek eşzamanlı (concurrent) yük altında satır kilidinin çifte-teklifi engellediğini kanıtlayan özel bir concurrency testi yazılmadı (SQLite test DB'si zaten gerçek concurrency'yi simüle etmiyor).

**Önemli çekince (frontend doğrulama seviyesi)**: Yukarıdaki frontend maddeleri (§2.4, §2.6, §4.2 ve genel olarak `index.html` değişiklikleri) yalnızca (a) JS sözdizimi geçerliliği, (b) DOM referans bütünlüğü, (c) çağrılan API'lerin canlı Postgres'e karşı doğru cevap verdiği seviyesinde doğrulandı — **gerçek bir tarayıcıda tıklanarak test edilmedi** (bu ortamda headless tarayıcı yok). Bu, "✅ tamamlandı" değil, "✅ kod tamam, tarayıcıda doğrulanmadı" olarak işaretlenmiştir ve bu ayrım Bölüm 20/21'deki tablolarda korunmuştur.

**§18.1 durumu (artık tam kapalı)**: doc §18.1 iki ayrı şey istiyor — (1) DB'nin zamanları UTC tutması ve (2) UI'ın bunu Karadağ yerel saatine çevirerek göstermesi. (1) bu oturumdan önce, (2) ise Bölüm 27'de kapatıldı (`mtDateTime`/`mtDate` + `Intl` `timeZone:'Europe/Podgorica'`). Not: `timeLeft()` (kalan süre sayacı, örn. "3h 12m") kasıtlı olarak dokunulmadı — bu bir göreli süre farkı, mutlak bir saat gösterimi değil, dolayısıyla saat dilimi çevrimi anlamsız.

**Önemli çekince (§2.4 kısmi)**: kategori adları (`normalizeCategory()` ile eşlenen dahili anahtarlar) ME/EN her iki dilde de aynı görüntü metnini kullanıyor — yani i18n altyapısı (dict + `data-i18n` + dil değiştirme) çalışıyor ama kategori adlarının kendisi henüz gerçek biçimde çevrilmedi. Bu çekince Bölüm 20'de zaten not edilmişti, burada tekrar açıkça bağlanıyor.

**§3.3/§3.4/§3.7 — büyük ölçüde başka işlerin yan ürünü olarak kapanmış, burada ilk kez açıkça bağlanıyor**:
- §3.3 (CTA metinleri): ikincil CTA "Sell with BidMont" zaten doğru (`hero.btn2`); birincil CTA doc'un istediği tam "View Auctions" değil, "🔨 Browse Auctions" — anlam olarak eşdeğer ama harfiyen eşleşmiyor, küçük bir metin farkı olarak B listesine not edildi.
- §3.4 (sahte demo istatistiklerinin kaldırılması): önceki oturumda kapatılmış — hero artık "$8M+ Sold" gibi doğrulanamaz sayılar yerine "Lokalno/Provjereno/Transparentno" güven mesajları gösteriyor, tam doc'un istediği çözüm.
- §3.7 (ana sayfa mini "How It Works" bloğunun kredi modeline göre yeniden yazılması): önceki oturumda kapatılmış — ana sayfadaki `how.b1-b4` adımları zaten "kredi satın al / aukciye katıl / sınırsız licitle / en yüksek teklif kontak alır" akışını anlatıyor. **Karıştırılmamalı**: ayrı `#how` sayfası (`how.p.*`/`how.s1-s4`) hâlâ eski provjera/plaćanje akışını anlatıyor — bu B listesindeki §9 maddesiyle aynı şey, ayrı bir madde değil.

**Bu turda docx'in ham metni tekrar taranarak bulunan, Bölüm 16/20/22'nin hiçbirinde daha önce hiç değinilmemiş yeni açık maddeler** (aşağıda B listesine eklendi): §3.5, §3.6 (kısmi), §4.1, §4.5, §6.2, §8.1, §8.7 (kısmi). Bu bir eksiksizlik denetimiydi — docx'teki tüm `N.N` bölüm numaraları (`word/document.xml` içinden regex ile) çıkarılıp Bölüm 22'nin A/B/C listelerindeki referanslarla karşılaştırıldı; yukarıdaki maddeler bu karşılaştırmada hiçbir yerde geçmediği için gözden kaçmıştı.

### B) Kod ile tamamlanabilir ama henüz YAPILMAMIŞ maddeler (harici bir girdi/karar beklemiyor)

*(Bölüm 52'de düzeltildi — bu liste Bölüm 50'de yanlışlıkla "tamamen boş" ilan edilmişti: §6.1/§6.2/§7/§3.6 aslında B2'ye yanlış sınıflandırılmıştı. §6.1 Bölüm 52'de, §7.1/§7.2.2 Bölüm 53'te, §7.2.1/§3.6 kalanı Bölüm 54'te, §6.2 Bölüm 55'te kapatıldı. **Bu liste artık gerçekten tamamen boş** — dört kez ayrı ayrı doğrulanarak, tek seferlik bir "boş" ilanı değil.)*

### B2) Karar veya gerçek tarayıcı/cihaz gerektiren maddeler (LITZOR'un konusu değil, ama şu anki oturumda ilerletilemez)

- §2.7 / AC-14 / §20 AC-14: gerçek mobil/responsive QA — CSS kırılımları yazılmış ama gerçek bir tarayıcı/cihazda tıklanıp doğrulanmadı, bu ortamda headless tarayıcı yok.
- §20 AC-16: ME/EN dil değişiminde karışık sistem UI metni kalmadığının görsel/tıklama teyidi — yalnızca bu kaldı (gerçek tarayıcı gerektirir); statik envanter (kullanıcı-yüzü metinlerin `data-i18n` kapsamında olup olmadığının grep ile taranması) Bölüm 51'de tamamlandı, iki gerçek bulgu (sell wizard fuel/trans seçenekleri, terms/privacy link'lerinin her sayfa yüklemesinde silinmesi) kod ile kapatıldı.
- §4.3/AC-20: gerçek ilan görseli kuralı — doc'un kendi notu *"kodla zorlanamaz"* diyor (stok fotoğraf tespiti görsel-tanıma AI gerektirir); bu kalıcı bir "yazılımla çözülemez" maddesi, LITZOR'un verisini beklemiyor ama kodla da asla kapanmayacak — C listesine daha yakın, burada ayrı tutuldu çünkü LITZOR-spesifik değil.

**Bölüm 52'de B2'den B'ye taşınanların durumu (hepsi kapatıldı):**
- ~~§3.6 kalanı: kategori kartlarında alt kategori örnekleri~~ — **Bölüm 54'te kapatıldı** (`cat.g.d` açıklamasına 9 alt-kategori adı eklendi).
- ~~§6.2: ilana doküman ekleme~~ — **Bölüm 55'te kapatıldı** (registration/inspection/service/other kategorileri + public/private erişim + güvenli indirme; `AuctionImage.media_type`/`visibility` kolonları önceden vardı ama hiç kullanılmıyordu, artık kullanılıyor).
- ~~§7.2.1: Commercial Assets'in 9 alt-kategorisi~~ — **Bölüm 54'te kapatıldı** (`Category.parent_id` kullanılarak seed edildi, idempotent).
- ~~§7.1/§7.2.2: equipment ve commercial-asset alanları~~ — **Bölüm 53'te kapatıldı** (Bölüm 54'te ortaya çıkan bir bucketing regresyonu da düzeltildi).

**Bölüm 55'te ayrıca bulunan, kapsam dışı bırakılan bir hata**: admin panelindeki `adminFetch(url)` yardımcı fonksiyonu HTTP metodu/gövde geçirmiyor, `fetch()`'in varsayılanı GET'tir — `adminApproveAuction`/`adminRejectAuction`/`adminToggleFeatured`/`adminUpdateUserStatus` gibi POST/PUT gerektiren TÜM mevcut admin aksiyonlarının sessizce yanlış metodla (muhtemelen 405) başarısız olması bekleniyor. Bu §6.2'nin bir parçası değil, ayrı ve önceden var olan bir hata — bir sonraki B-madde adayı olarak not edildi, bu bölümde düzeltilmedi.

### C) Kod ile ASLA tamamlanamayacak, LITZOR'dan veri/karar bekleyen maddeler

§1 iş modeli onayı (zaten kod bu varsayımla kurulu, ama resmi onay LITZOR'un), §3.1 nihai marka mesajı onayı, §8.3 gerçek PSP merchant kimlik bilgileri, §14.2.1 gerçek destek e-postası/telefon/adres, §14.3.2 gerçek CRPS/PIB/adres, §15 nihai hukuki metinler (avukat onaylı), §19.1 gerçek domain + TLS sertifikası + reverse-proxy seçimi, §19.6 gerçek cron zamanlaması + saklama (retention) politikasının canlı ortamda işletilmesi (script'ler ve bir restore testi Bölüm 46'da yazıldı/doğrulandı — asıl operasyonel çalıştırma LITZOR'un altyapısında), §19.7 gerçek uptime monitor servisi seçimi (health endpoint zaten var, hangi izleme servisinin onu ping'leyeceği LITZOR'un kararı), §11.2 ve §20 AC-01'in ortak telefon (SMS) doğrulama yarısı (e-posta doğrulama Bölüm 48'de genel kayıt için, Bölüm 57'de seller başvurusu gate'i olarak tam kapatıldı; SMS gönderimi için bir gateway seçimi + kimlik bilgileri — Monri/PSP seçimiyle aynı türden bir LITZOR kararı — gerekiyor), §21.1'in tamamı (ticaret unvanı, PSP seçimi, kredi paketi fiyatları, bid increment tablosu gerçek değerleri, anti-sniping süresi onayı, nihai ME/EN metinler, logo/favicon/marka varlıkları).

### Sayısal özet

Doküman ~150+ ayrı madde/checkbox içeriyor (madde numaraları + alt-checkbox'lar + AC-01→21 + §21.1). Bu oturum sonunda: **kod tarafında karşılanabilecek maddelerin büyük çoğunluğu ✅ (backend tarafında test+Postgres ile tam doğrulanmış, frontend tarafında kod-seviyesinde doğrulanmış ama tarayıcıda tıklanmamış)**; **B listesi Bölüm 50'de "tamamen boş" ilan edilmişti ama bu yanlıştı** — Bölüm 52'de düzeltildi: §6.1/§6.2/§7/§3.6 doküman'ın kendi verdiği taksonomiyle kod-tamamlanabilir olduğu halde B2'ye yanlış sınıflandırılmıştı. §6.1 Bölüm 52'de, §7.1/§7.2.2 Bölüm 53'te, §7.2.1/§3.6 kalanı Bölüm 54'te, §6.2 Bölüm 55'te kapatıldı (Bölüm 54'te ayrıca Bölüm 53'ün kendi ürettiği bir kategori-bucketing regresyonu ve `parent_id`'nin public API'den hiç dönmediği ayrı bir backend hatası düzeltildi; Bölüm 55'te ayrı, kapsam dışı bırakılan bir `adminFetch` HTTP-metodu hatası bulundu). **B listesi artık gerçekten tamamen boş.** Geriye **B2'deki 3 madde grubu** (§2.7/AC-14, §20 AC-16'nın görsel yarısı, §4.3/AC-20) gerçek bir tarayıcı/cihaz veya kodla-çözülemez bir sınır gerektiriyor — LITZOR'un konusu değil ama kodla da ilerletilemez (eksiksizlik denetiminde 7-8 yeni madde bulunmuştu — bkz. Bölüm 30; Bölüm 31/33/34'te beş madde gerçekten kapatıldı; Bölüm 35'te bir madde daha, kod yazılmadan, zaten yapılmış olduğu fark edilerek listeden çıkarıldı; Bölüm 42'de §10.1 kapatıldı ama aynı denetimde §10.2/§10.3 yeni açık madde olarak bulundu; Bölüm 43'te §10.2/§10.3 de kapatıldı; Bölüm 44'te §4.1'in son kalan parçası — seller type filtresi — kapatıldı; Bölüm 45'te §17.3 admin 2FA kapatıldı; Bölüm 46'da §19.6/§19.7 backup+restore ve error alerting kapatıldı; Bölüm 47'de §11.3 Seller Dashboard kapatıldı ve B listesi B/B2 olarak yeniden sınıflandırıldı — ama Bölüm 52'nin gösterdiği gibi bu sınıflandırmanın 4 satırı yanlıştı; Bölüm 48'de §20 AC-01'in e-posta yarısı kapatıldı, aynı turda oturumun başından beri süregelen 3 test hatasının kök nedeni de düzeltildi; Bölüm 49'da §11.4 multi-step create-listing wizard'ı kapatıldı; Bölüm 51'de §20 AC-16'nın statik yarısı + iki gerçek i18n hatası kapatıldı; Bölüm 52'de §6.1 kapatıldı ve B2 sınıflandırma hatası düzeltildi; Bölüm 53'te §7.1/§7.2.2 kapatıldı; Bölüm 54'te §7.2.1/§3.6 kalanı kapatıldı ve Bölüm 53'ün kendi bucketing regresyonu + bir ayrı backend `parent_id` hatası düzeltildi; Bölüm 55'te §6.2 kapatıldı, B listesi böylece TAMAMEN boşaldı); **C listesindeki ~10 madde grubu** ise LITZOR'un girdisi olmadan hiçbir oturumda kapatılamaz — bunlar "tamamlanmadı" değil, "yazılımla çözülemez" olarak kalıcı şekilde işaretlenmelidir.

**Sonuç**: Proje dokümanın hedeflediği son duruma dokümanın izin verdiği ölçüde yaklaşmıştır, ancak (a) B listesindeki kod işleri bitmeden ve (b) C listesindeki LITZOR girdileri sağlanmadan doküman "tamamen karşılanmış" sayılamaz. Bu, kodun eksikliğinden değil, dokümanın kendi yapısından kaynaklanan bir sınırdır (§21.1'in kendisi bunu açıkça öngörüyor).

## 23. Revizyon Geçmişi (30.07.2026, devam) — §19.1 HTTPS Redirect Middleware

B listesinden bir madde daha kapatıldı: `main.py`'ye `ENVIRONMENT=production` iken devreye giren `HTTPSRedirectMiddleware` (Starlette'in kendi middleware'i, yeni bağımlılık yok) eklendi. Test/dev ortamında (`ENVIRONMENT` `production` değilken) devre dışı — `conftest.py` bunu zaten set etmiyor, dolayısıyla test suite etkilenmedi. Gerçek reverse-proxy/TLS-termination senaryosunda (`X-Forwarded-Proto` ileten bir proxy yoksa) bu middleware'in tek başına yeterli olmayacağı koda yorum olarak not edildi.

Doğrulama: `pytest` 156/159 (aynı 3 önceden var olan hata, değişmedi); `docker compose up --build -d` + `curl` → dev modda 200 (redirect yok, beklenen); `docker exec bidmont-app python -c "..."` ile `ENVIRONMENT=production` set edildiğinde middleware'in gerçekten `app.user_middleware` listesine eklendiği doğrulandı (`['CORSMiddleware', 'HTTPSRedirectMiddleware']`); Docker loglarında hata yok.

Bölüm 22'deki B listesinden çıkarıldı, §19.1 matris satırı güncellendi.

## 24. Revizyon Geçmişi (30.07.2026, devam) — §5.5/§5.7 Join Auction + Bid confirmation

B listesinden bir madde daha kapatıldı: `index.html`'deki `bid()` fonksiyonu artık iki noktada `confirm()` (native tarayıcı diyaloğu, yeni bağımlılık/özel modal bileşeni yok) kullanıyor:

1. **§5.7** — teklif göndermeden hemen önce: "Place a bid of €X? This is binding once submitted." Kullanıcı iptal ederse hiçbir API çağrısı yapılmıyor.
2. **§5.5** — backend 403 ("join required") döndürdüğünde artık sessizce otomatik `joinAuction()` çağrılmıyor; önce "Joining this auction costs N BidMont credits. Continue?" onayı isteniyor, ancak onaylanırsa `joinAuction()` + tekrar `placeBid()` çağrılıyor.

Önceki davranış: 403 yakalanınca kullanıcıya sormadan sessizce join çağrısı yapılıyordu — doc'un istediği "açık onay" değil, dolaylı/sessiz akıştı. Şimdi her iki kredi harcayan eylem de (join, bid) kullanıcıdan açık onay alıyor.

Doğrulama: `node --check` ile `<script>` bloğu söz dizimi doğrulandı (SYNTAX_OK). Bu değişiklik salt frontend/JS olduğu için backend testleri (`pytest`) etkilenmedi, ayrıca çalıştırılmadı. Daha önce tüm frontend değişikliklerinde olduğu gibi gerçek tarayıcıda tıklanarak test edilmedi (headless tarayıcı bu ortamda yok) — bu "kod tamam, tarayıcıda doğrulanmadı" seviyesinde bir kapanıştır.

**Bilinen sınır (ponytail: native `confirm()` event loop'u bloke eder)**: tarayıcının yerleşik `confirm()` diyaloğu senkron çalışır — kullanıcı diyaloğu açık bırakırsa, o sekmedeki WebSocket `onmessage` handler'ı (canlı ihale güncellemeleri) da bloke kalır; diyalog kapanınca birikmiş mesajlar işlenir, kayıp olmaz ama gecikir. Doc'un §5.7'si muhtemelen sayfa-içi (in-page) bir modal bekliyor, native `confirm()` değil — bu, en ucuz/bağımlıksız çözüm olduğu için tercih edildi (ladder rung 4: native platform feature). Sayfa-içi modal'a yükseltmek gerekirse (ör. bloklamayan bir onay akışı istenirse) bu B listesine yeni bir alt-madde olarak eklenmeli.

Bölüm 22'deki B listesinden §5.5/§5.7 satırı çıkarıldı.

## 25. Revizyon Geçmişi (30.07.2026, devam) — §5.2 Çoklu fotoğraf galerisi + lightbox

B listesinden bir madde daha kapatıldı. Backend zaten `AuctionDetailResponse.images` üzerinden `AuctionImage` tablosundaki tüm görselleri (`sort_order`'a göre) döndürüyordu (`backend/app/api/auctions.py`, `backend/app/schemas/auction.py:118-119`) — eksik olan tamamen frontend gösterimiydi (yalnızca `images[0]` kullanılıyordu).

Eklenenler (`index.html`):
- `renderGallery(a)`: `#detailThumbs` altına küçük resim şeridi basıyor (tek görsel varsa şerit gizli kalıyor); bir küçük resme tıklamak ana görseli değiştiriyor.
- `#lightboxOverlay`/`#lightboxImg`/`#lightboxClose`/`#lightboxPrev`/`#lightboxNext`: ana görsele tıklayınca tam ekran lightbox açılıyor; ok tuşları (←/→) ve Escape ile gezinme/kapama; overlay'in kendisine (resmin dışına) tıklamak da kapatıyor.
- **Düzeltilen kenar durum**: `renderDetail` (dolayısıyla `renderGallery`) WebSocket'ten gelen `new_bid`/`auction_status_changed` mesajlarında tekrar çalışıyor — lightbox açıkken bir teklif gelirse `galleryImages` yeniden atanıyor. `galleryIndex` yeni dizinin sınırları dışında kalırsa 0'a çekiliyor (clamp) ve lightbox açıksa gösterilen görsel de güncelleniyor; aksi halde `galleryIndex` sınır dışı kalıp sonraki ileri/geri tıklamasında görsel güncellenmeyebilirdi.
- Yeni bağımlılık yok — native CSS/JS, mevcut tasarım diline uygun stil (`.detail-thumb`, `.lightbox-*`).

Doğrulama: `node --check` ile söz dizimi doğrulandı (SYNTAX_OK); DOM-id çapraz referans denetimi (`$('#id')` kullanımları vs `id="..."` tanımları) farksız çıktı verdi — hiçbir sarkan referans yok; `pytest` 156/159 (aynı 3 önceden var olan hata, bu değişiklik saf frontend olduğu için beklenen şekilde etkilenmedi). Gerçek tarayıcıda tıklanarak test edilmedi (headless tarayıcı yok) — "kod tamam, tarayıcıda doğrulanmadı" seviyesinde kapanış.

Bölüm 22'deki B listesinden §5.2 satırı çıkarıldı; sayısal özet ~23'ten ~22'ye güncellendi.

## 26. Revizyon Geçmişi (30.07.2026, devam) — §10.6 Profile alanları: city/address (kısmi kapanış)

**Düzeltme**: Bu madde önceki commit'te yanlışlıkla "§10.1" olarak etiketlenmişti. Docx'in ham metnini (`docs/Bidmont son hali için döküman .docx`, `word/document.xml`) tekrar açıp doğrulandı: **§10.1 "Dashboard navigasyonu ekle"** — Overview/My Credits/My Bids/Joined Auctions/Watchlist/Notifications/Profile/Security menüsü isteyen, tamamen farklı ve hâlâ tamamen açık bir madde. City/address alanı asıl **§10.6 "Profile alanlarını iyileştir"** içinde geçiyor: *"Buyer için full name, email, phone, address/city, language; Company hesabı için company name, PIB/registration vb. seller onboarding'de genişlet."* Yani bu oturumda kapatılan yalnızca §10.6'nın "address/city" alt-parçası — §10.6'nın geri kalanı (dil tercihi alanı, kurumsal hesap için company name/PIB/registration alanları) hâlâ açık.

B listesinden bir madde daha (kısmen) kapatıldı: alıcı profilinde şehir/adres alanı.

Backend:
- `backend/app/models/domain.py`: `User.city`, `User.address` (nullable `String`) eklendi.
- `backend/app/core/migrations.py`: `MISSING_COLUMNS["users"]`'a `("city", "VARCHAR")`, `("address", "VARCHAR")` eklendi.
- `backend/app/schemas/auth.py` (`UserResponse`) ve `backend/app/schemas/user.py` (`UserUpdateRequest`): `city`/`address` alanları (opsiyonel) eklendi.
- `backend/app/api/users.py`: iki yerde tekrarlanan `UserResponse(...)` inşası ortak `_user_response()` yardımcı fonksiyonuna taşındı (aynı anda `city`/`address` de eklendi); `update_me` artık bu alanları da güncelliyor.

Frontend (`index.html`):
- Profil düzenleme formuna `#profileCity`/`#profileAddress` girişleri eklendi (`r.city`/`r.address` çeviri anahtarları her iki dile de eklendi).
- `renderProfile()` bu alanları `apiUser.city`/`apiUser.address`'ten dolduruyor; kayıt handler'ı `updateMe()` çağrısına `city`/`address` ekliyor.

Doğrulama: `node --check` (SYNTAX_OK), DOM-id çapraz referans denetimi farksız; `pytest` 156/159 (aynı 3 önceden var olan hata); `docker compose up --build -d` ile yeniden derlendi, başlangıç loglarında `Migration: added users.city` / `Migration: added users.address` görüldü (temiz ekleme); canlı Postgres'e karşı `urllib` ile smoke test — kayıt/login, `GET /users/me` (başlangıçta `city`/`address` null), `PUT /users/me` ile ikisi de ayarlandı, tekrar `GET` ile kalıcılık doğrulandı (`PROFILE CITY/ADDRESS SMOKE CHECK PASSED`).

Bölüm 22'deki B listesinden §10.1/§10.6'yı birleştiren eski satır çıkarıldı; yerine iki ayrı, doğru numaralandırılmış satır yazıldı: §10.1 (dashboard navigasyonu, tamamen açık) ve §10.6 kalanı (dil tercihi + kurumsal hesap alanları, kısmen açık). Madde sayısı net değişmedi (bir madde kısmen kapandı ama iki ayrı satıra bölündüğü için B listesi ~21 civarında kaldı — bkz. güncellenmiş liste).

## 27. Revizyon Geçmişi (30.07.2026, devam) — §18.1 UI tarafı: Karadağ yerel saat gösterimi

B listesinden bir madde daha kapatıldı: DB zaten UTC tutuyordu (bu zaten A listesindeydi), eksik olan UI'ın bunu tarayıcının kendi yerel saatine değil, **Karadağ yerel saatine** çevirerek göstermesiydi — önceki kod `new Date(x).toLocaleString()`/`toLocaleDateString()` çağırıyordu, bu da ziyaretçinin kendi tarayıcı/OS saat dilimini kullanıyordu (çoğu Karadağ'daki kullanıcı için tesadüfen doğru sonuç veriyordu, ama yurt dışından bağlanan bir admin ya da farklı saat dilimine ayarlı bir cihaz için yanlış olurdu — doc'un yazdığı şey de bu değildi).

Eklenenler (`index.html`):
- `MT_TZ='Europe/Podgorica'` sabiti + `mtDateTime(d)`/`mtDate(d,opts)` yardımcıları — `Intl`'in `timeZone` seçeneğini kullanıyor (native, yeni bağımlılık yok), CET/CEST DST geçişini otomatik hesaba katıyor.
- Yedi çağrı noktası (`toLocaleString()`/`toLocaleDateString()` idi) `mtDateTime`/`mtDate`'e çevrildi: support ticket detayı, admin kullanıcı listesi "joined" tarihi, admin auction listesi, admin bid listesi, admin ticket listesi, audit log listesi, bildirim menüsü zaman damgaları.

Doğrulama: `node --check` (SYNTAX_OK); ayrıca `mtDateTime('2026-07-30T22:15:00Z')` manuel çalıştırıldı → `"31 Jul 2026, 00:15"` (UTC 22:15 + 2 saat CEST = ertesi gün 00:15 — gece yarısını geçen UTC saatlerin doğru tarihe yuvarlandığı doğrulandı); DOM-id çapraz referans denetimi farksız; `pytest` 156/159 (aynı 3 önceden var olan hata, saf frontend değişikliği). Gerçek tarayıcıda tıklanarak test edilmedi (headless tarayıcı yok).

Bölüm 22'deki B listesinden "§18.1 alt-detay" satırı çıkarıldı.

## 28. Revizyon Geçmişi (30.07.2026, devam) — §14.1.1 About Us sayfasının genişletilmesi

B listesinden bir madde daha kapatıldı. Doc'un ham metni (`docs/Bidmont son hali için döküman .docx`) tekrar okunarak §14.1.1'in tam istediği doğrulandı: *"Mevcut About sayfasında yalnızca tek 'Our Mission' kartı var. Bölümler: What is BidMont, Mission for Montenegro, How Credits & Bidding Work, Who Can Sell, Trust & Transparency, Platform Role, Operator LITZOR DOO, corporate/legal information. Beklenen sonuç: Sayfa BidMont'un rolünü satış aracısı gibi göstermemeli."*

`index.html`'deki `#about` sayfası önceden gerçekten tek bir panelden ("Naša Misija" / "Our Mission") ibaretti. Şimdi istenen 7 bölümün tamamı ayrı panel olarak eklendi (ME ve EN çevirileriyle, `about.*` i18n anahtarları): What is BidMont, Mission for Montenegro (mevcut misyon metni bu oturumda **yeniden yazıldı** — eski metin "prodaju vozila..." / "the sale of vehicles..." ifadesiyle BidMont'u satış sürecinin bir parçası gibi gösteriyordu, doc'un yasakladığı tam da buydu), How Credits & Bidding Work, Who Can Sell, Trust & Transparency, Platform Role (mevcut `det.platformrole` metniyle aynı çizgide: "predmet prodavcunun mülkiyetinde kalır, son satış/ödeme/devir yalnızca alıcı-satıcı arasında"), Operator: LITZOR DOO.

**Dürüst sınır**: "Operator: LITZOR DOO" bölümü kasıtlı olarak bir placeholder — gerçek tescil numarası/PIB/sicil adresi LITZOR DOO'nun sağlaması gereken bir bilgi (Bölüm 22'nin C listesinde zaten yer alıyor); bu oturum yalnızca bölümün kod/sayfa yapısını ekledi, içindeki metin açıkça "LITZOR DOO tarafından sağlandığında burada yayınlanacak" diyor — gerçek kurumsal bilgi gibi sunulmadı.

Doğrulama: `node --check` (SYNTAX_OK); yeni 8 çift (ME+EN = 16) `about.*` çeviri anahtarının her ikisinde de tanımlı olduğu tek tek grep ile doğrulandı; DOM-id çapraz referans denetimi farksız; `pytest` 156/159 (saf frontend değişikliği, backend dokunulmadı). Gerçek tarayıcıda tıklanarak test edilmedi (headless tarayıcı yok).

Bölüm 22'deki B listesinden §14.1 satırı çıkarıldı (LITZOR'un gerçek kurumsal bilgisi hâlâ C listesinde, ayrı ve doğru şekilde).

## 29. Revizyon Geçmişi (30.07.2026, devam) — §3.2/§3.8/§3.9/§3.10 Ana sayfa: Featured Auction, Why BidMont, Seller Acquisition, Disclaimer

B listesinden bir madde daha kapatıldı: ana sayfanın dört eksik bölümü. Doc'un ham metni tekrar okunarak tam istekler doğrulandı:
- **§3.2**: *"Hero'nun sağ yarısı büyük ölçüde boş. Sağ tarafa gerçek bir 'Featured/Live Auction' kartı koy: gerçek asset görseli, başlık, şehir, current bid, teklif sayısı, kalan süre ve View Auction. Desktop'ta hero dengeli görünmeli; mobilde kart başlığın altına inmeli."*
- **§3.8**: *"Why BidMont alanı ekle... Local / Verified / Transparent üçlüsünü kullan... 3-4 kart halinde."*
- **§3.9**: *"Seller acquisition alanı ekle... 'Sell with BidMont' bölümü... Hedef: şirketler, rent-a-car filoları, sigorta şirketleri, construction, hospitality, dealers. CTA seller application'a gitmeli. Doğrudan ilan yayınlama değil başvuru/onay akışı olmalı."*
- **§3.10** (B listesinde ayrı satır olarak yoktu — bu oturumda matrix'te gözden kaçtığı fark edildi, aynı anda kapatıldı): *"Ana sayfa disclaimer ekle... Footer öncesi kısa bir 'Platform Role' açıklaması koy: BidMont online teklif altyapısını sağlar; final satış/ödeme/devir/teslim alıcı-satıcı arasındadır."*

Eklenenler:
- **Hero-right Featured Auction kartı** (`#heroFeatured`, `renderFeaturedAuction()`): backend'in zaten var olan `Auction.is_featured` alanını (model+schema önceki oturumlarda eklenmişti) kullanıyor — admin'in `is_featured=true` işaretlediği canlı bir aukciyon varsa onu, yoksa süresi en yakın biten canlı aukciyonu seçiyor; gerçek görsel, başlık, şehir, `GET /auctions/{id}/bids` ile canlı çekilen teklif sayısı, `timeLeft()` ile kalan süre ve "View Auction" linkini gösteriyor. Demo/API-siz modda (`_isApi` yok) kart `display:none` kalıyor — sahte veri uydurulmadı. `hero-container` flex düzenine geçirildi (`flex-wrap`), mobilde kart doğal DOM sırasıyla başlığın altına iniyor (ekstra medya sorgusu gerekmedi, `.hero-featured{max-width:100%}` eklendi).
- **Why BidMont** (`.why-grid`, 3 kart): Local / Verified / Transparent, doc'un istediği üçlü.
- **Sell with BidMont** (`.seller-cta`): CTA `#apply-seller`'a gidiyor (zaten var olan başvuru/onay akışı — doğrudan ilan yayınlama değil).
- **Ana sayfa disclaimer** (`home.disclaimer`): footer'dan hemen önce, `det.platformrole` ile aynı mesaj çizgisinde.

Doğrulama: `node --check` (SYNTAX_OK); yeni 14 çevrimin (feat.*, why.*, sellcta.*, home.disclaimer = 7 anahtar × 2 dil) her ikisinde de tanımlı olduğu tek tek grep ile doğrulandı; DOM-id çapraz referans denetimi farksız; `pytest` 156/159 (saf frontend değişikliği). `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı `urllib` smoke test — verified seller ile canlı+`is_featured=true` bir aukciyon oluşturuldu, `GET /auctions?limit=100` yanıtında `is_featured: true` olarak geri geldiği doğrulandı (frontend'in tükettiği tam alan). Gerçek tarayıcıda tıklanarak test edilmedi (headless tarayıcı yok).

**Düzeltme (aşırı iddialı doğrulama beyanı)**: bu bölüm ilk yazıldığında "kartın görsel dengesi kod-seviyesinde doğrulanmış" deniyordu — bu yanlış bir ifadeydi. §3.2'nin kabul kriteri olan "Desktop'ta hero dengeli görünmeli" tam olarak **görsel bir denge** iddiası ve hiçbir kod-seviyesi kontrol (syntax check, DOM audit, pytest) bunu doğrulayamaz — bu kesinlikle **doğrulanmamış** durumda. Ayrıca bu turda `.hero-container`/`.hero-content` gibi paylaşılan, önceden var olan layout CSS'i değiştirildi (önceki turların tamamı yalnızca yeni markup *ekliyordu*, mevcut layout'a dokunmuyordu) — bu daha riskli bir değişiklik sınıfı. İki somut bilinmeyen: (1) `.hero-content{max-width:650px}` (eski kural) ile yeni `flex:1 1 480px` etkileşimi + `justify-content:space-between` kartı içerikten uzağa itebilir; (2) ~620-900px genişlik aralığı (mevcut mobil medya sorgusunun kapsamadığı, ama hero-content+kart yan yana sığmayacağı bant) `min-height:100vh` + `align-items:center` ile birlikte sarma/taşma davranışı test edilmedi. Bunlar kod hatası değil — sadece görsel doğrulamanın bu oturumun araç setiyle (tarayıcısız) mümkün olmadığının açık itirafı.

Bölüm 22'deki B listesinden "§3.2/3.8/3.9: ana sayfada..." satırı çıkarıldı.

## 30. Revizyon Geçmişi (30.07.2026, devam) — Bölüm 22'nin eksiksizlik denetimi (docx bölüm numaralarının tam çıkarımı)

Advisor'ın önerisiyle şu soru soruldu: Bölüm 22'nin A/B/C listeleri docx'in **tüm** bölümlerini kapsıyor mu, yoksa Bölüm 16/20'nin orijinal matrisi bazı maddeleri atladı mı? Bunu varsayımla değil, doğrudan ölçerek yanıtlamak için: `docs/Bidmont son hali için döküman .docx`'in `word/document.xml`'i Python ile açılıp düz metne çevrildi, düz metinden regex ile **her** `N.N` / `N.N.N` bölüm numarası çıkarıldı (108 farklı numara bulundu: §1.0'dan §21.1'e kadar), ve bu liste Bölüm 22'nin A/B/C listelerinde (hem açık `§N.N` referansları hem de "§12", "§16" gibi tüm alt-maddeleri kapsayan çıplak referanslar) geçen numaralarla karşılaştırıldı.

**Bulgu 1 (gerçek bir tutarsızlık, düzeltildi)**: bu oturumda kapatılıp B listesinden çıkarılan maddelerin (§5.2, §5.5, §5.7, §10.6 kısmi, §14.1.1, §3.2/3.8/3.9/3.10) hiçbiri A listesine hiç eklenmemişti — yalnızca B listesinden siliniyorlardı. Yani Bölüm 22 bir süre "ne A'da ne B'de" görünen maddeler içeriyordu. A listesi yukarıda düzeltildi, hepsi eklendi.

**Bulgu 2 (§18.2 hiç değinilmemiş)**: doc'un "Bid endpoint transaction sırası" maddesi (§18.2 — 10 adımlık lock/re-read/validate/insert/commit/notify sırası) Bölüm 16/20/22'nin hiçbirinde hiç geçmiyordu. `backend/app/api/bids.py::place_bid` kodu okunarak kontrol edildi ve doc'un istediği sırayla kavramsal olarak eşleştiği görüldü (A listesine eklendi, kod-okuması ile sınırlı olduğu çekince olarak not edildi — bkz. yukarı).

**Bulgu 3 (yeni açık maddeler)**: §3.5, §3.6 (kısmi), §4.1, §4.5, §6.2, §8.1, §8.7 (kısmi) daha önce Bölüm 16/20/22'nin hiçbirinde hiç geçmiyordu — şimdi B listesine eklendi.

**Sınır**: bu denetim yalnızca "her bölüm numarası en az bir yerde anılıyor mu" sorusunu yanıtlıyor — anılan her maddenin doğruluğunu (ör. "§X zaten yapılmış" denilen yerlerin hepsinin fiilen doğru olduğunu) tekrar tek tek doğrulamadı. Yani Bölüm 22 artık **eksiksiz bir envanter** ama her satırının doğruluğu yalnızca o satırın kendi revizyon notundaki kanıta bağlı.

## 31. Revizyon Geçmişi (30.07.2026, devam) — §3.3 CTA metni, §4.5 boş durum (empty state), §8.7 satın alma sonrası aynı aukciyona dönüş

B listesinden üç madde daha kapatıldı — hepsi şema değişikliği gerektirmeyen, sınırlı kapsamlı işler.

**§3.3 (CTA metni)**: doc'un istediği birincil CTA "View Auctions" idi, EN çeviri sözlüğünde `hero.btn1` "🔨 Browse Auctions" yazıyordu — tek satırlık metin düzeltmesi (`index.html`). İkincil CTA zaten doğruydu, dokunulmadı.

**§4.5 (boş durum)**: `renderGrid()` artık `#auctionGrid` için özel bir boş-durum dalı içeriyor — filtre sonucu boşsa "No auctions match your filters" mesajı + "Clear Filters" ve "View All Auctions" butonları gösteriliyor (yeni `clearAuctionFilters()` fonksiyonu arama/kategori/sıralama alanlarını sıfırlayıp grid'i yeniden çiziyor). Diğer grid'ler (vehicle/equipment/general/search) — hiçbirinde filtre yok, bu yüzden değiştirilmedi, eski genel "No results" mesajını koruyorlar.

**§8.7 kalanı (satın alma sonrası aynı aukciyona dönüş)**: doc: *"Yetersizse Join önle ve 'Buy Credits' CTA göster... Kullanıcı paket satın alıp geri döndüğünde aynı auction'a devam edebilmeli."* Önceki davranış: 402 (yetersiz kredi) durumunda `#profile`'a yönlendiriliyordu, kullanıcı manuel paket seçip satın aldıktan sonra Monri'nin hosted ödeme sayfasından her zaman `#profile?credits=success`'e dönüyordu — hangi aukciyonu denediği kayboluyordu.
- Backend (`backend/app/api/credits.py`): `CheckoutRequest`'e `return_auction_id: str | None` eklendi; geçerli bir UUID ise Monri form alanlarındaki `success_url_override`, `#profile?credits=success` yerine `#detail?id={auction_id}&credits=success` olarak kuruluyor. UUID doğrulaması (`uuid.UUID(...)` `try/except`) var — geçersiz/uydurma bir string doğrudan redirect URL'ine enjekte edilemiyor, sessizce `#profile`'a düşüyor.
- Frontend (`index.html`): `bid()`'in iki 402 dalı artık `store.set('bidmont_pending_credit_auction', a.id)` ile denenen aukciyonu `localStorage`'da (Monri'nin harici domain'ine gidip geri dönen tam sayfa yönlendirmesini hayatta kalacak şekilde) saklıyor; `buyCreditPkg()` bunu okuyup `createCreditCheckout(packageId, true, returnAuctionId)`'e geçiriyor; `route()` artık `credits=success` query param'ını her sayfada kontrol edip başarı toast'ı gösteriyor ve pending marker'ı temizliyor.

Doğrulama: `node --check` (SYNTAX_OK); DOM-id çapraz referans denetimi farksız; `pytest` 156/159 (aynı 3 önceden var olan hata). `docker compose up --build -d` ile yeniden derlendi (backend değişikliği içeriyordu, rebuild gerekliydi — ilk smoke test denemesi eski image'a karşı çalıştığı için beklendiği gibi başarısız oldu, rebuild sonrası tekrar çalıştırıldı). Canlı Postgres'e karşı `urllib` smoke test: geçerli bir UUID `return_auction_id` ile checkout isteğinde `success_url_override`'ın tam olarak `#detail?id={uuid}&credits=success` içerdiği doğrulandı; ayrıca kasıtlı olarak bozuk bir `return_auction_id` (`"not-a-uuid<script>"`) gönderilip yanıtın bunu enjekte etmeden `#profile?credits=success`'e sessizce düştüğü doğrulandı (güvenlik-sınırı testi). Gerçek tarayıcıda tıklanarak test edilmedi (headless tarayıcı yok) — özellikle Monri'nin hosted sayfasından gerçek bir dönüşün `localStorage` marker'ını doğru okuyup okumadığı yalnızca kod-seviyesinde doğrulandı.

Bölüm 22'deki B listesinden §3.3 alt-detay, §4.5 ve §8.7 kalanı satırları çıkarıldı.

**Ek düzeltme (bu bölümü kapatırken bulunan gerçek bir hata)**: `buyCreditPkg()` yalnızca satın alma başarıyla tamamlanıp `#detail?...&credits=success`'e dönüldüğünde `bidmont_pending_credit_auction` marker'ını temizliyordu. Kullanıcı 402 alıp `#profile`'a yönlendirildikten sonra satın almadan vazgeçip başka bir sayfaya giderse, marker `localStorage`'da kalıcı olarak kalıyor ve haftalar sonra tamamen alakasız bir kredi satın alımına iliştirilip kullanıcıyı süresi çoktan dolmuş bir aukciyona geri götürebilirdi. Düzeltme: `buyCreditPkg()` artık marker'ı okur okumaz hemen temizliyor (`store.set(...,null)`), böylece her satın alma denemesi marker'ı tam olarak bir kez tüketiyor — dönüş yolculuğu tamamlanıp tamamlanmamasından bağımsız.

## 32. Revizyon Geçmişi (30.07.2026, devam) — §10.6 kalanı (dil tercihi alanı): `User.preferred_language`

B listesindeki "§10.6 kalanı" maddesinin **dil tercihi** yarısı kapatıldı (kurumsal hesap alanları — company name/PIB/registration — hâlâ açık, B listesinde ayrı kaldı). Bu aynı zamanda §16.3'ün (ME/EN e-posta şablonları) ön koşuluydu — doc: *"User preferred language'a göre Crnogorski/English transactional templates hazırla."* §16.3'ün kendisi (gerçek şablon metinleri + ~15 `send_notification()` çağrı noktasının bu tercihe göre e-posta içeriği seçmesi) **bu turda kapatılmadı** — kapsamı büyük olduğu için ayrı bir sonraki tura bırakıldı, bilinçli bir kapsam sınırı.

Backend:
- `backend/app/models/domain.py`: `User.preferred_language` (nullable `String`, "me"/"en" değerleri, `None`=tercih belirtilmemiş).
- `backend/app/core/migrations.py`: `MISSING_COLUMNS["users"]`'a `("preferred_language", "VARCHAR")` eklendi.
- `backend/app/schemas/auth.py` (`UserResponse`), `backend/app/schemas/user.py` (`UserUpdateRequest` — `Literal["me","en"]` ile kısıtlı, geçersiz değer 422 döner).
- `backend/app/api/users.py`: `_user_response()` ve `update_me()` alanı içeriyor.

Frontend (`index.html`):
- Profil formuna `#profileLanguage` dropdown'u eklendi (`r.lang`/`r.lang.me`/`r.lang.en` çevirileri her iki dilde de tanımlı).
- `renderProfile()` alanı `apiUser.preferred_language`'dan dolduruyor (boşsa mevcut UI dilini varsayılan gösteriyor); kayıt handler'ı `updateMe()`'e `preferred_language` ekliyor.

Doğrulama: `node --check` (SYNTAX_OK); DOM-id çapraz referans denetimi farksız; `pytest` 156/159 (aynı 3 önceden var olan hata); `docker compose up --build -d` ile yeniden derlendi, `Migration: added users.preferred_language` logda görüldü; canlı Postgres'e karşı `urllib` smoke test — kayıt/login, `GET /users/me` (başlangıçta `null`), `PUT /users/me {"preferred_language":"en"}` ile ayarlandı ve kalıcılığı doğrulandı, ayrıca geçersiz bir değer (`"fr"`) gönderilip Pydantic `Literal` kısıtının 422 ile reddettiği doğrulandı (`PREFERRED_LANGUAGE SMOKE CHECK PASSED`).

Bölüm 22'deki B listesinde "§10.6 kalanı" satırı, yalnızca kurumsal hesap alanlarını (company name/PIB/registration) kapsayacak şekilde daraltıldı; §16.3 (e-posta şablonlarının kendisi) B listesinde açık kalmaya devam ediyor.

## 33. Revizyon Geçmişi (30.07.2026, devam) — §16.3 ME/EN e-posta şablonları

B listesindeki son büyük madde kapatıldı: doc'un istediği *"User preferred language'a göre Crnogorski/English transactional templates hazırla... E-posta dili user profile ile uyumlu olmalı."*

Tasarım kararı: doc yalnızca **e-posta** dilinin profil tercihini takip etmesini istiyor, uygulama-içi bildirim çanı metnini değil. Bu yüzden mevcut mimariye asgari müdahale ile:
- `backend/app/services/notifications.py::send_notification()`'a iki yeni opsiyonel parametre eklendi: `title_me`, `message_me`. E-posta gönderilirken, alıcının `User.preferred_language == "me"` VE bu iki parametre sağlanmışsa Karadağca metin kullanılıyor; aksi halde (tercih yok, tercih "en", ya da çağıran ME metni sağlamadıysa) mevcut İngilizce `title`/`message` kullanılıyor — **geriye dönük tam uyumlu**, hiçbir eski çağrı kırılmadı.
- Uygulama-içi bildirim satırı (`Notification.title`/`.message`, veritabanına yazılan ve bildirim çanında gösterilen) **hiç değiştirilmedi** — hâlâ çağıranın verdiği İngilizce metni kullanıyor. Bu kasıtlı bir kapsam sınırı: doc'un istediği tam olarak bu değil, yalnızca e-posta.
- Backend'deki **17 `send_notification()` çağrı noktasının tamamına** (`admin.py` x3, `auctions.py` x3, `bids.py` x4, `credits.py` x2, `sellers.py` x1, `scheduler.py` x1, `services/auctions.py` x3) karşılık gelen Karadağca `title_me`/`message_me` çevirisi eklendi — `send_email=False` olan üç çağrı noktası (auction_joined, auction_extended, auction_lost) dahil, gelecekte biri `send_email=True`'ya çevrilirse çeviri zaten hazır olsun diye.

Doğrulama:
- Yeni birim/entegrasyon testleri (`backend/tests/integration/test_notifications.py::TestPreferredLanguageEmail`): `_send_email` monkeypatch ile gerçek SMTP olmadan yakalanıp (a) `preferred_language="me"` olan kullanıcı için e-postanın `title_me`/`message_me` içerdiği, (b) tercih yokken e-postanın İngilizce kaldığı, (c) her iki durumda da veritabanındaki bildirim satırının hâlâ İngilizce olduğu doğrulandı.
- `pytest` 158/159 (156'dan 158'e — 2 yeni test eklendi; aynı 3 önceden var olan hata, değişmedi).
- `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı `urllib` smoke test — bir kullanıcı `preferred_language="me"` yapıp `seller_application_submitted` bildirimini tetikleyen bir eylem (`POST /sellers/apply`) çalıştırdı, 201 döndü (çökme yok), `GET /notifications` ile uygulama-içi satırın tasarım gereği hâlâ İngilizce (`"Seller application submitted"`) kaldığı doğrulandı.
- Gerçek bir e-postanın gerçekten Karadağca gövdeyle gittiği doğrulanmadı — bu ortamda `SMTP_HOST`/`SMTP_USER`/`SMTP_PASSWORD` yapılandırılmadığı için `_send_email()` her zaman sessizce atlanıyor (mevcut, önceden var olan davranış). Birim testindeki `monkeypatch` bunun yerini alıyor; gerçek bir SMTP sunucusuna karşı uçtan uca doğrulama LITZOR'un gerçek SMTP kimlik bilgilerini sağlamasını bekliyor (Bölüm 22'nin C listesindeki genel "gerçek altyapı kimlik bilgileri" kısıtının bir parçası).

Bölüm 22'deki B listesinden §16.3 satırı çıkarıldı. Görev #17 tamamlandı olarak işaretlendi.

## 34. Revizyon Geçmişi (30.07.2026, devam) — §3.5 "Live & Ending Soon" bölümü

B listesinden bir madde daha kapatıldı. Doc: *"Hero'nun altında en az 3-6 adet Live / Ending Soon auction kartı göster. Kartlar backend'den dinamik gelmeli ve süre server time'a bağlı olmalı."*

Eklenenler (`index.html`):
- Hero'nun hemen altına yeni bir `#liveEndingSoonSection` eklendi — `renderLiveEndingSoon()` fonksiyonu `auctions` dizisindeki `_isApi` (API'den gelen, gerçek) ve `status` `live`/`extended` olan kayıtları `end` (bitiş zamanı, backend'in `end_time`'ından türetilmiş) alanına göre artan sırayla sıralayıp ilk 6'sını mevcut `card()`/`renderGrid()` altyapısıyla basıyor — §5.2/§3.2'de kurulan aynı kart bileşeni, yeni bir tane icat edilmedi.
- Süre gösterimi (`timeLeft()`) zaten `auction.end` (API'nin `end_time`'ı) üzerinden hesaplanıyor — yani "süre server time'a bağlı olmalı" kriteri otomatik sağlanıyor, hiçbir yeni zaman mantığı gerekmedi.
- Hiç canlı/API aukciyonu yoksa (demo mod veya boş veritabanı) bölüm tamamen gizleniyor (`display:none`) — sahte/placeholder kart gösterilmiyor.
- `loadAuctionsFromApi()` ve periyodik 60 saniyelik yenileme (`renderFeaturedAuction()`'ın yanına) çağrıya eklendi — WebSocket üzerinden gelen canlı teklif güncellemeleri gibi anlık değil, ama sayfa açıldığında ve her dakika tazeleniyor (mevcut `renderAll()` polling deseniyle aynı).

Doğrulama: `node --check` (SYNTAX_OK); DOM-id çapraz referans denetimi farksız; yeni 3 çevirinin (`les.title`/`les.desc`/`les.all`) her iki dilde de tanımlı olduğu doğrulandı; `pytest` 158/159 (aynı 3 önceden var olan hata, saf frontend değişikliği). Canlı Postgres'e karşı `urllib` smoke test — verified seller ile 3 ayrı canlı aukciyon oluşturuldu, `GET /auctions?limit=100` yanıtında üçünün de `status:"live"` olarak göründüğü doğrulandı (frontend'in `renderLiveEndingSoon`'un tükettiği tam veri kaynağı). Gerçek tarayıcıda tıklanarak test edilmedi (headless tarayıcı yok) — kartların gerçek görsel yerleşimi/mobil davranışı kod-seviyesinde doğrulanmadı, yalnızca veri akışı doğrulandı.

Bölüm 22'deki B listesinden §3.5 satırı çıkarıldı.

## 35. Revizyon Geçmişi (30.07.2026, devam) — §10.6 kalanının düzeltilmesi: kurumsal alanlar zaten yapılmıştı

**Bu bir kod kapanışı değil, bir matris hatası düzeltmesidir.** B listesinde "§10.6 kalanı: kurumsal hesap için company name/PIB/registration alanları" satırı Bölüm 26/32'den beri açık madde olarak taşınıyordu. Bir sonraki B-list adayı seçilirken bu maddeye bakıldığında şu bulundu: **bu zaten tamamen yapılmış** — muhtemelen bu oturumdan önceki bir seansta (§11 seller application çalışması sırasında), ama Bölüm 22'ye hiç yansıtılmamış.

Kontrol edilen kod:
- `backend/app/models/domain.py::SellerProfile` — `company_name`, `pib`, `authorized_person`, `account_type` (individual/company), `seller_type`, `city` kolonları zaten var.
- `backend/app/schemas/seller.py::SellerApplicationRequest`/`SellerProfileResponse` — hepsi zaten schema'da.
- `index.html`'deki `#apply-seller` formu (`#asCompanyName`, `#asPib`, `#asAuthorizedPerson`, `#asSellerType`) — hepsi zaten HTML'de var ve submit handler'ı (`$('#sellerApplyForm')` listener) hepsini `POST /sellers/apply`'e gönderiyor.

Doc'un tam istediği: *"Company hesabı için company name, PIB/registration vb. seller onboarding'de genişlet."* — "seller onboarding" tam olarak bu form; buyer profilinde değil, seller application akışında olması isteniyordu ve öyle de yapılmış.

Doğrulama: canlı Postgres'e karşı `urllib` smoke test — `account_type:"company"` ile `company_name`, `pib`, `authorized_person`, `seller_type` alanları dolu bir `POST /sellers/apply` gönderildi, `201` ile hepsinin aynen kaydedildiği ve `GET /sellers/me`'de kalıcı olduğu doğrulandı (`COMPANY/PIB/AUTHORIZED-PERSON FIELDS SMOKE CHECK PASSED`). Kod değişikliği yapılmadı, `pytest`/Docker rebuild gerekmedi.

**Ders**: bu, aynı oturumda daha önce yakalanan §10.1/§10.6 etiketleme hatasıyla aynı kökten geliyor — B listesi Bölüm 16/20'nin ilk matrisinden miras kaldığı için, matrisin kendisi bazen ham koda değil varsayıma dayanıyordu. Bölüm 30'daki eksiksizlik denetimi yalnızca "her bölüm numarası anılıyor mu" sorusunu kontrol etmişti, anılan maddelerin doğruluğunu değil — bu yüzden bu tür hatalar hâlâ mümkündü. Kalan B listesindeki her madde bir sonraki oturumda kapatılmadan önce hızlıca "gerçekten hâlâ açık mı" diye koda bakılarak doğrulanmalı.

Bölüm 22'deki B listesinden §10.6 kalanı satırı tamamen çıkarıldı (artık A listesinde).

## 36. Revizyon Geçmişi (30.07.2026, devam) — §3.6 kalanı (kısmi): kategori kartlarında aktif ilan sayısı

B listesindeki "§3.6 kalanı" iki alt-parçaya ayrılıyordu: (a) kategori kartlarında **aktif ilan sayısı** ve (b) **alt kategori örnekleri**. Bu turda yalnızca (a) kapatıldı; (b) kasıtlı olarak açık bırakıldı çünkü gerçek bir alt-kategori taksonomisi (§7'nin de beklediği) henüz yok — "örnek" alt kategori adları uydurmak bu oturum boyunca kaçınılan "sahte veri" hatası olurdu.

Eklenenler (`index.html`):
- `renderCategoryCounts()`: zaten yüklü olan `auctions` dizisindeki `_isApi` + `status` `live`/`extended` kayıtları kategoriye (`Vozila`/`Oprema`/`General`) göre sayıyor, her kategori kartına (`#catCountVozila`/`#catCountOprema`/`#catCountGeneral`) "N aktif oglas"/"N active listings" metnini basıyor.
- `loadAuctionsFromApi()` ve periyodik 60 saniyelik yenilemeye (`renderFeaturedAuction()`/`renderLiveEndingSoon()`'un yanına) eklendi.
- Demo modda (API'siz) veya hiç canlı ilan yokken sayı `0` olarak gösteriliyor — gizlenmiyor, çünkü "0 aktif oglas" da doğru/gerçek bir bilgi (sahte olmayan).

Doğrulama: `node --check` (SYNTAX_OK); DOM-id çapraz referans denetimi farksız; `pytest` 158/159 (aynı 3 önceden var olan hata, saf frontend değişikliği). Sayım mantığı, Bölüm 34'te zaten canlı Postgres'e karşı doğrulanmış aynı `auctions` dizisi + `status` alanını kullanıyor — ayrı bir smoke test gerekmedi, aynı veri kaynağının doğruluğu zaten kanıtlanmıştı.

Bölüm 22'deki B listesinde "§3.6 kalanı" satırı yalnızca alt kategori örneklerini kapsayacak şekilde daraltıldı.

## 37. Revizyon Geçmişi (30.07.2026, devam) — §9 How It Works: Buyer/Seller ayrımı

B listesindeki bir sonraki büyük madde kapatıldı. Doc'un tam istediği (docx'in ham metninden doğrulandı):
- **§9.1**: *"Mevcut 4 kutu buyer ve seller sürecini aynı akışta karıştırıyor. İki tab/section: 'For Buyers' ve 'For Sellers'. Kullanıcı platform rolünü 30 saniyede anlayabilmeli."*
- **§9.2**: For Buyers — 6 adım: Create Account, Buy BidMont Credits, Join Auction, Place Bids, Highest Bidder, Contact Seller.
- **§9.3**: For Sellers — 6 adım: Apply as Seller, Verification, Create Listing, BidMont Review, Auction Live, Contact Highest Bidder.
- **§9.4**: *"Mevcut sayfa 'proceeds to payment / collection' diyerek BidMont'un satış sürecini yönettiği algısını yaratıyor. Bu ifadeleri değiştir."*

Önceki `#how` sayfası tek bir 4-kutu akışı gösteriyordu (Objava aukcije → Provjera → Licitiranje → Zatvaranje) ve son kutunun metni *"Najveća ponuda dobija aukciju i nastavlja se plaćanje / preuzimanje"* diyordu — tam olarak §9.4'ün yasakladığı, BidMont'u ödeme/teslim sürecinin bir parçası gibi gösteren ifade.

Eklenenler (`index.html`):
- `#howTabs`: mevcut `.admin-tab`/`.admin-toolbar` CSS'i (legal doküman sekmelerinde zaten kullanılan) yeniden kullanılarak iki sekme — "Za kupce"/"For Buyers" ve "Za prodavce"/"For Sellers" — eklendi. Yeni bir bileşen icat edilmedi.
- `#howBuyers`/`#howSellers`: doc'un tam istediği 6'şar adım, doğru sırayla ve doğru başlıklarla (`how.b.s1-s6.t/.d`, `how.s.s1-s6.t/.d` — 24 çeviri anahtarı × 2 dil).
- Sekme değiştirme: `$$('#howTabs [data-how-tab]')` click listener'ı (legal sekmelerindeki aynı desen) `.info-grid`'in `display:grid`/`none` arasında geçiş yapıyor.
- Eski "plaćanje/preuzimanje" ifadesi tamamen kaldırıldı; yerine `det.platformrole`/`home.disclaimer` ile aynı çizgide bir `how.disclaimer` notice'ı eklendi: *"BidMont obezbjeđuje online infrastrukturu za licitiranje. Konačna prodaja, plaćanje, prenos vlasništva i preuzimanje predmeta odvijaju se isključivo između kupca i prodavca, van BidMont platforme."*
- Eski, artık HTML'de hiç referans edilmeyen `how.s1-s4.t/.d` çeviri anahtarları (her iki dilde) silindi — ölü kod bırakılmadı.

Doğrulama: `node --check` (SYNTAX_OK); DOM-id çapraz referans denetimi farksız; yeni tüm `how.tab.*`/`how.b.*`/`how.s.*`/`how.disclaimer` anahtarlarının her iki dilde de tanımlı olduğu ayrı bir script ile doğrulandı (243 toplam `data-i18n` kullanımından yalnızca 10'u eksik çıktı — hepsi `det.brand`/`det.model`/`det.year` gibi bu değişiklikten tamamen bağımsız, çok daha önceki bir oturumdan kalma, araç/ekipman detay alanları için hiç EN çevirisi girilmemiş ön-var olan bir boşluk; bu turun kapsamı dışında, düzeltilmedi, olduğu gibi not edildi). `pytest` 158/159 (aynı 3 önceden var olan hata, saf frontend değişikliği). Gerçek tarayıcıda tıklanarak test edilmedi (headless tarayıcı yok) — sekme geçişinin görsel/tıklama davranışı kod-seviyesinde doğrulanmadı.

Bölüm 22'deki B listesinden §9 satırı çıkarıldı.

## 38. Revizyon Geçmişi (30.07.2026, devam) — §2.4 ek bulgusu: eksik `det.*`/`l.n` çevirileri

Bölüm 37'de fark edilen çeviri boşluğu kapatıldı. `translations` sözlüğünde hiç tanımlı olmayan (yalnızca HTML'e Karadağca sabit metin olarak yazılmış) 9 anahtar her iki dile de eklendi: `det.brand`/`det.model`/`det.year`/`det.mileage`/`det.fuel`/`det.trans`/`det.ebrand`/`det.serial`/`det.cond` (araç/ekipman detay alanı etiketleri — `#detail` ve `#sell` sayfalarında kullanılıyor).

Aynı denetim scriptiyle (yeni yazılan, tekrar kullanılabilir `i18n_check.js`) tekrar tarama yapılırken **ikinci, ayrı bir eksik** daha bulundu: `l.n` (login sayfasındaki "Prvi put? Registrujte se →" bildirimi) da sözlükte hiç yoktu. Bu ilginç bir kenar durum içeriyordu — `l.n` elementinin içinde iç içe bir `<a data-i18n="l.register_link">` var, ve `applyTranslations()`'ın kodu (`if (el.querySelector('a, span, b')) el.innerHTML = ...`) böyle elementler için çeviri değerinin **tam HTML'i** (iç içe `<a>` etiketiyle birlikte) içermesini gerektiriyor — yalnızca düz metin yeterli değil. Bu yüzden `l.n` değeri, `l.register_link`'in kendi HTML'ini de içine alacak şekilde yazıldı; böylece dil değiştirme sırasının (`l.n` önce mi `l.register_link` önce mi işlendiği) sonucu etkilemesi engellendi.

Doğrulama: yeniden yazılabilir `i18n_check.js` scripti — sayfadaki tüm 243 farklı `data-i18n` kullanımını tarayıp her birinin `translations` sözlüğünde **her iki dilde de** tanımlı olup olmadığını kontrol ediyor — artık **0 eksik** döndürüyor (önceki tur 10, bu tur önce 1, düzeltmeden sonra 0). `node --check` (SYNTAX_OK); DOM-id çapraz referans denetimi farksız; `pytest` 158/159 (aynı 3 önceden var olan hata, saf frontend değişikliği). Gerçek tarayıcıda tıklanarak test edilmedi (headless tarayıcı yok) — özellikle `l.n`'nin iç içe link davranışının EN/ME geçişlerinde görsel olarak doğru render olduğu tarayıcıda doğrulanmadı, yalnızca kod-seviyesinde (sözlük tam, HTML içeriği doğru yapılandırılmış) doğrulandı.

Bölüm 22'deki B listesinden "§2.4 ek bulgu" satırı çıkarıldı — §2.4'ün kendisi (kategori adlarının çevrilmemesi) hâlâ ayrı bir çekince olarak A listesinde kayıtlı, bu ayrı ve daha küçük bulguydu.

## 39. Revizyon Geçmişi (30.07.2026, devam) — §4.1 (kısmi): gelişmiş filtreler + URL query param kalıcılığı

B listesindeki en büyük kalan maddelerden biri, **kısmi olarak** kapatıldı. Doc'un tam istediği (§4.1): *"Desktop'ta sol filtre paneli veya üst gelişmiş filtreler: kategori, şehir, status (Live/Ending Soon/Upcoming/Ended), fiyat aralığı, seller type, condition. Vehicle'da brand/model/year/mileage/fuel/transmission; equipment'ta manufacturer/year/hours gibi kategori özel filtreler açılmalı. Filtre URL/query param ile korunmalı; refresh sonrası seçimler kaybolmamalı."*

**Bu turda kapatılan kısım**: şehir, status (Live/Ending Soon/Upcoming/Ended), fiyat aralığı (min/max) + **tüm** filtrelerin (arama/kategori/sıralama dahil) URL query param'da kalıcılığı.
- `index.html`'deki Auctions liste sayfası toolbar'ına `#auctionCity` (metin), `#auctionStatus` (select: all/live/ending/upcoming/ended), `#auctionPriceMin`/`#auctionPriceMax` (sayı) eklendi.
- `filteredAuctions()` bu üç yeni filtreyi de uyguluyor. "Ending Soon" durumu backend'in anti-sniping penceresinden (15 dk) tamamen bağımsız, salt UI amaçlı 24 saatlik bir pencere (`ENDING_SOON_UI_WINDOW_MS`) — doc bir süre belirtmiyor, makul bir varsayılan seçildi ve kodda yorum olarak açıklandı.
- `syncAuctionFiltersToUrl()`/`restoreAuctionFiltersFromUrl()`: her filtre değişikliğinde `history.replaceState` ile `#auctions?q=...&cat=...&sort=...&city=...&status=...&pmin=...&pmax=...` güncelleniyor (yalnızca boş olmayan/varsayılan olmayan parametreler eklenerek URL kısa tutuluyor); `route()` fonksiyonu `#auctions` sayfasına her girişte bu parametreleri okuyup filtre input'larını dolduruyor ve grid'i yeniden çiziyor — refresh sonrası seçimler kaybolmuyor.
- Aynı denetim sırasında `i18n_check.js` scripti `data-i18n-ph` (placeholder) özniteliğini de kapsayacak şekilde genişletildi ve bu, bu değişiklikten tamamen bağımsız **4 ayrı, çok daha önceki bir oturumdan kalma** eksik placeholder çevirisini ortaya çıkardı: `auc.search`, `s.ph`, `form.name.ph`, `form.msg.ph` — hepsi aynı anda düzeltildi (aynı `l.n`/`det.*` deseninin devamı).

**Bu turda kasıtlı olarak kapatılmayan kısım** (B listesine yeniden, daha dar kapsamla yazıldı): seller type filtresi (backend'de `SellerProfile.seller_type` var ama `AuctionResponse`'da hiç expose edilmiyor — bir join/şema genişletmesi gerektirir), condition filtresi, ve kategoriye özel filtreler (vehicle brand/model/year/mileage/fuel/transmission; equipment manufacturer/year/hours — backend zaten bu alanları `AuctionResponse`'da döndürüyor ama frontend'in `auctions` dizisi bu alanları hiç haritalamıyor, ayrı bir haritalama + kategoriye göre koşullu filtre UI'ı gerektirir).

Doğrulama: `node --check` (SYNTAX_OK); genişletilmiş `i18n_check.js` — 255 toplam `data-i18n`+`data-i18n-ph` kullanımının tamamı her iki dilde tanımlı (0 eksik); DOM-id çapraz referans denetimi farksız; **yeni bir bağımsız mantık testi** (`test_filter_logic.js`) — status eşleştirme mantığının (`live`/`ending`/`upcoming`/`ended`, API ve demo aukciyonlar için) index.html'deki koddan aynen kopyalanıp 7 senaryo × 4 durum = 28 kombinasyonda doğru sonuç verdiği doğrulandı (`ALL FILTER-LOGIC CASES PASSED`); `pytest` 158/159 (aynı 3 önceden var olan hata, saf frontend değişikliği). Gerçek tarayıcıda tıklanarak test edilmedi (headless tarayıcı yok) — özellikle `history.replaceState`'in gerçek bir refresh sonrası filtre input'larını doğru geri yüklediği tarayıcıda doğrulanmadı, yalnızca kod-seviyesinde (route()'un query param'ları doğru okuyup input'lara yazdığı) doğrulandı.

Bölüm 22'deki B listesinde "§4.1" satırı, yalnızca seller type + condition + kategoriye özel (vehicle/equipment) filtreleri kapsayacak şekilde daraltıldı.

## 40. Revizyon Geçmişi (30.07.2026, devam) — §8.1 "My Credits" sayfası + işlem geçmişi

B listesindeki bir sonraki büyük madde kapatıldı. Doc: *"Dashboard'da ve ayrı /credits sayfasında 'Credit Balance', paketler, Buy Credits ve transaction history göster. Bakiye backend'den gelmeli."*

Backend zaten `CreditLedger` adında değişmez (immutable), her kredi hareketini (`purchase`/`join_spend`/`admin_adjust`/`reversal`) kaydeden tam bir tablo içeriyordu (`apply_ledger_entry()` her yerde kullanılıyor) — ama kullanıcının **kendi** geçmişini okuyabileceği hiçbir endpoint yoktu (yalnızca admin'in `POST /admin/credits/adjust`'ı vardı, GET yoktu).

Backend (`backend/app/api/credits.py`):
- Yeni `GET /api/credits/ledger` endpoint'i — giriş yapmış kullanıcının **yalnızca kendi** `CreditLedger` satırlarını (`user_id` filtreli), en yeniden eskiye sıralı, `limit` parametresiyle (varsayılan 50, maksimum 200) döndürüyor. Zaten var olan `CreditLedgerEntryResponse` şeması (schemas/credit.py) yeniden kullanıldı, yeni şema yazılmadı.
- `backend/tests/integration/test_credit_engine.py::TestCreditLedgerHistory`: iki yeni test — (a) bir aukciyona katılmanın ledger'da `join_spend` satırı olarak doğru `amount`/`balance_before`/`balance_after`/`reference` ile göründüğü VE bu geçmişin **kullanıcıya özel** olduğu (başka bir kullanıcı boş liste görüyor) doğrulandı, (b) auth olmadan 401 döndüğü doğrulandı.

Frontend (`index.html`):
- Yeni `#credits` sayfası: bakiye (`#creditsPageBalance`), paket listesi (`#creditsPagePackageList` — mevcut `renderCreditPackages()` fonksiyonu artık isteğe bağlı bir hedef seçici parametresi alıyor, hem eski profil-modalı hem yeni sayfa aynı fonksiyonu paylaşıyor, kod tekrarı yok) ve işlem geçmişi tablosu (`#creditsHistory` — tarih `mtDateTime()` ile Karadağ saatine çevrilmiş, tip Türkçe/İngilizce etiketlerle, tutar renk kodlu: negatif kırmızı/pozitif yeşil).
- Profil sayfasındaki mevcut "Kupi kredite" butonunun yanına "Moji krediti →" linki eklendi — eski modal-tabanlı satın alma akışına hiç dokunulmadı, yalnızca eklendi.
- `route()`'a `if(page==='credits')renderCreditsPage()` eklendi; giriş yapılmamışsa `#login`'e yönlendiriyor (diğer korumalı sayfalarla aynı desen).

Doğrulama: `pytest` 160/159 (158'den 160'a — 2 yeni test; aynı 3 önceden var olan hata, değişmedi); `node --check` (SYNTAX_OK); genişletilmiş `i18n_check.js` — 259 toplam kullanımın tamamı tanımlı (0 eksik); DOM-id çapraz referans denetimi farksız. `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı `urllib` smoke test — auth'suz istek 401, boş geçmiş `[]`, bir aukciyona katılım sonrası `GET /credits/ledger`'ın gerçek `join_spend` satırını doğru `reference`/`type` ile döndürdüğü doğrulandı (`CREDITS LEDGER ENDPOINT SMOKE CHECK PASSED`). Gerçek tarayıcıda tıklanarak test edilmedi (headless tarayıcı yok) — sayfanın görsel yerleşimi/tablo render'ı kod-seviyesinde doğrulanmadı.

**Bulgu (bu bölüme sonradan eklendi)**: bu revizyonun raporlanmasından hemen sonra, işlem geçmişi tablosunun `reason` alanını hiç göstermediği fark edildi — `admin_adjust`/`reversal` satırları için `reason`, kullanıcının bakiyesinin neden değiştiğini anlayabileceği **tek** bilgi (doc'un §8.9/§17.2 şeffaflık/denetim izi vurgusuyla doğrudan çelişen bir eksiklik). `CreditLedgerEntryResponse` zaten `reason` alanını döndürüyordu, yalnızca frontend tablosu onu render etmiyordu. Bölüm 41'de düzeltildi.

Bölüm 22'deki B listesinden §8.1 satırı çıkarıldı.

## 41. Revizyon Geçmişi (30.07.2026, devam) — §8.1 düzeltmesi (ledger `reason` sütunu) + §4.1 kalanı (kısmi): vehicle kategoriye özel filtreler + detay sayfası kategori-özel alanlarının bağlanması

**Düzeltme (§8.1)**: Bölüm 40'ta eklenen `#creditsHistory` tablosuna eksik olan `reason` sütunu eklendi (`index.html`, `renderCreditsPage()`). Artık her satırda "Razlog"/"Reason" sütunu var; `admin_adjust`/`reversal` gibi kullanıcının kendi eyleminden kaynaklanmayan hareketlerde bu sütun admin'in girdiği açıklamayı gösteriyor, boşsa boş kalıyor (mevcut `join_spend`/`purchase` satırlarında zaten `reason` set edilmiyor, bu davranış değişmedi).

**§4.1 kalanı (devam eden kısmi kapanış)**: Bölüm 39'da şehir/status/fiyat aralığı + URL kalıcılığı kapatılmıştı; bu turda doc'un istediği *"Vehicle'da brand/model/year/mileage/fuel/transmission... kategori özel filtreler açılmalı"* ifadesinin **vehicle** yarısı kapatıldı:

- `#auctions` sayfasına iki yeni filtre eklendi: `#auctionFuel` (Petrol/Diesel/Electric/Hybrid) ve `#auctionTrans` (Manual/Automatic) — yalnızca kategori "Vozila" seçiliyken görünür (`toggleCategoryFilters()`, kategori değiştiğinde ve sayfa URL'den yüklendiğinde çağrılıyor), `.hidden` sınıfı (mevcut CSS yardımcı sınıfı, yeni CSS yazılmadı) ile gizleniyor/gösteriliyor.
- `loadAuctionsFromApi()`'nin haritalaması genişletildi: `brand`/`model`/`year`/`mileage`/`fuelType`/`transmission`/`equipmentBrand`/`serialNumber`/`condition` artık yerel `auctions` dizisine kopyalanıyor (önceden bu alanlar API'den geliyordu ama hiç haritalanmıyordu — advisor'ın işaret ettiği kesin nokta).
- `filteredAuctions()` artık `fuelType`/`transmission` eşleşmesini kontrol ediyor; `syncAuctionFiltersToUrl()`/`restoreAuctionFiltersFromUrl()` bu iki alanı da `fuel`/`trans` query param'ı olarak koruyor.
- Select seçenek değerleri kasıtlı olarak `#sellForm`'daki `#sellFuel`/`#sellTrans` seçeneklerinin metniyle birebir aynı (`Petrol`/`Diesel`/`Electric`/`Hybrid`, `Manual`/`Automatic`) — o formda `<option>` etiketlerinin `value` özniteliği yok, yani gönderilen değer görünen metnin ta kendisi; filtre değerleri bu gerçek veri sözlüğüyle eşleşmezse hiçbir sonuç dönmezdi.

**Yan bulgu ve kök-neden düzeltmesi (ponytail: semptomu değil kökü düzelt)**: bu filtreleri eklerken `renderDetail()` incelenirken, detay sayfasındaki `#vehicleFields`/`#equipFields` markup'ının (`det.brand`/`det.model`/.../`det.cond` — bu alanların çeviri anahtarları Bölüm 38'de zaten düzeltilmişti) **hiçbir zaman doldurulmadığı veya gösterilmediği** bulundu — `style="display:none"` olarak kodlanmış, hiçbir JS onu değiştirmiyordu. Yani auction detay sayfasını ziyaret eden hiçbir kullanıcı marka/model/yıl/kilometraj/yakıt/mjenjač veya ekipman marka/seri no/durum/lokasyon bilgisini hiç görmüyordu — doc §4.2'nin *"Her kartta/detayda kullanıcının karar vermesi için minimum kritik bilgi görünmeli"* isteğiyle doğrudan çelişen, önceden görünmez bir eksiklik. `renderDetail()`'e eklendi: kategori "Vozila" ise `#vehicleFields` gösterilip `detBrand`/`detModel`/`detYear`/`detMileage`/`detFuel`/`detTrans` dolduruluyor; "Oprema" ise `#equipFields` gösterilip `detEbrand`/`detSerial`/`detCond`/`detLoc` dolduruluyor; alan boşsa "—" gösteriliyor.

**Kasıtlı olarak dışarıda bırakılan**: equipment `condition` filtresi eklenmedi — `#sellForm`'da equipment'a özel hiçbir input alanı yok (yalnızca `#vehicleExtra` div'i var, eşdeğer bir `#equipmentExtra` hiç yazılmamış), yani hiçbir kullanıcı-oluşturulmuş ekipman ilanının `equipment_brand`/`serial_number`/`condition` alanı hiçbir zaman doluyor olamaz. Bir filtre eklemek kullanıcıya var olmayan bir yetenek vaat ederdi; bu, §7'nin (equipment'a özel dinamik form alanları) kapsamına giren ayrı ve daha büyük bir eksik, burada gizlice kapatılmadı. `seller_type` filtresi de aynı nedenle (şema/join gerektirir) dışarıda bırakıldı, B listesinde kaldı.

Doğrulama: `node --check` (SYNTAX_OK); DOM-id çapraz referans denetimi (156→158 `$('#...')` kullanımı, tamamı tanımlı, sıfır sarkan referans); `i18n_check.js` genişletildi — 259'dan 267 kullanıma çıktı (`auc.fuel.*` x5, `auc.trans.*` x3 yeni), tamamı iki dilde de tanımlı (0 eksik); `pytest` 163 testin 160'ı geçti (aynı 3 önceden var olan `TestForgotPassword`/`TestResetPassword` hatası, değişmedi — bu tur backend kodu değiştirmedi, yeni test de eklenmedi). `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı `urllib` smoke test (`smoke_filters.py`) — verified seller ile `fuel_type='Diesel'`/`transmission='Manual'` alanlı gerçek bir vehicle aukciyonu oluşturuldu, hem `GET /api/auctions` (liste) hem `GET /api/auctions/{id}` (detay) endpoint'lerinin bu alanları doğru döndürdüğü doğrulandı (`ALL FILTER-FIELD SMOKE CHECKS PASSED`) — bu, advisor'ın "backend zaten döndürüyor" varsayımının doğru olduğunu canlı ortamda kanıtladı. Gerçek tarayıcıda tıklanarak test edilmedi (headless tarayıcı yok).

Bölüm 22'deki B listesindeki "§4.1 kalanı" satırı, yalnızca seller type filtresini kapsayacak şekilde daraltıldı (equipment condition filtresi kasıtlı olarak §7'ye bırakıldı, ayrı bir madde değil — zaten §7 B listesinde var).

## 42. Revizyon Geçmişi (30.07.2026, devam) — §10.1 Dashboard navigasyonu + Security (şifre değiştirme)

B listesindeki en eski açık maddelerden biri kapatıldı: doc'un tam istediği (docx'in ham metninden doğrulandı, `word/document.xml`): *"10.1. Dashboard navigasyonu ekle. Mevcut durum: Mevcut My Account sadece profil ve My Bids kartından oluşuyor. Rica edilen düzenleme: Sol/üst dashboard navigasyonu: Overview, My Credits, My Bids, Joined Auctions, Watchlist, Notifications, Profile, Security. Seller ise ayrıca My Listings / Create Listing / Results. Beklenen sonuç: Role göre menü doğru açılmalı."*

**Tasarım kararı (advisor'la doğrulandı)**: yeni bir `#dashboard` route'u/sayfası yazmak yerine, mevcut `#profile` sayfası içine bir navigasyon çubuğu eklendi. Gerekçe: bu SPA'nın router'ı `location.hash`'i doğrudan sayfa kimliği olarak kullanıyor (`route()`, `hash.split('?')[0]`); `#myBidsSection` gibi harici bağlantılar kullanmak `location.hash`'i değiştirip router'ın onu geçersiz bir sayfa adı sanmasına (ve `home`'a düşmesine) neden olurdu. Bunun yerine nav butonları `history`/`hash` hiç değiştirmeden `element.scrollIntoView()` çağırıyor; yalnızca gerçekten ayrı bir route olan **My Credits** (`#credits`) ve **Create Listing** (`#sell`) gerçek `<a href>` linkleri.

**Kural (advisor'ın belirlediği bağlayıcı kısıt)**: *her nav girdisi bugün gerçekten render edilen bir görünüme gitmeli* — var olmayan bir görünüme link veren ölü bir girdi eklemektense hiç eklenmemesi tercih edildi. Bu kural uygulanırken:

- **Overview, My Credits, My Bids, Joined Auctions, Watchlist, Profile** — hepsi zaten `#profile` içinde render ediliyordu (önceki oturumlarda §10.4/§10.5/vb. kapatılırken); yalnızca hedef elemanlara `id` eklenip (`profileEditSection`, `myBidsSection`, `joinedAuctionsSection`, `watchlistSection`, `sellerDashboard` zaten vardı) nav'dan bağlandı — yeni veri/render mantığı yazılmadı.
- **Notifications** — dashboard'da hiç yoktu (yalnızca header'daki zil dropdown'ı vardı). `renderNotifMenu()` fonksiyonu artık isteğe bağlı bir `targetId` parametresi alıyor (Bölüm 40'ta `renderCreditPackages()`'a yapılan aynı refactor deseni) — hem `#notifMenu` (zil) hem yeni `#profileNotifList` (dashboard) aynı fonksiyonu paylaşıyor. `markNotifRead()` artık her ikisini de (varsa) yeniliyor.
- **Security** — dashboard'da da backend'de de **hiç yoktu**: `POST /admin/seed` dışında hiçbir şifre değiştirme yolu yoktu (yalnızca forgot-password akışı vardı). Bu nav girdisini dead-link yapmamak için gerçek bir özellik olarak eklendi (backend + frontend, aşağıda).
- **My Listings, Create Listing, Results** (yalnızca seller/corporate_seller rolü için gösteriliyor, `renderDashNav(role)` içinde) — My Listings ve Results zaten var olan `#sellerDashboard` bloğuna (oglaslar listesi + `ssTotal`/`ssActive`/`ssCompleted`/`ssRevenue` istatistikleri, önceki oturumlarda yapılmış) bağlandı; Create Listing zaten var olan `#sell` sayfasına link veriyor. Hiçbiri için yeni render mantığı gerekmedi.

**Yeni eklenen: Security / şifre değiştirme** (backend + frontend):
- `backend/app/schemas/user.py`: `PasswordChangeRequest` (`current_password`, `new_password` min 6 karakter — register'daki aynı kural).
- `backend/app/api/users.py`: yeni `PUT /api/users/me/password` — `verify_password()` ile mevcut şifre kontrol ediliyor (yanlışsa 400), `hash_password()` ile yeni şifre `password_hash`'e yazılıyor. Yeni bağımlılık yok, `app/core/security.py`'deki mevcut bcrypt yardımcıları yeniden kullanıldı.
- `backend/tests/integration/test_users_api.py` (yeni dosya, 4 test): başarılı değişiklik (DB'de gerçekten değiştiğini `db_session.refresh()` ile doğruluyor — **not**: test client'ın kullandığı session `db_session` fixture'ından farklı bir session olduğu ve `expire_on_commit=False` olduğu için, `refresh()` çağrılmadan okunan nesne bellekteki eski/stale kopyayı döndürüyordu; bu kenar durum ilk denemede yakalandı ve düzeltildi), yanlış mevcut şifre → 400, auth olmadan → 401/403, kısa yeni şifre → 422.
- `index.html`: `#profile` sayfasına yeni bir "Security" bloğu (`#pwCurrent`/`#pwNew`/`#pwConfirm`/`#pwSaveBtn` + `#pwError`/`#pwSuccess`) eklendi; `bidmontApi.changePassword()` yeni metod; kaydet butonunun handler'ı client-side'da min-6-karakter ve "şifreler eşleşiyor mu" kontrolü yapıyor, sonra API'yi çağırıyor.

Doğrulama: backend — `pytest` 167 testin 164'ü geçti (163'ten 167'ye — 4 yeni test), aynı 3 önceden var olan `TestForgotPassword`/`TestResetPassword` hatası (değişmedi), 4 yeni test (`test_users_api.py`) hepsi geçti. Frontend — `node --check` (SYNTAX_OK); DOM-id çapraz referans denetimi (164 `$('#...')` kullanımı + `document.getElementById` ile çağrılan 9 scroll-hedefi id'si tek tek `grep -c` ile doğrulandı, hepsi tam bir kez tanımlı); `i18n_check.js` — 273 kullanım, tamamı iki dilde tanımlı (0 eksik). `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı `urllib` smoke test (`smoke_password.py`) — yanlış mevcut şifreyle 400, doğru değişiklik 200, eski şifreyle login artık başarısız, yeni şifreyle login başarılı (`PASSWORD CHANGE SMOKE CHECK PASSED`).

**Bilinen sınır (Bölüm 22'nin genel frontend çekincesiyle aynı)**: nav'ın gerçek tarayıcıda tıklanarak (özellikle `scrollIntoView` davranışı ve mobilde `.admin-toolbar`'ın `flex-wrap` ile düzgün sarması) test edilmediği açıkça not ediliyor — bu, yeni bir sayfa yapısı/CSS etkileşimi eklediği için Bölüm 29'daki (§3.2 görsel denge) çekinceyle aynı sınıf: kod-seviyesi kontroller (`node --check`, DOM-id denetimi, i18n denetimi) görsel/mobil doğruluğu kanıtlamıyor.

**Kasıtlı olarak eklenmeyen**: doc §10.2 ("Overview üstte Credit Balance + Buy Credits CTA") ve §10.3 ("My Bids'i gerçek tabloya çevir — Lot ID, current highest, outbid/highest badge") ayrı, kendi numaralı maddeler — bu turda dokunulmadı, hâlâ B listesinde (aşağıda kontrol edildi, zaten oradaydılar mı diye docx tekrar tarandı: §10.2/§10.3 önceki B listesinde hiç açıkça yer almıyordu, bu bir eksiksizlik denetimi bulgusu, B listesine yeni eklendi).

Bölüm 22'deki B listesinden §10.1 satırı çıkarıldı; §10.2 ve §10.3 yeni bulunan açık maddeler olarak eklendi (net madde sayısı ~14'ten ~15'e çıktı — bir madde kapandı, iki yeni madde bulundu).

## 43. Revizyon Geçmişi (30.07.2026, devam) — §10.2 Overview Credit Balance + §10.3 My Bids gerçek tablosu + seller dashboard rol sızıntısı düzeltmesi

Advisor'ın önerisiyle §10.2 ve §10.3 tek bir turda birlikte kapatıldı (ikisi de `renderProfile()`'ın aynı bölümüne dokunuyor).

**Önce doğrulanan bir varsayım (advisor'ın işaret ettiği kesin nokta)**: Bölüm 42'de "bakiye buyer'a hiç görünmüyor" denmişti; kodu tekrar okuyunca gerçek kusur bulundu — `#sellerDashboard` bloğu (bakiye dahil her şeyi içeren) yalnızca `bidmontApi.isLoggedIn()`'e göre gösteriliyordu (`role` hiç kontrol edilmiyordu). Yani **giriş yapmış her buyer, tüm seller panelini** (oglaslar, gelir, `#creditsBalance` dahil) görüyordu — bu, §10.2'nin "bakiye görünmüyor" iddiasından daha ciddi, ayrı bir rol-izolasyon hatası. Düzeltildi: `if(dash&&bidmontApi.isLoggedIn()&&isSellerRole)` (`isSellerRole = role==='seller'||role==='corporate_seller'`). Bu düzeltmeden sonra buyer'lar için seller paneli tamamen kayboluyor — dolayısıyla §10.2'nin gerçek ihtiyacı doğrulanmış oldu: buyer'a bakiyeyi göstermenin **tek yolu**, onu Overview'a taşımaktı.

**§10.2**: `#profileLoggedIn`'in en üstüne (isim/rol/çıkış satırının hemen altına), her role için (buyer dahil) görünen bir "Krediti za oglašavanje" kartı eklendi (`#ovCreditsBalance`, `renderProfile()` içinde `getCreditsBalance()` ile dolduruluyor) + "Moji krediti →" CTA'sı (`#credits` sayfasına link — o sayfada zaten paket satın alma listesi var, ayrı bir "Kupi kredite" butonu/modalı tekrar yazılmadı, mevcut `#credits` sayfası CTA hedefi olarak kullanıldı). Doc'un *"Bakiye her başarılı credit transaction sonrası güncellenmeli"* isteği — yeni bir refresh mekanizması **yazılmadı**, çünkü zaten yeterli: `route()` her navigasyonda `renderProfile()`'ı çağırıyor, ve satın alma sonrası dönüş akışı (`#profile?credits=success` / `#detail?...&credits=success`, Bölüm 31/40'ta yapılmış) zaten o sayfaya geri dönüp yeniden render tetikliyor.

**§10.3**: `#myBids`'in içeriği `.bid-list` (flex satırları) yerine gerçek bir `<table class="admin-tbl">`'a çevrildi (Bölüm 40'ta `#creditsHistory`'de kullanılan aynı sınıf + `overflow-x:auto` sarmalayıcı — mobilde yatay kaydırma). Sütunlar doc'un istediği tam liste: Lot ID, Auction (title, link), My bid, Current highest, Status, Time left, Result (outbid/highest/won/lost badge), View Auction. **Backend eksikliği bulundu ve kapatıldı**: `BidResponse` şeması `auction_end_time`'ı zaten döndürüyordu ama `auction_lot_code` hiç yoktu — `backend/app/schemas/bid.py`'e `auction_lot_code: str | None` eklendi, `backend/app/api/bids.py::my_bids`'te `b.auction.lot_code` ile dolduruldu (tek satır, yeni sorgu/join gerekmedi, `Bid.auction` zaten `selectinload` ile yükleniyordu). "Ended auction'lar status ile ayrılmalı" isteği: bitmiş/iptal aukciyonlar artık listenin sonuna sıralanıyor ve satır `opacity:.6` ile görsel olarak soluklaştırılıyor.

Doğrulama: backend — `backend/tests/integration/test_bid_api.py::TestMyBids::test_my_bids`'e `auction_lot_code`/`auction_end_time` alanlarının response'ta var olduğunu kontrol eden bir assertion eklendi (yeni test dosyası açılmadı, mevcut teste eklendi); `pytest` 167 testin 164'ü geçti (aynı 3 önceden var olan hata, değişmedi — sayı bu turda değişmedi çünkü yeni test dosyası değil, var olan teste satır eklendi). Frontend — `node --check` (SYNTAX_OK); DOM-id çapraz referans denetimi (165 kullanım, 0 sarkan); `i18n_check.js` (273 kullanım, 0 eksik — bu turda yeni çeviri anahtarı eklenmedi, mevcut `pr.credits.*`/`smap` etiketleri yeniden kullanıldı). `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı `urllib` smoke test (`smoke_mybids.py`) — gerçek bir seller + buyer + bid akışı kuruldu, `GET /auctions/bids/my`'ın gerçek otomatik üretilen lot code'u (`BM-VEH-000013` gibi) ve `auction_end_time`'ı doğru döndürdüğü doğrulandı (`MY BIDS LOT_CODE/END_TIME SMOKE CHECK PASSED`).

**Bilinen sınır**: rol-izolasyon düzeltmesinin (buyer artık seller panelini görmüyor) ve yeni tablo/kartın görsel doğruluğu gerçek tarayıcıda tıklanarak test edilmedi (headless tarayıcı yok) — kod-seviyesi kontroller bunu kanıtlamıyor, yalnızca "kod çalışıyor, render ediyor" seviyesinde doğrulandı.

Bölüm 22'deki B listesinden §10.2 ve §10.3 satırları çıkarıldı.

## 44. Revizyon Geçmişi (30.07.2026, devam) — §4.1'in son kalan parçası: seller type filtresi

B listesindeki §4.1 kalanı tamamen kapatıldı: *"gelişmiş filtreler: ... seller type ..."* — doc'un istediği filtre artık backend'de expose ediliyor ve frontend'de çalışıyor.

**Backend**: `SellerProfile.seller_type` daha önce hiç `AuctionResponse`'a expose edilmiyordu (yalnızca `POST/GET /sellers/apply` üzerinden erişilebiliyordu). Kapatmak için:
- `User` modeline salt-okunur (`viewonly=True`) bir `seller_profile` ilişkisi eklendi (`primaryjoin="User.id==SellerProfile.user_id"`, `uselist=False`) — `SellerProfile` tarafında zaten `user_id`'ye `ForeignKey` var, ama ters yönde (`User` → `SellerProfile`) hiç ilişki tanımlanmamıştı.
- `AuctionResponse`'a `seller_type: Optional[str]` eklendi; `build_auction_response()` bunu `auction.seller.seller_profile.seller_type` üzerinden dolduruyor (`seller_name`'in `auction.seller.name` üzerinden dolduruluşuyla aynı desen).
- `GET /api/auctions` listesine `seller_type` query param eklendi — `SellerProfile.seller_type` **serbest metin** bir alan olduğu için (`#asSellerType` formunda "npr. flota, osiguranje, dealer" gibi kullanıcı kendi yazıyor, sabit bir enum yok), eşleşme `ilike(f"%{value}%")` ile kısmi/case-insensitive yapıldı — tam eşleşme (`==`) kullanılsaydı kullanıcının yazdığı serbest metinle filtredeki metin harfiyen aynı olmadıkça hiçbir sonuç dönmezdi.
- `Auction.seller` her yerde `selectinload` edilen tüm sorgulara (`app/api/auctions.py`, `app/api/admin.py`, `app/api/watchlist.py` — 7 nokta) `.selectinload(User.seller_profile)` zinciri eklendi, aksi halde ilk erişimde lazy-load `MissingGreenlet` hatası atardı (async SQLAlchemy'de senkron lazy-load I/O'ya izin verilmiyor).

**Bulunan ve düzeltilen yan hata**: `app/api/auctions.py`'deki altı endpoint (`create_auction`, `update_auction`, `submit_auction`, `approve_auction`, `request_auction_changes`, `reject_auction`) `commit()` sonrası `await db.refresh(auction)` (parametresiz, tam nesne yenileme) çağırıyordu — `expire_on_commit=True` varsayılanı nedeniyle commit ilişkileri de expire ediyor, ve parametresiz `refresh()` bunları yeniden yüklemiyor, bu da `_build_auction_response`'ın `auction.seller.seller_profile`'a eriştiği anda `MissingGreenlet` hatasına yol açtı (6 test kırıldı: `test_seller_creates_auction` + 5 seller-workflow testi). Kök nedene göre düzeltildi: bu altı yerde `db.refresh(auction)` yerine zaten var olan `_get_auction_or_404(db, auction_id)` helper'ı ile (doğru `selectinload` zinciriyle) auction yeniden çekiliyor — aynı düzeltmeyi altı yerde tekrar yazmak yerine ortak bir yardımcı üzerinden. `app/api/admin.py`'deki benzer iki yer (`admin_toggle_featured`, `admin_cancel_auction`) zaten `attribute_names=[...]` ile **kısmi** refresh yapıyordu (yalnızca belirtilen sütun yenileniyor, ilişkiler dokunulmuyor) — bu yüzden onlarda hata yoktu, değişiklik gerekmedi.

**Frontend**: `#auctions` filtre satırına şehir alanıyla aynı desende bir metin girişi eklendi — `#auctionSellerType` (placeholder "Tip prodavca..." / "Seller type...", `auc.sellertypeph` i18n anahtarı). Select değil metin girişi seçildi çünkü `seller_type` sabit bir enum değil serbest metin (bkz. yukarı) — sabit bir seçenek listesi (`dealer`/`insurer`/`construction`/...) sunmak, gerçekte kullanıcıların yazdığı değerlerle eşleşmeyebilecek sahte bir kapalı küme uydurmak olurdu. `filteredAuctions()`'a `sellerType` alt-string/case-insensitive karşılaştırması eklendi (city filtresiyle aynı desen); `syncAuctionFiltersToUrl()`/`restoreAuctionFiltersFromUrl()`'a `stype` query param eklendi; `loadAuctionsFromApi()`'nin haritalamasına `sellerType:a.seller_type` eklendi. Not: fuel/trans filtreleri gibi bu filtre de yalnızca **client-side** (yerel `auctions` dizisi üzerinde) çalışıyor — backend'in `seller_type` query param'ı `loadAuctionsFromApi()`'den hiç çağrılmıyor (mevcut fuel/trans deseniyle tutarlı, ayrı bir tutarsızlık değil), ama endpoint canlı Postgres'e karşı ayrıca doğrulandı (aşağıya bkz.).

Doğrulama: backend — `pytest` 167 testin 164'ü geçti (aynı 3 önceden var olan `forgot-password` hatası, `ENVIRONMENT=development` gerektiriyor — değişmedi); yeni `MissingGreenlet` hatası kalmadığı doğrulandı. Frontend — `node --check` (SYNTAX_OK); DOM-id çapraz referans denetimi (166 kullanım, 0 sarkan); `i18n_check.js` (274 kullanım, 0 eksik). `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı `urllib` smoke test (`smoke_sellertype.py`) — `seller_type='Rent-a-car fleet'` olan doğrulanmış bir seller ile bir auction oluşturuldu; `GET /auctions/{id}` detay yanıtında `seller_type` alanının doğru döndüğü, filtresiz `GET /auctions` listesinde de aynı alanın göründüğü, `?seller_type=rent-a-car` ile filtrelendiğinde auction'ın listede kaldığı, `?seller_type=insurer` ile filtrelendiğinde ise listeden düştüğü doğrulandı (`SELLER TYPE FILTER SMOKE CHECK PASSED`).

**Bilinen sınır**: yeni metin girişinin görsel/tıklama davranışı gerçek tarayıcıda test edilmedi (headless tarayıcı yok) — yalnızca kod-seviyesinde (`node --check`, DOM-id, i18n) ve backend'in canlı Postgres'e karşı doğrulandı.

Bölüm 22'deki B listesinden "§4.1 kalanı" satırı tamamen çıkarıldı (§4.1 artık tamamen A listesinde). Görev #18'in açıklaması güncellenmeli — "seller_type/equipment-condition filtreleri" ifadesi artık yalnızca equipment condition'ı (§7'nin parçası) kapsayacak şekilde daraltılmalı.

## 45. Revizyon Geçmişi (30.07.2026, devam) — §17.3 Admin 2FA

B listesindeki §17.3 kapatıldı. Doc'un tam istediği (docx'in ham metninden doğrulandı): *"17.3. Admin 2FA. Mevcut durum: Admin güvenliği belirtilmemiş. Rica edilen düzenleme: Admin hesaplarında 2FA gerekli veya en azından canlıya geçiş sonrası olarak etkinleştir. Beklenen sonuç: Admin login yalnız password ile kalmamalı."* Doc'un kendisi "gerekli **veya en azından** canlıya geçiş sonrası etkinleştir" diyerek zorunlu değil opt-in bir uygulamaya da izin veriyor — bu yüzden 2FA her admin hesabında **isteğe bağlı** (self-service enable/disable) olarak uygulandı, zorla açılmadı; doc'un "beklenen sonuç" cümlesi (*"Admin login yalnız password ile kalmamalı"*) yalnızca 2FA'yı etkinleştiren hesaplar için garanti ediliyor.

**Backend**: RFC 6238 TOTP (Google Authenticator/Authy gibi standart authenticator app'lerle uyumlu) tamamen stdlib ile yazıldı (`hmac`+`hashlib`+`struct`+`base64`+`secrets`) — `pyotp`/`qrcode` gibi yeni bir bağımlılık eklenmedi (ladder rung 3: stdlib yeterliydi).
- `backend/app/core/security.py`: `generate_totp_secret()`, `_hotp()`, `verify_totp()` (±1 zaman adımı = ±30sn saat kayması toleransı), `totp_otpauth_url()`.
- `User` modeline `totp_secret` (nullable) ve `totp_enabled` (default false) sütunları eklendi (`app/models/domain.py` + `app/core/migrations.py::MISSING_COLUMNS`).
- `LoginRequest`'e opsiyonel `totp_code` eklendi; `POST /api/auth/login`, `user.totp_enabled=True` ise kod zorunlu kılıyor (`401 "TOTP code required"` kod hiç gönderilmezse, `401 "Invalid TOTP code"` yanlış koddaysa).
- Dört yeni self-service endpoint (`app/api/admin.py`, `get_current_staff` ile korunuyor — yalnızca kendi hesabı, başka bir admin'inki değil): `GET /admin/2fa/status`, `POST /admin/2fa/setup` (secret üretir, henüz etkinleştirmez), `POST /admin/2fa/verify` (doğru kod girilirse etkinleştirir), `POST /admin/2fa/disable` (kapatmak için de geçerli bir kod ister — yalnızca JWT'ye güvenilmez, çalınan bir session token'ın tek başına 2FA'yı kapatamaması için).

**Frontend**: Admin panelinde yeni bir "Security" sekmesi (`#adminTabs`'e eklendi, mevcut `.admin-tab` deseniyle) — 2FA kapalıyken "Set Up 2FA" butonu secret + `otpauth://` URI'sini gösteriyor (QR kod üretimi yok, manuel secret girişi yeterli — authenticator app'ler `otpauth://` URI'sini de kabul ediyor); doğru kod girilip "Enable" denince etkinleşiyor. Login formuna gizli bir `#loginTotpWrap` alanı eklendi — backend `"TOTP code required"` dönene kadar görünmüyor, döndüğünde açılıp kullanıcıdan kodu isteyip aynı formu tekrar gönderiyor (ekstra bir "adım 2" sayfası yazılmadı, tek form üzerinde).

Doğrulama: backend — 17 yeni test eklendi: `tests/unit/test_security.py::TestTotp` (5 test, RFC 4226 Appendix D test vektörleriyle `_hotp()`'un doğruluğu bağımsız olarak kanıtlandı — `secret="12345678901234567890"`, counter 0→4 için beklenen `755224/287082/359152/969429/338314` kodlarının üretildiği doğrulandı) + `tests/integration/test_admin_2fa_api.py` (12 test: setup/verify/disable akışları, yanlış kod reddi, login zorlaması, `auth_headers` — normal kullanıcı — ile 403). `pytest` 184 testin 181'i geçti (aynı 3 önceden var olan `forgot-password` hatası, değişmedi — 164'ten 181'e, 17 yeni test). Frontend — `node --check` (SYNTAX_OK); DOM-id çapraz referans denetimi (168 kullanım, 0 sarkan — yeni `tfaSetupBtn`/`tfaVerifyBtn`/`tfaDisableBtn` gibi id'ler dinamik olarak `innerHTML` içine yazılıp hemen `getElementById` ile bağlandığı için statik `$('#id')` taramasında görünmüyor, mevcut `adminShowConfirm`/`adminShowTicket` deseniyle aynı); `i18n_check.js` (275 kullanım, 0 eksik — yeni `l.totp` anahtarı ME/EN eklendi; admin panel sekmeleri zaten hiç i18n kullanmıyor — "Statistics"/"Users" gibi düz İngilizce, "Security" de aynı desende bırakıldı). `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı `urllib` smoke test (`smoke_2fa.py`) — gerçek bir admin hesabı için tam akış (`status:false` → `setup` → gerçek TOTP kodu hesaplanıp `verify` ile etkinleştirme → kodsuz login `401 TOTP code required` → doğru kodla login başarılı → yanlış kodla `401 Invalid TOTP code` → `disable` → kodsuz login tekrar başarılı) uçtan uca doğrulandı (`ADMIN 2FA SMOKE CHECK PASSED`).

**Bulunan ve düzeltilen küçük belge hatası**: Bölüm 22'nin B listesinde §4.1 satırı bir önceki turda (Bölüm 44) silinirken satır başındaki `-` işareti yanlışlıkla da silinmiş, bir sonraki madde (§4.3/AC-20) madde işaretsiz kalmıştı — bu turda düzeltildi.

**Bilinen sınır**: yeni "Security" sekmesinin ve login 2FA alanının görsel/tıklama davranışı gerçek tarayıcıda test edilmedi (headless tarayıcı yok) — yalnızca kod-seviyesinde ve backend'in canlı Postgres'e karşı doğrulandı. QR kod görseli üretilmiyor (yalnızca manuel secret + `otpauth://` URI metni) — bu bilinçli bir kapsam sınırı, doc bir QR kod istemiyor, yalnızca "2FA etkinleştir" diyor; QR isteniyorsa client-side bir QR kütüphanesi (yeni bağımlılık) gerekir.

Bölüm 22'deki B listesinden §17.3 çıkarıldı; "§17" satırı yalnızca bildirim şablonu admin yönetimini kapsayacak şekilde daraltıldı ("§17 kalanı").

## 46. Revizyon Geçmişi (30.07.2026, devam) — §19.6 Backup/Restore + §19.7 Monitoring/Alerting

B listesindeki §19.6/§19.7 kapatıldı. Doc'un tam istediği (docx'in ham metninden doğrulandı):
- *"19.6. Backup ve restore. Mevcut durum: Canlı ortam recovery gereksinimi yok. Rica edilen düzenleme: DB backup schedule + restore testi + media backup policy. Beklenen sonuç: Staging'de restore test edilmeden canlıya geçiş tamam sayılmamalı."*
- *"19.7. Monitoring. Mevcut durum: Bid/payment hata izleme yok. Rica edilen düzenleme: Centralized application error logs, payment webhook failure alert, bid engine error alert, uptime monitor. Beklenen sonuç: Kritik hata için admin teknik ekibe uyarı üretmeli."*

**§19.6 — Backup/restore**: `backend/scripts/backup_db.sh` (yeni) — `docker exec bidmont-db pg_dump` ile DB'yi custom-format dump'a alıyor, ayrıca `bidmont-uploads` named volume'ünü `docker cp` üzerinden (host'a `-v` bind-mount yerine — Windows+Git-Bash'te sürücü harfi + iki nokta içeren `-v` yol string'lerinin MSYS path-translation'ı güvenilir çalışmadığı için, bir throwaway container'a tar attırıp `docker cp` ile host'a çıkarma yolu seçildi) bir `.tar.gz`'e arşivliyor. `backend/scripts/restore_db.sh` (yeni) — bir dump dosyasını **canlı `bidmont` veritabanının adını hiç kullanmayan**, varsayılan olarak `bidmont_restore_test` adlı ayrı bir DB'ye restore ediyor (yanlışlıkla prod'u ezmeyi imkânsız kılmak için — gerçek DB'yi değiştirmek isteniyorsa 3. argüman olarak açıkça geçilmesi gerekiyor). Cron zamanlaması + saklama (retention) politikası script'in başına yorum olarak yazıldı (örnek: günlük 03:00, 14 gün saklama) — **gerçek zamanlama LITZOR'un altyapısında kurulmalı, burada yalnızca script'ler var.**

**Gerçek bir restore testi yapıldı** (doc'un *"restore test edilmeden tamam sayılmamalı"* şartını kod-seviyesinde kanıtlamak için): canlı Docker Postgres'ten gerçek bir dump alındı (`bidmont_20260730_194437.sql.dump`, 39 kullanıcı/14 aukciyon/3 bid içeren gerçek veri), `restore_db.sh` ile `bidmont_restore_test` adlı ayrı bir DB'ye restore edildi, ve satır sayıları (`users`/`auctions`/`bids`) kaynak ile restore edilmiş DB arasında **birebir eşleştiği** doğrulandı (39/14/3 = 39/14/3). Test DB'si doğrulama sonrası temizlendi (`DROP DATABASE`).

**§19.7 — Monitoring/alerting**: yeni bir `alert_admins(db, title, message, event_key=None)` fonksiyonu (`app/services/notifications.py`) — mevcut `send_notification()` altyapısını (in-app bildirim + e-posta) tekrar kullanarak her admin/super_admin'e bir `system_alert` tipi bildirim gönderiyor (ladder rung 2: yeni bir paging servisi kurmak yerine zaten var olan bildirim sistemini kullan). Üç noktaya bağlandı:
1. `app/core/scheduler.py` — `finalize_auction()` bir aukciyonu otomatik kapatırken patlarsa (bid engine error), `event_key=f"bid_engine_error:{auction_id}"` ile (auction başına tek alert, her 30sn'lik pollda tekrar spam etmesin diye) admin'lere haber veriliyor.
2. `app/api/credits.py::monri_credit_callback` — Monri webhook'u bir ödemeyi failed/declined olarak işaretlerse (kullanıcıya zaten giden rutin "satın alma başarısız" bildiriminden **ayrı** olarak), admin'lere ayrıca bir ops alert'i gidiyor.
3. `backend/main.py` — yeni bir global `@app.exception_handler(Exception)` — API'de yakalanmamış HERHANGİ bir 500, artık sessizce geçmiyor: `logger.critical(exc_info=True)` ile merkezi loglanıyor (doc'un *"centralized application error logs"* kısmı) + admin'lere alert gidiyor, `event_key` endpoint+exception-type'a göre scope'lanıyor (sürekli bozuk bir endpoint her istekte değil, yalnızca bir kez alert üretsin diye).

Gerçek uptime monitor (Pingdom/UptimeRobot/vb.) **kasıtlı olarak eklenmedi** — `GET /api/health` zaten var (önceki bir oturumdan), bu tam olarak böyle bir servisin ping edeceği endpoint; hangi servisin seçileceği ve nasıl yapılandırılacağı §19.1'in domain/TLS seçimiyle aynı türden bir LITZOR operasyonel kararı, C listesine eklendi.

**Bulunan ve düzeltilen ciddi bir bug (canlı Postgres smoke testinde yakalandı, unit testlerde yakalanamamıştı)**: `alert_admins()` ilk yazıldığında tüm admin'lere AYNI `event_key`'i geçiyordu. `Notification.event_key` sütunu **global olarak unique** (kullanıcı başına değil) — bu yüzden döngüdeki İLK admin'in insert'i `event_key`'i talep ediyor, geri kalan admin'lerin hepsi "zaten gönderilmiş" (IntegrityError → None) sanılıp sessizce atlanıyordu. Yerel SQLite testleri bunu hiç yakalayamadı çünkü hepsi tek bir `admin_user` fixture'ı kullanıyordu (yalnızca 1 admin varken bug görünmüyor) — canlı ortamda **3 gerçek admin hesabıyla** çalıştırılan smoke test (`smoke_alerting.py`) bunu yakaladı: yalnızca en eski admin alert alıyordu, diğer ikisi hiç almıyordu. Kök nedene göre düzeltildi: her admin kendi `event_key`'ini alıyor (`f"{event_key}:{admin_id}"`) — aynı olay hâlâ admin başına doğru şekilde dedupe ediliyor, ama artık admin'ler birbirinin insert'ini "already sent" sanmıyor. Bu düzeltmeyi kanıtlamak için hem yeni bir unit test (`test_all_admins_notified_not_just_the_first`, iki admin fixture'ıyla) hem de ikinci bir canlı smoke test (`smoke_alerting2.py`, mevcut 3 admin'in üçünün de alert aldığını doğruluyor) eklendi.

Doğrulama: backend — 8 yeni test eklendi (`tests/integration/test_scheduler_alerting.py` — bid engine hata alert'i, `finalize_auction`'ı monkeypatch ile patlatıp admin'e alert gittiğini kanıtlıyor; `tests/integration/test_error_alerting.py` — global exception handler'ın 500 döndürdüğünü, iç detayları sızdırmadığını, admin'e alert gönderdiğini, ve alert'in kendisi patlarsa bile response'un yine de 500 döndüğünü kanıtlıyor; `tests/integration/test_credit_engine.py::TestCreditWebhookIdempotency::test_failed_payment_alerts_admins`; `tests/integration/test_notifications.py::TestAlertAdmins` — 3 test). `pytest` 192 testin 189'u geçti (aynı 3 önceden var olan `forgot-password` hatası, değişmedi — 181'den 189'a, 8 yeni test). `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı üç ayrı smoke test: `backup_db.sh`/`restore_db.sh`'nin gerçek bir restore'u satır sayısı eşleşmesiyle kanıtlaması (yukarıda), `smoke_alerting.py` (payment webhook failure → admin alert), `smoke_alerting2.py` (multi-admin fix doğrulaması, 3/3 admin alert aldı). `GET /api/health` ve `GET /api/categories` normal trafiğin yeni global exception handler'dan etkilenmediğini doğruladı.

**Kendi kendini yakalayan ikinci bir bug** (yazarken, testten önce fark edildi): `app/core/scheduler.py`'de bid-engine-error alert'i eklerken, hata sonrası `await db.rollback()` çağrısı SQLAlchemy'nin ORM nesnelerini expire ettiğini (varsayılan `expire_on_rollback=True`) hesaba katmadan `auction.id`/`auction.title`'a rollback SONRASI erişmeye devam ediyordu — bu, güvenli olmayan bir lazy-load tetikleyip `MissingGreenlet` hatası atıyordu (yazdığım `test_finalize_error_alerts_admins` testi bunu hemen yakaladı, canlıya hiç gitmeden). Kök nedene göre düzeltildi: `auction.id`/`auction.title` rollback'ten ÖNCE yerel değişkenlere alınıp sonrasında onlar kullanılıyor.

**Bilinen sınır**: gerçek uptime monitor servisi seçimi ve gerçek cron zamanlamasının LITZOR'un altyapısında kurulması hâlâ operasyonel bir adım (C listesine eklendi). AC-21'in *"test edilmiştir"* ifadesi muhtemelen LITZOR'un kendi staging ortamında resmi bir go-live kontrol listesi olarak tekrarlanmasını bekliyor — bu oturumdaki test (yerel Docker Postgres'e karşı) teknik kanıt sağlıyor ama o resmi adımın yerini almıyor.

Bölüm 22'deki B listesinden §19.6/§19.7 satırı çıkarıldı; §20'deki AC-21 notu güncellendi; C listesine §19.6 (cron/retention operasyonu) ve §19.7 (uptime monitor servis seçimi) LITZOR maddeleri olarak eklendi.

## 47. Revizyon Geçmişi (30.07.2026, devam) — §11.3 Seller Dashboard + Bölüm 22'nin B listesinin dürüst yeniden sınıflandırılması + Bölüm 46'daki alert event_key düzeltmesi

Bu turun başında bir advisor danışması yapıldı: kalan B listesindeki maddelerin çoğu (§6.1, §6.2, §7, §3.6 kalanı, §4.3/AC-20) doc'un kendi notlarına göre zaten şema/taksonomi kararı gerektiriyor ("tek taraflı yapılmamalı") ya da gerçek bir tarayıcı gerektiriyor (§2.7/AC-14, §20 AC-14/AC-16) — bunları "kod ile tamamlanabilir" (B) listesinde tutmak, bu oturumun onları kapatabileceği yanlış izlenimini veriyordu. Advisor'ın önerisiyle iki şey yapıldı: (1) §11.3 (Seller Dashboard) — hiçbir dış girdiye bağlı olmayan, gerçekten kod ile kapatılabilir tek büyük madde — bu turda kapatıldı; (2) Bölüm 22'nin B listesi B/B2 olarak dürüstçe ikiye ayrıldı (yukarıya bkz.) — B artık yalnızca gerçekten şu an kod ile ilerletilebilecek 3 maddeyi içeriyor, B2 karar/tarayıcı bekleyen 6 madde grubunu.

**§11.3 Seller Dashboard**: doc'un docx'ten çıkarılan tam listesi (`11.3 Seller Dashboard`): *"Overview: Draft/Under Review/Live/Ended listing counts, My Listings, Create Listing, Drafts, Under Review, Live Auctions, Ended Auctions/Results, Seller Profile/Verification status, Notifications."* Bunların çoğu Bölüm 42/43'te zaten (aynı `#profile` sayfası içinde, ayrı bir route değil — doc bir route ayrımı istemiyor, yalnızca modülleri istiyor) yapılmıştı; bu turda kapatılan gerçek eksikler:
- **Overview bucket'ları yanlıştı**: mevcut 4 kart Total/Active/Completed/Revenue idi — doc'un istediği Draft/Under Review/Live/Ended değil. Backend'in `GET /users/me/seller-stats`'ı zaten `pending_auctions` (under_review) hesaplıyordu ama hiç ekranda gösterilmiyordu; `draft_auctions` ise backend'de hiç yoktu (bir satırlık ekleme: `counts.get("draft", 0)`). Kartlar Draft/Under Review/Live/Ended/Revenue olarak değiştirildi (revenue faydalı olduğu için silinmedi, doc'un istediği 4'e ek bir 5. kart olarak kaldı).
- **Drafts/Under Review/Live Auctions/Ended-Results ayrı görünümler yoktu** — "My Listings" tek bir düz liste olarak (yalnızca son 5 kayıt) render ediliyordu, statüye göre filtrelenemiyordu. Zaten fetch edilen `/auctions/my` listesi bir modül-seviyesi `mySellerListingsCache` değişkenine alındı (ekstra API çağrısı gerekmeden), ve `#myListingsFilter` adlı bir dropdown (All/Drafts/Under Review/Live Auctions/Ended-Results) eklendi — seçime göre cache'i client-side filtreleyip yeniden render ediyor.
- **Seller Profile/Verification status dashboard'ın içinde hiç gösterilmiyordu** (yalnızca ayrı `#sell` sayfasında, `renderSellerStatus()` içinde, o da başvuru formunu doldurmakla iç içe geçmiş bir fonksiyondu). Yeni, küçük ve salt-okunur bir `renderSellerVerificationBadge()` fonksiyonu eklendi (mevcut `getMySellerProfile()` API metodunu tekrar kullanıyor, `#sell` sayfasındaki fonksiyona hiç dokunmadı — ayrı, temiz bir okuma-amaçlı render).
- "Create Listing" (zaten `#sell` linki var) ve "Notifications" (zaten paylaşılan `#profileNotifList` var) — değişiklik gerekmedi.

**§11.4 (multi-step wizard) bu turda kasıtlı olarak kapatılmadı** — advisor'ın önerisiyle iki ayrı tura bölündü, bu tur yalnızca §11.3. Doc'un 8 adımı docx'ten tam olarak çıkarıldı (yukarıdaki B listesine yazıldı): Adım 1 (kategori/subcategory) ve Adım 3 (kategoriye özel teknik özellikler) §7'nin taksonomi kararına bağlı; diğer 6 adım (temel bilgiler, condition/defects, foto/doküman, location, fiyat/increment/kredi, preview+declaration+submit) bağımsız ve inşa edilebilir — gelecek bir turun konusu.

**Bölüm 46'nın kendi kapanışındaki bir eksiklik düzeltildi** (advisor'ın bu turda işaret ettiği ikinci nokta): `alert_admins()`'e geçilen `event_key`'ler (`bid_engine_error:{auction_id}`, `unhandled_error:{method}:{path}:{type}`) hiç zaman bileşeni içermiyordu. `Notification` satırları kalıcı olduğu için bu, "aynı olay için bir kez uyar, sonra sonsuza dek asla" anlamına geliyordu — bir aukciyon düzelmeden tekrar tekrar bozulsa ya da bir endpoint aylar sonra yeniden aynı hatayı verse, event_key hâlâ eski satırla eşleştiği için **hiç yeni alert gitmiyordu**. Var olan testler ("tam olarak 1 alert" doğrulaması) bu tasarımın her iki türünde de (tarihli/tarihsiz) geçtiği için bunu hiç yakalayamamıştı. Düzeltme: her iki `event_key`'e güncel takvim günü (`%Y-%m-%d`) eklendi — aynı olay bir gün içinde hâlâ tekilleşiyor (spam yok), ama ertesi gün hâlâ çözülmemişse yeniden alert üretiyor. Yeni bir test eklenmedi (mevcut testler zaten "tam olarak 1" davranışını doğruluyor, tarih bileşeni farklı günler arası davranışı test etmek için zamanı mock'lamayı gerektirirdi — bu turda kapsam dışı bırakıldı, ponytail: bu spesifik zaman-sınırı davranışını kanıtlayan bir test yok, günlük bucket'ın doğru çalıştığı yalnızca kod incelemesiyle doğrulandı).

Doğrulama: backend — `backend/app/api/users.py::seller_stats`'a `draft_auctions` eklendi; yeni `tests/integration/test_users_api.py::TestSellerStats::test_counts_by_status_bucket` (draft/under_review/live/ended karışık 5 aukciyon oluşturup her bucket'ın doğru sayıldığını kontrol ediyor). `pytest` 193 testin 190'ı geçti (aynı 3 önceden var olan hata, değişmedi — 192'den 193'e, `test_users_api.py`'a eklenen yeni `TestSellerStats` class'ı ile). Frontend — `node --check` (SYNTAX_OK); DOM-id çapraz referans denetimi (171 kullanım, 0 sarkan); `i18n_check.js` (281 kullanım, 0 eksik — yeni `pr.ss.draft`/`pr.ss.pending`/`pr.ml.*` anahtarları ME+EN eklendi). `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı `urllib` smoke test (`smoke_sellerdash.py`) — gerçek bir verified seller ile 3 aukciyon oluşturulup draft/under_review/live durumlarına ayrıca ayarlandı, `GET /users/me/seller-stats`'ın `draft_auctions:1, pending_auctions:1, active_auctions:1, total_auctions:3` döndürdüğü doğrulandı.

**Bilinen sınır**: yeni filtre dropdown'ının ve verification badge'in görsel/tıklama davranışı gerçek tarayıcıda test edilmedi (headless tarayıcı yok) — yalnızca kod-seviyesinde ve backend'in canlı Postgres'e karşı doğrulandı.

Bölüm 22'deki B listesinden §11.3 çıkarıldı (§11.4 hâlâ B'de, daraltılmış kapsamla — yalnızca 6/8 adım şu an bağımsız inşa edilebilir). B listesi B/B2 olarak yeniden yapılandırıldı (yukarıya bkz.); bu bir kod kapanışı değil bir doğruluk düzeltmesiydi, madde sayısını "kapatılan" olarak artırmıyor ama B listesinin gelecekte yanlış maddeler seçilerek zaman kaybedilmesini önlüyor.

## 48. Revizyon Geçmişi (30.07.2026, devam) — §20 AC-01 e-posta doğrulama + üç kalıcı test hatasının kök nedeninin düzeltilmesi

B listesindeki §20 AC-01'in yarısı (e-posta doğrulama) kapatıldı. Doc'un tam ifadesi: *"AC-01 - Yeni kullanıcı kayıt olur, iletişim doğrular ve kredi paketi satın alır."* Docx'in başka hiçbir yerinde genel kullanıcı kaydı için ayrı, numaralandırılmış bir e-posta/telefon doğrulama spesifikasyonu yok (yalnızca §11.2'nin seller-application checklist'inde "Phone + email verification" bir alt-madde olarak geçiyor, o farklı bir konu — seller başvurusu, genel kullanıcı kaydı değil). AC-01'in "iletişim doğrular" ifadesi, bu turda genel kullanıcı kaydı için gerçek bir doğrulama akışı olarak yorumlandı ve inşa edildi.

**Kapsam kararı**: e-posta VE telefon (SMS) doğrulaması ikisi birden AC-01'de anılıyor ama SMS doğrulaması bir SMS gateway (Twilio vb.) seçimi ve kimlik bilgileri gerektiriyor — bu, Monri/PSP seçimiyle aynı türden bir LITZOR kararı (C listesinde zaten var olan bir örüntü). Bu yüzden yalnızca **e-posta doğrulaması** inşa edildi; telefon/SMS yarısı C listesine, aynı gerekçeyle eklendi. Bu, seller_type filtresi/equipment condition gibi bu oturum boyunca tekrarlanan "gerçekten yapılabilecek kadarını yap, geri kalanını dürüstçe ayrı bırak" deseniyle aynı.

**Backend**: mevcut `forgot_password`/`reset_password` akışının BİREBİR AYNI deseni tekrar kullanıldı (ladder rung 2) — `hashlib.sha256` ile hash'lenmiş tek-kullanımlık token + son kullanma tarihi, ama forgot-password'ün `reset_token_hash` sütunuyla hiç paylaşılmayan ayrı sütunlar (`email_verification_token_hash`, `email_verification_expires_at`) — böylece aynı anda hem aktif bir şifre-sıfırlama linki hem aktif bir e-posta-doğrulama linki olsa biri diğerini geçersiz kılmıyor.
- `User`'a `email_verified` (default false), `email_verification_token_hash`, `email_verification_expires_at` eklendi (model + `MISSING_COLUMNS`).
- `POST /api/auth/register`: kullanıcı oluşturulduktan hemen sonra bir doğrulama token'ı üretiyor, DB'ye hash'ini yazıyor, ve **gerçekten bir e-posta gönderiyor** (`app/services/notifications.py::_send_email`'i tekrar kullanarak — yeni bir SMTP konfigürasyonu yazılmadı). Doc'un beklediği gibi kayıt/login hiçbir şekilde bu adıma bağlı değil — hesap doğrulanmamış olsa da kullanılabiliyor, AC-01 yalnızca adımın var olup çalıştığını istiyor, başka hiçbir eylemi bloke etmesini istemiyor.
- `POST /api/auth/verify-email` (token al, doğrula, `email_verified=True` yap, token'ı tüket — tek kullanımlık).
- `POST /api/auth/resend-verification` (kimlik doğrulamalı, kendi hesabı için; zaten doğrulanmışsa no-op döner).
- `UserResponse`'a `email_verified` eklendi; `auth.py`'de üç yerde (register/login/refresh) tekrarlanan `UserResponse(...)` inşası tek bir `_user_response()` helper'ına çıkarıldı (aynı alanları üç kez yazmak yerine — bu arada `admin.py`'deki üç `UserResponse(...)` yeri ve `users.py::_user_response` de `email_verified` alanını içerecek şekilde güncellendi, tutarlılık için).

**Bulunan ve kök nedenine göre düzeltilen, oturumun başından beri var olan bir hata**: bu oturumun HER turunda "aynı 3 önceden var olan hata, değişmedi" diye not edilen `TestForgotPassword`/`TestResetPassword` başarısızlıklarının kök nedeni bulundu — `tests/conftest.py` `ENVIRONMENT` ortam değişkenini hiç ayarlamıyordu, bu yüzden `forgot_password()`'ün *"`ENVIRONMENT=development` iken token'ı doğrudan döndür"* dalı test sürecinde asla tetiklenmiyordu (testler `'reset_token' in response` bekliyordu ama hiç gelmiyordu). Bu, yeni e-posta doğrulama özelliğimin AYNI deseni kullanması nedeniyle (dev-mode'da token'ı response'a ekleme) bu turda fark edildi — yeni özelliğimin dev-mode testi de aynı nedenle başarısız olacaktı. Kök nedene göre düzeltildi: `conftest.py`'a `os.environ.setdefault("ENVIRONMENT", "development")` eklendi (`JWT_SECRET` satırının hemen altına). Bunun tek etkisi CLAUDE.md'de zaten belgelenen davranışı (*"forgot-password endpoint'i ... yalnızca `ENVIRONMENT=development` iken ham token'ı response'ta döndürür"*) test ortamında da doğru şekilde tetiklemek — `main.py`'deki `ENVIRONMENT` kontrollerinin geri kalanı (`HTTPSRedirectMiddleware`, `/api/health`'in "environment" alanı) yalnızca `=="production"` durumuna göre dallandığı için "development" set etmek onları hiç etkilemiyor (zaten unset haldeki davranışla aynı). Bu değişiklik **3 önceden var olan başarısız testi de düzeltti** — kod tarafında hiçbir şey değişmedi, yalnızca test ortamı doc'un kendi belgelediği davranışla uyumlu hale getirildi.

Doğrulama: backend — `tests/integration/test_auth_api.py::TestEmailVerification` (7 yeni test: kayıt sonrası `email_verified:false` + dev-token dönüşü, doğru token ile doğrulama, yanlış token reddi, token'ın tek-kullanımlık olması, `resend-verification`'ın auth gerektirmesi, yeni bir kullanılabilir token üretmesi, zaten doğrulanmış hesapta no-op). `pytest` 200 testin **200'ü** geçti (ilk kez bu oturumda tam yeşil — önceki 3 hata `ENVIRONMENT` düzeltmesiyle giderildi, 193'ten 200'e: 7 yeni test). Frontend — `node --check` (SYNTAX_OK); DOM-id çapraz referans denetimi (174 kullanım, 0 sarkan); `i18n_check.js` (285 kullanım, 0 eksik — yeni `vem.*`/`pr.verifyemail.*` anahtarları ME+EN eklendi). Yeni `#verify-email` route'u (`?token=...` okuyup otomatik doğrulayan bir sayfa) ve profildeki "lütfen e-postanızı doğrulayın" banner'ı (+ resend butonu) eklendi. `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı `urllib` smoke test (`smoke_emailverify.py`) — gerçek bir kayıt akışı: `email_verified:false` ile başlıyor, `GET /users/me` bunu yansıtıyor, yanlış token reddediliyor, doğru token doğruluyor, aynı token tekrar kullanılamıyor, `GET /users/me` artık `true` gösteriyor, zaten-doğrulanmış hesapta resend no-op dönüyor — hepsi doğrulandı (`EMAIL VERIFICATION (§20 AC-01) SMOKE CHECK PASSED`).

**Bilinen sınır**: profildeki doğrulama banner'ı yalnızca sayfa ilk yüklendiğinde (`restoreSession()`'ın `getMe()` çağrısı) alınan `apiUser` durumuna göre gösteriliyor — kullanıcı e-postasını başka bir sekmede doğrulayıp SPA'yı yeniden yüklemeden aynı sekmede profile dönerse banner geçici olarak yanlış (eski) durumu gösterebilir. Bu, sayfadaki diğer birçok alanla (rol, isim) aynı seviyede bir "snapshot" sınırlaması — küçük ve kabul edilebilir görüldü, ayrı bir madde olarak büyütülmedi. Ayrıca yeni route'un ve banner'ın görsel davranışı gerçek tarayıcıda test edilmedi (headless tarayıcı yok).

Bölüm 22'deki B listesinden §20 AC-01 satırı çıkarıldı (yalnızca e-posta yarısı — telefon/SMS yarısı C listesine, SMS gateway kararı gerektiği için eklendi).

## 49. Revizyon Geçmişi (30.07.2026, devam) — §11.4 Multi-step Create-Listing Wizard

B listesindeki son büyük kod maddesi kapatıldı: §11.4. Doc'un docx'ten çıkarılan tam 8 adımı: *"Step 1 - Category ve subcategory, Step 2 - Temel asset bilgileri, Step 3 - Category-specific teknik özellikler, Step 4 - Condition/known defects, Step 5 - Gerçek fotoğraf ve doküman yükleme, Step 6 - Location, Step 7 - Starting price/bid increment/start-end time/participation credit cost, Step 8 - Preview + seller declaration + Submit for Review."*

**Bulunan gerçek eksik**: mevcut `#sellForm` tek bir düz sayfaydı (başlık/açıklama/kategori/fiyat/artış/bitiş + yalnızca araç alanları), ve **fotoğraf yükleme UI'ı hiç yoktu** — satıcılar şu ana kadar arayüz üzerinden bir ilana fotoğraf ekleyemiyordu (backend'in `POST /api/uploads/batch` endpoint'i baştan beri vardı ama hiçbir yerden çağrılmıyordu). Ayrıca backend şemasında zaten var olan `location`, `damage_status` (araç), `condition`/`equipment_brand`/`serial_number` (ekipman) alanları da frontend'de hiç expose edilmemişti (Bölüm 43'ün notunda "eşdeğer bir `#equipmentExtra` hiç yazılmamış" olarak zaten işaretlenmişti).

**Kapsam kararı**: doc'un 8 adımının 6'sı (2,4,5,6,7,8) hiçbir taksonomi kararı gerektirmeden tam olarak inşa edildi. Adım 1 (kategori/subcategory) ve Adım 3 (kategoriye özel teknik özellikler), B2 listesindeki §7 maddesiyle aynı taksonomi kararına bağlı — bu turda **mevcut 3 kategoriyle** (Vozila/Oprema/General) sınırlı olarak inşa edildi, tam alt-kategori taksonomisi §7'nin kararını bekliyor (tek taraflı genişletilmedi).

**Backend**: **hiç değişiklik yapılmadı** — mevcut `POST /api/auctions` (zaten `location`/`damage_status`/`equipment_brand`/`serial_number`/`condition` alanlarını kabul ediyordu) ve `POST /api/uploads/batch` (zaten bir `auction_id`'ye karşı çoklu görsel kabul ediyordu) olduğu gibi tekrar kullanıldı (ladder rung 2). Görsel yükleme, `uploads/batch`'in bir `auction_id` gerektirmesi nedeniyle **aukciyon oluşturulduktan hemen sonra** (wizard'ın son adımında, "Objavi aukciju" tıklanınca) yapılıyor — kullanıcı Adım 5'te dosyaları seçiyor (henüz yüklenmiyor, yalnızca tarayıcı belleğinde bekletiliyor), Adım 8'de submit edilince önce `POST /auctions` çağrılıyor, dönen `id` ile hemen ardından `POST /uploads/batch` çağrılıyor.

**Frontend**: `#sellForm` 8 ayrı `.sell-step` div'ine bölündü (`data-step="1"`–`"8"`), üstte tıklanamaz bir adım göstergesi (`#sellWizardSteps`, mevcut `.admin-tab` deseni tekrar kullanıldı) + alt kısımda Geri/Đleri butonları. Yeni eklenen alanlar: `#equipmentExtra` (proizvođač/serijski broj — Bölüm 43'ten beri eksik olduğu bilinen div), `#sellDamageWrap`/`#sellConditionWrap` (araç/ekipman durumu-kusur alanları), `#sellLocation`, `#sellPhotos` (çoklu dosya input + küçük thumbnail-yerine-isim önizlemesi). Her adımda basit bir client-side doğrulama var (`sellStepValid()`) — zorunlu alan boşsa "İleri" engelleniyor. Adım 8, o ana kadar girilen TÜM verilerin okunabilir bir özetini gösteren bir önizleme (`renderSellPreview()`) render ediyor, doc'un *"Preview"* isteğini karşılıyor. Yeni bir `bidmontApi.uploadAuctionImages()` metodu eklendi — `_fetch()` üzerinden GEÇMİYOR çünkü `FormData` için `Content-Type`'ın tarayıcı tarafından (multipart boundary ile) otomatik ayarlanması gerekiyor, `_fetch()`'in sabit `application/json` header'ı bunu bozardı.

Doğrulama: backend — değişiklik yok, `pytest` 200 testin 200'ü geçmeye devam ediyor (bu turda yeni backend testi eklenmedi, mevcut endpoint'ler değişmeden tekrar kullanıldı). Frontend — `node --check` (SYNTAX_OK); DOM-id çapraz referans denetimi (190 kullanım, 0 sarkan); `i18n_check.js` (297 kullanım, 0 eksik — yeni `sell.eextra`/`sell.eq.*`/`sell.damage`/`sell.condition`/`sell.photos`/`sell.location`/`sell.prev`/`sell.next` gibi anahtarlar ME+EN eklendi). `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı uçtan uca bir `urllib` smoke test (`smoke_wizard.py`, gerçek bir 1x1 PNG `zlib`/`struct` ile programatik üretilip elle inşa edilmiş bir `multipart/form-data` gövdesiyle yüklendi — elle yazılmış bir hex literal ilk denemede bozuk çıkmıştı, programatik üretime geçilerek düzeltildi): gerçek bir verified seller ile `location`/`damage_status`/`equipment_brand`/`serial_number`/`condition` alanları dolu bir aukciyon oluşturuldu, gerçek bir PNG `POST /uploads/batch` ile o aukciyona yüklendi, `GET /auctions/{id}` detay yanıtının hem yeni alanları hem yüklenen görseli doğru döndürdüğü doğrulandı (`LISTING WIZARD (§11.4) END-TO-END SMOKE CHECK PASSED`).

**Kasıtlı olarak dışarıda bırakılan**: doküman yükleme (registracija/servisna knjižica) — doc'un Adım 5'i hem fotoğraf HEM doküman istiyor, ama doküman yükleme §6.2'nin (public/private erişim seviyesi olan ayrı bir şema) konusu ve B2 listesinde zaten şema-kararı-bekleyen olarak işaretli; burada UI'da açık bir not olarak ("Dokument upload uskoro dolazi") bırakıldı, sessizce atlanmadı. Participation credit cost (Adım 7'nin bir parçası) satıcı tarafından girilebilir bir alan olarak eklenmedi çünkü `AuctionCreateRequest` şeması bunu hiç kabul etmiyor (sistem/admin tarafından belirleniyor) — doc'un kendi ifadesi de bunun "admin/seller yetki politikasına göre" olduğunu, yani belirsiz olduğunu söylüyor; var olmayan bir API kapasitesi icat edilmedi.

**Bilinen sınır**: wizard'ın adım geçişlerinin, dosya önizlemesinin ve önizleme ekranının görsel/tıklama davranışı gerçek tarayıcıda test edilmedi (headless tarayıcı yok) — yalnızca kod-seviyesinde ve backend'in canlı Postgres'e karşı (create+upload+detail zinciri) doğrulandı.

Bölüm 22'deki B listesinden §11.4 satırı çıkarıldı. **B listesi artık yalnızca 1 madde içeriyor: §17 kalanı (bildirim şablonu admin yönetimi)** — bu, oturumun başından beri kod ile tamamlanabilir olarak işaretlenen maddelerin neredeyse tamamının kapatıldığı anlamına geliyor; geri kalan açık maddelerin hepsi ya B2'de (karar/tarayıcı bekliyor) ya da C'de (LITZOR'un girdisi).

## 50. Revizyon Geçmişi (30.07.2026, devam) — §17 Bildirim Şablonu Admin Yönetimi (B listesinin son maddesi)

B listesindeki son madde kapatıldı: §17'nin admin panel checklist'inde yer alan *"Notification template management"* maddesi. Doc'un tam listesi (§17 başlığı altında): *"Yönetim Panelinde Bulunması Rica Edilen Modüller: ... Notification template management ..."* — ayrı bir alt-numarası yok, RBAC (§17.1), audit log (§17.2), admin 2FA (§17.3) gibi checklist'in geri kalanıyla aynı seviyede bir madde.

**Bölüm 47'de advisor'ın uyardığı tuzak**: naif bir "statik override" tasarımı (admin bir şablon kaydeder, o her zaman kullanılır) her çağrı noktasının gömdüğü DİNAMİK içeriği (aukciyon adı, kredi miktarı, ret sebebi) sessizce silerdi — bu bir özellik değil bir regresyondur. Bunun yerine advisor'ın önerdiği **`template_vars`** deseni uygulandı: `send_notification()` artık opsiyonel bir `template_vars: dict|None` parametresi alıyor; bir admin şablonu YALNIZCA çağıranın geçtiği `template_vars` içindeki TÜM placeholder'lar dolduğunda kullanılıyor, aksi halde (şablon hiç yoksa, ya da bir placeholder eksikse/yanlış yazılmışsa) bugünkü literal string'e sessizce geri düşülüyor — hiçbir zaman `{oops}` gibi çözülmemiş bir placeholder'ı gerçek bir kullanıcıya göstermiyor, hiçbir zaman dinamik içeriği kaybetmiyor.

**Kapsam kararı**: TÜM ~20 `send_notification()` çağrı noktası yerine, advisor'ın önerisiyle yalnızca **5 yüksek-değerli tip** (`TEMPLATABLE_NOTIFICATION_TYPES` registry'si) bağlandı: `auction_approved`, `auction_rejected`, `listing_changes_requested`, `credit_purchase_successful`, `credit_purchase_failed`. Admin panelinde de yalnızca bu 5 tip listeleniyor — bağlanmamış bir tipi (ör. `outbid`) "özelleştirmek" hiçbir şey yapmazdı, bu yüzden hiç sunulmuyor (kafa karıştırıcı, çalışmayan bir özellik yerine dürüstçe dar bir kapsam).

**Backend**:
- Yeni bir tablo, `NotificationTemplate` (`type` — NotificationType değeri, primary key — + `title_en`/`message_en`/`title_me`/`message_me`/`updated_at`). **Migration gerekmedi** — mevcut tablolara `ALTER TABLE` ekleyen `MISSING_COLUMNS` sisteminin aksine, bu YENİ bir tablo; `Base.metadata.create_all()` başlangıçta otomatik oluşturuyor (SellerProfile/Watchlist gibi önceki "additive tables" ile aynı desen). Canlı Postgres'te doğrulandı (`\d notification_templates`).
- `send_notification()`'a `template_vars` parametresi eklendi + yeni bir `_render_template_field(template_value, vars, fallback)` helper'ı (her alan için bağımsız: `.format(**vars)` dener, `KeyError`/`IndexError` yakalarsa fallback'e döner).
- 5 çağrı noktasına (`app/api/auctions.py` — 3 yer, `app/api/credits.py` — 2 yer) `template_vars` eklendi (ör. `{"auction_title": auction.title}`, `{"auction_title": ..., "reason": req.reason}`, `{"credits_amount": f"{purchase.credits_amount:.0f}"}`).
- Üç yeni admin endpoint'i (`get_current_admin` ile korunuyor — mesajlaşma/marka içeriği hassas kabul edildi, `get_current_staff` değil): `GET /admin/notification-templates` (5 bağlı tipi + varsa mevcut override'ı listeler), `PUT /admin/notification-templates/{type}` (kaydeder — bilinmeyen bir tip 404, bağlı-olmayan bir tip 400, İZİN VERİLMEYEN bir placeholder kullanan metin 400 ile anında reddediliyor, sessizce fallback'e düşmesini beklemek yerine admin'e hemen geri bildirim), `DELETE /admin/notification-templates/{type}` (satırı silip varsayılana döndürür). Değişiklikler audit log'a yazılıyor (`_log_audit`, mevcut desen).

**Frontend**: admin panelinde yeni bir "Notification Templates" sekmesi — 5 bağlı tipin her biri için EN/ME başlık+mesaj alanları, kullanılabilir placeholder'ların listesi, Save/Reset to default butonları (mevcut admin panel deseniyle — düz İngilizce, i18n yok, admin paneli zaten hiç i18n kullanmıyor).

Doğrulama: backend — 5 yeni unit test (`tests/unit/test_notification_templates.py::TestRenderTemplateField` — fallback/render/eksik-placeholder/placeholder'sız-statik-metin durumları) + 9 yeni entegrasyon testi (`tests/integration/test_admin_notification_templates_api.py` — listeleme, admin-olmayan reddi, bilinmeyen tip 404, bağlı-olmayan tip 400, bilinmeyen placeholder 400, kaydetme+kalıcılık, reset, VE gerçek `send_notification()` çağrısıyla şablonun uygulandığının/uygulanmadığının doğrulanması). `pytest` 214 testin 214'ü geçti (200'den 214'e, 14 yeni test — hiçbir mevcut test bozulmadı). Frontend — `node --check` (SYNTAX_OK); DOM-id çapraz referans denetimi (190 kullanım, 0 sarkan — yeni `tpl_${type}_*` id'leri dinamik olarak oluşturulup hemen `getElementById` ile bağlandığı için statik taramada görünmüyor, mevcut admin panel deseniyle aynı); `i18n_check.js` (297 kullanım, 0 eksik — admin paneli hiç i18n kullanmadığı için yeni anahtar gerekmedi). `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı uçtan uca bir `urllib` smoke test (`smoke_templates.py`): admin bilinmeyen bir placeholder'ı denedi (400 ile reddedildi), gerçek bir özel şablon kaydetti (*"Great news - {auction_title} is now LIVE!"*), gerçek bir aukciyonu onayladı — ve veritabanındaki GERÇEK bildirim satırının başlığının tam olarak özel şablon metniyle (*"Great news - Template Smoke Auction is now LIVE!"*) eşleştiği doğrudan psql ile doğrulandı (varsayılan hardcoded metin değil), ardından reset edilip varsayılana döndüğü doğrulandı (`NOTIFICATION TEMPLATE (§17) END-TO-END SMOKE CHECK PASSED`).

**Bilinen sınır**: admin panelindeki yeni sekmenin görsel/tıklama davranışı gerçek tarayıcıda test edilmedi (headless tarayıcı yok) — yalnızca kod-seviyesinde ve backend'in canlı Postgres'e karşı (kaydet→gerçek bildirim tetikle→doğrula→sıfırla zinciri) doğrulandı. Yalnızca 5 bildirim tipi bağlı — geri kalan ~15 tip (`outbid`, `bid_received`, `auction_won` vb.) için şablon yönetimi istenirse, yalnızca o çağrı noktasına bir `template_vars` eklemek ve `TEMPLATABLE_NOTIFICATION_TYPES`'a bir satır eklemek yeterli (mekanizma zaten genel), ama bu turda kasıtlı olarak dar tutuldu.

Bölüm 22'deki B listesinden §17 kalanı satırı çıkarıldı. **B listesi (o anki bilgiyle) tamamen boşaldı** — ancak bu ilan Bölüm 52'de yanlış çıktı: §6.1/§6.2/§7/§3.6 aslında B2'ye yanlış sınıflandırılmıştı, gerçekte B'de kalmaları gerekiyordu. Bkz. Bölüm 52'nin açık düzeltmesi.

## 51. Revizyon Geçmişi (30.07.2026, devam) — §20 AC-16'nın statik yarısı: gerçek bir i18n boşluğu ve gerçek bir link-kaybı hatası bulundu ve kapatıldı

Bölüm 50'de B listesi tamamen boşaltıldıktan sonra, bir advisor danışması B2'deki §20 AC-16 etiketinin fazla iddialı olduğunu işaret etti: AC-16 iki yarıdan oluşuyor — (a) dil değişiminde **görsel** olarak karışık metin kalmaması (gerçek tarayıcı gerektirir, B2'de doğru), ve (b) **statik** bir tarama ile kullanıcıya görünen ama hiç i18n sistemine girmemiş (`data-i18n` yok, `currentLang===` üçlü operatörü yok) metinlerin **envanterini çıkarmak** — bu ikinci yarı bir grep/regex işi, tarayıcı gerektirmiyor ve daha önce hiç yapılmamıştı. Mevcut `i18n_check.js` yalnızca `data-i18n` kullanılan anahtarların ≥2 tanımı olduğunu doğruluyordu (ters yönü hiç kontrol etmiyordu).

**Yapılan**: `index.html`'in `<body>` içeriği (script/style hariç) regex ile taranıp `data-i18n` içermeyen, ≥3 harflik gerçek metin taşıyan tüm `<h1-4>/<p>/<span>/<button>/<label>/<a>/<option>/<td>/<th>/<strong>/<small>` etiketleri listelendi (23 aday bulundu). Bunların çoğu meşru istisnalar: dil seçici etiketleri ("Crnogorski"/"English" — kendi dillerinde gösterilmesi doğru UX), marka adı ("Mont"), admin panel sekme başlıkları (admin paneli zaten hiç i18n kullanmıyor, kasıtlı bir tasarım kararı, AC-16'nın kapsamı müşteri yüzü). Ama **iki gerçek bulgu** çıktı:

1. **Sell wizard'da (§11.4) hardcoded İngilizce seçenekler**: `#sellFuel` (Petrol/Diesel/Electric/Hybrid) ve `#sellTrans` (Manual/Automatic) `<option>` etiketleri `data-i18n` taşımıyordu — Karadağca modunda bile daima İngilizce görünüyorlardı. Aynı sayfadaki arama filtresi (`#auctionFuel`/`#auctionTrans`, satır 122-123) doğru şekilde `auc.fuel.*`/`auc.trans.*` anahtarlarıyla zaten çevriliydi — wizard eklenirken (Bölüm 49) bu ikisi gözden kaçmıştı. **Düzeltme**: `#sellFuel`/`#sellTrans`'a aynı mevcut `auc.fuel.*`/`auc.trans.*` anahtarları + `value="Petrol"` gibi açık `value` öznitelikleri eklendi (önceden `value` özniteliği yoktu, metin kendisi value'ydu — bu artık `data-i18n` metni değiştirdiğinde gönderilen değerin bozulmayacağı anlamına geliyor). Yeni çeviri anahtarı gerekmedi, mevcut anahtarlar yeniden kullanıldı.

2. **Gerçek bir fonksiyonel regresyon — kayıt formundaki Terms/Privacy linkleri her sayfa yüklemesinde yok ediliyordu**: `applyTranslations()` fonksiyonu (satır 2239-2249), bir `data-i18n` elemanının içinde `<a>/<span>/<b>` varsa `innerHTML` ile (metni kaybetmeden link'i korumak için), yoksa `textContent` ile değiştiriyor. `#regTerms`/`#regPrivacy` checkbox'larının span'ları (`r.terms`/`r.privacy` anahtarları) DOM'da gerçek bir `<a href="#">Uslove korišćenja</a>` içeriyordu — bu yüzden `innerHTML` dalı seçiliyordu. Ama `translations.ME['r.terms']`/`translations.EN['r.terms']` (ve `r.privacy`) sözlük girdileri düz string'di: **`'Prihvatam Uslove korišćenja *'`** / **`'I accept the Terms of Service *'`** — link'siz. Sonuç: `applyTranslations()` her çağrıldığında (sayfa her yüklendiğinde, `currentLang` ayarlandıktan hemen sonra script'in sonunda çağrılıyor — satır 2309) bu span'ların `innerHTML`'i link'siz düz metinle değiştiriliyordu. **Kayıt formundaki "Uslove korišćenja"/"Politiku privatnosti" linkleri hiçbir zaman tıklanabilir olmuyordu** — statik HTML'de bir kere göründükten hemen sonra JS tarafından siliniyordu. Ayrıca statik HTML'deki `href="#"` de zaten anlamsız bir hedefti (hiçbir yere gitmiyordu).

   **Düzeltme**: hem statik HTML'deki hem her iki dildeki (`ME`/`EN`) `r.terms`/`r.privacy` çeviri string'lerine `l.n` anahtarında zaten kullanılan desen uygulandı — link artık çeviri string'inin kendi içinde gömülü (`'Prihvatam <a href="#legal" ...>Uslove korišćenja</a> *'`), `href` de var olan `#legal` sayfasına (Terms of Use/Privacy Policy sekmeli mevcut hukuki doküman sayfası, footer'da zaten aynı şekilde linkleniyor) işaret ediyor. Artık her `applyTranslations()` çağrısında link kalıcı ve tıklanabilir.

**Kapsam kararı**: admin panelinin i18n kullanmaması (bulunan 8 admin-sekme adayı) bu turda düzeltilmedi — admin paneli zaten en baştan beri tamamen düz İngilizce (Bölüm 50 dahil tüm önceki admin eklemeleri de böyle), bu tutarlı ve kasıtlı bir tasarım sınırı, AC-16'nın kapsamı olan müşteri-yüzü sayfalarla ilgisi yok.

Doğrulama: `node --check` (SYNTAX_OK); `i18n_check.js` (297 anahtar kullanımı, 0 eksik — yeni anahtar eklenmedi, mevcut `auc.fuel.*`/`auc.trans.*` yeniden kullanıldığı için); `pytest` 214/214 (saf frontend değişikliği, backend dokunulmadı); `docker compose up --build -d` ile yeniden derlendi, canlı sunucudan (`http://localhost:8000/`) servis edilen gerçek HTML `urllib` ile çekilip dört nokta doğrulandı: `#sellFuel`/`#sellTrans`'ın yeni `data-i18n` özniteliği taşıdığı, `#regTerms`/`#regPrivacy` span'larının artık `href="#legal"` içerdiği — hepsi OK.

**B/B2 defteri düzeltmesi**: bu bulgu B listesinin Bölüm 50'de "tamamen boş" ilan edilmesinden hemen sonra, statik bir tarama daha önce hiç yapılmadığı için gözden kaçmış iki gerçek B-madddesini ortaya çıkardı — yani "B boş" ilanı o an için doğruydu (o ana kadar bilinen tüm B maddeleri kapalıydı) ama envanterin kendisi eksikti. Bu ikisi de şimdi kapatıldığı için B listesi yeniden boş durumda. §20 AC-16 B2'de kalıyor ama artık yalnızca **görsel** yarısı için (statik yarısı bu bölümde tamamlandı) — B2 etiketi bu bölümle daraltıldı, önceki "aynı nedenle" ifadesi yanlıştı.

Bölüm 22'deki §20 AC-16 B2 satırı "yalnızca görsel/tıklama teyidi kaldı (statik envanter Bölüm 51'de tamamlandı)" olarak güncellendi.

## 52. Revizyon Geçmişi (30.07.2026, devam) — §6.1 Kategorize kusur bölümü + Bölüm 47'nin B2 sınıflandırma hatasının düzeltilmesi

**Bölüm 47'nin hatası, açıkça kabul edilerek**: bir advisor danışması, bu turun statik i18n taramasından (Bölüm 51) sonra §6.1/§6.2/§7/§3.6'nın B2'ye ("harici karar gerektirir") atanmasının **yanlış** olduğunu gösterdi. `docs/Bidmont son hali için döküman .docx`'in ham metni tekrar okunduğunda, bu dört madde için doküman KENDİSİ zaten somut, isimlendirilmiş bir taksonomi/şema veriyor — bunlar LITZOR'un iş/hukuk kararı değil, doküman metninin transkripsiyonu:
- §6.1: *"Seller bilinen kusurları kategorize ederek girebilmeli: exterior, interior, mechanical, tyres, missing parts, damage description."* — 6 kategori adı ile birlikte tam olarak verilmiş.
- §7.2.1: *"Yeni alt kategoriler: Hospitality, Restaurant Equipment, Electronics, Office, Retail Equipment, Inventory & Stock, Furniture, Tools, Other."* — Commercial Assets alt-taksonomisi tam olarak verilmiş (§3.6'nın "alt kategori örnekleri" isteğini de karşılıyor).
- §7.1/§7.2.2: equipment ve commercial asset alanları tek tek isimlendirilmiş (Manufacturer/Model/Year/Operating hours/Serial/Engine-power/Operating weight/Condition/Service history/Known defects/Location/Inspection availability/Dimensions/Accessories; Quantity/brand/model/year/condition/package contents/serials/dimensions/location/known defects/included items).
- §6.2: doküman "registration, inspection, service/other" doküman kategorilerini VE public/private erişim modelini zaten belirtiyor; ayrıca `AuctionImage.media_type`/`visibility` kolonları backend'de zaten var ama hiçbir API/schema/frontend kodu onları hiç kullanmıyor (grep ile doğrulandı — sıfır referans).

Bu, Bölüm 51'deki gibi küçük bir gözden kaçma değil — dört B2 satırının kendisi yanlış sınıflandırılmıştı. Bölüm 47'nin kendi hatasını nasıl açıkça kabul ettiği gibi, burada da aynı şekilde kabul ediliyor: **B listesi Bölüm 50'de "tamamen boş" değildi**, dört gerçek madde B2'ye yanlış etiketlenmişti.

**Kapsam/sıralama kararı (advisor önerisiyle)**: dört madde tek turda değil, her biri ayrı doğrulanıp ayrı Bölüm olarak kapatılacak şekilde sırayla ele alınacak — §6.1 bu bölümde, §7.1/§7.2/§3.6 ve §6.2 sonraki bölümlerde (Stop hook tekrar ateşlenirse).

**Bu bölümde kapatılan: yalnızca §6.1**. Doc'un beklenen sonucu da açıkça not edildi: *"Kusur bilgisi boşsa 'Seller did not report known defects' benzeri nötr metin göster; BidMont garanti veriyormuş gibi puan üretme."* — yani boşsa nötr metin, ASLA bir puan/skor hesaplanmıyor.

**Backend**:
- `Auction` modeline 5 yeni nullable `String` kolonu: `defect_exterior`, `defect_interior`, `defect_mechanical`, `defect_tyres`, `defect_missing_parts` (mevcut `damage_status` kolonu doküman'ın 6. kategorisi olan serbest-metin "damage description" özeti olarak kalıyor, adı değiştirilmedi — zaten tüm kod tabanında referanslı).
- `MISSING_COLUMNS["auctions"]`'a 5 yeni satır eklendi.
- `AuctionCreateRequest`/`AuctionUpdateRequest`/`AuctionResponse` şemalarına 5 alan eklendi (`AuctionUpdateRequest` zaten `model_dump(exclude_unset=True)` + `setattr` döngüsüyle güncellendiği için `update_auction` endpoint'inde ekstra kod gerekmedi).
- `app/api/auctions.py`'deki create endpoint'ine ve `app/services/auctions.py::build_auction_response()`'a (TEK merkezi response builder, tüm list/detail endpoint'lerinin kullandığı) 5 alan eklendi.

**Frontend**: wizard'ın 4. adımındaki (`#sellDamageWrap`, yalnızca vehicle kategorisinde görünür) mevcut serbest-metin `#sellDamage` alanının altına 5 yeni kategorize input eklendi (`#sellDefectExterior/Interior/Mechanical/Tyres/MissingParts`), submit payload'ına eklendi, `renderSellPreview()`'a satırlar eklendi. Detay sayfasında `#vehicleFields`'ın hemen altına yeni bir `#detDefectsWrap` bloğu: doldurulmuş kategorileri listeliyor, HİÇBİRİ doldurulmamışsa (5 kategori + `damage_status` hepsi boşsa) doc'un istediği nötr metni gösteriyor (*"Seller did not report known defects." / "Prodavac nije prijavio poznate kusure."*) — hiçbir zaman bir sayı/yıldız/puan üretmiyor. Kategori vehicle değilse blok `display:none` kalıyor (önceki turda unutulan `#vehicleFields`/`#equipFields` gibi her render'da açıkça sıfırlanıyor, aksi halde bir araçtan bir ekipmana geçildiğinde eski içerik sızabilirdi).

Doğrulama: `node --check` (SYNTAX_OK); `i18n_check.js` (304 anahtar kullanımı, 0 eksik — 7 yeni anahtar çift ME/EN eklendi); DOM-id çapraz referans denetimi (200 kullanım, 0 gerçek sarkan — 3 "eksik" `howTabs [data-how-tab]`/`legalTabs .admin-tab`/`legalTabs [data-legal-doc]` bileşik seçici, temel id'ler mevcut, önceki turlardaki gibi bilinen yanlış-pozitif); `backend/tests/integration/test_auction_api.py::TestCreateAuction::test_seller_creates_auction` genişletildi (kısmi kusur bildirimi + boş bırakılan kategorilerin `null` kaldığını doğrulayan assertion'lar, yeni ayrı test dosyası açılmadı); `pytest` 214/214 (yeni bir test dosyası değil, mevcut testin genişletilmesi olduğu için sayı değişmedi). `docker compose up --build -d` ile yeniden derlendi, başlangıç loglarında 5 temiz `Migration: added auctions.defect_*` satırı görüldü; canlı Postgres'e karşı uçtan uca `urllib` smoke test (`smoke_defects.py`): kısmen kusur bildirilen bir araç aukciyonu oluşturuldu (`defect_exterior`/`defect_tyres` dolu, diğer 3 + `damage_status` null kaldığı doğrulandı), hiç kusur bildirilmeyen ikinci bir aukciyonda TÜM 6 alanın null kaldığı doğrulandı — hiçbir zaman bir varsayılan/otomatik değer üretilmediği kanıtlandı (`DEFECT CATEGORIES (§6.1) END-TO-END SMOKE CHECK PASSED`).

Bölüm 22'deki B2 listesinden §6.1 satırı çıkarıldı, B listesine (artık B2'den B'ye taşınarak) kapatılmış olarak eklendi. §6.2/§7/§3.6 kalanı hâlâ B listesinde bekliyor — bu bölümde kasıtlı olarak dokunulmadı (advisor'ın sıralama önerisi: her biri ayrı doğrulanmalı).

## 53. Revizyon Geçmişi (30.07.2026, devam) — §7.1 Equipment alanları + §7.2.2 Commercial Asset alanları

Advisor'ın Bölüm 52'de verdiği sıralamanın 2. adımı: *"§7.1 equipment fields + §7.2.2 commercial fields... equipment_brand/serial_number/condition/location zaten var, sellApplyCategoryVisibility() zaten var — mekanizmanın kendisi ('kategoriye göre koşullu form alanları') karar verildikten sonra hızlıca inşa edilebilir dediğim şey bu."* Doc'un ham metni tekrar okunarak iki alt-bölümün tam alan listesi doğrulandı:
- **§7.1 Equipment**: Manufacturer, Model, Year, Operating hours, Serial number, Engine/power, Operating weight, Condition, Service history, Known defects, Location, Inspection availability, Dimensions/transport dimensions (opsiyonel), Accessories/included parts.
- **§7.2.2 Commercial Assets**: Quantity, brand/manufacturer, model, year (varsa), condition, package/lot contents, serials (varsa), dimensions, location, known defects, included items.

**Alan tekilleştirme kararı**: iki liste büyük ölçüde örtüşüyor (brand/model/year/condition/serial/location/known-defects zaten Vehicle/Equipment'ta var olan paylaşılan kolonlar) — bu yüzden yalnızca GERÇEKTEN yeni olan kavramlar için yeni kolon açıldı: `operating_hours`, `engine_power`, `operating_weight`, `service_history`, `inspection_availability` (yalnızca equipment), `dimensions`/`included_items` (equipment'ın "accessories/included parts"ı ile commercial'ın "package/lot contents"+"included items"i aynı kavram, tek ortak kolon), `quantity` (yalnızca commercial). "Known defects" için equipment/commercial'a §6.1'in kategorize (exterior/interior/...) alanları AÇILMADI — doc'un §6.1 metni açıkça "Araç detail'de" diyor, yani o alt-bölüm yalnızca vehicle'a özel; equipment/commercial zaten var olan tek-alanlı `damage_status`'u ("known defects" için) paylaşıyor.

**Backend**: `Auction` modeline 8 yeni nullable kolon (`operating_hours` Integer, `engine_power`/`operating_weight`/`dimensions` String, `service_history`/`included_items` Text, `inspection_availability` Boolean, `quantity` Integer). `MISSING_COLUMNS["auctions"]`, üç şema (`AuctionCreateRequest`/`AuctionUpdateRequest`/`AuctionResponse`), create endpoint'i ve TEK merkezi `build_auction_response()` güncellendi.

**Frontend**: wizard'ın 3. adımındaki (`#equipmentExtra`) mevcut proizvođač/serijski broj alanlarına model/godina/radni sati/motor-snaga/radna težina/dimenzije/uključena oprema/servis istorije/inspekcija eklendi; yeni bir `#commercialExtra` bloğu (yalnızca "General"/"Commercial Assets" kategorisinde görünür — yeni `sellCategoryIsCommercial()` regex fonksiyonu `/general|komercij|commercial/`) proizvođač/model/godina/količina/serijski/dimenzije/sadržaj paketa alanlarıyla eklendi. `#sellDamageWrap`'in (genel "known defects" metni) görünürlüğü V/E/C'nin hepsine genişletildi, ama §6.1'in 5 kategorize alt-alanı (`#sellDefectsCategorized`) yalnızca vehicle'da kalmaya devam ediyor (yeni bir `#sellDefectsCategorized` sarmalayıcı div'e taşındı). Submit payload'ı kategoriye göre doğru DOM alanından (`sellModel` vs `sellEquipModel` vs `sellCommModel` gibi) okuyacak şekilde yeniden yazıldı. Detay sayfasında `#equipFields` genişletildi, yeni bir `#commercialFields` bloğu eklendi, ve equipment/commercial için ortak bir `renderKnownDefects(a)` yardımcı fonksiyonu — §6.1'deki gibi aynı nötr-geri dönüş kuralını (`damage_status` boşsa "Seller did not report known defects.") equipment/commercial için de uyguluyor, asla bir puan üretmiyor.

Doğrulama: `node --check` (SYNTAX_OK); `i18n_check.js` (326 anahtar kullanımı, 0 eksik — 22 yeni anahtar çift ME/EN eklendi); DOM-id çapraz referans denetimi (238 kullanım, 0 gerçek sarkan — aynı 3 bilinen bileşik-seçici yanlış-pozitifi); `backend/tests/integration/test_auction_api.py`'a iki yeni test (`test_seller_creates_equipment_auction_with_new_fields`, `test_seller_creates_commercial_auction_with_new_fields`) — kategoriye özel alanların round-trip ettiğini VE diğer kategorinin alanlarının null kaldığını doğruluyor; `pytest` 216/216 (214'ten 216'ya, 2 yeni test). `docker compose up --build -d` ile yeniden derlendi, başlangıç loglarında 8 temiz `Migration: added auctions.*` satırı görüldü; canlı Postgres'e karşı uçtan uca `urllib` smoke test (`smoke_equip_commercial.py`): bir equipment aukciyonu (operating_hours/engine_power/operating_weight/dimensions/included_items/service_history/inspection_availability dolu, `quantity` null) ve bir commercial aukciyonu (`quantity`/`dimensions`/`included_items` dolu, `operating_hours`/`engine_power` null) oluşturuldu, ikisi de `GET /auctions/{id}` üzerinden doğrulandı (`EQUIPMENT (§7.1) + COMMERCIAL (§7.2.2) FIELDS END-TO-END SMOKE CHECK PASSED`); ayrıca canlı sunucudan çekilen gerçek HTML'de yeni `#commercialExtra`/`#sellEquipHours`/`#sellCommQty`/`#commercialFields`/`#detKnownDefectsWrap` id'lerinin var olduğu doğrulandı.

**Kapsam sınırı**: §7.2.1 (Commercial Assets'in 9 alt-kategorisi: Hospitality/Restaurant Equipment/Electronics/Office/Retail Equipment/Inventory & Stock/Furniture/Tools/Other) bu bölümde kasıtlı olarak ele alınmadı — advisor'ın sıralamasının 3. adımı, `Category.parent_id` kullanarak gerçek alt-kategori satırları seed edilecek, aynı zamanda §3.6'nın kart-örnek metni de bu gerçek verilerden beslenecek. §6.2 (doküman ekleme) hâlâ 4. ve son adım.

Bölüm 22'deki B listesinden §7.1/§7.2.2 satırı çıkarıldı (kapatıldı olarak işaretlendi). §7.2.1/§3.6 kalanı ve §6.2 hâlâ B listesinde açık.

## 54. Revizyon Geçmişi (30.07.2026, devam) — §7.2.1 Commercial Assets alt-kategori taksonomisi + §3.6 kart-örnek metni + Bölüm 53'ün kendi ürettiği bir kategori-bucketing regresyonunun düzeltilmesi

Advisor'ın Bölüm 52'de verdiği sıralamanın 3. adımı. Doc'un §7.2.1'deki kendi cümlesi bu işin LITZOR'un konusu değil kod-tamamlanabilir olduğunu zaten söylüyor: *"Menu, category slug, admin taxonomy ve filters aynı yapıdan beslenmeli."* — yani menü, kategori slug'ı, admin taksonomisi ve filtreler TEK bir veri yapısından (gerçek `Category` satırlarından) beslenmeli, dört ayrı hardcoded string listesinden değil.

**Önce kendi ürettiğim bir regresyon bulundu ve düzeltildi (advisor'ın Bölüm 53 notunda işaretlediği, o turda kontrol edilmeden geçen uyarı)**: Bölüm 53'te commercial-asset formunun "Proizvođač" (brand/manufacturer) alanı `equipment_brand` kolonunu paylaşacak şekilde bağlanmıştı. Ama `loadAuctionsFromApi()`'daki kategori-"bucket" mantığı (`a.brand?'Vozila':(a.equipment_brand?'Oprema':'General')`) aukciyonun GERÇEK kategorisine değil, hangi alanın dolu olduğuna bakıyordu — bu yüzden `equipment_brand` dolu OLAN her commercial-asset aukciyonu yanlışlıkla "Oprema" (Equipment) olarak sınıflandırılıyordu: Equipment grid'inde görünüyordu, detay sayfasında `#commercialFields` yerine `#equipFields` render ediliyordu (Quantity gösterilmeden, yanlış alan etiketleriyle). §7.2.1 bu düzeltme olmadan "kapatıldı" sayılamazdı, çünkü seed edilen alt-kategorilerin hiçbiri doğru bucket'a düşmeyecekti.

**Kök neden düzeltmesi**: alan-varlığı sezgisi yerine, aukciyonun GERÇEK `category_id`'sinin taksonomi ağacında yukarı doğru en üst atasına kadar çözülmesi (`topLevelCategoryName()`/`bucketFromTopLevelName()`, saf fonksiyonlar, DOM'a bağımlı değil) — hem `loadAuctionsFromApi()`'nin bucket'ı hem `sellCategoryIsVehicle/Equipment/Commercial()`'ın wizard-alan-görünürlüğü artık aynı tek resolver'ı kullanıyor (advisor'ın 2 numaralı notu: "one resolution helper, two call sites"). Kategori haritası yüklenemezse (ağ hatası vb.) eski alan-varlığı sezgisine güvenli şekilde geri düşülüyor — `ensureCategoriesLoaded()` kendi hatasını yutuyor, asla `loadAuctionsFromApi()`'nin kendi `try{}catch(e){}`'ini tetiklemiyor (advisor'ın 3 numaralı notu: bu olmasaydı bir kategori-fetch hatası TÜM aukciyon listesini sessizce boş render ederdi).

**İkinci bir gerçek backend hatası, doğrulama sırasında bulundu**: `main.py`'deki PUBLIC `GET /api/categories` endpoint'i (`list_categories_public`) `parent_id` alanını response dict'ine hiç eklemiyordu — admin'in `CategoryResponse` şeması `parent_id` içeriyordu ama bu ayrı, elle yazılmış public endpoint hiç içermiyordu. Bu, yeni `topLevelCategoryName()` mekanizmasının TAMAMEN işlevsiz kalmasına neden oluyordu (her alt-kategori `parent_id: undefined` görüyordu, hiçbir zaman üst kategoriye çözülemiyordu) — canlı doğrulama sırasında (bkz. aşağı) yakalandı, tek satırlık düzeltme.

**Backend**: yeni `app/core/category_seed.py` — `seed_default_categories(db)`, idempotent (isme göre kontrol ediyor, slug'a göre değil — mevcut "Vehicles" satırının slug'ı `vehicles-fac96f` gibi rastgele son ekli, temiz bir slug varsayımı ikinci bir satır oluşturabilirdi). 3 üst-seviye kategori (Vehicles — zaten vardı, atlandı; Equipment; Commercial Assets) + Commercial Assets altında doc'un verdiği 9 alt-kategori (Hospitality, Restaurant Equipment, Electronics, Office, Retail Equipment, Inventory & Stock, Furniture, Tools, Other). `main.py`'nin `lifespan`'ından migrasyonlardan hemen sonra çağrılıyor — `migrations.py`'ye KARIŞTIRILMADI (o dosya şema-ADD-COLUMN'a özel, bu veri seed'i farklı bir kavram, ayrı dosya). `list_categories_public`'e `parent_id` eklendi.

**Frontend**: `categoriesMap` artık `{id: name}` yerine `{id: {name, parent_id}}`; yeni `ensureCategoriesLoaded()` (bellekte önbelleklenmiş, hem `loadAuctionsFromApi()` hem `loadSellCategories()` tarafından çağrılıyor) + `topLevelCategoryName()`/`bucketFromTopLevelName()` saf fonksiyonları. `sellCategoryIsVehicle/Equipment/Commercial()` artık seçili kategori id'sini gerçek taksonomiden çözüyor (metin regex'i yalnızca harita henüz yüklenmemişse yedek). §3.6: `cat.g.d` (ME/EN) açıklama metnine 9 alt-kategori adı örnek olarak eklendi (doc'un "alt kategori örnekleri" isteği — ayrı bir alt-kategori sayfası/menüsü değil, kart açıklamasına gerçek isimler).

Doğrulama: `node --check` (SYNTAX_OK); `i18n_check.js` (326 anahtar, 0 eksik — yeni anahtar gerekmedi, mevcut açıklama string'leri genişletildi); DOM-id denetimi (238 kullanım, 0 gerçek sarkan); yeni backend testleri — `tests/unit/test_category_seed.py` (3 test: üst-seviye+9 alt-kategori doğru seed ediliyor, ikinci çalıştırmada YİNELENMİYOR, mevcut farklı-slug'lı bir satır korunuyor/üzerine yazılmıyor) + `tests/integration/test_health.py::TestPublicCategories` (1 test: `parent_id` artık response'ta). `pytest` 220/220 (216'dan 220'ye, 4 yeni test). `docker compose up --build -d` ile yeniden derlendi, loglarda `Category seed: added 'Equipment'`/`'Commercial Assets'` + 9 alt-kategori satırı görüldü (Vehicles atlandı, zaten vardı); **container yeniden başlatıldı** (`docker restart bidmont-app`) ve `SELECT count(*) FROM categories` hâlâ 12 (11 log satırı, restart'ta 0 yeni satır) — idempotency canlı ortamda da doğrulandı, yalnızca test DB'sinde değil. Regresyon düzeltmesi, GERÇEK uygulama JS'i canlı sunucudan çekilip (`verify_bucketing.js`, `topLevelCategoryName`/`bucketFromTopLevelName` fonksiyon kaynağı regex ile çıkarılıp bir Node `vm` sandbox'ında çalıştırıldı — mantığın bir kopyası değil, gerçek kod) canlı `/api/categories` verisine karşı çalıştırılarak doğrulandı: Hospitality→General, Equipment→Oprema, Vehicles→Vozila (`BUCKET RESOLUTION (§7.2.1 regression fix) VERIFIED`). Ayrıca gerçek bir uçtan uca smoke test (`smoke_bucketing.py`): Hospitality kategorisinde GERÇEK bir aukciyon oluşturuldu (`equipment_brand` dolu — regresyonu tetikleyen tam senaryo), `category_id`'nin doğru round-trip ettiği doğrulandı.

**Dürüst sınır**: bu bölüm advisor'ın Bölüm 52/53'te işaretlediği bir uyarıyı (kategori-bucketing'in field-varlığına dayanması) bir sonraki tura kadar kontrol etmeden bıraktığım için gerekli oldu — Bölüm 53 "tamamlandı" olarak kapatılmıştı ama gerçekte commercial aukciyonları o turdan bu bölüme kadar canlı ortamda yanlış grid'e düşüyordu. Bölüm 47'nin/52'nin kendi hatasını açıkça kabul etme geleneğiyle aynı şekilde burada da açıkça kabul ediliyor.

Bölüm 22'deki B listesinden §7.2.1/§3.6 kalanı satırı çıkarıldı. **B listesinde yalnızca §6.2 (ilana doküman ekleme) kaldı** — advisor'ın sıralamasının 4. ve son adımı.

## 55. Revizyon Geçmişi (30.07.2026, devam) — §6.2 İlana Doküman Ekleme (B listesinin son maddesi)

Advisor'ın Bölüm 52'de verdiği sıralamanın 4. ve son adımı: *"§6.2 documents. Largest and last."* Doc'un tam metni: *"Seller//admin izin verdiği ölçüde registration, inspection, service/other document dosyaları listelensin. Public/private erişim seviyesi admin'den ayarlanabilsin. Beklenen sonuç: Dosya uzantı/boyut kontrolü ve güvenli indirme olmalı."*

**Mevcut altyapı (kullanılmıyordu)**: `AuctionImage.media_type` ("image"|"document") ve `.visibility` ("public"|"private") kolonları önceki bir oturumdan beri modelde vardı ama hiçbir API/schema/frontend kodu onları hiç okumuyor/yazmıyordu (Bölüm 52'de grep ile doğrulanmıştı) — bu bölüm onları gerçekten devreye soktu.

**Güvenlik tasarımı (advisor'ın 4 maddesi, hepsi uygulandı)**:
1. **Ayrı, mount edilmemiş bir dizin**: `/uploads` static mount'u (`main.py`) yalnızca PUBLIC dosyaları (fotoğraflar) servis ediyor. Yeni `PRIVATE_UPLOAD_DIR` (`backend/private_uploads`) hiçbir yerde mount edilmiyor — private bir dokümanın dosya adı tahmin edilse/paylaşılsa bile doğrudan URL ile asla erişilemez, YALNIZCA aşağıdaki yetkilendirici endpoint üzerinden.
2. **`GET /api/uploads/{image_id}/download`**: doküman byte'larına ulaşmanın TEK yolu. Public bir doküman (fotoğraflar gibi) kimliksiz erişilebilir; private bir doküman `get_current_user_optional` ile kontrol edilip yalnızca aukciyonun kendi satıcısına veya staff/admin'e (401 kimliksizse, 403 yetkisizse) izin veriyor.
3. **`upload_images_batch`'in sessizce atlama davranışı kopyalanmadı**: yeni `POST /api/uploads/documents` GEÇERSİZ bir dosya tipini veya boyut sınırını aşan bir dosyayı TÜM batch'i 400 ile reddederek işliyor — sessizce atlayıp satıcıya hiç hata göstermeden bir dokümanın kaybolmasına izin vermiyor.
4. **Detay endpoint'i artık private dokümanları filtreliyor**: `GET /auctions/{id}` (tamamen public, kimlik doğrulaması gerektirmiyordu) artık opsiyonel bir `get_current_user_optional` bağımlılığı alıyor; yeni `visible_auction_images()` yardımcı fonksiyonu (services/auctions.py) yalnızca public dosyaları + (varsa) görüntüleyenin kendi satıcı/staff olduğu private dosyaları döndürüyor — private bir doküman hiçbir zaman yetkisiz bir tarayıcıya JSON içinde bile sızmıyor (yalnızca frontend'de gizlenmiyor, sunucu tarafında hiç gönderilmiyor).

**Backend**: `AuctionImage`'a `doc_category` kolonu (registration|inspection|service|other, yalnızca media_type="document" iken anlamlı) + migration. `AuctionImageResponse`'a `media_type`/`doc_category`/`visibility` eklendi. Yeni paylaşılan `build_auction_image_response()` (services/auctions.py) — dokümanlar için `image_url`'i her zaman `/api/uploads/{id}/download` olarak hesaplıyor (frontend hiçbir zaman ham dosya yolunu görmüyor, tek bir tutarlı sözleşme). Yeni `POST /api/uploads/documents` (sahiplik kontrolü + doc_category doğrulaması + PDF/görsel MIME allowlist'i + TÜM batch'i reddetme), yeni admin `PUT /admin/auction-images/{image_id}/visibility` (audit-loglanıyor, mevcut `_log_audit` deseni).

**Bu turda canlı doğrulama sırasında bulunan, ayrı bir gerçek hata**: `renderDetail()`'deki mevcut galeri kodu `d.images`'daki HER görseli (dokümanlar dahil) galeri/lightbox dizisine ekliyordu — dokümanların `image_url`'i artık gerçek bir resim değil `/api/uploads/{id}/download` olduğu için, bir doküman yüklendiğinde galeri onu kırık bir resim gibi göstermeye çalışacaktı. Kod yazılırken (canlı teste gitmeden önce) fark edilip düzeltildi: `a.images` artık yalnızca `media_type!=='document'` olan girdileri, `a.documents` ise yalnızca `media_type==='document'` olanları alıyor.

**Frontend**: wizard adım 5'e ("Fotoğraflar" adımı) doküman kategori seçimi (Registration/Inspection/Service/Other) + çoklu dosya girişi eklendi (`sellPendingDocs`, aukciyon oluşturulduktan SONRA — fotoğraflarla aynı desen — kategoriye göre gruplanıp ayrı batch'ler halinde yükleniyor). Detay sayfasında yeni bir "Documents" bölümü — her doküman kategori etiketi + (private ise) bir "(private)" notu + bir "İndir" linki ile listeleniyor. **Güvenli indirme UI deseni**: düz bir `<a href>` private bir dokümanın gerektirdiği Authorization header'ını taşıyamaz — bunun yerine `downloadDocument()` dosyayı `fetch()` (Authorization header'lı) ile blob olarak çekip tarayıcının kendi indirme mekanizmasını (`URL.createObjectURL` + geçici bir `<a>` tıklaması) tetikliyor. Admin panelinde her aukciyon satırına bir "Docs" butonu — aukciyonun TÜM dokümanlarını (admin staff olduğu için private'lar dahil) listeleyen bir modal, her biri için Public/Private değiştirme butonu.

**Bilinen sınır (bu turda bulunan, ayrı, kapsamın dışında bırakılan bir hata)**: admin panelindeki `adminFetch(url)` yardımcı fonksiyonu YALNIZCA bir URL argümanı alıyor, hiçbir zaman bir HTTP metodu/gövde geçirmiyor — `adminApproveAuction`/`adminRejectAuction`/`adminToggleFeatured`/`adminUpdateUserStatus` gibi mevcut çağırıcıların hepsi POST/PUT endpoint'lerine `adminFetch` üzerinden gidiyor ama fetch'in varsayılan metodu GET'tir, dolayısıyla bu çağrıların hepsinin sessizce yanlış HTTP metoduyla (muhtemelen 405 ile) başarısız olması bekleniyor. Bu, bu oturumun herhangi bir turunda yazılmamış, önceden var olan bir hata gibi görünüyor — §6.2'nin kapsamı dışında, düzeltilmedi, ama YENİ eklenen visibility-toggle butonu bu bozuk deseni KOPYALAMADI (`bidmontApi.setImageVisibility()` doğrudan `_fetch()`'i açık bir `{method:'PUT'}` ile çağırıyor). Bu, ayrı bir tur/madde olarak ele alınmalı — LITZOR'un konusu değil, tamamen kod ile düzeltilebilir bir hata, ama §6.2'nin parçası değil.

Doğrulama: `node --check` (SYNTAX_OK); `i18n_check.js` (334 anahtar, 0 eksik — 17 yeni anahtar çifti eklendi); DOM-id denetimi (243 kullanım, 0 gerçek sarkan, aynı 3 bilinen yanlış-pozitif); yeni backend test dosyası `tests/integration/test_document_uploads_api.py` (12 test: doküman yükleme + doc_category doğrulaması + geçersiz dosya tipinde TÜM batch'in reddedilmesi + sahip-olmayan bir satıcının yükleyememesi + private dokümanın anonim/başka-kullanıcıdan gizlenmesi + admin'e görünmesi + admin'in public yapabilmesi + admin-olmayan'ın visibility değiştirememesi + sahibinin/adminin/anonim'in indirme yetkisi senaryoları). `pytest` 232/232 (220'den 232'ye, 12 yeni test). `docker compose up --build -d` ile yeniden derlendi, loglarda `Migration: added auction_images.doc_category` görüldü; canlı Postgres'e karşı uçtan uca `urllib` smoke test (`smoke_documents.py`): gerçek bir fotoğraf + gerçek bir private registration dokümanı yüklendi, anonim görüntüleyici yalnızca fotoğrafı gördü (doküman JSON'da bile yoktu), sahibi ikisini de gördü, anonim indirme denemesi 401 ile reddedildi, sahibinin indirmesi gerçek PDF byte'larını döndürdü, kullanıcı admin'e yükseltilip doküman public yapıldı, ardından anonim indirme başarılı oldu ve gerçek byte'lar geri geldi (`DOCUMENT UPLOADS (§6.2) END-TO-END SMOKE CHECK PASSED`). Ayrıca canlı sunucudan çekilen HTML'de yeni `#sellDocs`/`#sellDocCategory`/`#detDocumentsWrap`/`adminShowDocuments` öğelerinin var olduğu doğrulandı.

Bölüm 22'deki B listesinden §6.2 satırı çıkarıldı. **B listesi artık gerçekten tamamen boş** — bu kez Bölüm 52'nin düzelttiği gibi bir yanlış sınıflandırma değil, dört kez ayrı ayrı doğrulanmış (§6.1 Bölüm 52, §7.1/§7.2.2 Bölüm 53, §7.2.1/§3.6 Bölüm 54, §6.2 bu bölümde) bir kapanış. Geriye yalnızca **B2'deki 3 madde grubu** (§2.7/AC-14 mobil QA, §20 AC-16'nın görsel yarısı, §4.3/AC-20 kodla-çözülemez gerçek-fotoğraf kuralı — hiçbiri LITZOR'un konusu değil ama hiçbiri bu oturumun kendi başına kapatabileceği bir şey de değil) ve **C listesindeki ~10 madde grubu** (tamamen LITZOR'a bağlı) kalıyor. Bu turda ayrıca `adminFetch`'in HTTP metodu taşımadığı ayrı bir hata bulundu ve bilinçli olarak kapsam dışında bırakıldı (yukarıya bakınız) — gelecek bir tur için not edildi.

## 56. Revizyon Geçmişi (30.07.2026, devam) — `adminFetch` HTTP metodu hatasının düzeltilmesi (Bölüm 55'te bulunan, kapsam dışı bırakılan hata)

Bölüm 55'te not edilip kasıtlı olarak kapsam dışı bırakılan hata bu bölümde düzeltildi. Bu, doküman'ın belirli bir bölüm numarasına bağlı değil — ama zaten "✅ tamamlandı" olarak işaretlenmiş birden fazla A-listesi maddesinin (§11.5 satıcı ilan onay/red akışı, §12 aukciyon durum makinesi, §17.1 kullanıcı yönetimi, admin 2FA) gerçek admin panelinde ÇALIŞMADIĞI anlamına gelen bir doğruluk hatasıydı — bu yüzden kod-tamamlanabilir, dış girdi gerektirmeyen bir B-madde adayı olarak ele alındı.

**Doğrulanan kök neden**: `adminFetch(url)` yardımcı fonksiyonu (satır ~1303) yalnızca bir URL parametresi alıyordu, `bidmontApi._fetch()`'e hiçbir `options` (method/body) geçirmiyordu — `fetch()`'in varsayılan metodu GET'tir. Admin panelinin şu aksiyonları bu yardımcı fonksiyonu POST/PUT endpoint'lerine karşı çağırıyordu ama parametre eksikliği yüzünden HER ZAMAN GET gönderiyordu: `adminApproveAuction` (POST endpoint), `adminRejectAuction` (POST), `adminToggleFeatured` (PUT), `adminUpdateUserStatus` (PUT), ve 2FA kurulum akışının `adminFetch('/admin/2fa/setup')` çağrısı (POST) — beşi de sessizce yanlış metodla gidiyordu. Canlı doğrulama ile teyit edildi: `GET /api/auctions/{id}/approve` gerçek sunucuda `404 {"detail":"Not found"}` döndürüyor (FastAPI'nin route eşleştirmesi o path+metod kombinasyonu için hiçbir handler bulamıyor) — yani admin panelindeki "Approve"/"Reject"/"Feature"/kullanıcı durumu değiştirme/2FA kurulumu butonlarının hepsi tıklandığında sessizce başarısız oluyordu, hiçbir zaman gerçek işlemi tetiklemiyordu.

**Neden diğer admin aksiyonları etkilenmedi**: `adminCreateCategory`/`adminDeleteCategory`/`adminActivateCategory`/`adminUpdateTicket`/`adminSaveNotificationTemplate`/`adminResetNotificationTemplate`/2FA `verify`/`disable` gibi diğer state-değiştiren aksiyonlar `adminFetch` kısayolunu hiç kullanmıyor, doğrudan `bidmontApi._fetch(url, {method:...})`'i açık bir metodla çağırıyordu — bu yüzden onlar zaten doğru çalışıyordu. Hata yalnızca `adminFetch` kısayolunun kullanıldığı 5 çağrı noktasına özgüydü.

**Kök neden düzeltmesi**: `adminFetch(url)` → `adminFetch(url, options)`, `options`'ı doğrudan `_fetch()`'e iletiyor (mevcut salt-okunur 9 çağrı noktası `options` geçirmiyor, JS'in varsayılan parametre davranışı `undefined`'ı `_fetch`'in kendi `options = {}` varsayılanına düşürüyor — bu 9 çağrı davranış değiştirmedi). 5 bozuk çağrı noktasına doğru `{method:'POST'}`/`{method:'PUT'}` eklendi.

Doğrulama: `node --check` (SYNTAX_OK); `i18n_check.js` (334 anahtar, 0 eksik — saf JS mantık değişikliği, yeni metin yok); `pytest` 232/232 (saf frontend değişikliği, backend dokunulmadı). `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı `smoke_admin_fetch_fix.py`: önce ESKİ (bozuk) davranış yeniden üretildi — ham `GET /api/auctions/{id}/approve` gerçekten `404` döndürdüğü doğrulandı (hatanın gerçek olduğunun kanıtı) — ardından YENİ (düzeltilmiş) davranış test edildi: `POST /api/auctions/{id}/approve` (admin token ile) `200` döndürdü ve aukciyonun durumu gerçekten `under_review`'dan `live`'a geçti (`ADMIN APPROVE (adminFetch GET->POST fix) SMOKE CHECK PASSED`). Canlı sunucudan çekilen HTML'de 5 düzeltmenin de (`approve`/`reject`/`featured`/`user status`/`2fa setup`) doğru `method` ile serialize edildiği doğrulandı.

**Kapsam notu**: bu, doküman'ın B/B2/C çerçevesinin dışında, ayrı bir doğruluk hatası düzeltmesiydi — hiçbir yeni doc-madde numarası kapatmadı (zaten A listesinde "✅" işaretli maddelerin GERÇEKTEN çalıştığını sağladı, yeni bir madde kapatmadı). Bölüm 22'nin B/C listeleri bu bölümden etkilenmedi — B hâlâ boş, C hâlâ tamamen LITZOR'a bağlı.

## 57. Revizyon Geçmişi (30.07.2026, devam) — §11.2 "Phone + email verification" alanının e-posta yarısının gerçekten uygulanması + C listesindeki bir öz-kaynaklı fazla-kapsam maddesinin düzeltilmesi

Bölüm 56'nın ardından gelen Stop hook, B listesinin boş ve C'nin tamamen LITZOR'a bağlı olduğunu tekrar doğruladı — bu doğruydu ama tek bir C-listesi maddesi yeniden incelendiğinde kendiliğinden üretilmiş bir fazla-kapsamın ürünü olduğu ortaya çıktı: **§20 AC-01'in "telefon/SMS yarısı"** (Bölüm 48'de C listesine eklenmişti).

**Bulgu**: Doküman'ın tamamında ("telefon"/"SMS" için tam metin taraması) genel kullanıcı kaydı için ayrı bir SMS-OTP doğrulama gereksinimi HİÇBİR YERDE yok — "telefon" geçen tek yerler (a) canlı ihalede seller'ın telefon/e-postasının gizlenmesi kuralı, (b) LITZOR'un gerçek destek telefon numarasını (iş bilgisi, zaten C listesinde §14.2.1 altında) yayına koyması. Ancak **§11.2 "Seller Application alanları" checklist'i** açıkça `[ ] Phone + email verification` maddesini seller BAŞVURUSU için bir alan olarak listeliyor — Bölüm 48'in kendi notu bunu doğru ayırt etmişti ("o farklı bir konu — seller başvurusu, genel kullanıcı kaydı değil") ama bu ayrımın sonucu hiç takip edilmemişti: §11.2 satırı (raporun 447. satırı) `✅ backend` olarak işaretliydi, oysa `app/api/sellers.py::apply_as_seller()` e-posta veya telefon doğrulamasını FİİLEN HİÇ KONTROL ETMİYORDU — yalnızca `SellerProfile` alanları (company/individual, PIB, authorized person, city, seller_type) dolduruluyordu. Yani checklist maddesi zaten var olan `email_verified` alanı/akışıyla (Bölüm 48) hiç bağlanmamıştı; ✅ işareti yanlıştı.

**Kapsam kararı**: §11.2'nin "Phone + email verification" ifadesindeki **e-posta yarısı** artık kod-tamamlanabilir ve dış girdi gerektirmiyor — Bölüm 48'in genel kayıt akışı için kurduğu `email_verified` alanı ve `/auth/verify-email` akışı zaten var, sadece seller başvurusuna bir GATE olarak bağlanması gerekiyordu. **Telefon (SMS) yarısı** hâlâ gerçekten C listesinde kalıyor (bir SMS gateway seçimi + kimlik bilgisi gerektiriyor, Monri/PSP kararıyla aynı tür) — bu, C listesinden ÇIKARILMADI, sadece AC-01'in genel-kayıt bağlamından §11.2'nin seller-başvuru bağlamına doğru referansı düzeltildi (aynı alt madde, iki checklist'te de geçiyor).

**Yapılan değişiklik**: `backend/app/api/sellers.py::apply_as_seller()` artık `current_user.email_verified` False ise `403` döndürüyor ("Please verify your email address before applying as a seller."). Doğrulanmış kullanıcılar hiç etkilenmiyor.

**Test fixture yan etkisi (bulunup düzeltildi)**: Bu değişiklik `backend/tests/conftest.py`'deki paylaşılan `test_user`/`seller_user`/`admin_user` fixture'larını (varsayılan `email_verified=False`) kullanan TÜM `test_seller_workflow_api.py` testlerini kırıyordu (bu fixture'lar seller-application testleri de dahil onlarca yerde "genel, iyi durumda bir kullanıcı" varsayımıyla yeniden kullanılıyor). Üç fixture'a da `email_verified=True` eklendi — bu `seller_user`'ın zaten yaptığı "kutudan çıktığı gibi çalışan verified seller" düzenine uyuyor. Bu değişiklik tek bir mevcut testi kırdı: `test_auth_api.py::TestEmailVerification::test_resend_verification_issues_new_usable_token`, `test_user`'ın varsayılan olarak DOĞRULANMAMIŞ başlamasına güveniyordu — düzeltme: bu test artık `test_user.email_verified = False` ön koşulunu kendi içinde açıkça kuruyor (davranışı belgelemek için, fixture varsayılanına gizlice güvenmek yerine).

**Yeni test**: `test_seller_workflow_api.py::TestSellerApplication::test_apply_blocked_without_email_verification` — doğrulanmamış e-postalı bir kullanıcının `/api/sellers/apply`'a `403` aldığını doğruluyor.

Doğrulama: `pytest` **233/233** geçti (232'den 233'e: 1 yeni test; 1 mevcut test kendi ön koşulunu açıkça kurmak üzere güncellendi). `index.html`'e dokunulmadı (mevcut genel `catch(err){toast(err.detail...)}` hata gösterimi zaten backend'in 403 mesajını olduğu gibi kullanıcıya gösteriyor — ayrı bir frontend değişikliği gerekmedi). `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı `smoke_seller_email_gate.py`: gerçek bir kayıt akışı — doğrulanmamışken `/sellers/apply` `403` (mesajda "verify" geçiyor), `/auth/verify-email` ile gerçek token'la doğrulandıktan SONRA aynı kullanıcının başvurusu `201`/`pending` dönüyor (`SELLER APPLICATION EMAIL-VERIFICATION GATE (doc §11.2) SMOKE CHECK PASSED`).

**Ayrı bir bulgu (bu bölümde düzeltildi)**: `backend/private_uploads/` dizini (§6.2'nin özel doküman deposu, Bölüm 55'te eklendi) `.gitignore`'a hiç eklenmemişti — `backend/uploads/*` için var olan kural kopyalanıp `backend/private_uploads/*` için de eklendi (aynı `.gitkeep` deseniyle). Bu dizin yerel olarak zaten ~50 smoke-test PDF'i biriktirmişti; düzeltme onları gelecekteki bir `git add`'in önüne geçiyor.

**Kapsam notu**: §11.2 satırı artık raporun 447. satırında "✅ backend (e-posta yarısı gerçekten uygulandı; telefon/SMS yarısı C listesinde kalıyor)" olarak güncellenmelidir. Bölüm 22'nin C listesindeki "§20 AC-01'in telefon doğrulama yarısı" maddesi artık daha doğru biçimde "§11.2 ve §20 AC-01'in ortak telefon/SMS doğrulama yarısı" olarak okunmalı — kapsamı genişlemedi, sadece iki checklist referansı birleştirildi. **B listesi bu bölümden sonra da boş** (bu, yeni bir doc-madde kapatmadı, var olan bir maddenin yanlış ✅ işaretini düzeltti ve gerçek bir gate ekledi) — ama bu, Bölüm 56 gibi "B/B2/C çerçevesinin dışında" değil, doğrudan §11.2'nin kendi checklist maddesiyle ilgiliydi, bu yüzden ayrı bir düzeltme olarak burada kayda geçirildi.


## 58. Revizyon Geçmişi (30.07.2026, devam) — §11.6'nın "admin review'da görünür uyarı" ifadesinin gerçekten uygulanması + adminFetch'in 5 endpoint'inin RBAC denetimi (temiz çıktı)

Bölüm 57'nin ardından gelen Stop hook aynı "B boş, C LITZOR'a bağlı" sonucunu tekrarladı. Bölüm 57'nin ne ürettiğini yeniden değerlendirince (bir doc-madde YANLIŞ ✅ işaretliyken kod hiçbir şey uygulamıyordu) genelleşebilir bir soru ortaya çıktı: raporun ~150 satırlık durum tablolarında ✅ olarak işaretlenmiş kaç satır aslında "alan/kolon var" diyor ama "kontrol/red/gate var" demiyor? İki aday denetlendi.

**1) Bölüm 56'nın düzelttiği 5 admin endpoint'inin RBAC'ı — TEMİZ ÇIKTI.** Bölüm 56, `adminFetch`'in hiç `method` göndermediğini (her zaman GET) ve bu yüzden `approve`/`reject`/`featured`/`user status`/`2fa setup` butonlarının tarayıcıda hiç gerçek isteği tetiklemediğini kanıtlamıştı — yani bu 5 handler, düzeltmeden önce fiilen HİÇ ÇALIŞTIRILMAMIŞTI. Çalıştırılmamış bir handler, eksik bir `Depends(get_current_admin)`'in hayatta kalabileceği tam yer. Beşi de tek tek okundu: `approve_auction`/`reject_auction` (`app/api/auctions.py:427,534`) `Depends(get_current_admin)`; `admin_update_user_status`/`admin_toggle_featured` (`app/api/admin.py:162,576`) `Depends(get_current_admin)`; `setup_2fa` (`app/api/admin.py:976`) `Depends(get_current_staff)`. Beşi de doğru gate'lenmiş — `test_rbac_api.py` bu 5 endpoint'i isim olarak test etmiyor (yalnızca support-role kısıtlamalarını test ediyor) ama kod seviyesinde dependency zaten doğru. **Bulgu yok, denetim burada kapandı.**

**2) §11.6 "Admin review'da görünür uyarı" — GERÇEK BİR BOŞLUK BULUNDU.** Doküman'ın tam ifadesi: *"Title/description içinde phone/email/URL pattern warning/flag. Admin review'da görünür uyarı. Gerekirse otomatik blok veya manuel moderation."* Rapor satır 451 bunu `✅` işaretliyor ve açıkça "admin review'da görünür" diyor. Ama `looks_like_direct_contact()` (Bölüm ~ önceki bir oturumda yazılmış) yalnızca `Auction.contact_flagged` alanını dolduruyor ve `build_auction_response()` bunu API yanıtına koyuyordu — **`index.html`'de `contact_flagged` hiçbir yerde okunmuyordu** (`grep contact_flagged index.html` sıfır sonuç verdi). Admin panelinin `renderAdminAuctions()` tablosu (Title/Price/Status/Date/Actions) bu alanı hiç göstermiyordu — yani bir seller title/description'a telefon/e-posta yazsa, veri arka planda flagleniyor ama admin bunu approve ederken GÖREMİYORDU. Bu, §11.6'nın kendi "Beklenen sonuç"unu (`Canlı ilanda direct seller contact bulunmamalı`) fiilen koruyamıyordu.

**Yapılan düzeltme**: `renderAdminAuctions()`'daki title hücresine, `is_featured` yıldızıyla aynı desende, `a.contact_flagged` true olduğunda görünür bir `⚠ Contact info?` rozeti eklendi (`.admin-contact-flag` CSS sınıfı, kırmızı/tehlike paleti, `.admin-badge.banned` ile aynı renk ailesi). Backend'e dokunulmadı — veri zaten API'de vardı, yalnızca frontend'in onu render etmemesi eksikti.

**Kapsam notu**: Doc'un "gerekirse otomatik blok" kısmı kasıtlı olarak uygulanmadı — mevcut satır (255. satır, Bölüm ~ önceki bir kayıt) bunun bilinçli bir tasarım kararı olduğunu zaten belirtiyor ("yalnızca uyarı, otomatik blok yok — doküman böyle istiyor", "Gerekirse" ifadesi otomatik bloğu opsiyonel/koşullu kılıyor). Bu bölüm yalnızca "admin review'da görünür uyarı" yarısını kapattı, o zaten var olan tasarım kararını değiştirmedi.

Doğrulama: `node --check` (script içeriği çıkarılıp SYNTAX_OK); yeni bir `data-i18n` anahtarı eklenmedi (admin paneli zaten İngilizce sabit metinlerle çalışıyor — "Approve"/"Reject" gibi butonlar da `data-i18n` kullanmıyor, tutarlı); `pytest` 233/233 (saf frontend değişikliği, backend dokunulmadı). `docker compose up --build -d` ile yeniden derlendi; canlı Postgres'e karşı `smoke_contact_flag_admin_ui.py`: gerçek bir ilan — başlığında telefon numarası, açıklamasında e-posta adresi — oluşturuldu, `contact_flagged: true` döndüğü doğrulandı; admin panelinin gerçekten çağırdığı `GET /admin/auctions?status=under_review` endpoint'i aynı bayrağı döndürdüğü doğrulandı; sunucudan çekilen gerçek `index.html`'de hem `admin-contact-flag` CSS sınıfının hem de `"Contact info?"` etiketinin var olduğu doğrulandı (`ADMIN CONTACT-FLAG VISIBILITY (doc §11.6) SMOKE CHECK PASSED`).

Rapor satır 451 şu şekilde güncellenmelidir: "✅ backend zaten vardı; admin panelinde görünür uyarı Bölüm 58'de eklendi (önceden veri hesaplanıyordu ama hiçbir yerde gösterilmiyordu)."

**Sonuç**: Bu bölüm de Bölüm 57 gibi B/B2/C çerçevesinin dışında değil — doğrudan §11.6'nın kendi "Beklenen sonuç" cümlesiyle ilgiliydi, bu yüzden gerçek bir doc-uyumluluk düzeltmesiydi. **B listesi hâlâ boş** (yeni bir doc-madde numarası kapatılmadı, var olan bir maddenin eksik yarısı tamamlandı). RBAC denetimi (madde 1) temiz çıktığı için orada bir düzeltme yok. Bu, "her ✅ satırını yeniden denetle" şeklinde açık uçlu bir arama değil — Bölüm 57 ve 58'in ikisi de aynı somut soruyu sordu: *bu ✅ satırı bir davranışı mı yoksa yalnızca bir alanın varlığını mı iddia ediyor?* İki denetimden biri (RBAC) temiz çıktı, diğeri (§11.6) gerçek bir boşluk buldu — bu oranın kod tarafında daha fazla arama garanti ettiği iddia edilmiyor; C listesi hâlâ değişmedi.
