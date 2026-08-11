# EventFlow

EventFlow, organizatörlerin etkinlik yayımladığı ve katılımcıların kapasite güvenli rezervasyon yaptığı bir full-stack etkinlik yönetimi uygulamasıdır. Ürün, kaynak gereksinim PDF'i ile `EVENTFLOW_MASTER_PLAN.md` doğrultusunda altı küçük Pull Request halinde geliştirilmiştir.

P0 ürün akışlarının 52/52'si, P1 kriterlerinin 19/19'u ve seçilen P2 Prometheus teslimi kanıtlanmıştır. Loki/Alloy log hattı ile repository dosyalarından otomatik kurulan Grafana operasyon ekranları da aynı operasyon teslimini tamamlar. Altı PR'lık ana plan merge edilerek tamamlanmıştır. Ana teslimi izleyen [PR 7 UI/UX yeniden tasarımı](https://github.com/AlperenKaracan/EventFlow/pull/7) da kullanıcı onayı ve dört yeşil CI işiyle merge edilmiştir. Ayrıntılı son denetim ve kalan harici teslim adımları için [`docs/DELIVERY_AUDIT.md`](docs/DELIVERY_AUDIT.md) belgesine bakın.

## Roller ve hedef akışlar

- `ORGANIZER`: kendi etkinliklerini oluşturur, düzenler, iptal eder ve katılımcılarını görür.
- `ATTENDEE`: public etkinlikleri inceler, rezervasyon oluşturur/iptal eder ve geçmişini görür.
- Yetkilendirme her zaman server-side uygulanır; UI'da bir kontrolü gizlemek güvenlik sınırı değildir.

Seed bu iki rolü, altı etkinliği ve aktif/iptal edilmiş reservation örneklerini üretir. Public, organizer ve reservation API'leri ile ürün ekranları bu verilerle çalışır.

## Teknoloji yığını

- Backend: Python 3.14.3, FastAPI, async SQLAlchemy 2, Alembic, Pydantic Settings, uv
- Veri: PostgreSQL 17.6; Redis 8.2 yalnız geçici rate-limit state'i için
- Frontend: React 19, TypeScript, Vite, MUI, TanStack Query/Router, React Hook Form, Zod; production'da unprivileged Nginx
- Test: pytest, Testcontainers, Vitest, Playwright, Ruff, mypy, ESLint, Prettier
- Gözlemlenebilirlik: Prometheus 3, Loki 3, Grafana Alloy ve provision edilmiş Grafana 13
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
backend -> Prometheus -> Grafana
Docker logs -> Alloy -> Loki -> Grafana
```

Lokal URL'ler:

- Frontend: <http://localhost:8080>
- Backend health: <http://localhost:8000/health>
- Backend readiness: <http://localhost:8000/ready>
- Prometheus metrikleri: <http://localhost:8000/metrics>
- OpenAPI JSON: <http://localhost:8000/api/v1/openapi.json>
- Swagger UI: <http://localhost:8000/docs> (`production` dışında)
- Grafana: <http://localhost:3000>

`/health` yalnız process'in cevap verdiğini belirtir. `/ready`, PostgreSQL için `SELECT 1` ve Redis için `PING` çalıştırır; bağımlılık hazır değilse ortak hata envelope'u ile `503` döner.

Backend `SIGTERM` aldığında yeni bağlantı kabulünü durdurur ve `GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS` süresince akan istekleri tamamlar. Ardından Redis ve PostgreSQL pool'ları lifespan kapanışında kapatılır. Compose backend'e `SIGTERM` gönderir ve uygulamanın izin verdiği en yüksek 120 saniyelik drain süresinden daha uzun, 130 saniyelik zorla sonlandırma penceresi tanır:

```powershell
docker compose stop backend
```

Normal kapatma sırasında rezervasyon transaction'ı yarım commit edilmez; akan işlem timeout içinde commit olur, hata veya iptal durumunda session rollback ile kapanır.

Stack'i veri volume'unu koruyarak durdurmak için:

```powershell
docker compose down
```

`docker compose down --volumes` PostgreSQL lokal verisini siler; açıkça temiz veritabanı istediğiniz durumlar dışında kullanmayın.

## Seed hesapları

| Rol       | E-posta                     | Parola env anahtarı       |
| --------- | --------------------------- | ------------------------- |
| Organizer | `organizer@eventflow.local` | `SEED_ORGANIZER_PASSWORD` |
| Attendee  | `attendee@eventflow.local`  | `SEED_ATTENDEE_PASSWORD`  |

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
pnpm --filter @eventflow/e2e test
pnpm audit --prod --audit-level high
```

