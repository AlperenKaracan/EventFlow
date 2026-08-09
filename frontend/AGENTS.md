# Frontend Rules

- Use React 19, TypeScript, Vite, MUI, TanStack Query, TanStack Router, React Hook Form, and Zod.
- Consume the generated OpenAPI client. Update it in the same commit as public API changes.
- Keep access tokens in memory only. Never use localStorage or sessionStorage for authentication tokens.
- Collapse concurrent refresh attempts into one single-flight request.
- Preserve the same idempotency key through automatic retries; create a new key only for a new intentional submission.
- Every async screen must implement loading, empty, error, success, and retry behavior where retry is meaningful.
- Treat route guards and hidden buttons as UX only; backend authorization remains authoritative.
- API list responses expose only `nextCursor`. Implement backward navigation with route-level `CursorPagerState.cursors` history.
- Reset cursor history to `[null]` when filters, sort, limit, or a list-ordering mutation changes.
- Keep UI copy and validation messages in Turkish and maintain keyboard, label, contrast, and responsive accessibility.
