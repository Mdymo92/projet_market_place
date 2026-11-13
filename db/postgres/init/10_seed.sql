-- Small realistic seed so every tab shows something on first start.
-- product_id 1..12 match the MongoDB catalog seed (db/mongo/init/01_catalog.js).

INSERT INTO inventory.warehouses (name, capacity_units) VALUES
  ('Paris Nord - Gonesse', 5000),
  ('Lyon Saint-Priest',    3000),
  ('Marseille Vitrolles',  2000);

-- Stock per product and warehouse (a few deliberately low to trigger "rupture proche")
INSERT INTO inventory.stock (product_id, warehouse_id, quantity)
SELECT p, w,
       CASE WHEN p IN (3, 7) THEN 4 ELSE 40 + ((p * 37 + w * 11) % 160) END
FROM generate_series(1, 12) AS p, generate_series(1, 3) AS w;

INSERT INTO orders.customers (name, email)
SELECT 'Client ' || i, 'client' || i || '@example.com'
FROM generate_series(1, 25) AS i;

-- A few historical orders spread over the last days
WITH new_orders AS (
  INSERT INTO orders.orders (customer_id, status, total_cents, created_at)
  SELECT 1 + (i % 25),
         (ARRAY['paid', 'preparing', 'delivered', 'payment_failed'])[1 + (i % 4)],
         0,
         now() - (i || ' hours')::interval
  FROM generate_series(1, 40) AS i
  RETURNING id, created_at
)
INSERT INTO orders.order_items (order_id, order_created_at, product_id, quantity, unit_price_cents)
SELECT id, created_at, 1 + (id % 12), 1 + (id % 3), 1990 + (id % 12) * 500
FROM new_orders;

UPDATE orders.orders o
SET total_cents = s.total
FROM (SELECT order_id, sum(quantity * unit_price_cents) AS total FROM orders.order_items GROUP BY order_id) s
WHERE o.id = s.order_id;
