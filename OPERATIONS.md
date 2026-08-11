# EventFlow Operasyon Rehberi

Bu rehber yerel Compose stack'ini başlatma, izleme ve sorun giderme adımlarını içerir. Üretim deploy'u ve harici alarm servisi proje kapsamında değildir.

## Başlatma ve durdurma

```powershell
Copy-Item .env.example .env
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 120
docker compose ps -a
```

Normal durdurma volume'ları korur:

```powershell
docker compose down
```

`docker compose down --volumes` PostgreSQL, Loki, Prometheus, Alloy ve Grafana yerel verisini siler. Yalnız açıkça temiz başlangıç istendiğinde kullanılmalıdır.

## Servisler

| Servis | Adres veya kontrol | Görev |
|---|---|---|
| Frontend | <http://localhost:8080> | Ürün arayüzü |
| Backend | <http://localhost:8000/health> | API process liveness |
| Readiness | <http://localhost:8000/ready> | PostgreSQL ve Redis kontrolü |
| Metrics | <http://localhost:8000/metrics> | Prometheus exposition |
| Swagger | <http://localhost:8000/docs> | Production dışında API arayüzü |
| Grafana | <http://localhost:3000> | Metrik ve log operasyon ekranları |

Prometheus ve Loki host portu yayınlamaz; Grafana bunlara Compose ağı üzerinden bağlanır. Bu servisler uygulama API'sinin çalışma bağımlılığı değildir.

## Yapılandırma

`.env.example` güvenli lokal başlangıç değerlerini ve bütün zorunlu anahtarları içerir. Önemli operasyon grupları:

- Uygulama: `APP_ENV`, `LOG_LEVEL`, `FRONTEND_PUBLIC_URL`, `BACKEND_PUBLIC_URL`.
- Veri: `DATABASE_URL`, PostgreSQL bootstrap değerleri, `REDIS_URL`.
- Güvenlik: JWT, cookie, CORS ve rate-limit değerleri.
- Kapanış: `GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS`.
- Loki/Alloy: `LOKI_RETENTION_PERIOD`, `ALLOY_DOCKER_REFRESH_INTERVAL`, `DOCKER_SOCKET_GID`.
- Prometheus: `PROMETHEUS_RETENTION_PERIOD`.
- Grafana: `GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD`, `GRAFANA_PUBLIC_URL`.

Production ortamı demo/default secret değerleriyle başlamaz. `.env` repository'ye commit edilmez.

## Migration ve seed

Compose önce PostgreSQL healthcheck'ini, sonra one-shot migration ve seed servislerini tamamlar. Backend yalnız ikisi başarıyla bittikten sonra başlar.

```powershell
docker compose run --rm migrate
docker compose run --rm seed
```

Seed tekrar çalıştırıldığında duplicate üretmez. Şema değişikliği yalnız yeni Alembic revision ile yapılır; runtime schema generation kullanılmaz.

## Health ve readiness

`/health` dependency kontrol etmeden `200 {"status":"ok"}` döndürür. `/ready`, PostgreSQL `SELECT 1` ve Redis `PING` çalıştırır. Bir dependency hazır değilse güvenli `503 DEPENDENCIES_NOT_READY` envelope'u döner.

```powershell
Invoke-WebRequest http://localhost:8000/health
Invoke-WebRequest http://localhost:8000/ready
```

Readiness sonucu Prometheus içinde `eventflow_readiness_status{dependency="postgresql|redis"}` metrikleriyle de izlenir.

## Loglar ve request ID

Backend stdout'a satır başına bir JSON nesnesi yazar. Temel alanlar `timestamp`, `level`, `service`, `environment`, `requestId`, `event`, `method`, route template, `status` ve `durationMs` değerleridir. Token, cookie, parola, authorization header, e-posta ve request body loglanmaz.

Terminal araması:

```powershell
docker compose logs backend --no-color | Select-String 'REQUEST_ID'
```

Grafana araması:

1. <http://localhost:3000> adresinde `.env` içindeki admin bilgileriyle giriş yapın.
2. `Log dashboardunu aç` bağlantısını seçin.
3. `Ortam`, `Servis`, `Seviye`, `Rota` ve `HTTP durumu` filtreleriyle inceleme kapsamını daraltın.
4. Performans sorunu için `Yavaş istek eşiği` değerini seçip `Yavaş istekler` ve `Rota bazında p95 istek süresi` panellerini karşılaştırın.
5. Uygulama davranışı için `İşlem sonuçları`, `Uygulama hata kodları` ve `İş alanı olay ayrıntıları` panellerini kullanın.
6. Hata body veya `X-Request-ID` header değerini `Request ID` alanına yapıştırın.
7. `Request ID uçtan uca zaman çizelgesi` panelinde başlangıç, iş alanı sonucu, rejection ve completion kayıtlarını kronolojik inceleyin.

