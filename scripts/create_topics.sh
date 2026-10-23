#!/usr/bin/env bash
# Creates the Kafka topics used by the platform (auto-create is disabled on purpose).
# Partitioning: inventory and shipments are keyed by warehouse_id (see ADR on Kafka partitioning).
set -euo pipefail

BOOTSTRAP="${KAFKA_BOOTSTRAP:-kafka:9092}"
KT=/opt/kafka/bin/kafka-topics.sh

create() {
  local topic="$1" partitions="$2"
  "$KT" --bootstrap-server "$BOOTSTRAP" --create --if-not-exists \
    --topic "$topic" --partitions "$partitions" --replication-factor 1
}

create clicks 6
create orders 3
create payments 3
create inventory 3
create shipments 3
create alerts 1
create product_updated 1

"$KT" --bootstrap-server "$BOOTSTRAP" --list
echo "topics ready"
