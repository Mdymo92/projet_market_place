# Roles and rights (RBAC)

Source of truth in code: `services/common/market_common/rbac.py`. Kong refuses a missing or expired token (401); each service refuses a role that is not allowed (403) and logs the refusal (who, what, when).

| Action | admin | catalog_manager | analyst | logistics | service_account |
| --- | :-: | :-: | :-: | :-: | :-: |
| Read / create users | ✓ | | | | |
| Read orders | ✓ | | ✓ | ✓ | |
| Create an order | ✓ | | | | ✓ |
| Read catalog | ✓ | ✓ | ✓ | ✓ | ✓ |
| Create / edit products | ✓ | ✓ | | | |
| Read stock and warehouses | ✓ | | ✓ | ✓ | |
| Change stock | ✓ | | | ✓ | |
| Reserve / release stock (Saga) | ✓ | | | | ✓ |
| Create a payment | | | | | ✓ |
| Read payments | ✓ | | ✓ | | |
| Dashboard KPIs (tab 1) | ✓ | ✓ | ✓ | ✓ | |
| Alerts, low stock, logistics (tabs 1, 4) | ✓ | | ✓ | ✓ | |
| Services health (tab 5) | ✓ | | | | |

Test accounts (created by `make seed`, passwords in `.env`): `admin@market.local`, `catalog@market.local`, `analyst@market.local`, `logistics@market.local`, plus the service account `orders-service` (API key in `.env`).

Demo for the jury:
1. `GET /v1/orders` without token → 401 (Kong)
2. Same with an expired token → 401
3. `POST /v1/orders` as analyst → 403 (orders service)
4. `POST /v1/orders` as admin → 201
