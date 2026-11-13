"""Contracts stay valid and the code follows them."""

import json
import random
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

from tests.conftest import ROOT, load_service

OPENAPI = sorted((ROOT / "contracts" / "openapi").glob("*.yaml"))
EVENTS = {p.stem: json.loads(p.read_text()) for p in (ROOT / "contracts" / "events").glob("*.json")}


@pytest.mark.parametrize("path", OPENAPI, ids=lambda p: p.name)
def test_openapi_files_are_valid(path: Path):
    from openapi_spec_validator import validate

    validate(yaml.safe_load(path.read_text()))


@pytest.mark.parametrize("name", sorted(EVENTS))
def test_event_schemas_are_valid(name):
    jsonschema.Draft202012Validator.check_schema(EVENTS[name])


def test_generator_events_match_contracts():
    sys.path.insert(0, str(ROOT / "streaming" / "generator"))
    import generate

    rng = random.Random(42)
    session = generate.Session(rng)
    for _ in range(200):
        topic, _, event = session.next_event("black_friday")
        assert topic == "clicks"
        jsonschema.validate(event, EVENTS["click"])
        if session.done:
            session = generate.Session(rng)
    topic, _, event = generate.shipment_event(rng)
    jsonschema.validate(event, EVENTS["shipment"])


@pytest.mark.parametrize("service", ["orders", "inventory", "payment", "dashboard"])
def test_service_routes_match_openapi(service):
    """Every path in the contract exists in the service (contract first)."""
    contract = yaml.safe_load((ROOT / "contracts" / "openapi" / f"{service}.yaml").read_text())
    app = load_service(service).app
    routes = {(m, r.path) for r in app.routes for m in getattr(r, "methods", set())}
    for path, ops in contract["paths"].items():
        for method in ops:
            assert (method.upper(), path) in routes, f"{method.upper()} {path} missing in {service}"


def test_graphql_schema_loads():
    mod = load_service("catalog")
    assert "products" in mod.schema.query_type.fields
    for name in ("createProduct", "updateProduct", "archiveProduct", "deleteProduct"):
        assert name in mod.schema.mutation_type.fields
