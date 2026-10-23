#!/usr/bin/env bash
# Backup PostgreSQL (custom format) and MongoDB (archive) into ./backups (volet 1).
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a

mkdir -p backups
ts=$(date +%Y%m%d-%H%M%S)

docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "backups/postgres-$ts.dump"
docker compose exec -T mongo mongodump --quiet --archive \
  -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PASSWORD" --authenticationDatabase admin --db market > "backups/mongo-$ts.archive"

echo "Backups written:"
ls -lh "backups/postgres-$ts.dump" "backups/mongo-$ts.archive"
