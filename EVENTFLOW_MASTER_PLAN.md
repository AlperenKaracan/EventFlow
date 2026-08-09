# EventFlow - Uçtan Uca, PDF Uyumlu Nihai Master Plan

> Ana gereksinim kaynağı: `Full-Stack-MidLevel-Case1.pdf`
>
> Bu belge ürün, backend, frontend, veri bütünlüğü, güvenlik, gözlemlenebilirlik, Docker, test, CI, GitHub ve dokümantasyon teslimini tek uygulama planında birleştirir.
## 1. Teslim Hedefi ve Kapsam

### 1.1 Başarı tanımı

- Bütün P0 gereksinimleri tamamlanacak ve otomatik testlerle kanıtlanacak.
- P0 kapsamı PR 1-PR 5 içinde tamamlanacak; PR 5 sonunda ayrı bir P0 kabul kapısı çalıştırılmadan PR 6 ve P1 işlerine başlanmayacak.
- P1 kapsamında event arama, kategori/tarih filtresi, repo yönetişim dosyaları ve graceful shutdown yapılacak.
- PR 6 içinde önce bütün P1 kabul kriterleri tamamlanıp kanıtlanacak, ancak bundan sonra tek P2 çalışması olan Prometheus metrics endpoint'ine geçilecek; Grafana metrik ve log inceleme arayüzü bu gözlemlenebilirlik çalışmasının tamamlayıcı katmanı olarak sunulacak.
- Modüler monolit kullanılacak; mikroservis, Kubernetes, Terraform ve service mesh eklenmeyecek.
- UI ve dokümantasyon Türkçe; kod, API alanları, branch ve commit isimleri İngilizce olacak.
- Repo geliştirme sırasında private, teslim öncesinde secret/history kontrolünden sonra public yapılacak.
- Ödeme, cache, notification queue, WebSocket, mobil uygulama ve gerçek deploy kapsam dışında kalacak.
- Temiz makinede yalnız aşağıdaki akış gerekli olacak:

```bash
git clone <repository-url>
cd EventFlow
cp .env.example .env
docker compose up
```

### 1.2 Teknoloji seçimi

- Backend: Python 3.14, FastAPI, Pydantic, async SQLAlchemy 2, asyncpg, Alembic.
- Veritabanı: PostgreSQL.
- Rate-limit state: Redis; cache amacıyla kullanılmayacak.
- Frontend: React 19, TypeScript, Vite ve MUI.
- Client state: TanStack Query ve TanStack Router.
- Formlar: React Hook Form ve Zod.
- API client: FastAPI OpenAPI şemasından üretilmiş TypeScript client.
- Backend test: pytest ve Testcontainers.
- Frontend test: Vitest ve React Testing Library.
- Tarayıcı testi: Playwright.
- Backend paket yönetimi: `uv`.
- Frontend paket yönetimi: `pnpm`.
- Frontend production server ve reverse proxy: non-root Nginx.
- Gözlemlenebilirlik: seviyeli JSON loglar, Prometheus, Loki, Grafana Alloy ve provision edilmiş Grafana.
- Alloy Docker container loglarını toplayıp Loki'ye gönderecek; Grafana üzerinden request ID, seviye, route ve error code ile aranabilecek.

### 1.3 Bilinçli olarak yapılmayacaklar

- Mikroservis ayrımı.
- Kubernetes veya infrastructure-as-code.
- Gerçek ödeme.
- Cache katmanı.
- Asenkron bildirim kuyruğu.
- Canlı kontenjan/WebSocket.
- Yüzde 100 coverage hedefi.
- Mobil uygulama.
- Pixel-perfect tasarım.

Bu seçimler `README.md` ve `DECISIONS.md` içinde süre, risk ve trade-off gerekçeleriyle açıklanacak.

### 1.4 Lokal geliştirme ön koşulları ve bağlantılar

Zorunlu host araçları:

- Docker Desktop; Linux containers/WSL2 engine çalışır durumda olmalı.
- Docker Compose v2+ (`docker compose`).
- Git ve bir tarayıcı.
- Teslim için GitHub hesabı ve repository remote'u. HTTPS + Git Credential Manager veya SSH kullanılabilir.

Host'a ayrıca kurulmayacak servisler:

- PostgreSQL, Redis, Prometheus, Loki, Grafana Alloy ve Grafana ayrı Windows kurulumu olmayacak; tamamı `compose.yaml` ile version-pin edilmiş container olarak çalışacak.
- Grafana MCP proje runtime'ı, dashboard geliştirmesi veya log görüntüleme için gerekli değildir. Datasource ve dashboard'lar repository içindeki provisioning dosyalarıyla yönetilecek; arayüze tarayıcıdan girilecek.
- GitHub/Codex eklentisi zorunlu değildir. Git push/PR normal remote üzerinden yapılabilir.

Yalnız container dışı hızlı geliştirme istenirse opsiyonel host araçları:

- Python 3.14 ve `uv`.
- Node.js 22+, Corepack ve proje tarafından pinlenen `pnpm` sürümü.
- GitHub CLI (`gh`); repository oluşturma, PR açma ve branch-protection kontrolünü kolaylaştırır fakat uygulamanın çalışması için gerekmez.

İlk preflight:

```powershell
docker version
docker compose version
docker run --rm hello-world
git --version
```

Docker engine cevap vermeden scaffold veya servis kurulumuna başlanmayacak. Tam gözlemlenebilirlik stack'i için Docker Desktop'a pratikte en az 4 CPU, 6 GB RAM ve yeterli disk alanı ayrılması önerilir.

## 2. Repository ve Modüler Monolit Mimarisi

```text
EventFlow/
├── backend/
│   ├── app/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── categories/
│   │   ├── events/
│   │   ├── reservations/
│   │   ├── idempotency/
│   │   ├── audit/
│   │   ├── observability/
│   │   ├── shared/
│   │   └── main.py
│   ├── migrations/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── concurrency/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── AGENTS.md
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── events/
│   │   ├── reservations/
│   │   └── shared/
│   ├── tests/
│   ├── Dockerfile
│   └── AGENTS.md
├── e2e/
│   ├── tests/
│   ├── playwright.config.ts
│   └── AGENTS.md
├── observability/
│   ├── prometheus/prometheus.yml
│   ├── loki/loki.yml
│   ├── alloy/config.alloy
│   └── grafana/
│       ├── provisioning/
│       └── dashboards/
├── .github/
│   ├── workflows/ci.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── CODEOWNERS
├── AGENTS.md
├── README.md
├── ARCHITECTURE.md
├── DECISIONS.md
├── API.md
├── TESTING.md
├── OPERATIONS.md
├── SECURITY.md
├── CONTRIBUTING.md
├── compose.yaml
├── .env.example
└── .dockerignore
```

### 2.1 Katman sorumlulukları

- Router yalnız HTTP request/response dönüşümünü yapacak.
- Pydantic schema API sözleşmesini ve input/output validasyonunu temsil edecek.
- Application service iş kuralları, authorization ve transaction sınırlarını yönetecek.
- Repository SQLAlchemy sorgularını yönetecek.
- Repository kendi başına `commit()` çağırmayacak.
- ORM nesneleri doğrudan API response olarak dönmeyecek.
- Transaction başlatma, commit ve rollback application service'e ait olacak.
- Modüller başka modülün tablosunu router veya rastgele SQL ile değiştirmeyecek.
- Kritik invariant'lar yalnız tek application service akışından değiştirilecek.

## 3. Veri Modeli, Constraint ve İndeksler

### 3.1 `users`

- `id`: UUID primary key.
- `email`: normalize edilmiş, case-insensitive unique.
- `full_name`: zorunlu ve trim edilmiş.
- `password_hash`.
- `role`: `ORGANIZER | ATTENDEE`.
- `status`: `ACTIVE | ANONYMIZED | DISABLED`.
- `created_at`, `updated_at`, `anonymized_at`.

### 3.2 `refresh_tokens`

- `id`, `user_id`; kullanıcı silinmese de anonimleştirilebildiği için FK referential integrity korunacak.
- `token_hash`: raw refresh token saklanmayacak ve hash için unique constraint bulunacak.
- `family_id`: her login ile başlayan token ailesini temsil eden UUID; rotation boyunca değişmeyecek.
- `replaced_by_id`: nullable self-FK, `ON DELETE SET NULL`; yeni token önceki tokenı işaret zinciriyle takip edebilecek.
- `expires_at`, `revoked_at`, `created_at`, `last_used_at`.
- İndeksler: unique `token_hash`, `(user_id, expires_at)` ve `(family_id, revoked_at)`.
- Rotation yarışı tek transaction'da satır kilidiyle çözülecek; kullanılmış/eski token replay edilirse aynı `family_id` altındaki bütün aktif tokenlar revoke edilecek.
- Ayrı ve tekrar çalıştırılabilir cleanup komutu yalnız süresi dolmuş veya güvenli retention süresini geçmiş revoked tokenları silecek; aktif token family zincirini bozmayacak.

### 3.3 `categories`

- `id`, unique `slug`, `name`, `is_active`, `created_at`.
- Seed: Teknoloji, Müzik, Spor, Eğitim, Sanat ve İş Dünyası.
- Organizer kategori oluşturamayacak; yalnız aktif katalogdan seçim yapacak.
- Admin rolü case'te olmadığı için category CRUD yapılmayacak.

### 3.4 `events`

- `id`, `organizer_id`, `category_id`.
- `title`, `description`, `location`.
- `starts_at`: PostgreSQL `timestamptz`.
- `timezone`: IANA timezone.
- `capacity`, `reserved_count`.
- `status`: `ACTIVE | CANCELLED`.
- `version`: optimistic concurrency integer.
- `created_at`, `updated_at`, `cancelled_at`.

DB constraintleri:

```text
capacity > 0
reserved_count >= 0
reserved_count <= capacity
version > 0
```

### 3.5 `reservations`

- `id`, `event_id`, `attendee_id`.
- `status`: `ACTIVE | CANCELLED_BY_ATTENDEE | CANCELLED_BY_EVENT`.
- `created_at`, `updated_at`, `cancelled_at`.
- `(event_id, attendee_id)` unique constraint.
- İptal sonrası yeni satır yerine aynı kayıt yeniden etkinleştirilecek.

### 3.6 `idempotency_records`