Container doğrulaması:

```powershell
docker compose config --quiet
docker compose build backend frontend
docker compose up -d --wait --wait-timeout 120
docker compose exec -T backend id -u
docker compose exec -T frontend id -u
docker compose exec -T alloy id -u
docker compose exec -T prometheus id -u
docker compose exec -T grafana id -u
```

Beklenen runtime UID'leri backend için `10001`, frontend için `101`, Alloy için `473`, Prometheus için `65534` ve Grafana için `472`'dir. Loki image kullanıcı tanımı `10001`'dir.

## Monorepo yapısı

```text
backend/                 FastAPI modüler monolit, Alembic ve pytest
  app/
    auth/                Refresh-token persistence sınırı
    audit/               Immutable audit persistence sınırı
    categories/          Seed edilmiş kategori kataloğu
    events/              Public/owner event lifecycle, cursor ve timezone kuralları
    idempotency/         Request sahipliği/replay persistence modeli
    observability/       Request ID, JSON log, health/readiness ve Prometheus metrikleri
    reservations/        Reservation modeli
    shared/              Config, database ve ortak error envelope
    users/               User modeli ve rol/statü enum'ları
  migrations/            Tek şema kaynağı olan Alembic revision'ları
frontend/                React/Vite uygulaması ve unprivileged Nginx image'ı
e2e/                     Playwright test paketi
observability/           Prometheus, Loki, Alloy ve Grafana provisioning dosyaları
docs/                    P0/P1/P2 kabul kanıtları ve PR ekran görüntüleri
.github/workflows/       CI kalite kapıları
```

Mimari ve veri modeli için `ARCHITECTURE.md`, kabul edilen trade-off'lar için `DECISIONS.md`, HTTP sözleşmesi için `API.md`, test yaklaşımı için `TESTING.md`, günlük işletim için `OPERATIONS.md`, tehdit/kontrol özeti için `SECURITY.md` ve katkı kuralları için `CONTRIBUTING.md` okunmalıdır. Kabul kanıtları `docs/P0_ACCEPTANCE_MATRIX.md`, `docs/P1_ACCEPTANCE_MATRIX.md` ve `docs/P2_ACCEPTANCE_MATRIX.md` içindedir. Kaynak PDF ile master planın son durum karşılaştırması `docs/DELIVERY_AUDIT.md` içinde tutulur.

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

Süresi dolmuş idempotency kayıtlarının tekrar çalıştırılabilir temizliği:

```powershell
Push-Location backend
uv run python -m app.idempotency.cleanup
Pop-Location
```

## Ürün ve API özeti

### Arayüz ve deneyim

EventFlow tek koyu temalı, responsive ve erişilebilir bir tasarım sistemi kullanır. Keşif, kimlik, rezervasyon ve organizatör akışlarının tasarım kararları, önce/sonra görselleri ve doğrulama kapsamı [UI/UX yeniden tasarım belgesinde](docs/UI_UX_REDESIGN.md) bulunur.

- `GET /api/v1/categories`
- `GET /api/v1/events` ve `GET /api/v1/events/{eventId}`
- `POST /api/v1/events`, `PATCH /api/v1/events/{eventId}`, `DELETE /api/v1/events/{eventId}`
- `GET /api/v1/me/events` ve `GET /api/v1/me/events/{eventId}`
- `POST /api/v1/events/{eventId}/reservations`
- `DELETE /api/v1/reservations/{reservationId}`
- `GET /api/v1/me/reservations`
- `GET /api/v1/events/{eventId}/attendees`

Liste API'leri yalnız opaque `nextCursor` döndürür. Organizer mutasyonları authentication kimliğini kullanır; client organizer ID gönderemez. Event tarihleri açık ISO offset + IANA timezone ile doğrulanır ve UTC instant olarak saklanır. Ayrıntılı sözleşme `API.md` içindedir.

