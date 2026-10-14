"""Prioridad: nivel más probable y umbral con el `score` esperado, `>=` (FR-008)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from jevlab.domain.triage import ScoreAnswer, interpret_priority
from tests.builders import triage_spec

_SPEC = triage_spec().priority


def _answer(score: float, probabilities: dict[int, float]) -> ScoreAnswer:
    return ScoreAnswer(score=score, confidence=0.4, probabilities=probabilities)


def test_most_likely_distribution_and_threshold() -> None:
    outcome = interpret_priority(_SPEC, _answer(1.1, {0: 0.2, 1: 0.55, 2: 0.2, 3: 0.05}))

    assert outcome.most_likely == "media"
    assert outcome.distribution == (
        (0, "baja", 0.2),
        (1, "media", 0.55),
        (2, "alta", 0.2),
        (3, "critica", 0.05),
    )
    assert outcome.confidence == 0.4
    assert outcome.recomputed_confidence == pytest.approx(0.5)
    assert outcome.expected_score == 1.1
    assert (outcome.threshold_level, outcome.threshold_position) == ("alta", 2)
    assert outcome.threshold_justification == "provisional"
    assert outcome.reaches_threshold is False


def test_exactly_the_threshold_reaches_it() -> None:
    outcome = interpret_priority(_SPEC, _answer(2.0, {0: 0.1, 1: 0.1, 2: 0.7, 3: 0.1}))
    assert outcome.reaches_threshold is True


def test_most_likely_media_with_threshold_reached_is_not_contradictory() -> None:
    # Bimodal: «media» es el nivel más probable, pero el valor esperado alcanza «alta».
    outcome = interpret_priority(_SPEC, _answer(2.0, {0: 0.0, 1: 0.4, 2: 0.2, 3: 0.4}))
    assert outcome.most_likely == "media"
    assert outcome.reaches_threshold is True


def test_ties_resolve_to_first_level() -> None:
    outcome = interpret_priority(_SPEC, _answer(1.5, {0: 0.1, 1: 0.4, 2: 0.4, 3: 0.1}))
    assert outcome.most_likely == "media"


@pytest.mark.parametrize("probabilities", [{0: 0.5, 1: 0.3, 7: 0.2}, {}])
def test_positions_outside_the_legend_are_abstention(probabilities: dict[int, float]) -> None:
    outcome = interpret_priority(_SPEC, _answer(1.0, probabilities))
    assert outcome.most_likely is None
    assert outcome.reaches_threshold is None


def test_missing_answer_is_abstention() -> None:
    outcome = interpret_priority(_SPEC, None)
    assert outcome.most_likely is None
    assert outcome.distribution == ()
    assert outcome.expected_score is None
    assert outcome.reaches_threshold is None


@given(st.floats(min_value=0, max_value=3), st.floats(min_value=0, max_value=3))
def test_reaching_the_threshold_is_monotonic_in_score(a: float, b: float) -> None:
    low, high = sorted((a, b))
    probabilities = {0: 0.25, 1: 0.25, 2: 0.25, 3: 0.25}
    first = interpret_priority(_SPEC, _answer(low, probabilities)).reaches_threshold
    second = interpret_priority(_SPEC, _answer(high, probabilities)).reaches_threshold
    assert not (first and not second)