- `id`, `user_id`, `operation`, `key`.
- `request_hash`.
- `state`: `PROCESSING | COMPLETED`.
- `response_status`, request/correlation ID içermeyen güvenli semantik `response_body`.
- `original_request_id`: `PROCESSING` sırasında nullable, `COMPLETED` olurken zorunlu; domain işlemini ilk kez yürüten owner request'in correlation ID'si ve replay teşhis bağlantısı.
- `created_at`, `expires_at`.
- Unique `(user_id, operation, key)`.

### 3.7 `audit_logs`

- `id`, `actor_id`, `action`.
- `resource_type`, `resource_id`.
- `changes`: JSONB.
- `request_id`, `created_at`.
- Uygulamada yalnız INSERT.
- Alembic migration ile DB trigger; `UPDATE` ve `DELETE` reddedilecek.

### 3.8 İndeks kararları

- Normalize email unique index: register/login lookup.
- Refresh token unique `token_hash` indexi: token lookup ve duplicate savunması.
- Refresh token `(user_id, expires_at)` indexi: kullanıcı tokenlarını revoke etme ve cleanup.
- Refresh token `(family_id, revoked_at)` indexi: replay halinde token family iptali.
- `(event_id, attendee_id)` unique reservation index: duplicate savunması.
- Aktif eventlerde `(starts_at, id)` partial index: public cursor listesi.
- `(organizer_id, created_at, id)`: organizer dashboard.
- `(attendee_id, created_at, id)`: attendee reservation history.
- `(event_id, status, created_at)`: katılımcı listesi ve aktif reservation sorgusu.
- `(user_id, operation, key)`: idempotency replay.
- `expires_at`: idempotency retention cleanup.
- Başlık+açıklama generated search vector için GIN index.
- Her indeks desteklediği sorgu, yazma maliyeti ve `EXPLAIN` örneğiyle `ARCHITECTURE.md` içinde açıklanacak.
- Kullanılmayan veya yalnız 'best practice' gerekçeli indeks eklenmeyecek.

## 4. Auth, Yetkilendirme, IDOR ve Güvenlik

### 4.1 Kayıt ve giriş

Register payload:

```json
{
  "email": "user@example.com",
  "fullName": "Example User",
  "password": "secure-password",
  "role": "attendee"
}
```

- Kullanıcı organizer veya attendee rolünü seçebilecek.
- E-posta normalize edilip unique kontrol edilecek.
- Parola Argon2id ile hash'lenecek.
- Parola, token ve cookie loglanmayacak.

### 4.2 Token akışı

- Access JWT varsayılan 15 dakika.
- Access token yalnız frontend belleğinde tutulacak.
- localStorage/sessionStorage kullanılmayacak.
- Refresh token opaque random değer ve varsayılan 7 gün.
- DB'de yalnız refresh token hash'i tutulacak.
- Refresh token her kullanımda rotate edilecek.
- Eski token replay edilirse token family iptal edilecek.
- Logout refresh tokenı revoke edecek.
- Refresh cookie: `HttpOnly`, production'da `Secure`, `SameSite=Lax`, dar path.

### 4.3 Endpoint bazlı authorization ve IDOR politikası

Genel status politikası:

- Authentication yok veya access token geçersiz: `401 UNAUTHENTICATED`.
- URL'sinde kaynak UUID'si bulunan bir endpointte authenticated kullanıcının role veya ownership erişimi yoksa: `404 RESOURCE_NOT_FOUND`.
- Event, reservation veya attendee-list kaynağının varlığı hiçbir yetkisiz kullanıcıya `403` ile doğrulanmayacak.
- `403 FORBIDDEN` yalnız kaynak varlığını ifşa etmeyen genel capability işlemlerinde kullanılacak; örneğin attendee'nin `POST /events` çağrısı.
- Ownership-scoped sorgu hiçbir satır bulamazsa, gerçekten bulunmayan ve erişilemeyen kaynak aynı `404` cevabını verecek.

IDOR kontrolleri:

- Organizer event update sorgusu `event_id + organizer_id` ile yapılacak.
- Organizer event delete sorgusu `event_id + organizer_id` ile yapılacak.
- Organizer owner-detail sorgusu `event_id + organizer_id` ile yapılacak; public event detail organizer edit ekranının veri kaynağı olmayacak.
- Attendee listesi `event_id + organizer_id` ile scope edilecek.
- Reservation iptali `reservation_id + attendee_id` ile scope edilecek.
- Organizer'ın kendi event listesi current user ID'den türetilecek; client user ID kabul edilmeyecek.
- Attendee'nin reservation listesi current user ID'den türetilecek.
- URL/body içinde gönderilen `organizerId` veya `attendeeId` authorization kaynağı olmayacak.
- UI buton ve route gizleme yalnız UX olacak; backend kontrolünün yerine geçmeyecek.

Zorunlu saldırgan testleri:

- Organizer A, Organizer B'nin eventini GET owner-detail/update/delete edemez.
- Organizer A, Organizer B'nin attendee listesini göremez.
- Attendee A, Attendee B'nin reservation kaydını iptal edemez.
- Attendee organizer endpointine erişemez.
- Organizer reservation create edemez.
- UUID değiştirerek resource enumeration yapılamaz.
- JWT içindeki role veya user ID değiştirilmiş token kabul edilmez.
- Kaynak UUID'si içeren bütün yetkisiz saldırı senaryoları `404` döndürür; testler `403` dönmediğini de doğrular.

### 4.4 CORS, CSRF ve security headers

- Allowed origin listesi environment variable'dan gelecek.
- Wildcard `*` kabul edilmeyecek.
- Credentials ile wildcard startup config hatası olacak.
- Yalnız gerekli method/header'lara izin verilecek.
- Cookie kullanan refresh/logout endpointlerinde Origin kontrolü yapılacak.
- CSP, `X-Content-Type-Options`, frame koruması ve referrer policy uygulanacak.
- Production HSTS etkinleştirilecek.
- Swagger production'da env ile kapatılabilecek.

### 4.5 Rate limiting

- Login: IP + normalize email başına varsayılan 5/dakika.
- Reservation: authenticated user başına varsayılan 10/dakika.
- State Redis'te tutulacak; cache özelliği olarak kullanılmayacak.
- Limitler environment variable ile ayarlanabilecek.
- Aşımda `429` ve `Retry-After` header'ı.

### 4.6 KVKK politikası

Account deletion endpoint'i P0 kapsamında yapılmayacak; politika `DECISIONS.md` içinde belgelenecek:

- Email ve full name anonimleştirilir.
- Password hash temizlenir veya hesap girişe kapatılır.
- Bütün refresh tokenlar revoke edilir.
- Reservation ve audit referential integrity anonim UUID ile korunur.
- Audit kayıtları değişmeden kalır.
- Gerçek retention politikası hukuk ve operasyon ekipleriyle belirlenir.

## 5. Event ve Reservation İş Kuralları

### 5.1 Event create

- Title trim edilir, boş olamaz ve kontrollü uzunlukta olmalı.
- Description kontrollü uzunlukta olmalı.
- Location boş olamaz.
- Capacity pozitif integer olmalı.
- Category aktif olmalı.
- Timestamp offset içeren ISO-8601 olmalı.
- IANA timezone geçerli olmalı.
- Timestamp içindeki UTC offset, seçilen IANA timezone'un o instant için hesaplanan gerçek UTC offset'iyle aynı olmalı; uyuşmazlık `422 TIMEZONE_OFFSET_MISMATCH` olarak reddedilmeli.
- DST nedeniyle nonexistent yerel zaman reddedilmeli; ambiguous yerel zaman yalnız açık offset doğru IANA offset'iyle eşleşiyorsa kabul edilmeli.
- Başlangıç DB saatine göre gelecekte olmalı.
- Organizer ID request body'den değil auth context'ten alınacak.
- Event ve audit aynı transaction'da oluşturulacak.

### 5.2 Eşzamanlı event düzenleme

- Event response `version` alanı döndürecek.
- PATCH body `expectedVersion` taşıyacak.
- Update `id + organizer_id + version` ile koşullandırılacak.
- Başka sekme kaydı değiştirmişse sıfır satır update olur.
- API `409 EVENT_VERSION_CONFLICT` döndürür.
- Frontend form verisini koruyup güncel event'i yükleme seçeneği sunar.
- Sessiz 'son yazan kazanır' uygulanmayacak.
- PATCH ile değiştirilen bütün event alanları create ile aynı trim, uzunluk, kategori, gelecek zaman, IANA timezone ve offset-zone tutarlılığı kurallarından geçecek.
- Başlamış veya iptal edilmiş event update edilemeyecek; DB `now()` kontrolü ve integration testi zorunlu olacak.

### 5.3 Kapasite update

- Event satırı transaction içinde lock edilir.
- Yeni kapasite `reserved_count` altındaysa `409 CAPACITY_BELOW_RESERVATIONS`.
- Capacity, version ve audit aynı transaction'da değişir.

### 5.4 Event iptali ve silme politikası

DELETE fiziksel silme yapmayacak:

1. Event `SELECT ... FOR UPDATE` ile kilitlenir.
2. Organizer ownership, expected version ve başlamamış olma kontrol edilir.
3. Event `CANCELLED` olur.
4. Aktif rezervasyonlar `CANCELLED_BY_EVENT` olur.
5. `reserved_count = 0` olur.
6. Event ve reservation audit kayıtları bulk insert edilir.
7. Tek transaction commit edilir.

İptal edilen event public listeden çıkar; organizer panelinde ve reservation sahibi geçmişinde `İptal Edildi` görünür.

### 5.5 Reservation create ve kapasite garantisi

`POST /events/{eventId}/reservations` için `Idempotency-Key` zorunlu olacak. PostgreSQL `READ COMMITTED` altında uygulanacak algoritma:

1. Attendee authentication ve Redis rate limit çalışır.
2. Key boş olamaz, maksimum uzunluk/karakter formatı doğrulanır.
3. `operation = reservation.create` ve canonical request hash hazırlanır. Hash; HTTP method, route adı, `eventId` ve normalize body'nin SHA-256 değeridir. Böylece aynı key'in başka event için kullanılması conflict olur.
4. Transaction başlatılır.
5. Owner seçimi atomik yapılır:

```sql
INSERT INTO idempotency_records
  (user_id, operation, key, request_hash, state, created_at, expires_at)
VALUES
  (:user_id, 'reservation.create', :key, :request_hash, 'PROCESSING', now(), :expires_at)
ON CONFLICT (user_id, operation, key) DO NOTHING
RETURNING id;
```

