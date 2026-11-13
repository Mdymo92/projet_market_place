# ADR-004: Delta Lake on MinIO, organised in four zones

- Status: proposed
- Date: 2026-11-13
- Owner: Ilyes
- Volet: 2 (Data Lake & Lakehouse)

## Context

Events arrive continuously from Kafka and operational data is extracted in batch from PostgreSQL. Analysts need clean, queryable tables; logistics needs fill rates within seconds. Files must never be half written, and we must be able to go back to an older version of a table. Personal data (customer email) must not reach the analytical zones in clear.

## Options considered

| Option | For | Against |
| --- | --- | --- |
| Plain Parquet files on MinIO | Simple, columnar | No transactions: a crashed job leaves partial files; no history |
| Delta Lake on MinIO | ACID commits, time travel, MERGE, idempotent streaming sink, native in Spark | Small files need periodic compaction |
| Apache Iceberg on MinIO | Same guarantees, engine-neutral | Needs a catalog service; less direct with our Spark setup |

## Decision

Delta Lake on MinIO (S3 API), four buckets:

- **raw**: data as received, append only, never modified;
- **staging**: typed, deduplicated on `event_id`, quality checks, failed rows to `quarantine`, email replaced by a salted SHA-256 hash;
- **curated**: joined business tables;
- **consumption**: aggregates for the dashboard.

A row moves to the next zone only after the checks of that zone pass. Each job updates `lake/catalog.yaml` (source, owner, zone, last update).

## Consequences

- Delta + Spark checkpoint gives exactly-once writes into the lake (see ADR-006).
- Time travel is shown in the demo (`VERSION AS OF`).
- Streaming creates many small files: a compaction job (`OPTIMIZE`) runs on curated and consumption.
- Plan B: Iceberg, if a shared catalog with another engine becomes necessary.
