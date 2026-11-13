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
