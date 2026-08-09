# P0 Kabul Matrisi

Bu matris `Full-Stack-MidLevel-Case1.pdf` içindeki bütün P0 maddelerini PR 1-PR 5 arasında izler. Durumlar yalnız gerçek kanıt üretildiğinde ilerletilir.

Durum anahtarı: `⬜ Bekliyor` · `🟡 Devam ediyor` · `✅ Kanıtlandı` · `❌ Başarısız`

| ID | PDF P0 gereksinimi | Sahip PR | Otomatik/manüel kanıt | Durum |
|---|---|---:|---|---|
| P0-ID-01 | Kayıt ve giriş; organizer/attendee rolleri | 2 | Auth integration ve role testleri | ⬜ Bekliyor |
| P0-ID-02 | Her endpointte server-side yetkilendirme | 2-4 | Role/capability negatif matrisi | ⬜ Bekliyor |
| P0-ID-03 | IDOR koruması ve kaynak varlığını gizleyen 404 | 2-4 | Ownership-scoped saldırgan testleri | ⬜ Bekliyor |
| P0-EVT-01 | Organizer yalnız kendi eventini oluşturur/günceller/iptal eder | 3 | Event lifecycle + ownership testleri | ⬜ Bekliyor |
| P0-EVT-02 | Başlık, açıklama, zaman, konum, kapasite, kategori alanları | 1,3 | Migration şeması + API testleri | 🟡 Devam ediyor |
| P0-EVT-03 | Kapasite mevcut rezervasyon sayısının altına indirilemez | 3 | PostgreSQL lock/conflict integration testi | ⬜ Bekliyor |
| P0-EVT-04 | Organizer kendi event katılımcı listesini görür | 4 | Owner/not-owner attendee-list testleri | ⬜ Bekliyor |
| P0-EVT-05 | Public event listesi cursor ile sayfalanır | 3,5 | API sözleşmesi + cursor UI testleri | ⬜ Bekliyor |
| P0-RES-01 | Attendee rezervasyon oluşturur ve iptal eder | 4,5 | Lifecycle integration/E2E | ⬜ Bekliyor |
| P0-RES-02 | Aynı kullanıcı/event için ikinci aktif rezervasyon oluşmaz | 1,4 | Unique constraint + farklı-key yarış testi | 🟡 Devam ediyor |
| P0-RES-03 | Kapasite ve geçmiş zaman kuralları atomik uygulanır | 4 | 200 paralel istek + DB clock testleri | ⬜ Bekliyor |
| P0-RES-04 | İptal kontenjanı geri açar | 4 | Cancel transaction/invariant testi | ⬜ Bekliyor |
| P0-RES-05 | Attendee kendi rezervasyon geçmişini görür | 4,5 | Ownership integration + E2E | ⬜ Bekliyor |
| P0-UI-01 | Çalışan, gezilebilir ve responsive arayüz | 5 | Component/Playwright ve ekran kanıtı | ⬜ Bekliyor |
| P0-UI-02 | Loading/empty/error/success durumları | 5 | Component ve E2E state matrisi | ⬜ Bekliyor |
| P0-UI-03 | Client ve server validation | 2-5 | Zod/Pydantic/domain/DB testleri | ⬜ Bekliyor |
| P0-UI-04 | Tema tutarlı; pixel-perfect zorunlu değil | 5 | MUI theme + görsel QA | ⬜ Bekliyor |
| P0-DI-01 | Reservation create idempotent; retry ikinci kayıt üretmez | 1,4 | Schema + same-key owner/replay testleri | 🟡 Devam ediyor |
| P0-DI-02 | UTC instant + IANA timezone ve geçmiş kontrolü | 1,3,5 | Migration, DST/offset testleri, UI | 🟡 Devam ediyor |
| P0-DI-03 | Kritik event/reservation işlemleri immutable audit üretir | 1,3,4 | DB trigger + atomiklik testleri | 🟡 Devam ediyor |
| P0-DI-04 | Eşzamanlı event düzenleme bilinçli conflict üretir | 3,5 | Version 409 integration/E2E | ⬜ Bekliyor |
| P0-DI-05 | Event silme politikası gerekçeli ve tutarlı | 3,4 | Soft cancel/transition testleri + decision | ⬜ Bekliyor |
| P0-DI-06 | KVKK silme/anonymization politikası belgeli | 1 | `DECISIONS.md` kararı | 🟡 Devam ediyor |
| P0-SEC-01 | Login ve reservation endpoint rate limit | 2,4 | Redis 429 + Retry-After testleri | ⬜ Bekliyor |
| P0-SEC-02 | Security headers ve exact CORS allowlist | 2 | Header/config negatif testleri | ⬜ Bekliyor |
| P0-INF-01 | Her servis multi-stage Dockerfile kullanır | 1 | Docker build/history kontrolü | 🟡 Devam ediyor |
| P0-INF-02 | Compose DB, Redis ve uygulamayı tek komutla başlatır | 1,5 | Config + clean-clone smoke | 🟡 Devam ediyor |
| P0-INF-03 | Runtime containerlar non-root çalışır | 1 | Image/container UID testi | 🟡 Devam ediyor |
| P0-INF-04 | Healthcheck ve dependency-aware startup sırası | 1,5 | Compose health/start-order testi | 🟡 Devam ediyor |
| P0-INF-05 | `.dockerignore` bulunur | 1 | Repository/config kontrolü | 🟡 Devam ediyor |
| P0-CFG-01 | 12-factor env, eksik zorunlu env için fail-fast | 1 | Config unit/startup testleri | 🟡 Devam ediyor |
| P0-CFG-02 | `.env.example` bütün anahtarları açıklar; secret yok | 1 | Config/doc ve secret scan | 🟡 Devam ediyor |
| P0-DB-01 | Yalnız versiyonlanmış migration; runtime auto-schema yok | 1 | Alembic smoke + source guard | 🟡 Devam ediyor |
| P0-DB-02 | Migration container başlangıcında çalışır | 1 | Compose start-order smoke | 🟡 Devam ediyor |
| P0-DB-03 | Ayrı, idempotent, tekrar çalıştırılabilir seed | 1 | İki ardışık seed testi | 🟡 Devam ediyor |
| P0-DB-04 | İndeks kararları bilinçli ve sorgularla ilişkili | 1,3,4 | Migration introspection + EXPLAIN | 🟡 Devam ediyor |
| P0-API-01 | API `/api/v1` ile versiyonlanır | 1-4 | Route/OpenAPI testleri | 🟡 Devam ediyor |
| P0-API-02 | Bütün hatalar ortak envelope kullanır | 1-4 | Unit/integration error matrisi | 🟡 Devam ediyor |
| P0-API-03 | Domain hataları doğru HTTP status döndürür | 2-4 | Error mapping testleri | ⬜ Bekliyor |
| P0-API-04 | OpenAPI/Swagger mevcuttur | 1,5 | Schema snapshot/generated client | 🟡 Devam ediyor |
| P0-OBS-01 | Seviyeli structured JSON log | 1 | Log schema/redaction testleri | 🟡 Devam ediyor |
| P0-OBS-02 | Request/correlation ID header, body ve loglarda | 1 | Propagation/error/log testleri | 🟡 Devam ediyor |
| P0-OBS-03 | `/health` process, `/ready` dependency anlamını taşır | 1 | Healthy/unready integration testleri | 🟡 Devam ediyor |
| P0-OBS-04 | Loglarda secret/PII yok; print kullanılmaz | 1-5 | Redaction + source scan | 🟡 Devam ediyor |
| P0-TST-01 | Kritik iş kuralları otomatik testlidir | 1-5 | PR test paketleri | 🟡 Devam ediyor |
| P0-TST-02 | Kapasite ve zamanlılık concurrency testi zorunlu | 4 | Gerçek PostgreSQL 200-request testi | ⬜ Bekliyor |
| P0-TST-03 | Testler izole; lokal geliştirici DB’sine bağlı değil | 1-5 | Testcontainers/Compose test DB | 🟡 Devam ediyor |
| P0-CI-01 | Push CI: lint/format/type/test/build/audit | 1,5 | GitHub Actions sonuçları | 🟡 Devam ediyor |
| P0-GIT-01 | Feature branch + PR; doğrudan main geliştirmesi yok | 1-5 | Branch/PR geçmişi | 🟡 Devam ediyor |
| P0-GIT-02 | Anlamlı Conventional Commits ve açıklamalı PR’lar | 1-5 | Git log ve PR açıklamaları | 🟡 Devam ediyor |
| P0-DOC-01 | README kurulum, kullanım, yapı ve bilinçli eksikleri açıklar | 1,5 | Clean-clone doc doğrulaması | 🟡 Devam ediyor |
| P0-DOC-02 | DECISIONS alternatif/neden/feda formatında aktiftir | 1-5 | Karar kayıtları ve PR diff’i | 🟡 Devam ediyor |

## PR kapıları

| PR | Kapanış koşulu | Durum |
|---:|---|---|
| 1 | Foundation, schema, migration/seed, ortak HTTP/observability altyapısı ve CI kabul kriterleri yeşil | 🟡 Devam ediyor |
| 2 | Auth, refresh rotation/replay, authorization/IDOR ve security negatifleri yeşil | ⬜ Bekliyor |
| 3 | Event lifecycle, timezone/version/ownership ve public cursor API yeşil | ⬜ Bekliyor |
| 4 | Reservation/idempotency/audit ve gerçek PostgreSQL concurrency invariantları yeşil | ⬜ Bekliyor |
| 5 | Bütün P0 satırları `✅ Kanıtlandı`; clean-clone ve E2E yeşil, kullanıcı onayı alınmış | ⬜ Bekliyor |
