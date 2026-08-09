# Backend Rules

- Use Python 3.14, FastAPI, Pydantic, async SQLAlchemy 2, asyncpg, and Alembic.
- Keep routers limited to HTTP translation, schemas limited to contracts, repositories limited to persistence queries, and application services responsible for business rules and transaction boundaries.
- Repositories must never call `commit()`; ORM entities must never be returned directly as API responses.
- Use real PostgreSQL and Redis for integration/concurrency tests; never substitute SQLite for concurrency behavior.
- Every schema change requires a new Alembic revision. Never call `Base.metadata.create_all()` in runtime or tests.
- Audit writes belong to the same transaction as their critical domain operation. Never expose update/delete operations for audit rows.
- Never log passwords, cookies, tokens, authorization headers, email addresses, request bodies, secrets, or unnecessary PII.
- Reservation create/reactivate lock order is `idempotency row -> event -> reservation -> audit -> idempotency finalize`.
- Reservation cancellation performs a non-locking ownership lookup, then locks `event -> reservation -> audit`.
- Event cancellation locks `event -> active reservations ordered by id -> audits`. No reservation row may be locked before its event.
- Claim idempotency keys with `INSERT ... ON CONFLICT DO NOTHING RETURNING`; a loser must lock/read and validate the existing record before domain work.
- Idempotency snapshots exclude correlation metadata. Replay injects the current `X-Request-ID`, keeps error-body `requestId` equal to it, and returns the original owner ID only as `Idempotency-Original-Request-ID`.
- Organizer management detail uses owner-scoped `GET /api/v1/me/events/{eventId}`, never public detail.
- Event create/PATCH must validate ISO offset against the selected IANA zone at the same instant, including DST gaps and folds.

