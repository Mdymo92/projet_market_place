"""Inventory service: warehouses, stock, reservations. Contract: contracts/openapi/inventory.yaml

Routes and RBAC are wired; business logic is marked TODO (owner: Philip, week 2).
Reservation must lock the stock rows (SELECT ... FOR UPDATE) and decrement in one transaction,
and be idempotent on the Idempotency-Key (reservations.idempotency_key is UNIQUE).
Publish stock_changed events to the `inventory` topic, key = warehouse_id.
"""

from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel, Field

from market_common.app_factory import create_app
from market_common.security import Principal, require

app = create_app("inventory", "Market Inventory API")


class StockSet(BaseModel):
    warehouse_id: int
    quantity: int = Field(ge=0)


class ReservationItem(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)


class ReservationCreate(BaseModel):
    order_id: int
    items: list[ReservationItem] = Field(min_length=1)


def _todo(what: str):
    raise HTTPException(status_code=501, detail=f"not implemented yet: {what}")


@app.get("/v1/warehouses")
def list_warehouses(_: Principal = Depends(require("stock:read"))):
    _todo("warehouses with stored_units / capacity_units and status near_saturation above 0.9")


@app.get("/v1/inventory/stock")
def list_stock(product_id: int | None = None, below: int | None = None, _: Principal = Depends(require("stock:read"))):
    _todo("stock lines")


@app.put("/v1/inventory/{product_id}")
def set_stock(product_id: int, body: StockSet, _: Principal = Depends(require("stock:write"))):
    _todo("set stock level + stock_adjusted event")


@app.post("/v1/inventory/reservations", status_code=201)
def reserve(
    body: ReservationCreate,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    _: Principal = Depends(require("stock:reserve")),
):
    _todo("reserve stock (all or nothing)")


@app.post("/v1/inventory/reservations/{order_id}/release")
def release(order_id: int, _: Principal = Depends(require("stock:reserve"))):
    _todo("release reserved stock (Saga compensation, no effect if already released)")


@app.post("/v1/inventory/reservations/{order_id}/commit")
def commit(order_id: int, _: Principal = Depends(require("stock:reserve"))):
    _todo("commit reservation")
