"""Circuit breaker demo in a test: a dead dependency makes the breaker open, then calls fail fast."""

import asyncio

import httpx
import pytest

from market_common.resilience import CircuitOpen, ResilientClient


def _client(handler, fail_max=2):
    return ResilientClient("payment", "http://payment", fail_max=fail_max, transport=httpx.MockTransport(handler))


def test_retry_then_success():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(503 if calls["n"] < 3 else 201, json={})

    resp = asyncio.run(_client(handler).post("/v1/payments"))
    assert resp.status_code == 201
    assert calls["n"] == 3  # two retries


def test_breaker_opens_after_repeated_failures():
    def down(request):
        raise httpx.ConnectError("payment is down")

    client = _client(down, fail_max=2)

    async def scenario():
        for _ in range(2):
            with pytest.raises(httpx.ConnectError):
                await client.post("/v1/payments")
        with pytest.raises(CircuitOpen):
            await client.post("/v1/payments")  # fails fast, no network call

    asyncio.run(scenario())
