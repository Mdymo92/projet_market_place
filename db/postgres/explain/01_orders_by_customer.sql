-- EXPLAIN before / after an index (volet 1).
-- Run: docker compose exec postgres psql -U $POSTGRES_USER -d market -f /explain/01_orders_by_customer.sql
-- (or paste it in psql). Generate more rows first with scripts/bulk_orders.sql for a visible difference.

\echo '=== BEFORE: recent orders of one customer (tab Commandes) ==='
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, status, total_cents, created_at
FROM orders.orders
WHERE customer_id = 7
ORDER BY created_at DESC
LIMIT 20;

CREATE INDEX IF NOT EXISTS orders_customer_created_idx ON orders.orders (customer_id, created_at DESC);
ANALYZE orders.orders;

\echo '=== AFTER: same query with index on (customer_id, created_at DESC) ==='
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, status, total_cents, created_at
FROM orders.orders
WHERE customer_id = 7
ORDER BY created_at DESC
LIMIT 20;

\echo '=== Partition pruning: only the November partition is scanned ==='
EXPLAIN
SELECT count(*) FROM orders.orders
WHERE created_at >= '2026-11-01' AND created_at < '2026-12-01';
