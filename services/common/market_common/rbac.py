"""RBAC matrix (volet 3). One place, used by every service and documented in docs/rbac.md.

Kong already refused requests without a valid token (401). Here we decide, per action,
which roles may go on (else 403).
"""

ADMIN = "admin"
CATALOG_MANAGER = "catalog_manager"
ANALYST = "analyst"
LOGISTICS = "logistics"
SERVICE = "service_account"

ALL_ROLES = (ADMIN, CATALOG_MANAGER, ANALYST, LOGISTICS, SERVICE)
HUMAN_ROLES = (ADMIN, CATALOG_MANAGER, ANALYST, LOGISTICS)

# action -> roles allowed
MATRIX: dict[str, tuple[str, ...]] = {
    # auth
    "users:read": (ADMIN,),
    "users:write": (ADMIN,),
    # orders
    "orders:read": (ADMIN, ANALYST, LOGISTICS),
    "orders:create": (ADMIN, SERVICE),
    # catalog
    "catalog:read": ALL_ROLES,
    "catalog:write": (ADMIN, CATALOG_MANAGER),
    # inventory
    "stock:read": (ADMIN, LOGISTICS, ANALYST),
    "stock:write": (ADMIN, LOGISTICS),
    "stock:reserve": (ADMIN, SERVICE),
    # payments
    "payments:create": (SERVICE,),
    "payments:read": (ADMIN, ANALYST),
    # dashboard
    "dashboard:read": HUMAN_ROLES,
    "dashboard:ops": (ADMIN, ANALYST, LOGISTICS),
    "observability:read": (ADMIN,),
}


def allowed(action: str, roles: list[str] | tuple[str, ...]) -> bool:
    return any(role in MATRIX[action] for role in roles)
