-- Adds ~200k orders over 3 months so EXPLAIN before/after shows a real difference.
INSERT INTO orders.orders (customer_id, status, total_cents, created_at)
SELECT 1 + (random() * 24)::int,
       (ARRAY['paid', 'preparing', 'delivered', 'payment_failed'])[1 + (random() * 3)::int],
       (random() * 30000)::int,
       timestamptz '2026-10-01' + random() * interval '90 days'
FROM generate_series(1, 200000);
ANALYZE orders.orders;