Reservation create için `Idempotency-Key` zorunludur. Kapasite event satırı kilidi altında kontrol edilir; counter, reservation, audit ve semantic replay snapshot tek PostgreSQL transaction'ında commit edilir. Aynı key replay edilir, farklı payload/key reuse `409` olur ve Redis limit aşımı `429 + Retry-After` döndürür.

## Gözlemlenebilirlik

Backend `/metrics` endpoint'i HTTP, rezervasyon, idempotency, kilit bekleme, rate-limit ve readiness metriklerini Prometheus formatında sunar. Route etiketi her zaman path template veya sabit `unmatched` değeridir; request ID, kullanıcı, etkinlik UUID'si ve ham URL metrik etiketi yapılmaz.

Grafana ilk açılışta şu repository-managed ekranları otomatik yükler:

- `EventFlow - Genel Bakış`: metrik ve log çalışma alanlarına giriş.
- `EventFlow - Metrikler`: trafik, gecikme, hata, rezervasyon ve bağımlılık panelleri.
- `EventFlow - Log Analizi`: operasyon özeti, log seviyesi eğilimi, HTTP durum ve rota yoğunluğu, p95 süreler, yavaş istekler, iş alanı sonuçları, uygulama hata kodları, request ID zaman çizelgesi ve ayrıştırma sorunları.

Request ID ile terminal ve Loki araması:

```powershell
docker compose logs backend --no-color | Select-String 'REQUEST_ID'
```

```logql
{service_name="backend"} | json | requestId="REQUEST_ID"
```

Grafana koyu tema ve Türkçe varsayılan dil ile açılır. Yerel giriş bilgileri `.env` içindeki `GRAFANA_ADMIN_USER` ve `GRAFANA_ADMIN_PASSWORD` değerleridir. Ayrıntılı doğrulama ve sorun giderme akışları `OPERATIONS.md` içindedir.

## Teslim durumu ve kalan adımlar

- Repository: <https://github.com/AlperenKaracan/EventFlow>
- PR 1-7: merge edildi; ana plandaki P0, P1, seçilen P2 ve takip eden UI/UX yeniden tasarımı tamamlandı.
- Son doğrulanan uzak koşu: [GitHub Actions run #77](https://github.com/AlperenKaracan/EventFlow/actions/runs/31537371791); dört job ve kayıtlı bütün adımlar geçti.
- Repository halen private. Public görünürlük ve teslim paylaşımı ayrıca açık kullanıcı onayı olmadan değiştirilmez.
- `main` için branch protection kuralı yapılandırılmıştır; GitHub mevcut private kişisel repository planında kuralın uygulanmadığını bildirir. Ayrıca zorunlu Compose check adı güncel workflow job adıyla eşleştirilmelidir. Bunlar kod eksiği değil, yayın öncesi GitHub yönetim adımlarıdır.
- Sunum videosu kullanıcı tarafından repository dışında hazırlanacaktır; uygulama veya dokümantasyon eksiği olarak değerlendirilmez.

## Bilinçli olarak kapsam dışında bırakılanlar

- Account deletion endpoint'i: anonymization politikası `DECISIONS.md` D-014'te belgeli, uygulama P0 dışında.
- Cursor geçmişi route belleğindedir; hard refresh bilinçli olarak ilk sayfaya döner.
- Distributed tracing, alert notification, merkezi SaaS log servisi ve Kubernetes kapsam dışıdır.
- Üretim deploy'u, yüksek erişilebilirlik ve object storage tabanlı Loki topolojisi kapsam dışıdır.

Kapsam içindeki davranışlar gerçek PostgreSQL/Redis, tarayıcı ve Compose testleriyle kanıtlanır. Gözlemlenebilirlik sistemi domain transaction'larının bir bağımlılığı değildir; Prometheus, Loki, Alloy veya Grafana arızası ürün API'sini durdurmaz.

## Kaynak ve teslim disiplini

Ürün gereksinimi lokal PDF'tir ve yeniden dağıtım izni belirsiz olduğu için repository'ye commit edilmez. `EVENTFLOW_MASTER_PLAN.md` teknik uygulama sırasını belirler. Her PR feature branch'te, anlamlı Conventional Commit'lerle ve önce draft olarak açılır; kullanıcı onayı olmadan merge edilmez. Yapılamayan veya bilinçli bırakılan işler gizlenmez; son durum `docs/DELIVERY_AUDIT.md` ve kabul matrislerinde açıkça yazılır.
