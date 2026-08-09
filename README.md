# EventFlow

EventFlow, organizatörlerin etkinlik yayımladığı ve katılımcıların kapasite güvenli rezervasyon yaptığı bir full-stack etkinlik yönetimi uygulamasıdır. Proje, ürün gereksinimleri ile `EVENTFLOW_MASTER_PLAN.md` doğrultusunda altı küçük Pull Request halinde geliştirilmektedir.

Bu branch **PR 3 — Events** kapsamındadır. Foundation ve auth'a ek olarak kategori kataloğu, public/owner event okumaları, organizer event create/update/soft-cancel, imzalı cursor pagination, UTC/IANA/DST doğrulaması, optimistic version conflict ve aynı transaction event audit'leri hazırdır. Reservation iş endpointleri PR 4'e bilinçli olarak bırakılmıştır.

## Roller ve hedef akışlar

- `ORGANIZER`: kendi etkinliklerini oluşturur, düzenler, iptal eder ve katılımcılarını görür.
- `ATTENDEE`: public etkinlikleri inceler, rezervasyon oluşturur/iptal eder ve geçmişini görür.
- Yetkilendirme her zaman server-side uygulanacaktır; UI'da bir kontrolü gizlemek güvenlik sınırı değildir.

PR 1 seed'i bu iki rolü ve farklı durumları temsil eden altı etkinliği üretir. Public event API'si ve organizer event yönetim API'si bu verilerle çalışır; reservation API'si ve ürün ekranları henüz bu branch'in parçası değildir.

## Teknoloji yığını

- Backend: Python 3.14.3, FastAPI, async SQLAlchemy 2, Alembic, Pydantic Settings, uv
- Veri: PostgreSQL 17.6; Redis 8.2 yalnız geçici rate-limit state'i için
- Frontend: React, TypeScript, Vite, Vitest; production'da unprivileged Nginx
- Test: pytest, Testcontainers, Ruff, mypy, ESLint, Prettier
- Teslim: pnpm workspace, multi-stage/non-root Docker image'ları, Docker Compose, GitHub Actions

## Ön koşullar

- Git
- Docker Desktop ve çalışan Docker Compose engine
- Lokal kalite komutları için Node.js 22.17.1+, pnpm 11.16.0 ve uv 0.10.6

Uygulamayı yalnız Compose ile çalıştırmak için host Python veya Node kurulumu gerekmez.

## Hızlı başlangıç

PowerShell:

```powershell
Copy-Item .env.example .env
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 120
docker compose ps -a
```

Servis sırası healthcheck ve completion koşullarıyla zorlanır:

```text
PostgreSQL -> migrate -> seed -> backend -> frontend
Redis -----------------------> backend
```

Lokal URL'ler:

- Frontend: <http://localhost:8080>
- Backend health: <http://localhost:8000/health>
- Backend readiness: <http://localhost:8000/ready>
- OpenAPI JSON: <http://localhost:8000/api/v1/openapi.json>
- Swagger UI: <http://localhost:8000/docs> (`production` dışında)

`/health` yalnız process'in cevap verdiğini belirtir. `/ready`, PostgreSQL için `SELECT 1` ve Redis için `PING` çalıştırır; bağımlılık hazır değilse ortak hata envelope'u ile `503` döner.

Stack'i veri volume'unu koruyarak durdurmak için:

```powershell
docker compose down
```

`docker compose down --volumes` PostgreSQL lokal verisini siler; açıkça temiz veritabanı istediğiniz durumlar dışında kullanmayın.

## Seed hesapları

| Rol | E-posta | Parola env anahtarı |
|---|---|---|
| Organizer | `organizer@eventflow.local` | `SEED_ORGANIZER_PASSWORD` |
| Attendee | `attendee@eventflow.local` | `SEED_ATTENDEE_PASSWORD` |

Demo parolaları `.env.example` içinde yalnız lokal geliştirme için bulunur. Seed bunları Argon2id ile hash'ler, loglamaz ve aynı doğal anahtar/kararlı UUID'lerle tekrar çalıştırıldığında duplicate üretmez.

Seed veri seti 2 kullanıcı, 6 kategori, 6 etkinlik ve 2 rezervasyondur. Şu durumları kapsar: gelecek İstanbul/Berlin etkinlikleri, dolu etkinlik, boş etkinlik, geçmiş etkinlik, iptal edilmiş etkinlik ve iptal edilmiş rezervasyon.

Seed'i tekrar çalıştırmak için:

```powershell
docker compose run --rm seed
```

## Geliştirme komutları

Backend bağımlılıkları ve kontrolleri:

```powershell
Push-Location backend
uv sync --frozen --all-groups
uv run ruff format --check app migrations tests
uv run ruff check app migrations tests
uv run mypy app tests
uv run pytest --cov=app --cov-report=term-missing
uv run pip-audit
Pop-Location
```

