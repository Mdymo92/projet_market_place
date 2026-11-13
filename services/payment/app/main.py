"""Payment service (simulated). Contract: contracts/openapi/payment.yaml

Rule from the brief: any amount above 200 EUR (20000 cents) is refused.
The refusal rule is implemented; storing the payment and publishing the event are TODO (owner: Philip, week 2).
"""

from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel, Field

from market_common.app_factory import create_app
from market_common.security import Principal, require

app = create_app("payment", "Market Payment API")

MAX_AMOUNT_CENTS = 20_000


class PaymentCreate(BaseModel):
    order_id: int
    amount_cents: int = Field(ge=0)


def decide(amount_cents: int) -> tuple[str, str | None]:
    """Return (status, failure_reason)."""
    if amount_cents > MAX_AMOUNT_CENTS:
        return "failed", "amount_above_limit"
    return "succeeded", None


@app.post("/v1/payments", status_code=201)
def pay(
    body: PaymentCreate,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    _: Principal = Depends(require("payments:create")),
):
    status, reason = decide(body.amount_cents)
    raise HTTPException(
        status_code=501,
        detail=f"not implemented yet: store payment ({status}, {reason}) idempotently + publish event",
    )


@app.get("/v1/payments")
def list_payments(order_id: int, _: Principal = Depends(require("payments:read"))):
    raise HTTPException(status_code=501, detail="not implemented yet: payments of an order")
