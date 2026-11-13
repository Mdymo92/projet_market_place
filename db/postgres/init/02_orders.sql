-- Schema orders: customers, orders, order lines. Owned by orders_svc.
-- orders is partitioned by month on created_at (volet 1: split very large tables).
CREATE SCHEMA orders AUTHORIZATION orders_svc;
SET search_path = orders;

CREATE TABLE customers (
    id     serial PRIMARY KEY,
    name   text NOT NULL,
    email  text NOT NULL UNIQUE                   -- personal data: hashed from the lake staging zone onward
);

CREATE SEQUENCE orders_id_seq;

CREATE TABLE orders (
    id           bigint NOT NULL DEFAULT nextval('orders_id_seq'),
    customer_id  integer NOT NULL REFERENCES customers(id),
    status       text NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending', 'paid', 'preparing', 'payment_failed', 'delivered', 'cancelled')),
    total_cents  integer NOT NULL CHECK (total_cents >= 0),
    created_at   timestamptz NOT NULL DEFAULT now(),
    -- on a partitioned table the primary key must contain the partition key
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

ALTER SEQUENCE orders_id_seq OWNED BY orders.id;

-- Monthly partitions around the project period, plus a default for anything outside
CREATE TABLE orders_2026_09 PARTITION OF orders FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
CREATE TABLE orders_2026_10 PARTITION OF orders FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE orders_2026_11 PARTITION OF orders FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE orders_2026_12 PARTITION OF orders FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');
CREATE TABLE orders_2027_01 PARTITION OF orders FOR VALUES FROM ('2027-01-01') TO ('2027-02-01');
CREATE TABLE orders_default PARTITION OF orders DEFAULT;

CREATE TABLE order_items (
    id                bigserial PRIMARY KEY,
    order_id          bigint NOT NULL,
    order_created_at  timestamptz NOT NULL,
    product_id        integer NOT NULL,           -- application link to the catalog (no FK across databases)
    quantity          integer NOT NULL CHECK (quantity > 0),
    unit_price_cents  integer NOT NULL CHECK (unit_price_cents >= 0),
    FOREIGN KEY (order_id, order_created_at) REFERENCES orders (id, created_at) ON DELETE CASCADE
);

-- Idempotency: the same POST /v1/orders sent twice creates one order.
-- A separate table because a UNIQUE constraint on orders would have to include created_at.
CREATE TABLE idempotency_keys (
    key               text PRIMARY KEY,
    order_id          bigint NOT NULL,
    order_created_at  timestamptz NOT NULL,
    created_at        timestamptz NOT NULL DEFAULT now()
);

-- Saga trace: every step and compensation of an order, for debugging and the demo
CREATE TABLE saga_log (
    id         bigserial PRIMARY KEY,
    order_id   bigint NOT NULL,
    step       text NOT NULL CHECK (step IN ('reserve_stock', 'pay', 'release_stock', 'confirm')),
    outcome    text NOT NULL CHECK (outcome IN ('ok', 'failed', 'compensated')),
    detail     text,
    at         timestamptz NOT NULL DEFAULT now()
);

-- Indexes needed by foreign keys and joins. Query-specific indexes are added in db/postgres/explain/
-- so the before/after EXPLAIN can be shown.
CREATE INDEX order_items_order_idx ON order_items (order_id, order_created_at);

ALTER TABLE customers OWNER TO orders_svc;
ALTER TABLE orders OWNER TO orders_svc;
ALTER TABLE order_items OWNER TO orders_svc;
ALTER TABLE idempotency_keys OWNER TO orders_svc;
ALTER TABLE saga_log OWNER TO orders_svc;
ALTER ROLE orders_svc SET search_path = orders;
