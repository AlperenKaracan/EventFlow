# Observability Rules

- PR 1 provides structured JSON logging and health/readiness foundations only. Do not add Prometheus, Loki, Alloy, or Grafana runtime configuration before the P1 gate in PR 6.
- Keep request IDs as JSON fields, never Prometheus labels or Loki index labels.
- Restrict Loki labels to low-cardinality fields such as service, environment, level, and route template.
- Observability failures must never block domain transactions.
- Provision datasources and dashboards from version-controlled files; do not depend on manual UI setup.
