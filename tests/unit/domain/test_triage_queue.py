"""Interpretación de la cola: escape, opción ajena y respuesta ausente son abstención (FR-005)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from jevlab.domain.triage import ChoiceAnswer, interpret_queue
from tests.builders import triage_spec

_SPEC = triage_spec().queue
_OPTIONS = list(_SPEC.options)


def _answer(choice: str, probabilities: dict[str, float]) -> ChoiceAnswer:
    return ChoiceAnswer(choice=choice, confidence=0.5, probabilities=probabilities)


def test_assigned_queue_with_sorted_distribution() -> None:
    probabilities = {"facturacion": 0.88, "tecnico": 0.04, "cuenta": 0.06, "other": 0.02}
    outcome = interpret_queue(_SPEC, _answer("facturacion", probabilities))

    assert outcome.assigned == "facturacion"
    assert outcome.abstention_reason is None
    assert outcome.distribution == (
        ("facturacion", 0.88),
        ("cuenta", 0.06),
        ("tecnico", 0.04),
        ("other", 0.02),
    )
    assert outcome.confidence == 0.5
    assert outcome.recomputed_confidence == pytest.approx(0.84)


def test_ties_keep_definition_order() -> None:
    probabilities = {"other": 0.25, "cuenta": 0.25, "tecnico": 0.25, "facturacion": 0.25}
    outcome = interpret_queue(_SPEC, _answer("facturacion", probabilities))
    assert [name for name, _ in outcome.distribution] == _OPTIONS


def test_escape_is_abstention() -> None:
    outcome = interpret_queue(_SPEC, _answer("other", {"other": 0.9, "facturacion": 0.1}))
    assert outcome.assigned is None
    assert outcome.abstention_reason == "el ticket no encaja en ninguna cola"
    assert outcome.distribution[0] == ("other", 0.9)


def test_option_outside_definition_is_abstention() -> None:
    outcome = interpret_queue(_SPEC, _answer("envios", {"envios": 0.6, "facturacion": 0.4}))
    assert outcome.assigned is None
    assert outcome.abstention_reason == "respuesta fuera de la definición"
    assert outcome.distribution == (("envios", 0.6), ("facturacion", 0.4))


def test_missing_answer_is_abstention_without_distribution() -> None:
    outcome = interpret_queue(_SPEC, None)
    assert outcome.assigned is None
    assert outcome.abstention_reason == "sin respuesta válida"
    assert outcome.distribution == ()
    assert outcome.confidence is None
    assert outcome.recomputed_confidence is None


def test_probabilities_are_shown_as_they_come() -> None:
    probabilities = {"facturacion": 0.5, "tecnico": 0.2, "cuenta": 0.1, "other": 0.1}
    outcome = interpret_queue(_SPEC, _answer("facturacion", probabilities))
    assert sum(p for _, p in outcome.distribution) == pytest.approx(0.9)


@given(
    st.sampled_from([*_OPTIONS, "envios"]),
    st.lists(st.floats(min_value=0, max_value=1), min_size=4, max_size=4),
)
def test_escape_never_assigns_a_queue(choice: str, values: list[float]) -> None:
    outcome = interpret_queue(_SPEC, _answer(choice, dict(zip(_OPTIONS, values, strict=True))))
    assert outcome.assigned != _SPEC.escape
    assert (outcome.assigned is None) == (choice not in _OPTIONS or choice == _SPEC.escape)
    assert (outcome.assigned is None) == (outcome.abstention_reason is not None)
