# EventFlow Repository Rules

These rules apply to the entire repository. More specific nested `AGENTS.md` files add constraints for their directories.

## Delivery gates

- Follow the six-PR sequence in `EVENTFLOW_MASTER_PLAN.md`; do not move P1/P2 work into PRs 1-5.
- Do not create `feat/ops-delivery` until PR 5 is merged and every P0 row in `docs/P0_ACCEPTANCE_MATRIX.md` is approved and green.
- In PR 6, finish and verify every P1 criterion before writing P2 code.
- Never merge a PR or make the repository public without the user's explicit approval.

## Architecture and integrity

- Keep a modular monolith. Do not introduce microservices.
- Change the PostgreSQL schema only through new versioned Alembic migrations. Never use runtime `create_all`, synchronization, or automatic schema generation.
- Keep seeds separate from migrations, idempotent, and safely repeatable.
- Enforce authorization and ownership server-side. UI guards are UX only.
- Hide inaccessible UUID resources behind the same 404 response as missing resources. Use 403 only for general capability denial that does not reveal resource existence.
- Preserve the event-first lock ordering and the `reserved_count == ACTIVE reservations` invariant for every reservation writer.
- Store no request ID in idempotency response snapshots; inject the current request ID on every replay and preserve the original domain request ID only in its dedicated header.
- Write critical audit records in the same transaction as the domain change. Audit records are insert-only in the application and immutable in PostgreSQL.

## Engineering practice

- Never commit secrets, local `.env` files, or `Full-Stack-MidLevel-Case1.pdf`.
- Keep code, API fields, branches, and commit messages in English. Keep product UI and user-facing documentation in Turkish.
- Update the generated OpenAPI client, API tests, and documentation together when the public API changes.
- Update `DECISIONS.md` and tests with every material architecture or business-rule change.
- Use Conventional Commits; each commit must contain one coherent logical change.
- Run relevant format, lint, type, test, and build checks before each commit.
- Keep `docs/P0_ACCEPTANCE_MATRIX.md` honest: never mark evidence green for a command that was not run.