Migration yönetimi yalnız `backend` dizininden yapılır:

```powershell
Push-Location backend
uv run alembic upgrade head
uv run alembic check
Pop-Location
```

Runtime kodunda `create_all` kullanılmaz; şema yalnız versiyonlanmış migration'larla değişir. Seed de migration değildir ve ayrı komut olarak kalır.

Frontend/workspace kontrolleri:

```powershell
pnpm install --frozen-lockfile
pnpm peers check
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm audit --prod --audit-level high
```

Container doğrulaması:

```powershell
docker compose config --quiet
docker compose build backend frontend
docker compose up -d --wait --wait-timeout 120
docker compose exec -T backend id -u
docker compose exec -T frontend id -u
```

Beklenen runtime UID'leri backend için `10001`, frontend için `101`'dir.

## Monorepo yapısı

```text
backend/                 FastAPI modüler monolit, Alembic ve pytest
  app/
    auth/                Refresh-token persistence sınırı
    audit/               Immutable audit persistence sınırı
    categories/          Seed edilmiş kategori kataloğu
    events/              Public/owner event lifecycle, cursor ve timezone kuralları
    idempotency/         Request sahipliği/replay persistence modeli
    observability/       Request ID, JSON log, health/readiness
    reservations/        Reservation modeli
    shared/              Config, database ve ortak error envelope
    users/               User modeli ve rol/statü enum'ları
  migrations/            Tek şema kaynağı olan Alembic revision'ları
frontend/                React/Vite uygulaması ve unprivileged Nginx image'ı
e2e/                     Playwright test paketi
observability/           PR 6 provisioning alanı; kuralları şimdiden tanımlı
docs/                    P0 kabul matrisi
.github/workflows/       CI kalite kapıları
```

Mimari ve veri modeli için `ARCHITECTURE.md`, kabul edilen trade-off'lar için `DECISIONS.md`, HTTP sözleşmesi için `API.md`, tehdit/kontrol özeti için `SECURITY.md` ve P0 izlenebilirliği için `docs/P0_ACCEPTANCE_MATRIX.md` okunmalıdır.

## Konfigürasyon ve secret güvenliği

- Uygulama `.env` dosyasını doğrudan okumaz; environment eksik veya geçersizse startup'ta fail-fast olur.
- Compose `${NAME:?NAME is required}` kontrolleriyle eksik anahtarı servis başlamadan reddeder.
- Wildcard CORS origin kabul edilmez.
- Production, demo JWT secret değerlerini reddeder.
- `.env` ignore edilir; yalnız güvenli örnek değerli `.env.example` commitlenir.
- Structured loglara secret ve gereksiz PII yazılmaz; her HTTP isteği güncel `X-Request-ID` taşır.

Refresh token bakım temizliği:

```powershell
Push-Location backend
uv run python -m app.auth.cleanup
Pop-Location
```

## PR 3 event API özeti

- `GET /api/v1/categories`
- `GET /api/v1/events` ve `GET /api/v1/events/{eventId}`
- `POST /api/v1/events`, `PATCH /api/v1/events/{eventId}`, `DELETE /api/v1/events/{eventId}`
- `GET /api/v1/me/events` ve `GET /api/v1/me/events/{eventId}`

Liste API'leri yalnız opaque `nextCursor` döndürür. Organizer mutasyonları authentication kimliğini kullanır; client organizer ID gönderemez. Event tarihleri açık ISO offset + IANA timezone ile doğrulanır ve UTC instant olarak saklanır. Ayrıntılı sözleşme `API.md` içindedir.

## Bilinçli olarak bu PR'da yapılmayanlar

- Event cancellation sırasında reservation bulk transition, reservation transaction'ları, reservation rate limit, concurrency, idempotency replay ve reservation audit yazımı: PR 4
- Tam responsive MUI arayüzü, generated OpenAPI client ve P0 E2E kapanışı: PR 5
- Search/filtre, governance, graceful shutdown ve provisioning tabanlı observability stack: PR 6

Şemada sonraki PR'ların bütünlük kuralları şimdiden vardır; bunun anlamı iş davranışlarının hazır olduğu değildir. Her davranış kendi PR'ında gerçek PostgreSQL/Redis ve saldırgan negatif testleriyle kanıtlanacaktır.

## Kaynak ve teslim disiplini

Ürün gereksinimi lokal PDF'tir ve yeniden dağıtım izni belirsiz olduğu için repository'ye commit edilmez. `EVENTFLOW_MASTER_PLAN.md` teknik uygulama sırasını belirler. Her PR feature branch'te, anlamlı Conventional Commit'lerle ve önce draft olarak açılır; kullanıcı onayı olmadan merge edilmez.
