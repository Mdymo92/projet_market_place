"""Orders service: orders + Saga orchestrator. Contract: contracts/openapi/orders.yaml

Routes and RBAC are wired; business logic is marked TODO (owner: Philip, week 2-3).

Saga for POST /v1/orders (see docs/adr and the workplan):
  1. insert order (status pending) + idempotency key, in ONE transaction
  2. inventory: POST /v1/inventory/reservations   (Idempotency-Key = f"{key}:reserve")
       409 -> order cancelled, return 409
  3. payment:   POST /v1/payments                 (Idempotency-Key = f"{key}:pay")
       failed -> inventory release (compensation), status payment_failed
  4. inventory: commit, status paid, publish order_paid to Kafka
Every step is written to orders.saga_log.
Outbound calls go through market_common.resilience.ResilientClient (timeout, retry, breaker, bulkhead).
"""

from datetime import datetime

from fastapi import Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from market_common.app_factory import create_app
from market_common.security import Principal, require

app = create_app("orders", "Market Orders API")


class OrderItemCreate(BaseModel):
    product_id: int = Field(ge=1)
    quantity: int = Field(ge=1, le=20)


class OrderCreate(BaseModel):
    customer_id: int
    items: list[OrderItemCreate] = Field(min_length=1)


def _todo(what: str):
    raise HTTPException(status_code=501, detail=f"not implemented yet: {what}")


@app.get("/v1/orders")
def list_orders(
    status: str | None = None,
    customer_id: int | None = None,
    limit: int = Query(50, le=200),
    before: datetime | None = None,
    _: Principal = Depends(require("orders:read")),
):
    _todo("list orders (SELECT ... ORDER BY created_at DESC LIMIT %s)")


@app.get("/v1/orders/{order_id}")
def get_order(order_id: int, _: Principal = Depends(require("orders:read"))):
    _todo("order detail with items and saga_log")


@app.post("/v1/orders", status_code=201)
def create_order(
    body: OrderCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=64),
    _: Principal = Depends(require("orders:create")),
):
    _todo("Saga: reserve stock -> pay -> commit or release")
