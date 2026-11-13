"""Dashboard API: tabs 1, 4 and 5. Contract: contracts/openapi/dashboard.yaml

Reads (all read-only):
  - Delta tables of the lake consumption zone (KPIs, alerts) -> e.g. with the `deltalake` package
  - the Inventory API for remaining stock and warehouses (never the inventory tables directly)
  - Prometheus HTTP API (services health)
Routes and RBAC are wired; data access is TODO (owner: Ilyes, week 4).
"""

from fastapi import Depends, HTTPException

from market_common.app_factory import create_app
from market_common.security import Principal, require

app = create_app("dashboard", "Market Dashboard API")


def _todo(what: str):
    raise HTTPException(status_code=501, detail=f"not implemented yet: {what}")


@app.get("/v1/dashboard/summary")
def summary(_: Principal = Depends(require("dashboard:read"))):
    _todo("today's KPIs from consumption/kpis_daily")


@app.get("/v1/dashboard/hourly-orders")
def hourly_orders(_: Principal = Depends(require("dashboard:read"))):
    _todo("orders per hour from consumption/orders_hourly")


@app.get("/v1/dashboard/low-stock")
def low_stock(threshold: int = 10, _: Principal = Depends(require("dashboard:ops"))):
    _todo("GET inventory /v1/inventory/stock?below=threshold + names from catalog GraphQL")


@app.get("/v1/dashboard/alerts")
def alerts(limit: int = 20, _: Principal = Depends(require("dashboard:ops"))):
    _todo("latest alerts, deduplicated on alert_id")


@app.get("/v1/dashboard/alerts/stream")
def alerts_stream(_: Principal = Depends(require("dashboard:ops"))):
    _todo("Server-Sent Events fed by a Kafka consumer on topic alerts")


@app.get("/v1/dashboard/services-health")
def services_health(_: Principal = Depends(require("observability:read"))):
    _todo("query Prometheus: up, p95 latency, error rate per service")