Dashboard dört bölüme ve 17 analiz paneline ayrılır. Serbest arama için `Metin / regex` alanı kullanılabilir. Request ID, actor, event ve reservation kimlikleri JSON alanı olarak sorgulanır; Loki index label değildir.

Provision edilen dashboardun bütün LogQL sorgularını çalışan Grafana ve Loki üzerinde doğrulamak için:

```powershell
python observability/verify_log_dashboard.py
```

Eşdeğer LogQL:

```logql
{service_name="backend"} | json | requestId="REQUEST_ID"
```

Request ID JSON alanıdır, Loki index label değildir. Index label kümesi düşük cardinality `service_name`, `environment`, `level` ve route template alanlarıyla sınırlıdır. Beklenen HTTP reddetmeleri güvenli `errorCode`, status, method ve route template alanlarıyla `http.request.rejected` olayı olarak loglanır; response ayrıntıları veya kaynak kimlikleri toplu hata analizine taşınmaz.

## Audit log

Audit kayıtları ürün UI'sinde gösterilmez. Yetkili lokal operasyon incelemesi PostgreSQL üzerinden yapılır:

```powershell
docker compose exec -T db psql -U eventflow -d eventflow -c "SELECT created_at, actor_id, action, resource_type, resource_id, request_id, changes FROM audit_logs ORDER BY created_at DESC LIMIT 25;"
```

Audit satırı domain değişikliğiyle aynı transaction'da INSERT edilir. Uygulama UPDATE/DELETE yapmaz ve PostgreSQL trigger bu işlemleri reddeder.

## Prometheus ve Grafana

Prometheus backend `/metrics` endpoint'ini beş saniyede bir scrape eder. Target kontrolü:

```powershell
docker compose exec -T prometheus promtool check config /etc/prometheus/prometheus.yml
```

Grafana ilk başlangıçta iki datasource ve üç dashboard yükler:

- Prometheus UID: `eventflow-prometheus`.
- Loki UID: `eventflow-loki`.
- Genel bakış UID: `eventflow-overview`.
- Metrik UID: `eventflow-metrics`.
- Log UID: `eventflow-logs`.

Dashboard JSON ve provisioning YAML dosyaları `observability/grafana` altındadır. UI'da yapılan geçici düzenleme repository dosyasını değiştirmez; kalıcı değişiklik JSON'a uygulanmalı ve test edilmelidir.

## Retention ve volume'lar

- Loki varsayılan retention: `168h`, yani 7 gün.
- Prometheus varsayılan retention: `15d`.
- PostgreSQL, Loki, Alloy, Prometheus ve Grafana named volume kullanır.

Loki compactor eski chunk ve index kayıtlarını retention politikasına göre temizler. Bu lokal demo storage modelidir; çok düğümlü veya object storage tabanlı üretim topolojisi değildir.

## Graceful shutdown

```powershell
docker compose stop backend
```

Backend `SIGTERM` sonrası yeni bağlantı kabulünü durdurur, devam eden istekleri yapılandırılmış timeout içinde bitirir ve ardından Redis/PostgreSQL pool'larını kapatır. Compose `stop_grace_period` uygulamanın en yüksek drain süresinden uzundur.

## Sorun giderme

### Swagger boş görünüyorsa

- `APP_ENV=production` ise Swagger bilinçli olarak kapalıdır.
- Önce <http://localhost:8000/api/v1/openapi.json> ve backend health sonucunu kontrol edin.
- Frontend adresi `8080`, Swagger adresi backend portu `8000` üzerindedir.

### Grafana dashboard görünmüyorsa

```powershell
docker compose logs --no-color grafana
docker compose restart grafana
```

Datasource veya dashboard provisioning hatası arayın. Dosyaların read-only mount edildiğini ve `.env` Grafana anahtarlarının dolu olduğunu doğrulayın.

### Prometheus target down ise

```powershell
docker compose exec -T prometheus wget -qO- http://backend:8000/metrics
docker compose logs --no-color prometheus backend
```

### Loglar Grafana'ya ulaşmıyorsa

```powershell
docker compose logs --no-color alloy loki
docker compose exec -T alloy id
```

Docker socket read-only mount edilir. Linux/CI ortamında `DOCKER_SOCKET_GID`, socket group ID değeriyle eşleşmelidir. Alloy yalnız `com.docker.compose.project=eventflow` label'ına sahip containerları keşfeder.

### Gözlemlenebilirlik servisi durursa

Prometheus, Loki, Alloy veya Grafana'yı durdurmak backend domain transaction'ını durdurmamalıdır. `/health` ve ürün API'sini ayrı kontrol edin; Docker JSON logu container logging driver tarafından korunur.
