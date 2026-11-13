# ADR-006: Spark Structured Streaming with exactly-once into Delta, and where we do not stream

- Status: proposed
- Date: 2026-11-13
- Owner: Ilyes
- Volet: 4 (Real time)

## Context

Kafka carries clicks, orders, payments, stock moves and shipments. Logistics and payment need alerts within seconds; analysts are fine with data under a minute old; the catalog team does not need streaming. If the job crashes it must restart where it stopped, without losing or counting twice an event.

## Options considered

| Option | For | Against |
| --- | --- | --- |
| Spark Structured Streaming | Windows, watermark, state, checkpoint; same engine as batch; native Delta sink | Micro-batch latency (seconds, not milliseconds) |
| Apache Flink | Lowest latency, rich state | A second engine to learn and run |
| Kafka Streams | Light, inside a service | Java only, no direct lake output |

Delivery level: at-least-once with deduplication, or exactly-once end to end.

## Decision

- Spark Structured Streaming, checkpoints on MinIO.
- **Exactly-once into the lake**: Kafka offsets are stored in the checkpoint and the Delta sink commits each micro-batch once (idempotent on batch id).
- **At-least-once for alerts** written to the `alerts` topic, with a deterministic `alert_id`; the dashboard drops duplicates.
- Sliding one-minute windows with a two-minute watermark for KPIs; 30-minute session windows for abandoned carts; Kafka partitioned by `warehouse_id` for stock and shipments.
- No streaming for the catalog team (plain API) and micro-batches of 30 s to 1 min for analysts (see `docs/architecture/justification.md`, section 5).

## Consequences

- Demo: kill the streaming container, restart it, counts in the lake are identical to the number of Kafka messages.
- Lag, messages per second and errors are on Grafana (kafka-exporter + Spark metrics); adding partitions makes the lag drop.
- Plan B if latency is not enough: lower the trigger interval, or move the payment alert to a small Kafka consumer service.
