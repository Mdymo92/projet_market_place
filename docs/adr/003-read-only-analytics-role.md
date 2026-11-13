# ADR-003: A read-only analytics role on the business schemas

- Status: proposed
- Date: 2026-11-13
- Owner: Ilyes

## Context

The rule is "a service never reads another service's tables". The Spark batch extraction to the lake needs to read orders, stock and payments in bulk (volet 2 requires batch ingestion).

## Options considered

| Option | For | Against |
| --- | --- | --- |
| Call each service API | Respects the rule fully | Batch extraction of millions of rows through REST is slow |
| CDC (Debezium) into Kafka | Clean, real time | One more component to run and explain |
| Read-only role `analytics_reader` | Simple, fast, no write possible, no access to `auth` | Analytics depends on the internal table layout |

## Decision

A role `analytics_reader` with `SELECT` only on `orders`, `inventory` and `payments`, never on `auth`, used **only** by the Spark JDBC batch extraction to the raw zone. It is a data platform job, not a service. The dashboard API reads the remaining stock through the Inventory API, as the brief requires; services keep strict isolation.

## Consequences

- Schema changes in a service can break a batch job: covered by the quality checks in the staging zone.
- If time allows, replace with CDC and mention it as the target design.
