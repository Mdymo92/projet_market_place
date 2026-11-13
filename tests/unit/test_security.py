"""The four cases the jury checks (volet 3): 401 no token, 401 expired, 403 wrong role, OK right role."""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import load_service


@pytest.fixture(scope="module")
def client():
    return TestClient(load_service("orders").app)


ORDER = {"customer_id": 1, "items": [{"product_id": 1, "quantity": 1}]}
KEY = {"Idempotency-Key": "test-key-0001"}


def test_no_token_is_401(client):
    assert client.post("/v1/orders", json=ORDER, headers=KEY).status_code == 401


def test_expired_token_is_401(client, token):
    r = client.post("/v1/orders", json=ORDER, headers=KEY | token("admin", ttl_minutes=-1))
    assert r.status_code == 401
    assert r.json()["detail"] == "token expired"


def test_bad_signature_is_401(client):
    r = client.get("/v1/orders", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401


def test_analyst_cannot_create_order(client, token):
    r = client.post("/v1/orders", json=ORDER, headers=KEY | token("analyst"))
    assert r.status_code == 403


def test_service_account_passes_rbac(client, token):
    # passes authentication and RBAC; the Saga itself is not written yet (501)
    r = client.post("/v1/orders", json=ORDER, headers=KEY | token("service_account"))
    assert r.status_code == 501


def test_idempotency_key_required(client, token):
    r = client.post("/v1/orders", json=ORDER, headers=token("admin"))
    assert r.status_code == 422


def test_health_and_metrics_are_open(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/metrics").status_code == 200