6. PostgreSQL insert'i çakışan uncommitted transaction commit/rollback olana kadar statement seviyesinde bekletir. Bekleme sonrasında iki kesin yol vardır:
   - İlk transaction rollback etmişse bekleyen `INSERT` başarılı olur, `RETURNING id` satır döndürür ve bu request owner olarak domain akışına devam eder.
   - İlk transaction commit etmişse `ON CONFLICT DO NOTHING` çalışır, `RETURNING` boş döner ve bu request replay/loser koluna girer.
7. Replay/loser kolu aynı transaction içinde key satırını `SELECT ... FOR UPDATE` ile okur:
   - Satır normal retention süresi içinde silinemez. Operasyonel cleanup yarışı/bozuk veri nedeniyle yine de görünmüyorsa transaction rollback edilir ve bütün claim algoritması en fazla bir kez yeni transaction'da tekrarlanır; ikinci kayıpta `409 IDEMPOTENCY_IN_PROGRESS` döner ve alarm metriği üretilir.
   - `request_hash` farklıysa hiçbir domain lock alınmadan `409 IDEMPOTENCY_KEY_REUSED` döner.
   - Kayıt `COMPLETED` ise saklanan status ve request ID dışındaki semantik body replay edilir. Bu HTTP denemesinin güncel request ID'si response header ve hata body alanına en son aşamada enjekte edilir; `Idempotent-Replayed: true` ve `Idempotency-Original-Request-ID` header'ları eklenir.
   - Tek-transaction tasarımında başka request tarafından görünür `PROCESSING` kayıt beklenmez. Bakım/bozuk veri nedeniyle görülürse bounded bekleme yapılmaz; `409 IDEMPOTENCY_IN_PROGRESS` ve `Retry-After` döner, warning log/metric üretilir.
8. Owner request event satırını `SELECT ... FOR UPDATE` ile kilitler.
9. Event aktif ve DB `now()` değerine göre başlamamış mı kontrol edilir.
10. Attendee/event reservation satırı varsa event lock'tan sonra `FOR UPDATE` ile kilitlenir.
11. Aktif reservation varsa deterministik `409 ALREADY_RESERVED` response'u idempotency kaydına yazılıp commit edilir.
12. `reserved_count >= capacity` ise `409 EVENT_FULL` response'u idempotency kaydına yazılıp commit edilir.
13. Yeni reservation oluşturulur veya önceki iptal kaydı yeniden etkinleştirilir.
14. Yeni reservation INSERT'i DB unique constraint ihlaline karşı nested transaction/savepoint içinde çalışır. Beklenmeyen unique conflict'te savepoint rollback edilir, mevcut kayıt okunur ve outer transaction kullanılabilir durumda tutularak deterministik `ALREADY_RESERVED` response'u saklanır.
15. `reserved_count += 1`, reservation audit, `original_request_id` ve request ID içermeyen tamamlanmış idempotency response'u aynı outer transaction'da yazılır.
16. Tek commit ile reservation, sayaç, audit ve replay response görünür olur.

Concurrent aynı-key sonucu:

- İlk request commit ederse bekleyen request unique-conflict yolundan aynı status ve semantik response'u replay eder; her HTTP denemesi kendi güncel request ID'sini taşır.
- İlk request beklenmeyen exception nedeniyle rollback ederse idempotency satırı dahil bütün yazımlar kaybolur; bekleyen request insert'i kazanıp gerçek işlemi yürütür.
- İlk request DB commit sonrası ağ yanıtını gönderemese bile retry saklanan response'u replay eder.
- Deterministik `EVENT_FULL`, `EVENT_STARTED`, `ALREADY_RESERVED` ve validation-domain conflict sonuçları aynı key için saklanır. Kullanıcının koşullar değiştikten sonra yeni denemesi yeni key kullanır.
- Beklenmeyen 5xx saklanmaz; transaction tamamen rollback edilir.
- Idempotency kayıtları varsayılan 24 saat tutulur ve ayrı tekrar çalıştırılabilir cleanup komutuyla temizlenir.

Davranışlar:

- Aynı key ve aynı payload: aynı status ve semantik body replay edilir; correlation metadata her HTTP denemesi için yeniden üretilir.
- Replay response'unda `Idempotent-Replayed: true`.
- Replay response'unda ilk domain işleminin correlation ID'si `Idempotency-Original-Request-ID`, güncel denemenin correlation ID'si `X-Request-ID` olarak bulunur; hata body içindeki `requestId` güncel `X-Request-ID` ile aynıdır.
- Aynı key ve farklı payload: `409 IDEMPOTENCY_KEY_REUSED`.
- Farklı key ve aktif reservation: `409 ALREADY_RESERVED`.
- Dolu event: `409 EVENT_FULL`.
- Geçmiş event: `409 EVENT_STARTED`.
- Beklenmeyen 5xx rollback eder; yarım reservation veya sayaç değişimi kalmaz.
- İptal sonrası rebook yapılabilir fakat event bu sırada dolduysa eski reservation öncelik sağlamaz.

### 5.6 Reservation iptali

Deadlock riskini önlemek için bütün reservation yazımlarının ortak lock sırası `event -> reservation -> audit` olacak. Cancellation akışı reservation ID ile başladığı halde reservation satırı önce kilitlenmeyecek:

1. Transaction başlatılır.
2. `SELECT event_id FROM reservations WHERE id=:reservation_id AND attendee_id=:current_user_id` ile yalnız event ID non-locking ve ownership-scoped okunur. Satır yoksa kaynak varlığını gizleyen `404` döner.
3. Event `SELECT ... FOR UPDATE` ile kilitlenir.
4. Reservation `SELECT ... FOR UPDATE WHERE id=:reservation_id AND attendee_id=:current_user_id AND event_id=:event_id` ile kilitlenir.
5. Lock sonrası event/reservation durumu yeniden doğrulanır.
6. Reservation zaten `CANCELLED_BY_ATTENDEE` veya `CANCELLED_BY_EVENT` ise idempotent `204` döner; sayaç ve audit değişmez.
7. Reservation aktif fakat event başlamışsa `409 EVENT_STARTED` döner.
8. Reservation `CANCELLED_BY_ATTENDEE` yapılır ve `cancelled_at` yazılır.
9. Event için `reserved_count > 0` invariant'ı assert edilir ve `reserved_count -= 1` yapılır.
10. Cancellation audit kaydı eklenir.
11. Transaction commit edilir.

Global lock sırası:

- Reservation create/rebook: `idempotency key row -> event -> reservation -> audit -> idempotency finalize`.
- Reservation cancellation: `event -> reservation -> audit`.
- Event cancellation: `event -> active reservations ORDER BY id -> audits`.
- Capacity update: `event -> audit`.
- Hiçbir application service event lock almadan reservation satırını `FOR UPDATE` ile kilitleyemez.
- Lock sırası `backend/AGENTS.md`, `ARCHITECTURE.md` sequence diagramı ve deadlock regression testleriyle korunur.

### 5.7 Zaman dilimi

- PostgreSQL'de UTC instant `timestamptz` olarak saklanır.
- Event IANA timezone ayrıca tutulur.
- Gönderilen ISO-8601 offset ile IANA timezone'un `starts_at` instantındaki offset'i server-side karşılaştırılır; ikisi uyuşmadan kayıt oluşturulamaz veya güncellenemez.
- 'Event geçmiş mi?' kontrolü client saatine değil DB `now()` değerine göre yapılır.
- UI event lokasyon saatini ana, browser timezone karşılığını ikincil gösterir.
- DST nedeniyle nonexistent yerel zaman server-side reddedilir; ambiguous yerel zaman yalnız gönderilen açık offset seçilen IANA zone'un geçerli offsetlerinden biriyse kabul edilir.
- Tarih filtreleri UTC aralığına güvenli dönüştürülür.

## 6. API Sözleşmesi

### 6.1 Auth endpointleri

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### 6.2 Category endpointi

- `GET /api/v1/categories`

### 6.3 Event endpointleri

- `GET /api/v1/events`
- `GET /api/v1/events/{eventId}`
- `POST /api/v1/events`
- `PATCH /api/v1/events/{eventId}`
- `DELETE /api/v1/events/{eventId}?expectedVersion=N`
- `GET /api/v1/me/events`
- `GET /api/v1/me/events/{eventId}`
- `GET /api/v1/events/{eventId}/attendees`

### 6.4 Reservation endpointleri

- `POST /api/v1/events/{eventId}/reservations`
- `DELETE /api/v1/reservations/{reservationId}`
- `GET /api/v1/me/reservations`

### 6.5 Sistem endpointleri

- `GET /health`
- `GET /ready`
- `GET /metrics`
- `GET /api/v1/openapi.json`
- Swagger UI.

### 6.6 Cursor pagination

Public event sırası:

```text
starts_at ASC, id ASC
```

Dashboard ve history sırası:

```text
created_at DESC, id DESC
```

Response:

```json
{
  "items": [],
  "nextCursor": "opaque-cursor",
  "hasMore": false
}
```

- Varsayılan limit 20, maksimum 100.
- Cursor sürüm, sort tuple ve aktif filtre hash'i taşır.
- Bozuk cursor `400 INVALID_CURSOR`.
- Filtre değişince eski cursor kullanılmaz.
- Offset pagination kullanılmaz.
- Public query: `q`, `category`, `dateFrom`, `dateTo`, `limit`, `cursor`.

API yalnız `nextCursor` döndürecek; önceki sayfa navigasyonu frontend client cursor history ile sağlanacak:

```ts
type CursorPagerState = {
  cursors: Array<string | null>; // İlk sayfa null
  index: number;
  nextCursor: string | null;
};
```

