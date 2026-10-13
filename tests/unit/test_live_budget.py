import pytest

from tests.live.budget import DEFAULT_BUDGET_USD, check_budget, parse_budget


def test_budget_defaults_to_ten_cents() -> None:
    assert parse_budget(None) == DEFAULT_BUDGET_USD == 0.10
    assert parse_budget("  ") == DEFAULT_BUDGET_USD


def test_budget_is_read_from_the_variable() -> None:
    assert parse_budget("0.5") == 0.5


def test_negative_budget_is_rejected() -> None:
    with pytest.raises(ValueError, match="negativo"):
        parse_budget("-1")


def test_caps_within_budget_pass() -> None:
    assert check_budget({"a": 0.04, "b": 0.06}, 0.10) is None


def test_caps_over_budget_abort() -> None:
    reason = check_budget({"a": 0.08, "b": 0.05}, 0.10)
    assert reason is not None
    assert "0.13" in reason


def test_undeclared_cap_aborts() -> None:
    reason = check_budget({"tests/live/test_x.py::test_y": None}, 1.0)
    assert reason is not None
    assert "test_y" in reason
