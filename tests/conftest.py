import importlib
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "common"))
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-test-secret-123")
os.environ.setdefault("JWT_ISSUER", "market-auth")
os.environ.setdefault("LOG_FORMAT", "text")


def load_service(name: str):
    """Import services/<name>/app/main.py. Every service has a package called `app`, so clear it first."""
    for mod in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
        del sys.modules[mod]
    path = str(ROOT / "services" / name)
    sys.path = [p for p in sys.path if not p.startswith(str(ROOT / "services")) or p.endswith("common")]
    sys.path.insert(0, path)
    return importlib.import_module("app.main")


@pytest.fixture
def token():
    from market_common.security import create_access_token

    def make(*roles: str, ttl_minutes: int = 15) -> dict:
        return {"Authorization": f"Bearer {create_access_token('tester@market.local', list(roles), ttl_minutes)}"}

    return make
