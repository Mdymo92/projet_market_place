-- Schema payments. Owned by payments_svc. The payment service refuses any amount above 200 EUR (20000 cents).
CREATE SCHEMA payments AUTHORIZATION payments_svc;
SET search_path = payments;

CREATE TABLE payments (
    id               serial PRIMARY KEY,
    order_id         bigint NOT NULL,             -- application link to orders
    amount_cents     integer NOT NULL CHECK (amount_cents >= 0),
    status           text NOT NULL CHECK (status IN ('succeeded', 'failed', 'refunded')),
    failure_reason   text,
    idempotency_key  text NOT NULL UNIQUE,
    created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX payments_order_idx ON payments (order_id);

ALTER TABLE payments OWNER TO payments_svc;
ALTER ROLE payments_svc SET search_path = payments;
