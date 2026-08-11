# P2 Gözlemlenebilirlik Kabul Matrisi

Tarih: 2026-08-11

Kapsam: PR 6 içindeki tek P2 teslimi olan Prometheus metrics endpoint'i ve onu tamamlayan Loki, Alloy ve provision edilmiş Grafana operasyon arayüzü.

Ön koşul: `docs/P1_ACCEPTANCE_MATRIX.md` tamamen yeşil ve P1 remote CI kapısı başarıyla tamamlandıktan sonra P2 çalışmasına başlandı.

## Sonuç özeti

| Alan | Sonuç | Kanıt |
|---|---|---|
| Backend kalite ve test | Yeşil | 141 geçti, Windows POSIX SIGTERM için 1 açık skip, coverage yüzde 92 |
| Frontend kalite ve test | Yeşil | 35 component testi, lint, typecheck ve production build |
| Playwright | Yeşil | Desktop/mobile toplam 6 kullanıcı yolculuğu |
| Fresh Compose | Yeşil | Ayrı `eventflow-acceptance` projesi ve sıfır named volume ile bütün servisler healthy |
| Prometheus | Yeşil | Config geçerli, `eventflow-backend` target `UP=1`, dashboard PromQL sorguları geçerli |
| Loki ve Alloy | Yeşil | Request ID LogQL sonucu, tam lifecycle, exact düşük cardinality label kümesi |
| Grafana | Yeşil | 2 datasource, 3 sabit dashboard UID, default home ve pinned eklentiler |
| Dayanıklılık | Yeşil | Loki dururken backend `/health` 200 ve Docker JSON logu korunuyor |
| Dependency audit | Yeşil | `pip-audit` ve production `pnpm audit` bulgu üretmedi |
| Secret/history scan | Yeşil | Gitleaks 8.30.1 ile 172 commit, gerçek leak yok |

## Metrik sözleşmesi

| Kriter | Sonuç | Kanıt |
|---|---|---|
| HTTP trafik ve gecikme | Yeşil | `eventflow_http_requests_total`, duration histogram ve in-progress gauge |
| HTTP error | Yeşil | Method, route template ve status etiketli counter |
| Reservation outcomes | Yeşil | Created, reactivated, replayed ve güvenli red sonuçları |
| Event row lock wait | Yeşil | Operation etiketli histogram |
| Idempotency | Yeşil | Owner, replay, conflict ve in-progress sonuçları |
| Cancellation, rate limit, readiness | Yeşil | Counter/gauge serileri ve gerçek PostgreSQL ile Redis flow testi |
| Uptime | Yeşil | Label içermeyen process start time gauge |
| Cardinality sınırı | Yeşil | Request ID, actor/event UUID, e-posta ve ham URL metric label değil |
| Route güvenliği | Yeşil | Path template veya sabit `unmatched`; `/metrics` self-instrument edilmez |
| Failure isolation | Yeşil | Metric update ve fallback log hatası domain akışından dışarı kaçmıyor |

## Loki ve Alloy sözleşmesi

| Kriter | Sonuç | Kanıt |
|---|---|---|
| Docker discovery scope | Yeşil | `COMPOSE_PROJECT_NAME` ile seçilen tek Compose project label filtresi |
| Docker socket | Yeşil | Read-only mount ve Linux socket GID desteği |
| JSON parsing | Yeşil | Geçerli JSON alanları çıkarılıyor; malformed/plain satır kaybolmuyor |
| Index labels | Yeşil | Tam küme: `environment`, `level`, `route`, `service_name` |
| Request ID | Yeşil | JSON field olarak LogQL JSON parser ile sorgulanıyor, index label değil |
| Request lifecycle | Yeşil | Aynı ID için `http.request.started`, domain sonucu ve `http.request.completed` |
| Loki storage | Yeşil | Single-binary TSDB v13, filesystem named volume, compactor retention |
| Retention | Yeşil | Lokal varsayılan `168h` |
| Pipeline outage | Yeşil | Loki kapalıyken backend 200; Docker stdout JSON kaydı mevcut |

