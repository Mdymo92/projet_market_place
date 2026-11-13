# Market platform

Data and e-commerce platform for Market (EFREI final project, Ilyes and Philip): PostgreSQL and MongoDB storage, a Delta Lake on MinIO, FastAPI and GraphQL microservices behind Kong, Kafka and Spark Structured Streaming, observability with Prometheus, Grafana, OpenTelemetry, Jaeger and Loki.

## Start

Requirements: Docker Desktop with about 10 GB of RAM for the full stack, `make`.

```bash
make env       # creates .env from .env.example: change the passwords
make up        # everything (core + data + obs); make up-core for a lighter start
make seed      # one test user per role
make ps
```

| What | URL |
| --- | --- |
| API gateway (all APIs) | http://localhost:8000 |
| Kafka UI | http://localhost:8080 |
| MinIO console | http://localhost:9001 |
| Grafana | http://localhost:3000 |
| Jaeger (traces) | http://localhost:16686 |
| Prometheus | http://localhost:9090 |
| Spark UI | http://localhost:4040 |

Quick check:

```bash
curl -s localhost:8000/v1/auth/login -H 'content-type: application/json' \
  -d '{"email":"analyst@market.local","password":"<SEED_ANALYST_PASSWORD>"}'
curl -i localhost:8000/v1/orders                                   # 401, no token
curl -i localhost:8000/v1/orders -H "Authorization: Bearer <token>" # analyst can read
```

## Layout

```
contracts/       OpenAPI (REST), GraphQL schema, Kafka event JSON schemas: written first
db/postgres/     init scripts (roles, schemas, partitions, seed), explain/ before-after demos
db/mongo/        catalog collection, validation, indexes, seed
services/        auth, orders, inventory, payment, catalog (GraphQL), dashboard + common/ (JWT, RBAC, logs, metrics, resilience)
gateway/         Kong declarative config (JWT, rate limit, routes)
streaming/       event generator, Spark Structured Streaming jobs
lake/            batch jobs, quality checks, data catalog
observability/   Prometheus, alerts, Grafana dashboards, OpenTelemetry collector, Loki
frontend/        React app (5 tabs)
tests/           unit and contract tests (run in CI)
docs/            ADRs, RBAC matrix, architecture, dossier
```

## Status

| Part | State |
| --- | --- |
| docker-compose, Makefile, configs | done, to be run on a laptop |
| PostgreSQL schemas, roles, partitions, seed, EXPLAIN demo | done, tested |
| MongoDB catalog | done |
| Contracts (OpenAPI, GraphQL, events) | done |
| Auth service (login, refresh, service accounts, users) | done, tested against PostgreSQL |
| JWT + RBAC + 401/403 logging, resilience client | done, unit tested |
| Orders Saga, inventory, payment storage, catalog mutations | routes and RBAC wired, logic TODO |
| Generator, Spark Kafka to raw | first version |
| Lake zones, quality, catalog, streaming KPIs and alerts | TODO |
| Dashboard API, frontend | TODO |

## Tests

```bash
pip install -r requirements-dev.txt
make lint
make test
```

## Rules

- No secret in the repo: `.env` only (git-ignored).
- Contract first: change `contracts/` before the code.
- One PR per task, reviewed by the other person.
- See `CLAUDE.md` for conventions and AI usage.
