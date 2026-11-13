# Market web app

React + Vite + TypeScript, rebuilt from the maquette. Not started yet (owner: Philip for the shell and tabs 2-3, Ilyes for tabs 1 and 4, tab 5 shared).

Rules:
- Every number comes from the APIs behind Kong (`http://localhost:8000`), nothing hard coded.
- One `src/api.ts` client adds the JWT to every call and sends back to login on 401.
- The UI hides what the role cannot do; a 403 shows a clear message.

| Tab | Reads from |
| --- | --- |
| Login | `POST /v1/auth/login` |
| 1 Vue d'ensemble | `/v1/dashboard/summary`, `/hourly-orders`, `/low-stock`, `/alerts/stream` |
| 2 Commandes | `GET/POST /v1/orders` |
| 3 Catalogue | `POST /graphql` (liste + formulaire pour créer, modifier, archiver, supprimer un produit) |
| 4 Logistique | `GET /v1/warehouses` |
| 5 Observabilité | `/v1/dashboard/services-health` + link to Grafana |

Start: `npm create vite@latest . -- --template react-ts`, then add a `frontend` service to `docker-compose.yml`.
