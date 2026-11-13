# Market platform: conventions for humans and AI assistants

EFREI final project, two people: Ilyes (data track: lake, Kafka, Spark, dashboard API, tabs 1 and 4) and Philip (platform track: PostgreSQL, MongoDB, services, Kong, tabs 2 and 3).

## Stack (do not change without an ADR)

Python 3.12, FastAPI, Ariadne (GraphQL, schema first), psycopg 3, pymongo, PostgreSQL 16, MongoDB 7, Kafka 3.8 (KRaft), Spark 3.5 + Delta 3.2, MinIO, Kong 3.7 DB-less, Prometheus, Grafana, OpenTelemetry, Jaeger, Loki. Frontend: React + Vite + TypeScript.

## Rules

- **Contract first.** Edit `contracts/openapi/*.yaml`, `contracts/graphql/schema.graphql` or `contracts/events/*.json` before the code. `tests/unit/test_contracts.py` checks that every OpenAPI path exists in its service.
- **Security.** Every route uses `Depends(require("<action>"))` from `market_common.security`. Add new actions to `market_common/rbac.py` and `docs/rbac.md`.
- **Data isolation.** A service only uses its own PostgreSQL role and schema. Never query another schema; call the other service's API.
- **Money in integer cents.** Never floats.
- **Idempotency.** Every POST that changes state takes an `Idempotency-Key` header.
- **Outbound HTTP** only through `market_common.resilience.ResilientClient`.
- **Events** carry `event_id`, `event_type`, `occurred_at`, `producer`, `payload`, and are validated against `contracts/events/`.
- **No secrets** in code or config: environment variables from `.env`.
- **Lake.** Never modify the raw zone. Everything else in Delta format, partitioned by date.

## Commands

```bash
make up / make up-core / make down / make clean
make seed            # test users
make test            # unit + contract tests, no Docker needed
make lint / make fmt
```

## Working with AI

- One small task per request (one route, one job, one test file), then run the tests and commit.
- Generate code from the contracts, never the other way round.
- AI-written tests must fail when the code is broken on purpose.
- Before merging, the author must be able to explain every block to the jury.
- Log notable generations in `docs/ai-usage.md` (what was generated, what we changed).

## Git

- Branches from `develop`, PR into `develop`, reviewed by the other person. `main` = what we present.
- Commit messages in English, imperative: `Add stock reservation endpoint`.
