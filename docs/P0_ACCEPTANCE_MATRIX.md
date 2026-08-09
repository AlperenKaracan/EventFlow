# P0 Kabul Matrisi

Bu matris `Full-Stack-MidLevel-Case1.pdf` içindeki bütün P0 maddelerini PR 1-PR 5 arasında izler. Durumlar yalnız gerçek kanıt üretildiğinde ilerletilir.

Durum anahtarı: `⬜ Bekliyor` · `🟡 Devam ediyor` · `✅ Kanıtlandı` · `❌ Başarısız`

| ID | PDF P0 gereksinimi | Sahip PR | Otomatik/manüel kanıt | Durum |
|---|---|---:|---|---|
| P0-ID-01 | Kayıt ve giriş; organizer/attendee rolleri | 2 | Auth integration ve role testleri | ✅ Kanıtlandı |
| P0-ID-02 | Her endpointte server-side yetkilendirme | 2-4 | Role/capability negatif matrisi | ⬜ Bekliyor |
| P0-ID-03 | IDOR koruması ve kaynak varlığını gizleyen 404 | 2-4 | Ownership-scoped saldırgan testleri | ⬜ Bekliyor |
| P0-EVT-01 | Organizer yalnız kendi eventini oluşturur/günceller/iptal eder | 3 | Event lifecycle + ownership testleri | ✅ Kanıtlandı |
| P0-EVT-02 | Başlık, açıklama, zaman, konum, kapasite, kategori alanları | 1,3 | Migration şeması + API testleri | ✅ Kanıtlandı |
| P0-EVT-03 | Kapasite mevcut rezervasyon sayısının altına indirilemez | 3 | PostgreSQL lock/conflict integration testi | ✅ Kanıtlandı |
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
| P0-DI-06 | KVKK silme/anonymization politikası belgeli | 1 | `DECISIONS.md` D-014 | ✅ Kanıtlandı |
| P0-SEC-01 | Login ve reservation endpoint rate limit | 2,4 | Redis 429 + Retry-After testleri | 🟡 Devam ediyor |
| P0-SEC-02 | Security headers ve exact CORS allowlist | 2 | Header/config negatif testleri | ✅ Kanıtlandı |
| P0-INF-01 | Her servis multi-stage Dockerfile kullanır | 1 | Backend/frontend Docker build ve image inspection | ✅ Kanıtlandı |
| P0-INF-02 | Compose DB, Redis ve uygulamayı tek komutla başlatır | 1,5 | Config + clean-clone smoke | 🟡 Devam ediyor |
| P0-INF-03 | Runtime containerlar non-root çalışır | 1 | Image user + runtime UID: backend `10001`, frontend `101` | ✅ Kanıtlandı |
| P0-INF-04 | Healthcheck ve dependency-aware startup sırası | 1,5 | Compose health/start-order testi | 🟡 Devam ediyor |
| P0-INF-05 | `.dockerignore` bulunur | 1 | Root `.dockerignore` + Docker build context | ✅ Kanıtlandı |
| P0-CFG-01 | 12-factor env, eksik zorunlu env için fail-fast | 1 | `test_config.py` ve Compose required-env ifadeleri | ✅ Kanıtlandı |
| P0-CFG-02 | `.env.example` bütün anahtarları açıklar; secret yok | 1 | Config/doc ve secret scan | 🟡 Devam ediyor |
| P0-DB-01 | Yalnız versiyonlanmış migration; runtime auto-schema yok | 1 | Alembic twice/check + CI `create_all` source guard | ✅ Kanıtlandı |
| P0-DB-02 | Migration container başlangıcında çalışır | 1 | Compose migrate one-shot exit `0` ve start-order smoke | ✅ Kanıtlandı |
| P0-DB-03 | Ayrı, idempotent, tekrar çalıştırılabilir seed | 1 | Integration testi + ikinci Compose seed sayımı `2\|6\|6\|2` | ✅ Kanıtlandı |
| P0-DB-04 | İndeks kararları bilinçli ve sorgularla ilişkili | 1,3,4 | Migration introspection + EXPLAIN | 🟡 Devam ediyor |
| P0-API-01 | API `/api/v1` ile versiyonlanır | 1-4 | Route/OpenAPI testleri | 🟡 Devam ediyor |
| P0-API-02 | Bütün hatalar ortak envelope kullanır | 1-4 | Unit/integration error matrisi | 🟡 Devam ediyor |
| P0-API-03 | Domain hataları doğru HTTP status döndürür | 2-4 | Error mapping testleri | ⬜ Bekliyor |
| P0-API-04 | OpenAPI/Swagger mevcuttur | 1,5 | Schema snapshot/generated client | 🟡 Devam ediyor |
| P0-OBS-01 | Seviyeli structured JSON log | 1 | Unit schema testi + 11 container satırının JSON parse'ı | ✅ Kanıtlandı |
| P0-OBS-02 | Request/correlation ID header, body ve loglarda | 1 | UUIDv7/preserve/error/log propagation testleri | ✅ Kanıtlandı |
| P0-OBS-03 | `/health` process, `/ready` dependency anlamını taşır | 1 | Healthy ve dependency-unready integration testleri | ✅ Kanıtlandı |
| P0-OBS-04 | Loglarda secret/PII yok; print kullanılmaz | 1-5 | Redaction + source scan | 🟡 Devam ediyor |
| P0-TST-01 | Kritik iş kuralları otomatik testlidir | 1-5 | PR test paketleri | 🟡 Devam ediyor |
| P0-TST-02 | Kapasite ve zamanlılık concurrency testi zorunlu | 4 | Gerçek PostgreSQL 200-request testi | ⬜ Bekliyor |
| P0-TST-03 | Testler izole; lokal geliştirici DB’sine bağlı değil | 1-5 | Testcontainers/Compose test DB | 🟡 Devam ediyor |
| P0-CI-01 | Push CI: lint/format/type/test/build/audit | 1,5 | [PR 1 CI run #2](https://github.com/AlperenKaracan/EventFlow/actions/runs/31323243906) | ✅ Kanıtlandı |
| P0-GIT-01 | Feature branch + PR; doğrudan main geliştirmesi yok | 1-5 | Branch/PR geçmişi | 🟡 Devam ediyor |
| P0-GIT-02 | Anlamlı Conventional Commits ve açıklamalı PR’lar | 1-5 | Git log ve PR açıklamaları | 🟡 Devam ediyor |
| P0-DOC-01 | README kurulum, kullanım, yapı ve bilinçli eksikleri açıklar | 1,5 | Clean-clone doc doğrulaması | 🟡 Devam ediyor |
| P0-DOC-02 | DECISIONS alternatif/neden/feda formatında aktiftir | 1-5 | 19 aktif karar; her biri alternatif/neden/feda içeriyor | ✅ Kanıtlandı |

## PR 1 kanıt günlüğü

| Kapı | Komut/kanıt | Sonuç |
|---|---|---|
| Backend statik kalite | Ruff format/lint ve mypy | 41 dosya formatted; 39 source file typed; temiz |
| Backend test | `uv run pytest --cov=app --cov-report=term-missing` | 16/16 geçti; toplam coverage `%94` |
| Migration | Disposable PostgreSQL 17 üzerinde `upgrade head` iki kez + `alembic check` | Geçti; pending operation yok |
| DB bütünlüğü | Constraint/index introspection ve audit UPDATE/DELETE trigger testi | Geçti |
| Seed | Integration testi ve ikinci Compose seed | Duplicate yok; `2\|6\|6\|2` |
| Frontend | Peer, format, lint, typecheck, Vitest, production build | Geçti; 1/1 component testi |
| Dependency audit | `pip-audit`, `pnpm audit --prod --audit-level high` | Bilinen açık yok |
| Docker | Backend/frontend build, image user ve runtime UID | Geçti; `10001:10001` ve `101:101` |
| Compose | Config, dependency-aware up, health/ready, one-shot exit'ler | Geçti; migrate/seed exit `0` |
| Log şeması | Backend container stdout satırlarını JSON parse | 11/11 geçti |
| CI workflow | Actionlint + [GitHub Actions run #2](https://github.com/AlperenKaracan/EventFlow/actions/runs/31323243906) | Backend, frontend ve Compose job'ları geçti |

## PR 2 kanıt günlüğü

| Kapı | Komut/kanıt | Sonuç |
|---|---|---|
| Backend statik kalite | Ruff format/lint ve strict mypy | 57 dosya formatted; 55 source file typed; temiz |
| Backend test | `uv run pytest --cov=app --cov-report=term-missing` | 45/45 geçti; toplam coverage `%93` |
| Auth API | Gerçek PostgreSQL/Redis register/login/me/refresh/logout testleri | Başarı, duplicate, invalid credential, cookie ve Origin yolları geçti |
| Refresh saldırı yarışı | Aynı token ve eski-token/successor eşzamanlı refresh testleri | Advisory family lock + row lock; replay sonrası aktif family üyesi yok |
| Authorization/IDOR | Forged/changed claim ve HTTP 401/403/404 saldırı matrisi | Geçti; UUID tabanlı erişim resource-hiding 404 |
| Browser güvenliği | Exact CORS preflight, CSP/security header ve production HSTS testleri | Geçti |
| Rate limit | Gerçek Redis Lua sayacı | 5 deneme sonrası `429` + `Retry-After`; key'de ham IP/e-posta yok |
| Dependency audit | `pip-audit`, `pnpm audit --prod --audit-level high` | Bilinen açık yok |
| Compose smoke | Config/build/up + auth HTTP journey + cleanup CLI | `201/200/200/200/204`; backend UID `10001`; cleanup structured log |

## PR 3 kanıt günlüğü

| Kapı | Komut/kanıt | Sonuç |
|---|---|---|
| Backend statik kalite | Ruff format/lint ve strict mypy | 69 dosya formatlı; 67 source file typed; temiz |
| Backend tam test | `uv run pytest --cov=app --cov-report=term-missing` | 83/83 geçti; toplam coverage `%94`, event service `%94` |
| Event read API | Category, public/owner list-detail ve saldırgan cursor testleri | Stable cursor, cancelled/past görünürlük ve owner-bound cursor geçti |
| Event lifecycle | Gerçek PostgreSQL create/update/soft-cancel ve ownership testleri | Role, owner-hiding 404, kapasite ve DB-clock kuralları geçti |
| Timezone | IANA zone, ISO offset, DST gap/fold unit/integration matrisi | Normal zaman ve iki geçerli fold kabul; gap/mismatch/naive reddedildi |
| Optimistic concurrency | Aynı `expectedVersion` ile beş update/update ve beş update/cancel yarışı | Her yarışta tek başarı, tek `409`, sürüm `2` ve tek mutation audit'i |
| Audit atomikliği | Create/update/cancel sırasında zorlanan audit INSERT hatası | Üç domain mutasyonu da rollback; auditsiz domain commit yok |
| İndeks planı | Public ve owner cursor SQL'i için kontrollü PostgreSQL `EXPLAIN` | İlgili iki bileşik event indeksi seçildi |
| OpenAPI | Stable operation ID, ortak error ref ve yalnız `nextCursor` testi | Lokal sözleşme testi geçti |
| Frontend/workspace regresyonu | Peer, format, Markdownlint, ESLint, typecheck, Vitest, build | Geçti; 1/1 component testi ve production build yeşil |
| Dependency audit | `pip-audit`, `pnpm audit --prod --audit-level high` | Bilinen açık yok |
| Compose lifecycle smoke | Temiz restart + gerçek HTTP olumlu/saldırgan event matrisi | Migrate/seed exit `0`; `403/404/409/422` negatifleri ve lifecycle geçti; UID `10001/101` |
| Seed/log/audit smoke | İkinci seed + DB audit sorgusu + container JSON parse | Seed `2\|6\|6\|2`; audit `created,updated,cancelled`; JSON log `37/37` |
| Remote CI | [GitHub Actions run #12](https://github.com/AlperenKaracan/EventFlow/actions/runs/31327179809) | Backend, frontend ve Compose job'ları geçti |

## PR kapıları

| PR | Kapanış koşulu | Durum |
|---:|---|---|
| 1 | Foundation, schema, migration/seed, ortak HTTP/observability altyapısı ve CI kabul kriterleri yeşil | ✅ Kanıtlandı |
| 2 | Auth, refresh rotation/replay, authorization/IDOR ve security negatifleri yeşil | ✅ Kanıtlandı |
| 3 | Event lifecycle, timezone/version/ownership ve public cursor API yeşil | ✅ Kanıtlandı |
| 4 | Reservation/idempotency/audit ve gerçek PostgreSQL concurrency invariantları yeşil | ⬜ Bekliyor |
| 5 | Bütün P0 satırları `✅ Kanıtlandı`; clean-clone ve E2E yeşil, kullanıcı onayı alınmış | ⬜ Bekliyor |
