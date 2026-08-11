# EventFlow Katkı Rehberi

## Branch ve PR düzeni

- Feature branch adları İngilizce ve kısa olmalıdır. Ana plandaki altı onaylı branch kendi sabit adlarını korur; yeni bağımsız Codex branch'leri `codex/` öneki kullanır.
- Ana planın altı PR sırası tamamlanmıştır. P1 kabul kapısının P2'den önce tamamlandığını gösteren tarihsel kanıt `docs/P1_ACCEPTANCE_MATRIX.md` içinde korunur.
- PR önce draft açılır. Kullanıcı açıkça onaylamadan merge yapılmaz ve repository public yapılmaz.
- PR açıklaması kapsam, davranış, mimari karar, test kanıtı, güvenlik notu, manuel test ve ekran görüntüsü bölümlerini içerir.

## Commitler

Conventional Commits kullanılır:

```text
feat(metrics): expose reservation outcomes
fix(ui): preserve filters after validation error
test(ops): verify Loki request ID query
docs(operations): explain Grafana troubleshooting
```

Her commit tek bir mantıksal değişiklik taşır. Kod, API alanları, branch ve commit mesajları İngilizce; ürün UI metinleri ve kullanıcı dokümantasyonu Türkçedir.

## Geliştirme kuralları

- Modüler monolit sınırı korunur; mikroservis eklenmez.
- Yetkilendirme ve ownership server-side uygulanır. UI guard yalnız UX'tir.
- Kaynak UUID'si yetkisiz kullanıcıdan 404 ile gizlenir.
- Reservation writer'ları event-first kilit sırasını ve `reserved_count == ACTIVE reservations` invariantını korur.
- Kritik audit kaydı domain değişikliğiyle aynı transaction'da yazılır.
- PostgreSQL şeması yalnız yeni Alembic migration ile değişir.
- Seed migration'dan ayrı, idempotent ve tekrar çalıştırılabilir kalır.
- Request ID idempotency response snapshot'ına veya Prometheus/Loki index etiketine yazılmaz.
- Gözlemlenebilirlik güncelleme hatası domain transaction'ını engellemez.

## Public API değişikliği

Endpoint, payload, hata veya response değişirse aynı commit serisinde şunlar güncellenir:

1. Backend schema ve testleri.
2. OpenAPI snapshot.
3. Generated TypeScript client.
4. Frontend kullanımı ve component/E2E testleri.
5. `API.md` ve gerekiyorsa `DECISIONS.md`.

## Migration ve dependency değişikliği

- Merge edilmiş migration yeniden yazılmaz; yeni revision eklenir.
- Migration downgrade ve temiz `upgrade head` smoke testi çalıştırılır.
- Dependency sürümü exact/pinned tutulur ve lockfile aynı değişiklikte güncellenir.
- Backend için `pip-audit`, frontend için production `pnpm audit` sonucu kontrol edilir.

## Commit öncesi kontroller

Değişikliğe göre en az ilgili komutlar çalıştırılır:

```powershell
Push-Location backend
uv run ruff format --check app migrations tests
uv run ruff check app migrations tests
uv run mypy app tests
uv run pytest
Pop-Location

pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Compose, Docker veya gözlemlenebilirlik değişikliğinde ayrıca:

```powershell
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 120
pnpm --filter @eventflow/e2e test
```

## Definition of Done

- İstenen davranış ve negatif senaryolar otomatik testlidir.
- Client ve server validation birlikte günceldir.
- Güvenlik, IDOR, concurrency, timezone ve idempotency invariantları gerilememiştir.
- Format, lint, type, test ve build kontrolleri yeşildir.
- Compose temiz başlangıç, migration ve seed tekrarı çalışır.
- Dokümantasyon ve kabul matrisi gerçek çalıştırılan kanıtla günceldir.
- Secret, `.env`, lokal cache, PDF ve kişisel veri stage edilmemiştir.
- PR açıklaması ve ekran görüntüleri GitHub üzerinde render olur.
