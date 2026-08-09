# EventFlow API

API kökü `/api/v1`'dir. OpenAPI belgesi `/api/v1/openapi.json`, Swagger UI production dışı ortamlarda `/docs` adresindedir.

## Ortak hata sözleşmesi

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "E-posta veya parola hatalı.",
    "requestId": "019...",
    "details": []
  }
}
```

Her hata hem body'de hem `X-Request-ID` header'ında aynı güncel request ID'yi taşır. Validation ayrıntıları güvenli alan/type bilgisiyle sınırlıdır; internal exception, SQL ve stack trace dönmez.

## Auth endpointleri

### `POST /api/v1/auth/register`

```json
{
  "email": "user@example.com",
  "fullName": "Example User",
  "password": "minimum-12-characters",
  "role": "attendee"
}
```

`role`, `attendee` veya `organizer` olabilir. E-posta lowercase normalize edilir, ad trim edilir. Başarı `201`; duplicate e-posta `409 EMAIL_ALREADY_REGISTERED`; şema hatası `422 VALIDATION_ERROR` döner.

### `POST /api/v1/auth/login`

```json
{
  "email": "user@example.com",
  "password": "minimum-12-characters"
}
```

Başarı body’si access tokenı, token tipini, saniye cinsinden ömrü ve kullanıcı projection'ını döner. Opaque refresh token yalnız `eventflow_refresh` HttpOnly cookie'sinde bulunur. Yanlış e-posta ve yanlış parola aynı `401 INVALID_CREDENTIALS` sonucunu üretir. IP + normalize e-posta limiti aşıldığında `429 RATE_LIMIT_EXCEEDED` ve `Retry-After` döner.

### `GET /api/v1/auth/me`

`Authorization: Bearer <access-token>` gerektirir. Token imzası/claim'leri ve aktif kullanıcının DB rolü birlikte doğrulanır. Eksik, bozuk, süresi dolmuş veya server state'iyle uyuşmayan token `401 UNAUTHENTICATED` ve `WWW-Authenticate: Bearer` döner.

### `POST /api/v1/auth/refresh`

Refresh cookie ve allowlist'te birebir eşleşen `Origin` header'ı gerektirir. Başarı eski tokenı revoke eder, aynı family içinde yeni opaque token üretir ve login response'u döner. Revoke edilmiş token replay'i family'nin bütün aktif üyelerini revoke eder; geçersiz token `401 INVALID_REFRESH_TOKEN`, eksik/yabancı origin `403 INVALID_ORIGIN` döner.

### `POST /api/v1/auth/logout`

Exact `Origin` gerektirir; bilinen cookie'nin tüm token family'sini revoke eder, cookie'yi siler ve `204` döner. Cookie yoksa işlem idempotent kalır.

## Authorization status politikası

- Authentication yok/geçersiz: `401 UNAUTHENTICATED`.
- Kaynak UUID'si içermeyen genel capability reddi: `403 FORBIDDEN`.
- UUID tabanlı ownership/role erişimi yok veya kaynak yok: aynı `404 RESOURCE_NOT_FOUND`.

## Event endpointleri

### `GET /api/v1/categories`

Aktif kategori kataloğunu ad ve UUID ile kararlı sırada döner. Authentication gerekmez.

### `GET /api/v1/events`

Query parametreleri:

- `limit`: `1-100`, varsayılan `20`.
- `cursor`: Önceki yanıttaki opaque ve imzalı `nextCursor`.

Yalnız gelecekte başlayan `ACTIVE` eventler `(startsAt ASC, id ASC)` sırasıyla döner. Yanıt `items`, `nextCursor` ve `hasMore` alanlarını içerir; API `previousCursor` üretmez. Bozuk, değiştirilmiş veya başka liste bağlamından kopyalanmış cursor `400 INVALID_CURSOR` döner.

### `GET /api/v1/events/{eventId}`

Public event projection'ını döner. İptal edilmiş veya bulunmayan event aynı `404 RESOURCE_NOT_FOUND` sonucunu üretir.

### `POST /api/v1/events`

Organizer bearer token gerektirir; attendee için `403 FORBIDDEN` döner.

```json
{
  "categoryId": "20000000-0000-7000-8000-000000000001",
  "title": "EventFlow Buluşması",
  "description": "Teknik topluluk etkinliği",
  "location": "İstanbul",
  "startsAt": "2036-05-12T19:00:00+03:00",
  "timezone": "Europe/Istanbul",
  "capacity": 120
}
```

`startsAt` açık ISO-8601 offset taşımalıdır. Offset seçilen IANA timezone ile aynı instantta eşleşmezse, zaman DST gap içindeyse, kategori aktif değilse veya DB saatine göre gelecek değilse `422` döner. Başarı `201`, başlangıç sürümü `1` ve durum `ACTIVE`'dir.

### `PATCH /api/v1/events/{eventId}`

Owner-scoped mutasyondur. Body `expectedVersion` ve en az bir değişiklik taşımalıdır. `startsAt` ile `timezone` birlikte değiştirilir. Kapasite `reservedCount` altına indirilemez. Başlamış/iptal edilmiş event değiştirilemez. Başarıda sürüm bir artar; stale sürüm `409 EVENT_VERSION_CONFLICT`, lifecycle/kapasite çatışmaları kendi `409` domain kodlarını döner. Başka organizer'a ait veya bulunmayan UUID aynı `404 RESOURCE_NOT_FOUND` sonucunu üretir.

### `DELETE /api/v1/events/{eventId}?expectedVersion=1`

Hard delete yapmaz; event'i `CANCELLED` durumuna geçirir, `cancelledAt` yazar ve sürümü artırır. Başarı `204`'tür. Aktif reservation'ların `CANCELLED_BY_EVENT` bulk transition'ı PR 4 transaction kapsamındadır.

### `GET /api/v1/me/events`

Organizer'ın kendi eventlerini iptal/geçmiş kayıtlar dahil `(createdAt DESC, id DESC)` sırasıyla, public listeyle aynı `limit/cursor` sözleşmesiyle döner. Genel organizer capability yoksa `403` döner.

### `GET /api/v1/me/events/{eventId}`

Organizer yönetim ekranı için status, version ve lifecycle tarihlerini içeren owner projection'ıdır. Başkasına ait UUID, eksik UUID ve UUID tabanlı rol reddi aynı `404 RESOURCE_NOT_FOUND` sonucunu üretir.

Create/update/cancel başarılarında `event.created`, `event.updated` veya `event.cancelled` audit satırı domain değişikliğiyle aynı PostgreSQL transaction'ında yazılır.

Reservation endpoint sözleşmeleri PR 4'te bu belgeye eklenecektir.
