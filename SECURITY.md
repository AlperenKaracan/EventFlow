# EventFlow Security

## Desteklenen sürümler

Aktif geliştirme yalnız `main` dalının son sürümünde desteklenir. Henüz yayımlanmış kararlı sürüm veya geriye dönük güvenlik düzeltmesi politikası yoktur. Repository public yapılmadan ya da ilk sürüm yayımlanmadan önce bu tablo semantik sürüm aralıklarıyla güncellenecektir.

## Credential modeli

- Parolalar Argon2id ile hash'lenir; düz parola/token/cookie loglanmaz.
- Access JWT varsayılan 15 dakika yaşar; issuer, audience, subject, role, issued-at, expiry ve unique JWT ID zorunludur.
- Refresh credential 48 random byte'tan üretilen opaque değerdir; PostgreSQL yalnız SHA-256 hash'ini saklar.
- Her login yeni token family başlatır. Her refresh önce PostgreSQL transaction advisory lock ile family'yi, ardından eski satırı `FOR UPDATE` ile kilitler ve rotate eder.
- Eski token replay'i, yarışın kazananı dahil aynı family'nin bütün aktif tokenlarını revoke eder. Client bu nedenle refresh isteklerini single-flight yapmalıdır.

Refresh cookie `HttpOnly`, `SameSite=Lax`, `/api/v1/auth` path'li ve production'da `Secure`'dır. Refresh/logout exact allowlist `Origin` kontrolü olmadan çalışmaz. Access token browser storage'a yazılmaz; yalnız frontend process belleğinde tutulur.

## Authorization ve IDOR

Server, JWT rolünü DB'deki aktif kullanıcı rolüyle yeniden karşılaştırır. UI görünürlüğü güvenlik sınırı değildir. Genel capability reddi 403'tür; UUID içeren owner-scoped kaynak erişimi 404 ile gizlenir. Event/reservation writer'ları client'tan organizer/attendee kimliği kabul etmeyecek, current user context'inden türetecektir.

## Browser ve transport kontrolleri

- CORS originleri environment exact allowlist'idir; wildcard startup'ta reddedilir.
- İzinli methodlar `GET, POST, PATCH, DELETE, OPTIONS`; request header'ları `Authorization, Content-Type, Idempotency-Key, X-Request-ID` ile sınırlıdır.
- CSP, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` ve `Referrer-Policy: no-referrer` her response'a eklenir.
- HSTS yalnız production'da etkinleştirilir. Swagger production'da kapalıdır.

## Brute force ve dependency failure

Login limiti IP + normalize e-posta, reservation limiti authenticated user UUID değerinin HMAC özetini Redis anahtarı olarak kullanır; ham IP/e-posta/user ID key'e yazılmaz. Sayaç ve TTL Lua ile atomiktir. Limit aşımı 429 + `Retry-After`; Redis erişilemezliği korumayı sessizce geçmek yerine 503 üretir.

## Token cleanup

Bakım komutu:

```powershell
Push-Location backend
uv run python -m app.auth.cleanup
Pop-Location
```

Cleanup yalnız aktif, revoke edilmemiş ve süresi dolmamış hiçbir üyesi bulunmayan family'lerden eligible expired/revoked satırları siler. Böylece aktif replacement zincirinin replay kanıtı korunur. Komut tekrar çalıştırılabilir ve silinen sayıyı structured loglar.

Idempotency semantic snapshot'ları request ID içermez; replay güncel request ID'yi enjekte eder ve original owner ID'yi yalnız ayrı header'da taşır. Kayıtlar 24 saat tutulur. Süresi dolan kayıtlar `uv run python -m app.idempotency.cleanup` ile tekrar çalıştırılabilir biçimde temizlenir.

## Secret ve Git geçmişi taraması

CI full history checkout üzerinde Gitleaks çalıştırır. `.gitleaksignore` yalnız doğrulanmış test-only değerlerin tam commit, dosya, kural ve satır fingerprint'lerini içerir; wildcard path, genel kural veya gerçek secret allowlist edilmez. Yeni bulgu önce redacted raporla incelenir. Gerçek secret bulunursa yalnız dosyadan silmek yeterli değildir; credential revoke/rotation ve Git history temizliği ayrı güvenlik işlemi olarak ele alınır.

## Zafiyet bildirimi

Credential, kişisel veri, erişim tokenı, çalışan exploit veya henüz giderilmemiş zafiyet ayrıntısı issue, pull request, discussion ya da herkese açık başka bir kanalda paylaşılmamalıdır.

Repository private durumdayken erişimi olan güvenlik araştırmacıları ve ekip üyeleri GitHub içindeki **Security > Advisories > New draft security advisory** akışını kullanmalıdır. Bildirim şu bilgileri içermelidir:

- Etkilenen endpoint, bileşen veya commit.
- Tekrar üretme adımları ve beklenen etki.
- Varsa güvenli proof-of-concept; gerçek kullanıcı verisi içermemelidir.
- Önerilen azaltım veya düzeltme fikri.

İlk alındı yanıtı için hedef süre 3 iş günü, ilk risk değerlendirmesi için 7 iş günüdür. Düzeltme doğrulanmadan ve koordineli açıklama tarihi kararlaştırılmadan ayrıntılar yayımlanmamalıdır. Repository halen private olduğu için GitHub Advanced Security ayarlarında private vulnerability reporting kontrolü sunulmaz. Public görünürlük açıkça onaylanırsa görünürlük değişikliğinin hemen ardından ve teslim bağlantısı paylaşılmadan önce private vulnerability reporting etkinleştirilip doğrulanmalıdır.

## Güvenlik düzeltmesi süreci

1. Bildirim private advisory içinde doğrulanır ve önem derecesi belirlenir.
2. Düzeltme private fork veya erişimi kısıtlı dalda hazırlanır; secret ve gerçek PII test verisine alınmaz.
3. Authorization, IDOR, replay, rate-limit ve ilgili regresyon testleri eklenir.
4. Gerekirse credential rotation, token-family revoke veya veri etki analizi uygulanır.
5. Düzeltme ve koordineli açıklama, doğrulama tamamlandıktan sonra yayımlanır.
