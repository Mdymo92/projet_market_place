from tests.conftest import load_service


def test_payment_limit_is_200_eur():
    decide = load_service("payment").decide
    assert decide(20_000) == ("succeeded", None)
    assert decide(20_001) == ("failed", "amount_above_limit")
    assert decide(0) == ("succeeded", None)
