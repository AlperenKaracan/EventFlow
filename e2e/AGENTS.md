# End-to-End Test Rules

- Use Playwright with isolated users and deterministic data ownership.
- Do not use fixed sleeps; wait for semantic UI, network, or application state.
- Prefer accessible roles, labels, and stable semantic selectors.
- Capture trace and screenshot artifacts on failure.
- Keep database concurrency proofs in backend PostgreSQL integration tests, not browser tests.
- Do not hide flakes with unconditional retries.

