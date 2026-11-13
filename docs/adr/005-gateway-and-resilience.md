# ADR-005: Kong as API gateway, resilience in each service

- Status: proposed
- Date: 2026-11-13
- Owner: Philip
- Volet: 3 (Platform & API)

## Context

Six services must be reachable through one entry point that checks who calls (JWT) and limits calls. A slow or down payment service must not block order taking, and a retried request must not create two orders.

## Options considered

| Option | For | Against |
| --- | --- | --- |
| Kong (DB-less) | JWT and rate limiting plugins, declarative config in Git, Prometheus plugin | Heavier than a plain proxy |
| Traefik | Light, auto-discovery from Docker | No complete JWT verification without extra middleware |
| NGINX | Very fast, well known | JWT and rate limiting per route to write by hand |

For resilience: a service mesh (Istio) versus a small shared library.

## Decision

- Kong checks the token (401) and limits calls; each service checks the role (403).
- A shared `ResilientClient` (httpx + tenacity + pybreaker + semaphore) for every outbound call: 2 s timeout, 3 retries on network errors and 502/503/504, circuit breaker opening after 5 failures for 30 s, at most 10 concurrent calls per dependency.
- Orchestrated Saga in Orders; `Idempotency-Key` header on every state-changing POST.

## Consequences

- Availability over waiting: when the breaker is open, the API answers 503 immediately.
- Demo: stop the payment container, place orders, the breaker opens and Grafana shows the service degraded.
- A mesh would move this out of the code; rejected as too heavy for a laptop demo.
