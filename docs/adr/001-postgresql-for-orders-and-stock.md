# ADR-001: PostgreSQL for orders, stock and payments

- Status: proposed (draft, to complete)
- Date: 2026-11-13
- Owner: Philip

## Context

Orders, stock and payments must never be inconsistent: an order must not be paid without stock, two customers must not buy the last unit, and a refused payment must release the stock. These are relations with strong integrity rules (customer → order → lines, product × warehouse → stock).

## Options considered

| Option | For | Against |
| --- | --- | --- |
| PostgreSQL | ACID transactions, foreign keys, CHECK constraints (stock never below 0), row locks (`SELECT ... FOR UPDATE`), native partitioning | Scales mostly vertically |
| MongoDB | Flexible schema, horizontal scaling | Multi-document transactions are heavier, no foreign keys, integrity left to the code |
| Cassandra | Very high write throughput | No joins, no transactions, eventual consistency (BASE) |

## Decision

PostgreSQL 16, one schema and one role per service (`orders`, `inventory`, `payments`, `auth`). Orders partitioned by month on `created_at`.

## Consequences

- CAP: we choose consistency over availability for money and stock (CP within one node). A stale stock value would sell what we do not have.
- A service never reads another schema (checked in CI). Cross-service consistency goes through the Saga, not a distributed transaction.
- The orders primary key is `(id, created_at)` because of partitioning; `order_items` and `idempotency_keys` carry `order_created_at`.
- TODO: EXPLAIN before/after numbers (db/postgres/explain), backup/restore timing.
