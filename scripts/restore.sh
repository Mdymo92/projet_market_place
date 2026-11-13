#!/usr/bin/env bash
# Restore the latest backups and print row counts, to prove the restore works (volet 1).
# Demo: make backup -> delete some rows -> make restore -> counts are back.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a

pg=$(ls -t backups/postgres-*.dump | head -1)
mg=$(ls -t backups/mongo-*.archive | head -1)
echo "Restoring $pg and $mg"

docker compose exec -T postgres pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists < "$pg"
docker compose exec -T mongo mongorestore --quiet --archive --drop \
  -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PASSWORD" --authenticationDatabase admin < "$mg"

docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
  "SELECT 'orders' AS t, count(*) FROM orders.orders UNION ALL SELECT 'stock', count(*) FROM inventory.stock;"
docker compose exec -T mongo mongosh --quiet -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PASSWORD" \
  --authenticationDatabase admin --eval 'db.getSiblingDB("market").catalog.countDocuments()'
