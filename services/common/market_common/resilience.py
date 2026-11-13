"""Resilience for outbound calls (volet 3): timeout, retry, circuit breaker, bulkhead.

One ResilientClient per dependency, e.g. in the orders service:
    payment = ResilientClient("payment", settings.payment_url, max_concurrent=10)
    resp = await payment.post("/v1/payments", json=..., headers=...)

- timeout: every call gives up after `timeout_s` (default 2 s)
- retry: up to 3 attempts with exponential backoff, only on network errors and 502/503/504
- circuit breaker: after 5 failures in a row the circuit opens for 30 s and calls fail fast
  with CircuitOpen (the API answers 503 instead of hanging)
- bulkhead: at most `max_concurrent` calls in flight to this dependency, so a slow payment
  service cannot use up all the workers of the orders service
"""

import asyncio
import logging

import httpx
import pybreaker
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

log = logging.getLogger("resilience")


class CircuitOpen(Exception):
    """The dependency is considered down; fail fast."""


class RetryableStatus(Exception):
    def __init__(self, response: httpx.Response):
        super().__init__(f"retryable status {response.status_code}")
        self.response = response


class ResilientClient:
    def __init__(
        self,
        name: str,
        base_url: str,
        timeout_s: float = 2.0,
        max_concurrent: int = 10,
        fail_max: int = 5,
        reset_timeout_s: int = 30,
        transport: httpx.AsyncBaseTransport | None = None,  # tests inject a fake transport
    ):
        self.name = name
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout_s, transport=transport)
        self._bulkhead = asyncio.Semaphore(max_concurrent)
        self.breaker = pybreaker.CircuitBreaker(fail_max=fail_max, reset_timeout=reset_timeout_s, name=name)

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        if self.breaker.current_state == pybreaker.STATE_OPEN:
            raise CircuitOpen(self.name)
        async with self._bulkhead:
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential(multiplier=0.2, max=2),
                    retry=retry_if_exception_type((httpx.TransportError, RetryableStatus)),
                    reraise=True,
                ):
                    with attempt:
                        response = await self._client.request(method, url, **kwargs)
                        if response.status_code in (502, 503, 504):
                            raise RetryableStatus(response)
                self._record_success()
                return response
            except (httpx.TransportError, RetryableStatus):
                self._record_failure()
                raise

    async def post(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def get(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    def _record_success(self) -> None:
        try:
            self.breaker.call(lambda: None)
        except pybreaker.CircuitBreakerError:
            pass

    def _record_failure(self) -> None:
        def fail():
            raise RuntimeError("call failed")

        try:
            self.breaker.call(fail)
        except (RuntimeError, pybreaker.CircuitBreakerError):
            pass
        log.warning("call to %s failed, breaker state=%s", self.name, self.breaker.current_state)

    async def aclose(self) -> None:
        await self._client.aclose()