- Başlangıç state'i `{ cursors: [null], index: 0, nextCursor: null }`.
- Başarılı response'taki `nextCursor`, mevcut sayfanın ileri cursor'ı olarak saklanır.
- Kullanıcı `İleri` dediğinde cursor `cursors[index + 1]` olarak append edilir ve index artırılır.
- Kullanıcı `Geri` dediğinde API'den `previousCursor` beklenmez; index azaltılır ve daha önce saklanan `cursors[index]` yeniden kullanılır.
- `index === 0` iken geri butonu disabled olur; `hasMore=false` iken ileri butonu disabled olur.
- TanStack Query key'i filtre hash'i, limit ve aktif `cursors[index]` değerini içerir.
- Arama, kategori, tarih, sort veya limit değişirse history `[null]` olarak reset edilir.
- Event create/update/cancel gibi liste sıralamasını değiştiren mutation sonrasında cursor history ilk sayfaya reset edilir.
- Invalid cursor `400` dönerse kullanıcıya kısa mesaj gösterilip ilk sayfaya dönülür.
- Cursor stack route-level `useCursorPager` state'inde tutulur; detail sayfasına gidip geri dönmede korunur. Hard refresh'te ilk sayfaya reset edilmesi bilinçli ve dokümante edilmiş davranıştır.
- Random page jump veya toplam sayfa numarası sunulmaz.

### 6.7 Tutarlı hata formatı

```json
{
  "error": {
    "code": "EVENT_FULL",
    "message": "Etkinlik kapasitesi dolu.",
    "requestId": "019...",
    "details": []
  }
}
```

- Validation, auth, permission, domain, rate-limit ve beklenmeyen exceptionlar aynı envelope'a map edilir.
- `details` yalnız güvenli validation ayrıntılarında bulunur.
- Internal exception, SQL veya stack trace client'a dönmez.
- Her hata response header ve body içinde request ID taşır.
- İdempotency replay'inde saklanan semantik hata body'sine güncel request ID enjekte edilir; body `requestId` ile `X-Request-ID` hiçbir zaman farklı olmaz.
- Event full `409`, genel capability reddi `403`, erişilemeyen veya bulunmayan ID tabanlı kaynak `404`, validation `422`, rate limit `429`.
- OpenAPI her response schema ve hata kodunu belgeler.

## 7. Frontend Uçtan Uca Akış

### 7.1 Routes

- `/`: public event listesi.
- `/events/:eventId`: event detay.
- `/login` ve `/register`.
- `/attendee/reservations`.
- `/organizer/events`.
- `/organizer/events/new`.
- `/organizer/events/:eventId/edit`.
- `/organizer/events/:eventId/attendees`.
- 403, 404 ve genel hata sayfaları.

### 7.2 Public event ekranı

- Full-text arama.
- Kategori select.
- Başlangıç/bitiş tarih filtresi.
- Cursor tabanlı ileri/geri navigasyon.
- Skeleton loading.
- Filtreye özel empty state.
- Retry butonlu error state.
- Event yerel saati ve browser karşılığı.
- Kalan kapasite ve durum.

### 7.3 Auth UX

- Access token yalnız memory'de.
- Sayfa yenilenince refresh cookie ile session bootstrap.
- Eşzamanlı 401 yanıtları tek refresh isteğinde birleştirilir.
- Refresh başarısızsa session temizlenip login'e yönlendirilir.
- Route guard yalnız UX; backend security yerine geçmez.
- Logout token revoke ve query cache temizliği yapar.

### 7.4 Organizer UX

- Kendi eventlerini bütün durumlarla listeler.
- Edit ve attendee ekranlarının doğrudan URL açılışında veri `GET /api/v1/me/events/{eventId}` üzerinden owner-scoped yüklenir; public detail endpoint'i organizer yönetim verisi için kullanılmaz.
- Create/edit formunda React Hook Form + Zod.
- Server validation error mapping.
- Version conflict dialog; kullanıcının form verisi kaybolmaz.
- Capacity conflict için açık mesaj.
- Cancel confirmation.
- Attendee listesi minimum gerekli alanları gösterir: full name, email, reservation zamanı.
- Başkasının event URL'si backend'den 404 alır.

### 7.5 Attendee UX

- Reserve butonu her bilinçli submit için UUID idempotency key üretir.
- Otomatik retry boyunca aynı key korunur.
- Yeni bilinçli denemede yeni key üretilir.
- Full, duplicate, past ve version/domain hataları ayrı güvenli mesajlarla gösterilir.
- Aktif, attendee tarafından iptal ve event tarafından iptal reservation history.
- Başlamış eventte cancel butonu pasif; backend yine kontrol eder.
- İptal sonrası event detail ve reservation listesi hedefli invalidate edilir.

### 7.6 UI durum standardı

Her async ekranda:

- Loading.
- Empty.
- Error.
- Success.
- Retry.
- Accessible label ve keyboard navigation.
- Responsive masaüstü/mobil düzen.
- Güvenli hata mesajı ve kopyalanabilir request ID.

## 8. Config, Docker, Migration ve Seed

### 8.1 12-factor ve fail-fast config

`pydantic-settings` startup sırasında en az şu değişkenleri doğrulayacak:

- `APP_ENV`
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- Access/refresh TTL.
- `CORS_ALLOWED_ORIGINS`
- `LOG_LEVEL`
- Rate-limit değerleri.
- DB/Redis timeout.
- Graceful shutdown timeout.
- Frontend/backend public URL.
- Grafana local demo config.
- Loki retention ve Alloy scrape/refresh ayarları.

Kurallar:

- Eksik zorunlu env bütün eksik adlarıyla tek anlamlı hata üretir.
- Uygulama port açmadan non-zero exit eder.
- JWT secret minimum şartı sağlamazsa startup reddedilir.
- Wildcard CORS reddedilir.
- Production ortamında demo/default secret reddedilir.
- `.env.example` her anahtarı ve kısa açıklamasını içerir.
- Gerçek secret repo veya Git geçmişine girmez.

### 8.2 Migration

- Yalnız Alembic versioned migration.
- Her schema değişikliği yeni migration.
- Merge edilmiş migration rewrite edilmez.
- `Base.metadata.create_all`, ORM synchronize ve startup schema generation yasaktır.
- One-shot `migrate` service DB healthy olduktan sonra `alembic upgrade head` çalıştırır.
- Backend migration başarıyla bitmeden başlamaz.

### 8.3 Seed

Ayrı, idempotent ve tekrar çalıştırılabilir seed service:

- Lokal organizer hesabı.
- Lokal attendee hesabı.
- Kategoriler.
- Farklı şehir ve timezone'larda gelecek eventler.
- Dolu event.
- Boş event.
- Geçmiş event.
- İptal edilmiş event.
- Aktif ve iptal örnek reservationlar.

Compose başlangıcında otomatik çalışır; ayrıca:

```bash
docker compose run --rm seed
```

ile duplicate üretmeden tekrar çalışır.

### 8.4 Compose servisleri ve başlangıç sırası

- `db`
- `redis`
- `migrate`
- `seed`
- `backend`
- `frontend`
- `prometheus`
- `grafana`
- `loki`
- `alloy`

Sıra:

1. PostgreSQL ve Redis healthcheck geçer.
2. Migrate `service_completed_successfully`.
3. Seed `service_completed_successfully`.
4. Backend `/ready` olur.
5. Frontend başlar.
6. Prometheus backend'i scrape eder.
7. Loki log kabul etmeye hazır olur.
8. Alloy Docker loglarını keşfedip Loki'ye gönderir.
9. Grafana Prometheus ve Loki datasource'larını, dashboard'ları ve Explore görünümünü provision eder.

Backend Prometheus, Loki, Alloy veya Grafana'ya bağımlı olmayacak. Gözlemlenebilirlik pipeline arızası iş transaction'larını durdurmayacak.

### 8.5 Container güvenliği

- Backend ve frontend ayrı multi-stage Dockerfile.
- Runtime imajlarında compiler ve build araçları yok.
- Sabit UID/GID ile non-root çalışma.
- Yalnız gerekli portlar expose edilir.
- `.dockerignore`: virtualenv, node_modules, git, `.env`, cache ve secretlar.
- Healthcheck tanımları.
- Compose `stop_grace_period`, backend graceful timeout'tan uzun.

## 9. Gözlemlenebilirlik ve Grafana Arayüzü

### 9.1 Seviyeli JSON loglar

Backend log alanları:

- `timestamp`, `level`, `service`, `environment`.
- `requestId`, güvenli `actorId`.
- `method`, route template, `status`, `durationMs`.
- `event`, `errorCode`.

Kurallar:

- Seviyeler `DEBUG`, `INFO`, `WARNING`, `ERROR`.
- `LOG_LEVEL` env'den gelir.
- `contextvars` ile request ID katmanlar arasında taşınır.
- Authorization, cookie, password, token, email ve request body loglanmaz.
- Beklenmeyen exception server logunda bir ERROR kaydı üretir.
- Dağınık `print` ve `console.log` yasaktır.
- Frontend production build'de debug console çağrısı bulunmaz.

Request ID ile arama:

```bash
docker compose logs backend --no-color |
  jq 'select(.requestId == "REQUEST_ID")'
```

Bu terminal fallback'i korunacak; ana operasyon akışı Grafana Explore içinde Loki sorgusu olacak:

```logql
{service_name="backend"} | json | requestId="REQUEST_ID"
```

### 9.2 Request/correlation ID

- Geçerli `X-Request-ID` kabul edilir; geçersizse yeni UUID.
- Response header'a eklenir.
- Her hata body içinde döner.
- Audit kaydında saklanır.
- Metric label olarak kullanılmaz.
- Idempotency response snapshot'ına gömülmez. Replay sırasında güncel denemenin request ID'si header ve hata body'sine enjekte edilir; owner request ID ayrı `Idempotency-Original-Request-ID` header'ıyla ilişkilendirilir.

### 9.3 `/health` ve `/ready`

`/health` harici dependency kontrol etmeden process durumunu döndürür:

```json
{"status":"ok"}
```

`/ready`:

- PostgreSQL `SELECT 1`.
- Redis `PING`.
- Kısa timeout.
- Her şey hazırsa 200.
- Bir dependency hazır değilse güvenli durumla 503.

### 9.4 Graceful shutdown

- SIGTERM geldiğinde yeni trafik kabulü durur.
- Akan istekler timeout içinde tamamlanır.
- Aktif transaction commit veya rollback olur.
- DB ve Redis pool'ları kapanır.
- Compose zorla öldürmeden önce yeterli `stop_grace_period` verir.

### 9.5 Prometheus metrikleri

- `eventflow_http_requests_total`
- `eventflow_http_request_duration_seconds`
- `eventflow_http_requests_in_progress`
- `eventflow_http_errors_total`
- `eventflow_reservation_attempts_total{outcome}`
- `eventflow_reservation_lock_wait_seconds`
- `eventflow_idempotency_requests_total{outcome}`
- `eventflow_event_cancellations_total`
- `eventflow_rate_limit_rejections_total{endpoint}`
- `eventflow_readiness_status{dependency}`

