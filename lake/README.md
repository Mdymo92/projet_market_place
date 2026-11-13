# Data Lake (volet 2)

MinIO buckets, one per zone, all tables in Delta Lake format.

| Zone | Bucket | Content | Rule to enter |
| --- | --- | --- | --- |
| raw | `raw` | Kafka events and batch extracts, as received | Nothing is changed or deleted |
| staging | `staging` | Typed, deduplicated on `event_id`, customer email hashed (SHA-256 + salt) | Passes the quality checks, else goes to `quarantine` |
| curated | `curated` | Joined business tables (orders with lines and products, stock history) | Business rules applied |
| consumption | `consumption` | Aggregates read by the dashboard (KPIs per day and hour, alerts, fill rates) | Built for one use |

Also: `quarantine` (rows that failed a check, with the reason), `checkpoints` (Spark streaming state), `backups`.

Planned files:
- `jobs/batch_postgres_to_raw.py`: Spark JDBC extract of orders, stock, payments (role analytics_reader)
- `jobs/raw_to_staging.py`, `jobs/staging_to_curated.py`, `jobs/curated_to_consumption.py`
- `quality/checks.py`: nulls, duplicates, ranges, referential checks; writes a quality report
- `catalog.yaml`: one entry per dataset (source, owner, zone, last update), updated by each job
