from market_common.rbac import ALL_ROLES, MATRIX, allowed


def test_every_action_uses_known_roles():
    for action, roles in MATRIX.items():
        assert set(roles) <= set(ALL_ROLES), action


def test_matrix_rules_from_the_brief():
    assert not allowed("orders:create", ["analyst"])  # analyst POST order -> 403
    assert allowed("catalog:write", ["catalog_manager"])
    assert not allowed("catalog:write", ["logistics"])
    assert allowed("stock:write", ["logistics"])
    assert not allowed("users:write", ["catalog_manager"])
    assert allowed("payments:create", ["service_account"])
    assert not allowed("payments:create", ["admin"])  # only the orders service pays


def test_matrix_matches_the_brief_table():
    # rows of "Qui a le droit d'appeler quoi" in the project brief
    expected = {
        "orders:read": {"admin", "analyst", "logistics", "service_account"},
        "orders:create": {"admin", "service_account"},
        "catalog:read": {"admin", "catalog_manager", "analyst", "logistics", "service_account"},
        "catalog:write": {"admin", "catalog_manager"},
        "stock:read": {"admin", "analyst", "logistics"},
        "stock:write": {"admin", "logistics", "service_account"},
        "dashboard:read": {"admin", "catalog_manager", "analyst", "logistics"},
        "users:write": {"admin"},
        "roles:write": {"admin"},
    }
    for action, roles in expected.items():
        assert set(MATRIX[action]) == roles, action
