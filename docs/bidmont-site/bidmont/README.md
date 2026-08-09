# BidMont — bidmont.me

Statik, bağımlılıksız, tam responsive bir site. Build adımı yok: dosyaları sunucuya
kopyalayın, çalışır.

```
index.html        Ana sayfa (hero, arama, öne çıkan açık artırmalar, nasıl çalışır, paketler)
credits.html      Kredi satın alma (cüzdan, paketler, karşılaştırma tablosu, SSS, CTA)
auctions.html     Partner açık artırmaları (filtreler, sonuç grid'i, partnerler, kategoriler)
auth.html         Giriş + 3 adımlı hesap oluşturma / doğrulama akışı
assets/css/style.css
assets/js/main.js
assets/img/*       Görseller (WebP + marka dosyaları)
robots.txt, sitemap.xml
build.py          Sayfaları üreten script (header/footer tek yerden yönetilir)
favicon.ico, favicon-32.png, apple-touch-icon.png
```

## Kırılma noktaları

| Genişlik | Davranış |
| --- | --- |
| < 600px | Tek kolon, hamburger menü, açık artırmalarda alt sekme çubuğu, filtreler alttan açılan sheet |
| 600–899px | 2 kolon kart grid'i |
| 900–1119px | 3 kolon grid, yan yana hero |
| ≥ 1120px | Tam masaüstü navigasyon + sabit filtre kenar çubuğu |

## Görseller

Tüm görseller gerçek ve WebP. Ürün görsellerinin üç boyutu var, HTML `srcset` ile
doğru olanı seçiliyor:

| Son ek | Boyut | Kullanım |
| --- | --- | --- |
| `-sm.webp` | 300×203 | Hero'daki mini float kartlar |
| `-md.webp` | 600×405 | Mobil / tablet kart görseli |
| `.webp` | 1200×810 | Masaüstü kart görseli, retina |

- **Ürünler:** `car`, `villa`, `excavator`, `yacht`, `generator`, `watch`, `cnc`,
  `truck`, `suv`
- **Hero:** `hero.webp` (1200×800, şeffaf) + `hero-sm.webp` (700×467)
- **Kategori kartları:** `cat-cars`, `cat-heavy`, `cat-real-estate`, `cat-marine`,
  `cat-industrial` — `.webp` (800×640) + `-md.webp` (400×320)
- **CTA banner:** `handshake.webp` (1400×500) + `handshake-sm.webp` (700×250)
- **Marka:** `logo.webp` / `logo-sm.webp` / `logo.png` (871×178, şeffaf),
  `logo-mark.png` (512×512 ikon), `og-image.jpg` (1200×630)
- **İkonlar (kök dizin):** `favicon.ico`, `favicon-32.png`, `apple-touch-icon.png`

Kategori ikonları, güven rozetleri, sosyal medya ve form ikonları kod içinde inline
SVG — ayrı dosya gerektirmiyor.

Görsel değiştirirken aynı isimleri koruyun; boyut varyantlarını üretmezseniz
`srcset` satırını tek `src`'ye indirin.

## İçeriği düzenleme

İki yol var:

1. **Doğrudan HTML'i düzenleyin** — normal statik site gibi çalışın.
2. **`build.py` üzerinden** — header, footer, kart ve fiyat verileri tek yerde
   tanımlı. Düzenleyip `python3 build.py` çalıştırın, dört sayfa yeniden üretilir.
   (Bu yolu seçerseniz HTML'de yaptığınız elle değişiklikler ezilir.)

Açık artırma verisi `build.py` içindeki `AUCTIONS` listesinde; son sütun kalan
süredir (saniye) ve JavaScript bunu canlı geri sayıma çevirir.

## Renkler

`assets/css/style.css` başındaki `:root` bloğu tüm sistemi kontrol eder.
Markayı değiştirmek için `--red`, `--red-600` ve `--red-50` yeterli.

## Backend'e bağlarken

- Formlar `data-form="login"` / `data-form="signup"` ile işaretli; `main.js`
  içindeki submit handler'ında `e.preventDefault()` yerine kendi `fetch`
  çağrınızı koyun. İstemci tarafı doğrulama zaten çalışıyor.
- Filtre paneli hem masaüstü hem mobilde aynı işaretlemeyi kullanır; input
  id'leri `-d` (desktop) ve `-m` (mobil) son ekiyle ayrılır.
- Favori butonları `aria-pressed` ile durum tutuyor, kalıcılık için kendi
  endpoint'inizi bağlayın.

## Erişilebilirlik ve performans

- Klavye ile tam gezinilebilir; drawer'lar odak tuzağı ve Esc ile kapanma içerir.
- `prefers-reduced-motion` tüm animasyonları devre dışı bırakır.
- Görseller `width`/`height` ile boyutlanır (layout shift yok), hero dışındakiler
  `loading="lazy"`.
- Harici bağımlılık yalnızca Google Fonts (Inter). Kaldırırsanız sistem fontuna düşer.
