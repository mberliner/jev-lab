"""Fórmulas oficiales de la confianza de Choice y Score (research.md R3)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from jevlab.domain.confidence import choice_confidence, most_likely_position, score_confidence

_PROBS = st.lists(st.floats(min_value=0, max_value=1), min_size=2, max_size=8)


def test_choice_example_from_contract() -> None:
    probabilities = {"facturacion": 0.88, "tecnico": 0.06, "cuenta": 0.04, "other": 0.02}
    assert choice_confidence(probabilities) == pytest.approx(0.84)


def test_choice_uniform_is_zero_and_certain_is_one() -> None:
    assert choice_confidence({"a": 0.25, "b": 0.25, "c": 0.25, "d": 0.25}) == pytest.approx(0)
    assert choice_confidence({"a": 1.0, "b": 0.0}) == pytest.approx(1)


def test_choice_is_not_clipped_nor_normalized() -> None:
    # Suma 0,5: se usa tal como llega, aunque quede por debajo de cero.
    assert choice_confidence({"a": 0.2, "b": 0.2, "c": 0.1}) == pytest.approx(
        (0.2 - 1 / 3) / (1 - 1 / 3)
    )


def test_choice_needs_two_options() -> None:
    with pytest.raises(ValueError):
        choice_confidence({"a": 1.0})


@given(_PROBS, st.floats(min_value=0, max_value=1))
def test_choice_is_monotonic_in_p_max(values: list[float], extra: float) -> None:
    probabilities = {str(i): v for i, v in enumerate(values)}
    raised = dict(probabilities)
    top = max(probabilities, key=lambda k: probabilities[k])
    raised[top] = max(probabilities[top], extra)
    assert choice_confidence(raised) >= choice_confidence(probabilities) - 1e-12


def test_score_example() -> None:
    # n = 4, MAD_unif = 1; m = 1; Σ p_i·|i - m| = 0,5.
    assert score_confidence([0.20, 0.55, 0.20, 0.05]) == pytest.approx(0.5)


def test_score_certain_is_one_and_spread_is_floored_at_zero() -> None:
    assert score_confidence([0.0, 0.0, 1.0, 0.0]) == pytest.approx(1)
    assert score_confidence([0.5, 0.0, 0.0, 0.5]) == 0


def test_score_needs_two_levels() -> None:
    with pytest.raises(ValueError):
        score_confidence([1.0])


@given(_PROBS)
def test_score_is_within_unit_interval(values: list[float]) -> None:
    total = sum(values)
    probabilities = [v / total for v in values] if total else values
    assert 0 <= score_confidence(probabilities) <= 1


def test_ties_resolve_to_first_level() -> None:
    assert most_likely_position([0.4, 0.4, 0.2]) == 0
    assert most_likely_position([0.1, 0.45, 0.45]) == 1
