**Performans uygulama planı**

Her aşama yerel kod, regresyon kontrolü ve ölçümle tamamlanır. Canlı veritabanı/deployment değişiklikleri bu çalışma kapsamında çalıştırılmaz.

| Aşama | Kapsam | Kabul ölçütü | Durum |
|---|---|---|---|
| 1 | Teklif/medya/katılım/bildirim indeksleri, N+1, gereksiz eager-load | 100 katılımda 3 sorgu; migration iki kez çalıştırıldı | Yerelde tamamlandı |
| 2 | E-posta beklemesini ayırma, SMTP timeout, kapanış önceliği, WebSocket | İstekte SMTP çağrısı yok; yavaş soket testi geçti | Yerelde tamamlandı |
| 3 | API/arayüz sayfalama, yönetim sekmelerinin ihtiyaçta yüklenmesi | Tarayıcıda 125 tekil ihale ve yönetimde 50/50/25 sayfalama | Yerelde tamamlandı |
| 4 | Galeri tekrar kullanım/temizlik, küçük resimler, metin sıkıştırması | WebP küçük resim önbelleği ve özel medya yetki testi; gzip başlığı | Yerelde tamamlandı |
| 5 | Regresyon, karşılaştırmalı ölçüm, yayın notları | Test ve ölçüm sonuçları delivery-notes.md içinde | Yerel doğrulama tamamlandı; staging bekliyor |

Uygulama tercihleri: mevcut SQLAlchemy/FastAPI ve tarayıcı özellikleri; DB/Redis/worker sayısı ölçümsüz büyütülmez. Sıralama eşitliklerinde deterministik kayıt kimliği kullanılır. Sayfalama API ve arayüz birlikte değiştirilir. E-posta işi ORM session'ını paylaşmaz. Görsel optimizasyonu özel dosyaların erişim kontrolünü korur.

Üretim doğrulaması: staging PostgreSQL migration ve EXPLAIN, gerçek ters vekil sıkıştırma başlıkları, aynı/farklı ihaleye eşzamanlı teklif, p95/p99 ve kaynak kullanımı. Yerel SQLite süreleri üretim hedefi değildir.

Docker CLI bulundu fakat Docker Desktop Linux engine bağlantısı kurulamadı. Bu nedenle PostgreSQL çalıştırma/yük testi yapılmadı. Canlı yayın gerçekleştirilmedi.
