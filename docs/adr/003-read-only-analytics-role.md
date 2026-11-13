# ADR-003: A read-only analytics role on the business schemas

- Status: proposed
- Date: 2026-11-13
- Owner: Ilyes

## Context

The rule is "a service never reads another service's tables". But the dashboard API and the Spark batch extraction to the lake need to read orders, stock and payments.

## Options considered

| Option | For | Against |
| --- | --- | --- |
| Call each service API | Respects the rule fully | Batch extraction of millions of rows through REST is slow |
| CDC (Debezium) into Kafka | Clean, real time | One more component to run and explain |
| Read-only role `analytics_reader` | Simple, fast, no write possible, no access to `auth` | Analytics depends on the internal table layout |

## Decision

A role `analytics_reader` with `SELECT` only on `orders`, `inventory` and `payments`, never on `auth`. Used by the dashboard API and Spark JDBC batch jobs. Services themselves keep strict isolation.

## Consequences

- Schema changes in a service can break a batch job: covered by the quality checks in the staging zone.
- If time allows, replace with CDC and mention it as the target design.
