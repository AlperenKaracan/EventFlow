# EventFlow Security

## Credential modeli

- Parolalar Argon2id ile hash'lenir; düz parola/token/cookie loglanmaz.
- Access JWT varsayılan 15 dakika yaşar; issuer, audience, subject, role, issued-at, expiry ve unique JWT ID zorunludur.
- Refresh credential 48 random byte'tan üretilen opaque değerdir; PostgreSQL yalnız SHA-256 hash'ini saklar.
- Her login yeni token family başlatır. Her refresh eski satırı `FOR UPDATE` ile kilitler ve rotate eder.
- Eski token replay'i, yarışın kazananı dahil aynı family'nin bütün aktif tokenlarını revoke eder. Client bu nedenle refresh isteklerini single-flight yapmalıdır.

Refresh cookie `HttpOnly`, `SameSite=Lax`, `/api/v1/auth` path'li ve production'da `Secure`'dır. Refresh/logout exact allowlist `Origin` kontrolü olmadan çalışmaz. Access tokenın browser storage yerine yalnız frontend belleğinde tutulması hedeflenir.

## Authorization ve IDOR

Server, JWT rolünü DB'deki aktif kullanıcı rolüyle yeniden karşılaştırır. UI görünürlüğü güvenlik sınırı değildir. Genel capability reddi 403'tür; UUID içeren owner-scoped kaynak erişimi 404 ile gizlenir. Event/reservation writer'ları client'tan organizer/attendee kimliği kabul etmeyecek, current user context'inden türetecektir.

## Browser ve transport kontrolleri

- CORS originleri environment exact allowlist'idir; wildcard startup'ta reddedilir.
- İzinli methodlar `GET, POST, PATCH, DELETE, OPTIONS`; request header'ları `Authorization, Content-Type, Idempotency-Key, X-Request-ID` ile sınırlıdır.
- CSP, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` ve `Referrer-Policy: no-referrer` her response'a eklenir.
- HSTS yalnız production'da etkinleştirilir. Swagger production'da kapalıdır.

## Brute force ve dependency failure

Login limiti IP + normalize e-posta birleşiminin HMAC özetini Redis anahtarı olarak kullanır; ham IP/e-posta key'e yazılmaz. Sayaç ve TTL Lua ile atomiktir. Limit aşımı 429 + `Retry-After`; Redis erişilemezliği korumayı sessizce geçmek yerine 503 üretir.

## Token cleanup

Bakım komutu:

```powershell
Push-Location backend
uv run python -m app.auth.cleanup
Pop-Location
```

Cleanup yalnız aktif, revoke edilmemiş ve süresi dolmamış hiçbir üyesi bulunmayan family'lerden eligible expired/revoked satırları siler. Böylece aktif replacement zincirinin replay kanıtı korunur. Komut tekrar çalıştırılabilir ve silinen sayıyı structured loglar.

## Zafiyet bildirimi

Public issue içinde credential, kişisel veri veya exploit ayrıntısı paylaşılmamalıdır. Repository public yapılmadan önce özel vulnerability reporting kanalı etkinleştirilecek ve bu bölüm iletişim bilgisiyle güncellenecektir.
