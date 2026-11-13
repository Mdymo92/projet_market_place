-- Schema inventory: warehouses, stock levels, reservations. Owned by inventory_svc.
CREATE SCHEMA inventory AUTHORIZATION inventory_svc;
SET search_path = inventory;

CREATE TABLE warehouses (
    id              serial PRIMARY KEY,
    name            text NOT NULL UNIQUE,
    capacity_units  integer NOT NULL CHECK (capacity_units > 0)
);

CREATE TABLE stock (
    product_id    integer NOT NULL,               -- application link to the catalog
    warehouse_id  integer NOT NULL REFERENCES warehouses(id),
    quantity      integer NOT NULL CHECK (quantity >= 0),   -- never sell what is not there
    updated_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (product_id, warehouse_id)
);

-- A reservation is taken by the order Saga and either committed or released.
CREATE TABLE reservations (
    id               bigserial PRIMARY KEY,
    order_id         bigint NOT NULL,             -- application link to orders
    product_id       integer NOT NULL,
    warehouse_id     integer NOT NULL REFERENCES warehouses(id),
    quantity         integer NOT NULL CHECK (quantity > 0),
    status           text NOT NULL DEFAULT 'reserved' CHECK (status IN ('reserved', 'committed', 'released')),
    idempotency_key  text NOT NULL UNIQUE,        -- same request twice = reserved once
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX stock_warehouse_idx ON stock (warehouse_id);
CREATE INDEX reservations_order_idx ON reservations (order_id);

ALTER TABLE warehouses OWNER TO inventory_svc;
ALTER TABLE stock OWNER TO inventory_svc;
ALTER TABLE reservations OWNER TO inventory_svc;
ALTER ROLE inventory_svc SET search_path = inventory;
