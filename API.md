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

Event ve reservation endpoint sözleşmeleri ilgili PR'larda bu belgeye eklenecektir.