Örnek doğrulanan LogQL:

```logql
{service_name="backend"} | json | requestId="44444444-4444-7444-8444-444444444444"
```

## Grafana sözleşmesi

| Varlık | Beklenen | Sonuç |
|---|---|---|
| Prometheus datasource | UID `eventflow-prometheus`, health `OK` | Yeşil |
| Loki datasource | UID `eventflow-loki`, health `OK`, request ID derived field | Yeşil |
| Ana ekran | UID `eventflow-overview`, 3 panel | Yeşil |
| Metrik dashboard | UID `eventflow-metrics`, 12 panel | Yeşil |
| Log dashboard | UID `eventflow-logs`, 4 bölüm ve 17 analiz paneli | Yeşil |
| Dashboard sorguları | Genel bakış, metrik ve log ekranlarında toplam 33 PromQL/LogQL target; 17 log targetı gerçek Loki üzerinde ayrıca yürütüldü | Yeşil |
| Pinned eklentiler | Loki Explore `2.5.0`, Metrics Drilldown `2.4.0` | Yeşil |
| Dil ve sunum | Türkçe başlık/açıklama, doğru units/legend/threshold, yanıltıcı sıfır yok | Yeşil |

Ekran kanıtları:

- [Grafana genel bakış](screenshots/pr6-p2-grafana-overview.png)
- [Grafana metrik dashboard](screenshots/pr6-p2-grafana-metrics.png)
- [Request ID log korelasyonu](screenshots/pr6-p2-grafana-request-id-logs.png)
- [Gelişmiş log analizi özeti](screenshots/pr6-p2-grafana-log-analysis.png)
- [İş alanı ve hata analizi](screenshots/pr6-p2-grafana-log-analysis-details.png)
- [Request ID zaman çizelgesi](screenshots/pr6-p2-grafana-request-id-timeline.png)

Log analizi geliştirme doğrulaması:

- operasyon özeti, HTTP, iş alanı ve request ID incelemesi için 4 bölüm ve 17 panel provision edildi
- 17 LogQL targetın tamamı Grafana datasource API üzerinden gerçek Loki'ye karşı hatasız çalıştı
- yeni `http.request.rejected` ve `RESOURCE_NOT_FOUND` kaydı backend, Alloy ve Loki zincirinde bulundu
- query selectorları request ID, actor ID, event ID veya reservation ID içermiyor

## Çalıştırılan kabul komutları

```powershell
Push-Location backend
uv run ruff format --check app migrations tests
uv run ruff check app migrations tests
uv run mypy app tests
uv run pytest --cov=app --cov-report=term-missing
uv run pip-audit
Pop-Location

pnpm peers check
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm audit --prod --audit-level high
```

Güncel normal stack üzerinde log analizi sorguları ayrıca çalıştırıldı:

```powershell
docker compose config --quiet
python observability/verify_log_dashboard.py
```

Fresh stack mevcut geliştirici volume'larını silmeden ayrı projede çalıştırıldı:

```powershell
$env:COMPOSE_PROJECT_NAME='eventflow-acceptance'
docker compose --env-file .env.example up --build -d --wait --wait-timeout 180
docker compose --env-file .env.example run --rm seed
$env:E2E_BASE_URL='http://localhost:8080'
pnpm --filter @eventflow/e2e test
```

Geçici kabul volume'ları proje label'ı ve `eventflow-acceptance_*` ad önekiyle doğrulandıktan sonra kaldırıldı. Kullanıcının normal `eventflow_*` volume'larına dokunulmadı ve normal stack tekrar healthy başlatıldı.

## Platform notu

Windows lokal koşuda POSIX `SIGTERM` gönderilemediği için graceful shutdown integration testi açıkça skip olur. Aynı test P1 Linux GitHub Actions kabulünde geçti. P2 değişiklikleri graceful shutdown uygulama yolunu değiştirmedi.
