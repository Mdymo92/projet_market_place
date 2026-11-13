"""Catalog service: GraphQL over MongoDB. Contract: contracts/graphql/schema.graphql (schema first).

Queries read MongoDB; mutations check the role then are TODO (owner: Philip, week 2).
Kong already checked the token; each resolver checks the role (RBAC matrix).
"""

from functools import lru_cache
from pathlib import Path

from ariadne import MutationType, QueryType, ScalarType, load_schema_from_path, make_executable_schema
from ariadne.asgi import GraphQL
from fastapi import HTTPException, Request
from graphql import GraphQLError
from pymongo import MongoClient

from market_common.app_factory import create_app
from market_common.config import get_settings
from market_common.rbac import allowed
from market_common.security import current_principal

# /srv/contracts in the image, <repo>/contracts when run from the repo
SCHEMA_PATH = next(
    p / "contracts" / "graphql" / "schema.graphql"
    for p in Path(__file__).resolve().parents
    if (p / "contracts" / "graphql" / "schema.graphql").exists()
)

query = QueryType()
mutation = MutationType()
json_scalar = ScalarType("JSON")
datetime_scalar = ScalarType("DateTime")


@datetime_scalar.serializer
def _serialize_dt(value):
    return value.isoformat()


@lru_cache
def catalog():
    return MongoClient(get_settings().mongo_url, serverSelectionTimeoutMS=2000)["market"]["catalog"]


def _to_graphql(doc: dict) -> dict:
    return {
        "productId": doc["product_id"],
        "name": doc["name"],
        "category": doc["category"],
        "priceCents": doc["price_cents"],
        "status": doc["status"],
        "tags": doc.get("tags", []),
        "description": doc.get("description"),
        "attributes": doc.get("attributes"),
        "stock": None,  # TODO: ask the inventory service (batch per page, not one call per product)
        "indexedAt": doc.get("indexed_at"),
    }


def _check(info, action: str) -> None:
    principal = info.context["principal"]
    if not allowed(action, principal.roles):
        raise GraphQLError(f"forbidden: role not allowed for {action}", extensions={"code": "FORBIDDEN"})


@query.field("products")
def resolve_products(_, info, filter=None, limit=20, offset=0):
    _check(info, "catalog:read")
    f = filter or {}
    mongo_filter: dict = {}
    if f.get("category"):
        mongo_filter["category"] = f["category"]
    if f.get("status"):
        mongo_filter["status"] = f["status"]
    if f.get("maxPriceCents") is not None:
        mongo_filter["price_cents"] = {"$lte": f["maxPriceCents"]}
    if f.get("search"):
        mongo_filter["$text"] = {"$search": f["search"]}
    col = catalog()
    docs = col.find(mongo_filter).sort("product_id", 1).skip(offset).limit(min(limit, 100))
    return {"items": [_to_graphql(d) for d in docs], "total": col.count_documents(mongo_filter)}


@query.field("product")
def resolve_product(_, info, productId):
    _check(info, "catalog:read")
    doc = catalog().find_one({"product_id": productId})
    return _to_graphql(doc) if doc else None


@query.field("categories")
def resolve_categories(_, info):
    _check(info, "catalog:read")
    return sorted(catalog().distinct("category"))


@mutation.field("createProduct")
def resolve_create(_, info, input):
    _check(info, "catalog:write")
    raise GraphQLError("not implemented yet: insert product")


@mutation.field("updateProduct")
def resolve_update(_, info, productId, input):
    _check(info, "catalog:write")
    raise GraphQLError("not implemented yet: update product + publish product_updated")


schema = make_executable_schema(load_schema_from_path(str(SCHEMA_PATH)), query, mutation, json_scalar, datetime_scalar)


async def _context(request: Request, _data=None) -> dict:
    # 401 here if the token is missing or invalid (same rules as the REST services)
    creds = request.headers.get("authorization", "")
    scheme, _, token = creds.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401, "missing bearer token")
    from fastapi.security import HTTPAuthorizationCredentials

    principal = current_principal(request, HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))
    return {"request": request, "principal": principal}


app = create_app("catalog", "Market Catalog GraphQL")
app.mount("/graphql", GraphQL(schema, context_value=_context, debug=False))
