"""Urgencia explícita: sí, no o incierto según la banda, con los límites incluidos (FR-007)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from jevlab.domain.triage import NoulAnswer, UrgencyVerdict, interpret_urgency
from tests.builders import triage_spec

_SPEC = triage_spec().urgency
_PROBABILITY = st.floats(min_value=0, max_value=1)
_RANK = {UrgencyVerdict.NO: 0, UrgencyVerdict.INCIERTO: 1, UrgencyVerdict.SI: 2}


@pytest.mark.parametrize(
    ("probability", "verdict"),
    [
        (0.0, UrgencyVerdict.NO),
        (0.29, UrgencyVerdict.NO),
        (0.30, UrgencyVerdict.INCIERTO),
        (0.5, UrgencyVerdict.INCIERTO),
        (0.70, UrgencyVerdict.INCIERTO),
        (0.71, UrgencyVerdict.SI),
        (1.0, UrgencyVerdict.SI),
    ],
)
def test_band_with_inclusive_limits(probability: float, verdict: UrgencyVerdict) -> None:
    outcome = interpret_urgency(_SPEC, NoulAnswer(probability=probability))
    assert outcome.verdict is verdict
    assert outcome.probability == probability
    assert outcome.band == _SPEC.uncertain_band


def test_missing_answer_is_abstention() -> None:
    outcome = interpret_urgency(_SPEC, None)
    assert outcome.verdict is UrgencyVerdict.ABSTENCION
    assert outcome.probability is None


@given(_PROBABILITY, _PROBABILITY)
def test_verdict_is_monotonic_in_probability(a: float, b: float) -> None:
    low, high = sorted((a, b))
    first = interpret_urgency(_SPEC, NoulAnswer(probability=low)).verdict
    second = interpret_urgency(_SPEC, NoulAnswer(probability=high)).verdict
    assert _RANK[first] <= _RANK[second]
