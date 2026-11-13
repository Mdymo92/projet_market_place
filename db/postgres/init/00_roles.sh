#!/usr/bin/env bash
# One PostgreSQL role per service (volet 1). Passwords come from .env, never from the repo.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v auth_pw="$AUTH_DB_PASSWORD" \
  -v orders_pw="$ORDERS_DB_PASSWORD" \
  -v inventory_pw="$INVENTORY_DB_PASSWORD" \
  -v payments_pw="$PAYMENTS_DB_PASSWORD" \
  -v analytics_pw="$ANALYTICS_DB_PASSWORD" <<-'EOSQL'
  CREATE ROLE auth_svc         LOGIN PASSWORD :'auth_pw';
  CREATE ROLE orders_svc       LOGIN PASSWORD :'orders_pw';
  CREATE ROLE inventory_svc    LOGIN PASSWORD :'inventory_pw';
  CREATE ROLE payments_svc     LOGIN PASSWORD :'payments_pw';
  -- read-only role for the dashboard API and Spark batch extraction (see ADR-003)
  CREATE ROLE analytics_reader LOGIN PASSWORD :'analytics_pw';

  -- nobody gets anything by default
  REVOKE ALL ON SCHEMA public FROM PUBLIC;
  REVOKE ALL ON DATABASE market FROM PUBLIC;
  GRANT CONNECT ON DATABASE market TO auth_svc, orders_svc, inventory_svc, payments_svc, analytics_reader;
EOSQL