High-cardinality label olarak user ID, event ID, email, request ID veya raw URL kullanılmayacak. Route label path template kullanacak.

### 9.6 Loki ve Grafana Alloy log pipeline

- Alloy `discovery.docker` ile Compose containerlarını keşfedecek.
- `loki.source.docker` container stdout/stderr loglarını okuyacak.
- `loki.process` JSON log alanlarını parse edecek ve hatalı JSON satırlarını ayrı bir parse-error alanıyla koruyacak.
- `loki.write` logları `http://loki:3100/loki/api/v1/push` adresine gönderecek.
- Docker socket Alloy containerına read-only mount edilecek.
- Alloy yalnız EventFlow Compose project label'ına sahip servisleri toplayacak; host üzerindeki diğer container loglarını toplamamalı.
- Loki tek binary modda, lokal filesystem storage ve named volume ile çalışacak.
- Lokal demo retention varsayılan 7 gün olacak; compactor retention etkin olacak.
- Loki label'ları yalnız düşük cardinality alanlar olacak: `service_name`, `environment`, `level` ve gerekirse route template.
- `requestId`, `actorId`, email ve event ID Loki index label'ı olmayacak; JSON field olarak LogQL ile filtrelenecek.
- Loki ve Alloy healthcheck tanımlanacak.
- Alloy pipeline arızası backend requestini veya Docker logging akışını bloklamayacak.

Uygulama sırasında esas alınacak resmî referanslar:

