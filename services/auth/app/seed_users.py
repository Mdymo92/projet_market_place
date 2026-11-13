"""Create one test user per role + the orders service account. Passwords come from .env.

Run with: make seed   (docker compose exec auth python -m app.seed_users)
"""

import hashlib
import os

from market_common.security import hash_password

from . import db

USERS = [
    ("admin@market.local", "SEED_ADMIN_PASSWORD", ["admin"]),
    ("catalog@market.local", "SEED_CATALOG_MANAGER_PASSWORD", ["catalog_manager"]),
    ("analyst@market.local", "SEED_ANALYST_PASSWORD", ["analyst"]),
    ("logistics@market.local", "SEED_LOGISTICS_PASSWORD", ["logistics"]),
]


def main() -> None:
    for email, env_var, roles in USERS:
        if db.get_user_by_email(email):
            print(f"exists  {email}")
            continue
        db.create_user(email, hash_password(os.environ[env_var]), roles)
        print(f"created {email} {roles}")

    key = os.environ["ORDERS_SERVICE_API_KEY"]
    db.upsert_service_account("orders-service", hashlib.sha256(key.encode()).hexdigest())
    print("service account orders-service ready")
    db.close()


if __name__ == "__main__":
    main()
