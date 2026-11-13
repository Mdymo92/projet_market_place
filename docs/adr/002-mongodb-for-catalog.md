# ADR-002: MongoDB for the product catalog

- Status: proposed (draft, to complete)
- Date: 2026-11-13
- Owner: Philip

## Context

Products have different fields per category (shoe sizes, headphone battery life, cable length). The catalog is read far more than written, and the tab Catalogue needs search by name and category.

## Options considered

| Option | For | Against |
| --- | --- | --- |
| PostgreSQL with JSONB | One database to run, transactions | Querying and validating free attributes is more awkward |
| MongoDB | Documents fit products naturally, `$jsonSchema` validation on required fields, text index | One more database, no foreign key to orders |
| Elasticsearch | Best search | Not a primary store, heavy to run |

## Decision

MongoDB 7, collection `catalog`, required fields validated by `$jsonSchema`, flexible `attributes`, prices in integer cents. The link with PostgreSQL is `product_id`, checked by the code.

## Consequences

- BASE is acceptable here: a price shown a few seconds late is not a loss, the order service re-reads the price when the order is placed.
- No foreign key across databases: the order service must check that a `product_id` exists.
- Changes publish a `product_updated` event so the lake keeps the price history.
