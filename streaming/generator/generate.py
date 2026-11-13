"""Realistic event generator for Kafka (volet 4): browsing sessions, carts, checkouts, shipments.

Events follow contracts/events/*.json. Orders placed through the API also produce events
(from the orders service); this generator adds the browsing traffic the API never sees.

Env:
  KAFKA_BOOTSTRAP     kafka:9092
  EVENTS_PER_SECOND   20
  MODE                normal | black_friday  (x10 traffic, more add_to_cart)
"""

import json
import os
import random
import signal
import time
import uuid
from datetime import UTC, datetime

PRODUCTS = {
    i: price for i, price in enumerate([12990, 5990, 3990, 8990, 6990, 11990, 2990, 990, 1490, 15990, 4990, 9990], 1)
}
WAREHOUSES = [1, 2, 3]
DEVICES = ["mobile", "desktop", "tablet"]


def envelope(event_type: str, payload: dict) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "occurred_at": datetime.now(UTC).isoformat(),
        "producer": "generator",
        "payload": payload,
    }


class Session:
    """One visitor: views pages, maybe adds to cart, sometimes checks out, often abandons."""

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.id = str(uuid.uuid4())
        self.customer_id = rng.randint(1, 25) if rng.random() < 0.6 else None
        self.device = rng.choice(DEVICES)
        self.cart: list[int] = []
        self.done = False

    def next_event(self, mode: str) -> tuple[str, str, dict]:
        """Return (topic, key, event)."""
        r = self.rng.random()
        add_prob = 0.35 if mode == "black_friday" else 0.2
        base = {"session_id": self.id, "customer_id": self.customer_id, "device": self.device}
        if self.cart and r < 0.08:
            self.done = True
            return "clicks", self.id, envelope("checkout_started", {**base, "product_id": None, "page": "/checkout"})
        if r < 0.08 + add_prob:
            pid = self.rng.choice(list(PRODUCTS))
            self.cart.append(pid)
            return "clicks", self.id, envelope("add_to_cart", {**base, "product_id": pid, "page": f"/product/{pid}"})
        if r > 0.97:
            self.done = True  # leaves the site: an abandoned cart if self.cart is not empty
        pid = self.rng.choice(list(PRODUCTS))
        return "clicks", self.id, envelope("product_view", {**base, "product_id": pid, "page": f"/product/{pid}"})


def shipment_event(rng: random.Random) -> tuple[str, str, dict]:
    wid = rng.choice(WAREHOUSES)
    return (
        "shipments",
        str(wid),
        envelope(
            rng.choice(["shipment_prepared", "shipment_shipped", "shipment_delivered"]),
            {
                "shipment_id": str(uuid.uuid4()),
                "order_id": rng.randint(1, 5000),
                "warehouse_id": wid,
                "units": rng.randint(1, 5),
            },
        ),
    )


def run() -> None:
    from confluent_kafka import Producer

    bootstrap = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
    rate = float(os.getenv("EVENTS_PER_SECOND", "20"))
    mode = os.getenv("MODE", "normal")
    if mode == "black_friday":
        rate *= 10

    producer = Producer({"bootstrap.servers": bootstrap, "enable.idempotence": True, "linger.ms": 20})
    rng = random.Random()
    sessions: list[Session] = []
    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    print(f"generator: {rate} events/s to {bootstrap}, mode={mode}", flush=True)

    sent = 0
    while running:
        started = time.monotonic()
        while len(sessions) < max(5, int(rate)):
            sessions.append(Session(rng))
        for _ in range(int(rate)):
            if rng.random() < 0.05:
                topic, key, event = shipment_event(rng)
            else:
                s = rng.choice(sessions)
                topic, key, event = s.next_event(mode)
                if s.done:
                    sessions.remove(s)
            producer.produce(topic, key=key, value=json.dumps(event))
            sent += 1
        producer.poll(0)
        if sent % 1000 < rate:
            print(f"generator: {sent} events sent", flush=True)
        time.sleep(max(0.0, 1.0 - (time.monotonic() - started)))
    producer.flush(5)


if __name__ == "__main__":
    run()
