# EventFlow Test Rehberi

Bu belge test katmanlarını, çalıştırma komutlarını ve kabul kanıtı kurallarını açıklar. Testler lokal geliştirici veritabanına bağlı değildir; PostgreSQL ve Redis gerektiren senaryolar izole containerlarla çalışır.

## Test katmanları

| Katman | Araç | Ana kapsam |
|---|---|---|
| Backend unit | pytest | Şema, cursor, zaman dilimi, hata eşleme, log ve metrik yardımcıları |
| Backend integration | pytest + Testcontainers | Auth, IDOR, event, reservation, audit, idempotency, readiness |
| Backend concurrency | pytest + gerçek PostgreSQL | Kapasite, aynı key yarışı, rollback takeover, kilit sırası |
| Frontend component | Vitest + Testing Library | Form validasyonu, session, hata/loading/empty/success ve rol ekranları |
| Tarayıcı | Playwright | Public, organizer ve attendee kullanıcı yolculukları |
| Operasyon | Docker Compose | Migration, seed, non-root, health, metrics, log pipeline ve Grafana provisioning |

## Backend

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

Integration ve concurrency testleri Docker engine gerektirir. Fixture her test oturumu için PostgreSQL ve Redis containerlarını yönetir; host üzerindeki `localhost:5432` veya `localhost:6379` verisine bağlanmaz.

Önemli yarış kanıtları:

- Aynı etkinliğe paralel rezervasyon kapasiteyi aşmaz.
- Beş aynı idempotency key isteğinde yalnız bir domain write oluşur.
- İlk owner transaction rollback ederse bekleyen istek key'i güvenle devralır.
- Bütün reservation writer'ları etkinlik satırını reservation satırından önce kilitler.
- `reserved_count`, aktif reservation sayısına eşit kalır.

## Frontend ve tarayıcı

```powershell
pnpm install --frozen-lockfile
pnpm peers check
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm --filter @eventflow/e2e test
```

Playwright testleri `E2E_BASE_URL` verilmezse yerel Vite test sunucusunu, CI ve Compose kabulünde `http://localhost:8080` adresini kullanır. Selectorlar rol, label ve görünür metin gibi semantik yüzeylere dayanır; sabit sleep kullanılmaz. Hata halinde trace, screenshot ve video test sonucu klasörüne yazılır.

## Gözlemlenebilirlik smoke testi

```powershell
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 120
docker compose exec -T prometheus promtool check config /etc/prometheus/prometheus.yml
```

CI ayrıca şunları doğrular:

- Prometheus `eventflow-backend` target değeri `UP=1` olur.
- Loki, Alloy, Prometheus ve Grafana health endpointleri cevap verir.
- Bilinen bir `X-Request-ID` backend logundan Loki'ye ulaşır ve LogQL ile bulunur.
- Loki index label kümesi yalnız `service_name`, `environment`, `level` ve `route` alanlarından oluşur.
- Grafana datasource health sonuçları `OK`, dashboard UID'leri sabit ve ana ekran `eventflow-overview` olur.
- Log dashboardundaki 17 LogQL target çalışan Grafana datasource API'si üzerinden Loki'ye karşı hatasız yürütülür; yapılandırılmış `RESOURCE_NOT_FOUND` rejection kaydı uçtan uca bulunur.
- Gözlemlenebilirlik containerları root olmayan kullanıcıyla çalışır.

Örnek PromQL:

```promql
sum(rate(eventflow_http_requests_total[5m]))
```

Örnek LogQL:

```logql
{service_name="backend"} | json | requestId="REQUEST_ID"
```

## Kabul kanıtı disiplini

`docs/P0_ACCEPTANCE_MATRIX.md`, `docs/P1_ACCEPTANCE_MATRIX.md` ve `docs/P2_ACCEPTANCE_MATRIX.md` yalnız gerçekten çalıştırılmış komutları yeşil gösterir. Atlanan veya platform nedeniyle çalışmayan test açıkça belirtilir. Yaklaşık sonuç, beklenen sonuç veya önceki commit sonucu güncel HEAD için kanıt sayılmaz.
