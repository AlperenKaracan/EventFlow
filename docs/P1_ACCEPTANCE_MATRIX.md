# P1 Kabul Matrisi

Bu matris PR 6 içindeki bütün P1 isterlerini P2 başlangıcından önce doğrular. Bir satır bile kırmızı veya beklemede kalırsa Prometheus, Loki, Alloy ya da Grafana kodu yazılmaz.

Durum anahtarı: `⬜ Bekliyor` · `🟡 Devam ediyor` · `✅ Kanıtlandı` · `❌ Başarısız`

| ID | P1 gereksinimi | Otomatik veya manuel kanıt | Durum |
|---|---|---|---|
| P1-SRC-01 | Başlık ve açıklamada Türkçe full-text arama | Generated `tsvector`, `websearch_to_tsquery`, gerçek PostgreSQL API testi | ✅ Kanıtlandı |
| P1-SRC-02 | Arama sorgusu GIN indeksini kullanır | Migration introspection ve `EXPLAIN` testi `ix_events_search_vector_gin` seçti | ✅ Kanıtlandı |
| P1-FLT-01 | Kategori slug filtresi çalışır | API integration ve production Playwright | ✅ Kanıtlandı |
| P1-FLT-02 | Dahil tarih aralığı etkinliğin IANA yerel gününe göre çalışır | Berlin yerel günü API integration ve production Playwright | ✅ Kanıtlandı |
| P1-FLT-03 | Arama, kategori ve tarih birlikte uygulanır | Combined API integration ve desktop/mobile Playwright | ✅ Kanıtlandı |
| P1-CUR-01 | Cursor bütün aktif filtrelere bağlıdır | Filtre değiştirilmiş cursor `400 INVALID_CURSOR` integration testi | ✅ Kanıtlandı |
| P1-CUR-02 | Frontend filtre değişiminde cursor geçmişini ilk sayfaya sıfırlar | Component testi | ✅ Kanıtlandı |
| P1-UI-01 | Arama, kategori ve Türkçe tarih kontrolleri responsive ve erişilebilirdir | 35 component testi ve Desktop Chrome/Pixel 7 Playwright | ✅ Kanıtlandı |
| P1-UI-02 | Boş sonuç, kategori hatası, temizleme ve client tarih validasyonu açıklayıcıdır | Component davranışı ve backend `422 INVALID_DATE_RANGE` testi | ✅ Kanıtlandı |
| P1-GOV-01 | PR açıklama şablonu kapsam, risk, test, görsel ve merge kapılarını içerir | `.github/PULL_REQUEST_TEMPLATE.md` ve CI governance kontrolü | ✅ Kanıtlandı |
| P1-GOV-02 | CODEOWNERS varsayılan ve hassas alan sahipliğini tanımlar | `.github/CODEOWNERS` ve CI governance kontrolü | ✅ Kanıtlandı |
| P1-GOV-03 | SECURITY private bildirim ve düzeltme sürecini açıklar | `SECURITY.md` ve CI governance kontrolü | ✅ Kanıtlandı |
| P1-SIG-01 | SIGTERM yeni bağlantı kabulünü durdurur ve akan isteği drain eder | Gerçek Linux container probe: slow request `200`, process exit `0` | ✅ Kanıtlandı |
| P1-SIG-02 | Uvicorn graceful timeout environment ayarından gelir | Server unit testi | ✅ Kanıtlandı |
| P1-SIG-03 | Redis ve PostgreSQL pool'ları lifespan sonunda kapanır | `aclose` ve `dispose` unit testi | ✅ Kanıtlandı |
| P1-SIG-04 | Compose zorla sonlandırma süresi uygulama üst sınırından uzundur | `SIGTERM`, `stop_grace_period=130s`, config ve CI kontrolü | ✅ Kanıtlandı |
| P1-REG-01 | P0 backend kabulü regresyonsuzdur | 129 passed, 1 Windows POSIX skip; Linux probe ayrıca geçti | ✅ Kanıtlandı |
| P1-REG-02 | P0 frontend kabulü regresyonsuzdur | 33/33 component testi, lint, typecheck ve production build | ✅ Kanıtlandı |
| P1-REG-03 | P0 browser yaşam döngüsü regresyonsuzdur | Production Compose Playwright toplam 6/6 | ✅ Kanıtlandı |

## Yerel P1 kanıt günlüğü

| Kapı | Komut veya kanıt | Sonuç |
|---|---|---|
| Backend statik kalite | Ruff format/lint ve strict mypy `app tests` | 98 dosya formatted; 95 source/test file typed; temiz |
| Backend test | `uv run pytest --cov=app --cov-report=term-missing` | 129 passed, 1 POSIX-only skip; toplam branch coverage `%92` |
| Search migration | `alembic upgrade head` iki kez ve `alembic check` | Revision `20260811_0002`; drift yok |
| Query plan | PostgreSQL `EXPLAIN` | Cursor B-tree ve search GIN indeksleri seçildi |
| Frontend | Prettier, ESLint, TypeScript, Vitest, production Vite build | 35/35; giriş paketi `302.19 kB`, gzip `97.20 kB` |
| Browser | Production Compose Desktop Chrome ve Pixel 7 | P0 ve P1 toplam 6/6 geçti |
| Graceful shutdown | Linux container içinde slow request sırasında `docker stop` | HTTP `200`, exit `0`, lifespan stopped marker üretildi |
| Governance | Markdownlint, Prettier ve zorunlu içerik kontrolleri | PR template, CODEOWNERS ve SECURITY temiz |
| Compose | `docker compose config --quiet` ve stop ayarı inspection | `SIGTERM`, `2m10s`; backend/frontend healthy |

## P2 geçiş kararı

Yerel P1 matrisi tamamen yeşildir. P2 başlangıcı için bu commit'in GitHub Actions Linux koşusunda backend, frontend ve Compose job'larının da yeşil olması zorunludur. Remote CI sonucu doğrulanana kadar P2 kodu yazılmaz.
