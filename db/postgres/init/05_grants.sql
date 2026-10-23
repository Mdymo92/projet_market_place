-- Isolation check (volet 1): each service role only sees its own schema.
-- Try it: connect as orders_svc and run SELECT * FROM inventory.stock; -> permission denied.

GRANT USAGE ON SCHEMA auth      TO auth_svc;
GRANT USAGE ON SCHEMA orders    TO orders_svc;
GRANT USAGE ON SCHEMA inventory TO inventory_svc;
GRANT USAGE ON SCHEMA payments  TO payments_svc;

-- analytics_reader: read only on business schemas (never auth), used by the dashboard API
-- and the Spark batch extraction to the lake. Justified in ADR-003.
GRANT USAGE ON SCHEMA orders, inventory, payments TO analytics_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA orders, inventory, payments TO analytics_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE orders_svc    IN SCHEMA orders    GRANT SELECT ON TABLES TO analytics_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE inventory_svc IN SCHEMA inventory GRANT SELECT ON TABLES TO analytics_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE payments_svc  IN SCHEMA payments  GRANT SELECT ON TABLES TO analytics_reader;