- [Grafana Alloy ile Docker container metric ve loglarını izleme](https://grafana.com/docs/alloy/latest/monitor/monitor-docker-containers/)
- [Alloy `loki.source.docker` bileşeni](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.docker/)
- [Alloy ile Loki'ye log gönderme](https://grafana.com/docs/loki/latest/send-data/alloy/)
- [Grafana Loki datasource ve derived fields](https://grafana.com/docs/grafana/latest/datasources/loki/configure-loki-data-source/)

### 9.7 Grafana arayüz geliştirmesi

- Prometheus datasource otomatik provision edilir.
- Loki datasource otomatik provision edilir.
- Dashboard provider otomatik tanımlanır.
- Version-controlled dashboard JSON yüklenir.
- EventFlow dashboard varsayılan ana ekran olur.
- Sabit dashboard UID kullanılır.
- Manuel import veya UI tıklaması gerekmez.
- Loki datasource derived field ayarı `requestId` değerini yakalayıp aynı request için Explore sorgusuna bağlantı oluşturur.
- Grafana Explore ve Logs Drilldown üzerinden JSON alanları açılarak incelenebilir.

Dashboard panelleri:

1. Request throughput.
2. HTTP status dağılımı.
3. p50/p95/p99 latency.
4. En yavaş route'lar.
5. Reservation outcome dağılımı.
6. Capacity rejection oranı.
7. Event row-lock bekleme histogramı.
8. Idempotency replay ve duplicate oranı.
9. Rate-limit rejection.
10. PostgreSQL ve Redis readiness.
11. 5xx error trend.
12. Uygulama uptime.
13. Son ERROR logları.
14. Seçilen route için canlı log akışı.
15. Request ID ile tek isteğin uçtan uca log kayıtları.

Arayüz standardı:

- Türkçe panel başlıkları.
- Doğru birimler ve okunabilir legends.
- Success yeşil, warning turuncu, error kırmızı.
- `$route`, `$status`, `$level`, `$service` ve `$interval` değişkenleri.
- Her panelde kısa açıklama.
- No-data durumu yanıltıcı sıfır göstermez.
- Manuel inceleme sırasında tek ekranda okunabilir düzen.
- Metrics dashboard ile log dashboard'u ayrı Grafana klasöründe düzenlenir; operasyon overview ekranı ikisine link verir.
- CI Grafana API üzerinden Prometheus/Loki datasource, dashboard UID ve LogQL sorgu sonucunu doğrular.

Manuel doğrulamada API hata gövdesindeki request ID kopyalanacak, Grafana'da request ID filtresiyle aynı isteğin başlangıç, domain sonucu ve response logları gösterilecek.

## 10. Test Stratejisi

### 10.1 Backend unit testleri

- Event validation.
- Timezone ve DST dönüşümü.
- ISO offset ile IANA timezone uyuşmazlığı, nonexistent ve ambiguous DST senaryoları.
- Capacity policy.
- Version conflict mapping.
- Error-code mapping.
- Idempotency request hash.
- Idempotency semantic snapshot'tan request ID çıkarma ve replay sırasında güncel request ID enjeksiyonu.
- Cursor encode/decode ve filter hash.
- Audit diff üretimi.
- Config fail-fast.
- Log redaction.

### 10.2 Integration testleri

Gerçek PostgreSQL ve Redis Testcontainers ile:

- Register/login/me/refresh/logout.
- Refresh rotation ve token replay.
- Refresh `token_hash` unique constraint'i, aynı tokenla eşzamanlı refresh yarışı, family-wide revoke ve cleanup'ın aktif family zincirini koruması.
- Tüm role ve IDOR matrisi.
- Event create/update/cancel.
- Owner-scoped `GET /me/events/{eventId}` için own/not-found/başkasına ait kaynakta gizlenen 404 matrisi.
- Create ve PATCH için offset-IANA eşleşmesi; başlamış/iptal edilmiş event update reddi.
- Capacity decrease.
- Attendee list ownership.
- Reservation create/cancel/reactivate.
- Geçmiş event.
- Idempotency replay.
- Replay'de status ve semantik body eşitliği, güncel `X-Request-ID` ile hata body'sindeki `requestId` eşitliği ve `Idempotency-Original-Request-ID` doğrulaması.
- Aynı key ve farklı payload.
- Concurrent unique-conflict yolu: owner transaction açık tutulurken ikinci request aynı key'i claim etmeye çalışır; ikinci insert'in beklediği, owner commit'inden sonra mevcut satırı okuyup aynı response'u replay ettiği ve ikinci domain write üretmediği kanıtlanır.
- Concurrent owner rollback yolu: ilk transaction rollback edilir; bekleyen ikinci request key'i claim edip işlemi bir kez tamamlar.
- Beklenmeyen `PROCESSING` kaydı yolu: kontrollü fixture ile `409 IDEMPOTENCY_IN_PROGRESS`, `Retry-After`, warning log ve metriğin birlikte üretildiği doğrulanır.
- Audit aynı transaction'da oluşuyor.
- Audit update/delete DB trigger tarafından reddediliyor.
- Migration boş DB'de çalışıyor.
- Seed iki kez duplicate üretmiyor.
- `/health` ve `/ready` ayrımı.
- Rate-limit 429 ve `Retry-After`.
- JSON log schema ve request ID propagation.
- Loki/Alloy smoke: bilinen request ID içeren backend logu Loki'ye ulaşır ve LogQL ile bulunur.
- Yetkisiz ID tabanlı endpointlerin kaynak var olsun veya olmasın aynı 404 envelope'unu döndürmesi.
- CORS wildcard fail-fast.
- Eksik zorunlu env fail-fast.
- SIGTERM sırasında akan request tamamlama.

### 10.3 Zorunlu concurrency testleri

Kapasitesi 1 olan event için 200 farklı attendee paralel istek:

- Tam bir `201`.
- 199 adet `409 EVENT_FULL`.
- Bir aktif reservation.
- `reserved_count == 1`.
- Bir reservation-created audit.

Ek yarış testleri:

- Aynı attendee ve aynı idempotency key ile beş paralel istek: bir owner çalışır, dört istek unique-conflict/replay yoluna girer; beşi de aynı status/body'yi alır, tek reservation ve tek create audit oluşur.
- Aynı attendee ve farklı keyler.
- Booking/cancellation yarışı.
- Booking/capacity update yarışı.
- Booking/event cancellation yarışı.
- Cancellation deadlock regression: iki kontrollü transaction barrier ile cancellation ve create/rebook akışları çakıştırılır; her ikisinin de `event -> reservation` sırasını izlediği, timeout/deadlock oluşmadığı ve nihai sayacın doğru kaldığı kanıtlanır.
- Cancellation lock doğrulaması testte adım adım yapılır: ownership-scoped non-locking `event_id` lookup, event `FOR UPDATE`, reservation `FOR UPDATE`, state revalidation, sayaç/audit ve commit.
- Her test sonunda `reserved_count == ACTIVE reservation count`.

### 10.4 Frontend testleri

- Form validation.
- Loading/empty/error/success.
- API error ve request ID mapping.
- Token refresh single-flight.
- Retry sırasında idempotency key korunması.
- Timezone gösterimi.
- Version conflict dialog.
- Query invalidation.
- Role navigation.
- `CursorPagerState`: ilk sayfa `null`, ileri giderken cursor append, geri giderken API'den `previousCursor` beklemeden client history kullanımı.
- Filtre/sort/limit değişiminde ve sıralamayı etkileyen mutation sonrasında cursor history reseti.
- Detail sayfasından browser back ile dönüşte cursor history'nin korunması; hard refresh'in bilinçli olarak ilk sayfaya dönmesi.

### 10.5 Playwright E2E

- Public event list/detail/search/filter.
- Attendee register/login.
- Organizer register/login.
- Organizer event create/edit.
- İkinci sekme version conflict.
- Attendee reservation.
- Duplicate ve full event.
- Reservation cancellation.
- İptal sonrası rebook.
- Arada dolan eventte rebook rejection.
- Organizer attendee listesi.
- Organizer event cancellation.
- Loading, empty ve error ekranları.
- Direct URL role koruması.
- Request ID gösterimi.
- Docker ile tam user journey.

Playwright MCP keşifsel/görsel QA için kullanılabilir; commit edilen testlerin yerine geçmez.

## 11. GitHub, Commit ve Pull Request Disiplini

### 11.1 Branch protection

- İlk bootstrap sonrasında `main` doğrudan commit almayacak.
- PR zorunlu olacak.
- CI kontrolleri zorunlu olacak.
- Conversation resolution zorunlu olacak.
- Force push ve branch delete koruması uygulanacak.
- En az bir approval, tek kişilik case'te mümkün değilse açıklamalı self-review ve bütün CI kanıtı kullanılacak; değerlendirici erişimi sonrası gerçek review tercih edilecek.

### 11.2 Branch adları

- `chore/foundation-db`
- `feat/auth-authorization`
- `feat/events`
- `feat/reservations-integrity`
- `feat/frontend`
- `feat/ops-delivery`
- Bug fix için `fix/<short-description>`.

### 11.3 Commit standardı

Conventional Commits kullanılacak:

```text
<type>(<scope>): <imperative summary>
```

Kurallar:

- Subject kısa, net ve imperative olacak.
- Her commit tek mantıksal değişiklik taşıyacak.
- `wip`, `changes`, `fix stuff`, `final`, `last fix` gibi mesajlar yasak.
- Refactor ve davranış değişikliği aynı belirsiz committe karıştırılmayacak.
- Migration, model ve ilgili test mümkün olduğunca aynı anlamlı committe olacak.
- Generated client güncellemesi API değişikliğiyle aynı committe olacak.
- Secret veya local `.env` hiçbir committe bulunmayacak.
- PR merge stratejisi `Rebase and merge`; iyi hazırlanmış commit geçmişi korunacak.

Örnek commit dizisi PR sınırlarına göre gruplanacak:

```text
# PR 1 - Foundation + DB/migrations
chore(repo): initialize monorepo tooling
feat(db): define relational schema and constraints
feat(db): add versioned Alembic migrations
feat(seed): add idempotent demo data
ci: add baseline quality gates
docs(architecture): record modular monolith boundaries

# PR 2 - Auth + authorization
feat(auth): implement rotating refresh token flow
feat(authz): hide unauthorized resources behind not-found responses
feat(security): enforce CORS and rate-limit policies
test(authz): cover role and IDOR attack matrix

# PR 3 - Events
feat(events): add organizer-owned event lifecycle
feat(events): reject stale updates with version checks
feat(events): add cursor-paginated public listing
test(events): cover ownership and capacity updates

# PR 4 - Reservations + concurrency + idempotency + audit
feat(reservations): enforce capacity with event row locks
feat(reservations): apply deterministic cancellation lock ordering
feat(idempotency): claim keys and replay concurrent conflicts
feat(audit): persist immutable critical action logs
test(reservations): prove capacity under concurrent requests

# PR 5 - Frontend
feat(frontend): add in-memory auth session flow
feat(frontend): add public event discovery flow
feat(frontend): preserve backward paging with cursor history
feat(frontend): add organizer event management
feat(frontend): add attendee reservation lifecycle
test(e2e): cover P0 organizer and attendee journeys

# PR 6 - Ops/P1/P2 and delivery
feat(search): add full-text and category-date filters
feat(observability): add structured request logging
feat(metrics): expose reservation and HTTP metrics
feat(logs): ship Docker logs with Alloy and Loki
feat(grafana): provision metrics and log operations dashboards
feat(ops): add readiness and graceful shutdown
ci: enforce delivery and security quality gates
docs: complete delivery guidance
```

### 11.4 Pull Request planı

Tam olarak aşağıdaki altı okunabilir ve domain-odaklı PR planlanacak. Bir PR başka başlıktaki işi erkenden içine almayacak:

#### PR 1 - Foundation + DB/migrations (`chore/foundation-db`)

- Monorepo, backend/frontend tooling, root ve nested AGENTS, Docker/Compose foundation.
- PostgreSQL/Redis servisleri, bütün temel tablolar, constraint/indexler ve ilk Alembic migration.
- Refresh token unique hash, token-family/self-FK constraintleri ve destekleyici indeksler.
- İdempotent seed komutu ve migration/seed smoke testleri.
- P0 ortak altyapı: tutarlı error envelope, request ID middleware, seviyeli JSON logger, `/health`, DB/Redis kontrollü `/ready` ve başlangıç sırası.
- Baseline CI: lint, format, type, unit, migration/seed smoke, dependency audit ve Docker build skeleton.
- İlk `ARCHITECTURE.md` ve `DECISIONS.md` kararları.
- Kabul: temiz DB `alembic upgrade head` ile kuruluyor, seed iki çalıştırmada duplicate üretmiyor, refresh token constraint/index migration testleri ve ortak error/log/request-ID/health-ready testleri yeşil.

#### PR 2 - Auth + authorization (`feat/auth-authorization`)

- Register, login, me, refresh rotation/replay ve logout.
- Argon2id, access JWT, opaque refresh token ve cookie politikası.
- Role dependencies ve kaynak varlığını gizleyen IDOR politikası.
- ID tabanlı yetkisiz erişimde 404; yalnız genel capability reddinde 403.
- CORS, security headers ve login rate limiting.
- Auth/authorization/IDOR integration testleri; eşzamanlı refresh rotation, token replay, family-wide revoke ve güvenli cleanup testleri.
- Kabul: saldırgan matrisi ve token replay testleri yeşil.

#### PR 3 - Events (`feat/events`)

- Seed edilmiş category read API.
- Organizer event create/update/soft-delete ve ownership.
- Organizer yönetim ekranları için owner-scoped `GET /me/events/{eventId}`.
- Optimistic version conflict ve kapasite düşürme kuralı.
- UTC/IANA timezone, ISO offset-zone eşleşmesi, DST ve başlamış event kuralları.
- Event create/update/cancel audit kayıtları ilgili domain işlemiyle aynı transaction'da.
- P0 public event listing/detail ve cursor pagination.
- Event unit/integration testleri ve query/index kanıtı.
- P1 search/category/date filter bu PR'a alınmayacak; PR 6'da tamamlanacak.
- Kabul: organizer event yaşam döngüsü, owner-detail 404 matrisi, offset-zone/DST kuralları, same-transaction audit ve stale edit testi yeşil.

#### PR 4 - Reservations + concurrency + idempotency + audit (`feat/reservations-integrity`)

- Reservation create/cancel/history ve organizer attendee listesi.
- Ortak event-first lock ordering ve `reserved_count` invariant'ı.
- Concurrent idempotency owner/unique-conflict/replay algoritması.
- Request ID içermeyen semantik response snapshot'ı; replay sırasında güncel request ID enjeksiyonu ve original request ID header'ı.
- Reservation endpoint'i Redis rate limiting ve `429 Retry-After` testi.
- Event cancellation sırasında reservation bulk transition.
- Event ve reservation kritik işlemleri için immutable audit.
- 200 parallel request, same-key winner/loser, different-key duplicate ve deadlock regression testleri.
- PR açıklamasında test komutu, başarı/409 dağılımı ve final DB invariant sonucu.
- Kabul: capacity, idempotency, replay request-ID tutarlılığı, reservation rate limiting, cancellation ve audit atomikliği gerçek PostgreSQL/Redis ile kanıtlanır.

#### PR 5 - Frontend + P0 kapanışı (`feat/frontend`)

- Auth bootstrap/refresh/logout UX.
- Public event list/detail ve `CursorPagerState` ile geri navigasyon.
- Organizer event CRUD/conflict/attendee ekranları.
- Attendee reservation/cancellation/rebook ekranları.
- Loading, empty, error, validation, request ID ve accessibility durumları.
- Generated OpenAPI client, component testleri ve bütün P0 Playwright journey'leri.
- P0 full Compose: DB/Redis health, migrate/seed tamamlanması, backend readiness ve frontend başlangıç sırası.
- P0 CI kapanışı: backend/frontend testleri, gerçek PostgreSQL concurrency, Docker build, dependency audit, migration/seed ve clean-clone smoke.
- P0 dokümantasyon kapanışı: README ve DECISIONS gerçek davranış, seed hesapları, çalıştırma komutları ve bilinçli bırakılanlarla güncel olacak.
- PR açıklamasında ana ekran screenshotları veya kısa GIF.
- Kabul: PDF'teki ürün, veri bütünlüğü, güvenlik, altyapı, API, gözlemlenebilirlik, test, CI ve dokümantasyon dahil bütün P0 maddeleri ayrı P0 kabul matrisiyle yeşildir.
- PR 5 merge edilmeden ve P0 kabul matrisi onaylanmadan PR 6 branch'i açılmaz; P1 veya P2 kodu yazılmaz.

#### PR 6 - Ops/P1/P2 ve teslim düzenlemeleri (`feat/ops-delivery`)

- Başlangıç koşulu: PR 5 P0 kabul matrisi tamamen yeşil ve onaylanmış olmalı.
- P1 aşaması: full-text search, category/date filter ve ilgili frontend kontrolleri.
- P1 aşaması: graceful shutdown, PR template, CODEOWNERS ve SECURITY governance dosyaları.
- P1 kabul kapısı: arama/filtre, governance ve SIGTERM drain testleri yeşil olmadan P2'ye geçilmez.
- P2 aşaması: seçilen tek bonus olan Prometheus metrics endpoint'i; ardından bunu tamamlayan Loki, Alloy ve Grafana metric/log dashboard'ları.
- Teslim hardening: tam Compose regresyonu, Playwright hardening, dependency audit, secret scan ve observability smoke.
- README, DECISIONS, ARCHITECTURE, API, TESTING, OPERATIONS ve CONTRIBUTING finalizasyonu.
- PR açıklamasında clean-clone çıktısı, Grafana screenshotı ve PromQL/LogQL örnekleri.
- Kabul: daha önce kapanmış P0 matrisi regresyonsuz; P1 ve ardından tek seçili P2 ayrı ayrı yeşil; CI ve teslim kriterleri tamamlanmış.

PR açıklama şablonu:

- Amaç.
- Yapılan değişiklikler.
- Teknik karar ve trade-off.
- API/schema/migration etkisi.
- Security ve privacy etkisi.
- Test komutları ve sonuçları.
- Screenshot/Grafana ekranı.
- Dokümantasyon güncellemesi.
- Bilinçli bırakılanlar.

## 12. CI ve Kalite Kapıları

Her push ve PR'da:

1. Markdown lint ve internal link kontrolü.
2. Compose ve config validation.
3. Backend Ruff format/lint.
4. Backend strict type check.
5. Frontend ESLint/Prettier.
6. TypeScript type check.
7. Backend unit/integration/concurrency.
8. Frontend component testleri.
9. OpenAPI client regeneration ve temiz diff.
10. Alembic migration smoke.
11. Seed repeatability.
12. Backend/frontend Docker build.
13. Tam Compose ve Playwright.
14. `promtool check config`.
15. Prometheus target `UP`.
16. Loki ready ve Alloy component health kontrolü.
17. Backend test logunun Loki'ye ulaştığını ve request ID ile LogQL sorgulanabildiğini doğrulama.
18. Grafana health, Prometheus/Loki datasource ve dashboard smoke.
19. `pip-audit`.
20. `pnpm audit --prod`.
21. Secret/history scan.

Coverage raporu üretilecek fakat yapay yüzde kapısı konmayacak.

P0 kabul kapısı PR 5 sonunda CI sonuçlarından ayrı, okunabilir bir matris olarak üretilecek. Bu matrisin tek bir maddesi bile kırmızıysa PR 6 branch'i açılmayacak ve P1/P2 işi başlamayacak.

## 13. Dokümantasyon ve Aktif AGENTS.md

### 13.1 Markdown paketi

- `README.md`: ürün, roller, kurulum, URL'ler, seed hesaplar, komutlar, kapsam ve yapılmayanlar.
- `ARCHITECTURE.md`: context/container/component/ER/sequence diyagramları, modül sınırları, indeksler ve ölçek.
- `DECISIONS.md`: karar, alternatif, neden, feda formatıyla en az 15 karar.
- `API.md`: auth, error, cursor, idempotency, version ve timezone sözleşmeleri.
- `TESTING.md`: test matrisi, Testcontainers, concurrency ve E2E.
- `OPERATIONS.md`: env, migration, seed, logs, request ID, health/ready, Prometheus/Loki/Alloy/Grafana ve troubleshooting.
- `SECURITY.md`: auth, IDOR, CORS, CSRF, PII, rate limit ve vulnerability reporting.
- `CONTRIBUTING.md`: branch, commit, PR, migration, dependency ve Definition of Done.
- `.github/PULL_REQUEST_TEMPLATE.md` ve `.github/CODEOWNERS`.

### 13.2 DECISIONS.md aktif kullanım

Kararlar:

1. FastAPI modüler monolit.
2. PostgreSQL ve async SQLAlchemy.
3. Event row lock ve `reserved_count`.
4. Idempotency table ve natural unique constraint.
5. UTC instant ve IANA timezone.
6. Version optimistic concurrency.
7. Soft event cancellation.
8. Immutable DB audit.
9. Access JWT ve opaque rotating refresh.
10. Redis rate limiting.
11. Cursor pagination.
12. Seed edilmiş kategori kataloğu.
13. Prometheus, Loki, Alloy ve Grafana gözlemlenebilirlik pipeline'ı.
14. KVKK anonymization.
15. Loki label cardinality ve 7 günlük lokal retention politikası.
16. Refresh token unique hash, family zinciri, rotation kilidi ve replay halinde family-wide revoke.
17. Idempotency snapshot'ından request ID'yi ayırma; replay'de güncel ve original correlation ID semantiği.
18. Event ISO offset-IANA timezone eşleşmesi ve DST kabul politikası.
19. Organizer yönetim ekranlarında public detail yerine owner-scoped detail endpoint'i.

Her karar:

```text
Karar:
Değerlendirdiğim alternatifler:
Neden bunu seçtim:
Neyi feda ettim:
```

- Mimari veya iş kuralı değişen PR, ilgili decision güncellenmeden tamamlanmış sayılmayacak.
- 'Best practice olduğu için' gerekçesi kabul edilmeyecek.

### 13.3 Katmanlı AGENTS.md

Root kuralları:

- P0 bitmeden P1/P2'ye geçme.
- PR 5 sonunda P0 kabul matrisi tamamen yeşil ve onaylanmış değilse PR 6 branch'i açma; PR 6 içinde bütün P1 kriterleri bitmeden P2 kodu yazma.
- Mikroservis oluşturma.
- Secret/PII commit veya loglama.
- Public API değişiminde OpenAPI client, docs ve test güncelle.
- Migration rewrite etme.
- Reservation/capacity/event cancellation lock invariant'ını bozma.
- Server-side authorization ve ownership zorunlu.
- Kritik davranış değişiminde test ve DECISIONS güncelle.
- Docker Compose kabul akışını doğrula.

Backend kuralları:

- Async SQLAlchemy.
- Router'da iş kuralı yok.
- Repository'de commit yok.
- Transaction application service'te.
- Concurrency testinde SQLite yok.
- Schema değişiminde Alembic zorunlu.
- Audit aynı transaction'da.
- PII loglama yok.
- Reservation writer'larında kilit sırası sabittir: create/rebook için `idempotency row -> event -> reservation -> audit -> idempotency finalize`; cancellation için non-locking ownership lookup sonrası `event -> reservation -> audit`.
- Event lock alınmadan reservation satırına `FOR UPDATE` uygulanamaz; yeni bir writer eklenirse aynı deadlock regression test matrisi genişletilir.
- Idempotency claim atomik `INSERT ... ON CONFLICT DO NOTHING RETURNING` ile yapılır; `RETURNING` boşsa mevcut kayıt lock edilip hash/state kontrol edilmeden domain işlemi başlatılamaz.
- Idempotency snapshot'ında request ID saklanmaz; replay edilen semantik response'a güncel request ID enjekte edilir ve body/header correlation ID değerleri eşit tutulur.
- Owner edit/detail akışında public event detail kullanılmaz; `GET /me/events/{eventId}` ownership-scoped sorgu zorunludur.
- Event create ve PATCH işlemlerinde ISO offset ile IANA timezone aynı instant için uyuşmalıdır.

Frontend kuralları:

- Generated API client.
- Access token kalıcı storage'a yazılmaz.
- Refresh single-flight.
- Idempotency key retry boyunca korunur.
- Loading/empty/error zorunlu.
- UI guard security kabul edilmez.
- Accessibility ve responsive kontrol.
- Liste API'sinden `previousCursor` beklenmez; geri navigasyon route-level `CursorPagerState.cursors` geçmişinden yapılır.
- Filtre, sort, limit veya liste sırasını değiştiren mutation cursor geçmişini `[null]` durumuna resetler.

E2E kuralları:

- Fixed sleep yok.
- Testler izole.
- Semantic selector.
- Failure artifact: trace ve screenshot.
- Concurrency backend integration testinde.
- Retry ile flake gizlenmez.

## 14. On Günlük Uygulama Takvimi

### Gün 1 - PR 1: Foundation başlangıcı

- Git repo, private remote ve branch protection.
- Monorepo.
- Root ve nested AGENTS.md.
- Markdown belgelerin ilk gerçek sürümü.
- CI skeleton.
- Backend/frontend boş health build.
- P0 error envelope, request ID middleware ve seviyeli JSON logging temeli.
- PR 1 ilk commitleri hazırlanır; henüz merge edilmez.
- Kabul: lint, type ve build skeleton yeşil.

### Gün 2 - PR 1: DB/migrations ve merge

- Tablolar, constraintler ve indeksler.
- İlk Alembic migration.
- Audit trigger.
- Refresh token unique hash, family/self-FK constraintleri ve cleanup indeksleri.
- Idempotent seed.
- Multi-stage ve non-root Dockerfile.
- Compose foundation.
- `/health`, DB/Redis `/ready` ve dependency-aware başlangıç sırası.
- Migration/seed smoke ve schema dokümantasyonu.
- PR 1 self-review, temiz diff ve CI sonrası rebase-merge.
- Kabul: temiz volume ile DB kurulumu ve tekrar seed çalışır.

### Gün 3 - PR 2: Auth + authorization

- Register/login/me/refresh/logout.
- Argon2id ve refresh rotation.
- Fail-fast config.
- CORS ve security headers.
- Login Redis rate limiting.
- Resource-hiding 404 authorization politikası.
- Auth, token replay, role ve IDOR saldırgan testleri.
- PR 2 self-review ve rebase-merge.
- Kabul: kaynak ID'si içeren bütün yetkisiz erişimler 404; genel capability reddi 403.

### Gün 4 - PR 3: Events

- Category API.
- Event CRUD.
- Owner-scoped organizer event detail endpoint'i.
- Optimistic version.
- Soft cancellation altyapısı.
- UTC/IANA, ISO offset-zone ve DST validation.
- Event create/update/cancel same-transaction audit.
- P0 public cursor listing/detail; search ve filtre henüz yok.
- Query plan kontrolü.
- PR 3 self-review ve rebase-merge.
- Kabul: event P0, owner ve stale-edit testleri yeşil.

### Gün 5 - PR 4: Reservations + concurrency + idempotency + audit

- Row lock ve `reserved_count`.
- Concurrent owner/unique-conflict/replay idempotency algoritması.
- Semantik response replay, güncel request ID enjeksiyonu ve original request ID correlation header'ı.
- Reservation Redis rate limiting.
- Reserve/cancel/reactivate.
- Event-first cancellation lock sırası.
- Event cancellation bulk transition.
- Immutable audit.
- 200 parallel ve race testleri.
- PR 4 açıklamasına test dağılımı ve DB invariant sonucu eklenip rebase-merge edilir.
- Kabul: bütün reservation, idempotency, lock-order ve audit invariantları gerçek PostgreSQL'de kanıtlanır.

### Gün 6 - PR 5: Frontend foundation ve public akış

- MUI theme/layout.
- Generated API client.
- Auth bootstrap/refresh.
- Public list/detail ve client cursor history ile ileri/geri navigasyon.
- Loading/empty/error.
- PR 5 açık tutulur.
- Kabul: public, auth ve cursor-back journey çalışır.

### Gün 7 - PR 5: Rol panelleri, P0 kabul kapısı ve merge

- Organizer CRUD/conflict/attendees.
- Attendee reservation/cancellation.
- Idempotency UX.
- Timezone gösterimi.
- Component ve Playwright testleri.
- P0 full Compose, clean-clone, dependency audit, migration/seed ve gerçek PostgreSQL concurrency kapanışı.
- PDF'teki bütün P0 maddeleri için ayrı kabul matrisi; tek kırmızı maddede PR 6 ve P1/P2 başlangıcı engellenir.
- PR 5 screenshot/GIF, self-review ve rebase-merge.
- Kabul: PDF P0 kullanıcı akışlarıyla birlikte güvenlik, altyapı, API, gözlemlenebilirlik, test, CI ve dokümantasyon maddelerinin tamamı yeşil.

### Gün 8 - PR 6: Önce P1, sonra P2 gözlemlenebilirlik

- Ön koşul: PR 5 P0 kabul matrisi tamamen yeşil ve onaylanmış.
- Full-text search, category/date filter ve frontend kontrolleri.
- Graceful shutdown ve P1 governance dosyaları.
- P1 arama/filtre/governance/SIGTERM kabul kapısı.
- P1 tamamen yeşil olduktan sonra Prometheus metrics.
- Loki single-binary storage ve retention.
- Alloy Docker discovery, JSON parsing ve Loki write pipeline.
- Grafana Prometheus/Loki datasource ve dashboard provisioning.
- Metrics/log dashboard panelleri ve variables.
- Request-ID ile Grafana log arama doğrulaması.
- PR 6 açık tutulur.
- Kabul: P1 kabul kapısı önce yeşildir; ardından seçilen tek P2 ve tamamlayıcı dashboard ilk açılışta metrik/log gösterir, request ID LogQL ile bulunur.

### Gün 9 - PR 6: Hardening ve governance

- Tam Playwright paketi.
- Security negatifleri.
- Compose clean-clone provası.
- Migration/seed tekrarı.
- Prometheus/Loki/Alloy/Grafana smoke.
- Dependency ve secret scan.
- Daha önce oluşturulan PR template, CODEOWNERS ve SECURITY içeriğinin/erişim desenlerinin doğrulanması ve final CI gates.
- Kabul: bütün otomatik kalite kapıları yeşil.

### Gün 10 - PR 6: Teslim düzenlemeleri ve merge

- Doküman/code tutarlılığı.
- PR ve commit geçmişi.
- CODEOWNERS, SECURITY ve governance.
- Repo history secret scan.
- Repo public.
- README repository linki ve bütün çalıştırma komutları doğrulanır.
- PR 6 clean-clone/Grafana kanıtlarıyla self-review edilip rebase-merge edilir.
- Kabul: değerlendirici manuel yardım almadan sistemi çalıştırır.

## 15. Teknik Riskler ve Ölçek Sınırları

- En zayıf nokta: `reserved_count` ve reservation ledger eşitliği bütün writer'ların aynı lock protokolünü kullanmasına dayanır; reconciliation job sonraki adımdır.
- İlk ölçek darboğazı: genel kullanıcı sayısından ziyade tek hot event satırındaki lock kuyruğu ve latency.
- Daha büyük ölçekte: waiting room, queue, reconciliation, idempotency cleanup ve object-storage tabanlı Loki ölçeklendirmesi.
- Bilinçli bırakılanlar: notification/outbox, distributed tracing, cache, canlı kontenjan ve deploy.
- Baştan başlanırsa audit/outbox sınırı ve cleanup job'ları daha erken modellenir.

## 16. PDF Gereksinimleri Kabul Matrisi

| PDF gereksinimi | Plan ve kabul kanıtı |
|---|---|
| Register/login, iki rol | Auth API, Argon2id, JWT/refresh ve role testleri |
| Server-side authorization | Role dependency ve application service kontrolleri |
| IDOR yok | Ownership-scoped SQL; ID tabanlı bütün yetkisiz erişimler kaynak varlığını gizlemek için 404 |
| Organizer event CRUD | Owner-scoped create/update/soft-delete |
| Capacity aşağı düşmez | Event lock ve `CAPACITY_BELOW_RESERVATIONS` |
| Katılımcı listesi | Yalnız event owner endpointi |
| Public pagination | API yalnız `nextCursor`; frontend route-level cursor history ile ileri/geri, filtre değişiminde reset |
| Reserve/cancel/history | Attendee reservation lifecycle |
| Duplicate reservation yok | Unique constraint ve domain conflict |
| Capacity concurrency | Row lock, sayaç, check constraint ve 200 request testi |
| Cancellation seat açar | Non-locking ownership lookup sonrası uygulanabilir `event -> reservation -> audit` lock sırası ve aynı transaction'da `reserved_count -= 1` |
| Past event block | DB `now()` kontrolü |
| Loading/empty/error | Her async UI ekranı için standart state |
| Client/server validation | Zod, Pydantic, domain ve DB constraint |
| Idempotency | Atomik key claim; concurrent unique-conflict bekleme/read/replay, owner rollback takeover, request hash, aynı semantik response ve her deneme için tutarlı güncel request ID |
| Timezone | UTC instant, IANA zone, ISO offset-zone eşleşmesi, DST ve DB clock |
| Audit | Same-transaction insert ve immutable DB trigger |
| Concurrent edit | `expectedVersion` ve 409 conflict |
| Organizer owner detail | `GET /me/events/{eventId}` ve ownership-scoped 404 matrisi |
| Refresh token integrity | Unique token hash, family ID, self-FK, rotation lock, family-wide replay revoke ve cleanup indeksleri |
| Delete policy | Soft cancellation ve reservation transition |
| KVKK | Anonymization decision |
| Rate limiting | Redis login/reservation limitleri |
| Security headers/CORS | Exact allowlist ve headers |
| Multi-stage/non-root | İki Dockerfile ve runtime UID |
| Healthcheck/start order | DB/Redis healthy, migrate/seed completed |
| 12-factor/fail-fast | Pydantic settings ve startup validation |
| Versioned migrations | Alembic; auto schema yasak |
| Repeatable seed | One-shot idempotent seed service |
| Conscious indexes | Query-linked index list ve EXPLAIN |
| Versioned API | `/api/v1` |
| Consistent errors | Tek error envelope ve request ID |
| OpenAPI/Swagger | Generated OpenAPI ve client |
| JSON structured logs | Seviyeli, context-aware ve redacted logs; Alloy ile Loki'ye gönderim |
| Request ID | Header, logs, audit, error body ve Grafana LogQL araması |
| `/health` ve `/ready` | Process/dependency ayrımı |
| Isolated tests | PostgreSQL/Redis Testcontainers |
| CI | Lint, type, tests, build, audit ve security scan |
| Git discipline | Protected main, Conventional Commits ve 6 PR |
| README/DECISIONS | Aktif ve CI/PR checklist ile güncel |
| Search/filter | FTS, category ve date filters |
| Governance files | PR template, CODEOWNERS, SECURITY |
| Graceful shutdown | SIGTERM drain ve integration test |
| One P2 | Prometheus metrics; Loki log görüntüleme ve provision edilmiş Grafana aynı gözlemlenebilirlik teslimini tamamlar |

## 17. Nihai Kabul Kriterleri

- `docker compose up` bütün sistemi manuel adımsız başlatır.
- PostgreSQL, Redis, backend, frontend, Prometheus, Loki, Alloy ve Grafana healthy olur.
- Migration ve seed otomatik; seed tekrar çalıştırılabilir.
- Eksik env'de uygulama port açmadan anlamlı hata verir.
- Runtime containerlar non-root.
- CORS wildcard kabul edilmez.
- Her hata aynı envelope ve request ID döndürür.
- İdempotency replay'inde hata body `requestId` değeri güncel `X-Request-ID` ile aynıdır; ilk owner correlation ID'si ayrı header'da korunur.
- Bütün backend logları seviyeli JSON'dur; secret veya gereksiz PII yoktur.
- `/health` ve `/ready` farklı davranır.
- Aynı event iki sekmede düzenlenince stale update reddedilir.
- Organizer edit ekranı owner-scoped detail endpoint'ini kullanır; başka organizerın event ID'si kaynak varlığını gizleyen 404 döndürür.
- Event create ve PATCH, ISO offset ile IANA timezone uyuşmazlığını ve geçersiz DST zamanını reddeder.
- Her async UI ekranında loading, empty, error ve success bulunur.
- Client ve server validation vardır.
- IDOR ve role bypass testleri başarısız saldırıları kanıtlar; kaynak UUID'si içeren yetkisiz erişimler 403 değil 404 döndürür.
- Kapasite hiçbir concurrency testinde aşılmaz.
- Beş eşzamanlı aynı-key istekte yalnız bir owner domain işlemini yürütür; unique-conflict loser'ları aynı response'u replay eder ve ikinci reservation/audit üretmez.
- Owner transaction rollback ederse bekleyen request key'i devralıp işlemi yalnız bir kez tamamlar.
- Cancellation bütün reservation writer'larıyla aynı `event -> reservation` kilit sırasını izler ve deadlock regression testi geçer.
- Cursor API yalnız `nextCursor` döndürür; frontend ileri/geri navigasyonu client cursor history ile yapar ve reset/geri-dönüş davranışları testlidir.
- Event cancellation reservationları güvenli kapatır.
- Audit kayıtları değiştirilemez veya silinemez.
- Prometheus target UP, Loki/Alloy pipeline healthy ve Grafana metrics/log dashboard'ları otomatik yüklüdür.
- Üretilen bir test request ID'si Grafana/Loki içinde bulunabilir.
- Testler lokal DB'ye bağımlı değildir.
- Search, category ve date filter çalışır.
- Graceful shutdown akan isteği yarım bırakmaz.
- README, DECISIONS ve diğer belgeler uygulama davranışıyla uyumludur.
- PR 5 sonunda bütün P0 kabul matrisi yeşil olmadan PR 6/P1 başlamaz; PR 6 içinde bütün P1 kabul kriterleri yeşil olmadan P2 başlamaz.
- Main protected, commit mesajları anlamlı ve en az altı açıklamalı PR bulunur.
- CI'ın bütün kalite, test, build, security ve observability kontrolleri yeşildir.

## 18. Sabit Varsayımlar

- Grafana metrics ve logs dashboard geliştirmesi kapsam içindedir; Loki/Alloy varsayılan Compose stack'inde çalışır.
- Structured loglar Docker stdout'unda üretilir, Alloy tarafından toplanır ve Loki'de 7 gün tutulur.
- Redis yalnız rate limiting içindir.
- Public event list/detail auth gerektirmez; reservation attendee auth gerektirir.
- Organizer rolü register sırasında seçilebilir.
- Category katalogu seed edilmiş ve salt okunurdur.
- Başlamış event update/cancel edilemez; attendee reservation iptal edemez.
- Public liste yalnız aktif ve gelecek eventleri gösterir.
- Event iptalinde fiziksel silme yapılmaz.
- Prometheus, Loki, Alloy ve Grafana tek bütünsel gözlemlenebilirlik çalışması olarak sunulur; PDF'teki P2 karşılığı Prometheus metrics endpoint'idir.
