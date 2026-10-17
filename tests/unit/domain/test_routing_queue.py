"""Regla de «mover a cola» (research.md R4; FR-003, FR-013; data-model.md, «Resultado»)."""

from hypothesis import given
from hypothesis import strategies as st

from jevlab.domain.policy import ActionName
from jevlab.domain.routing import ActionStatus, PendingReason, decide_routing
from jevlab.domain.triage import ChoiceAnswer, QueueOutcome, interpret_queue
from tests.builders import QUEUE, REQUEST_KIND, choice_answer, route_spec
from tests.routing_builders import policy

_SPEC = route_spec()
_CONSULTA = interpret_queue(
    _SPEC.request_kind, choice_answer("consulta", 0.9, REQUEST_KIND["options"])
)


def _queue(choice: str | None, confidence: float = 1.0) -> QueueOutcome:
    answer = None if choice is None else choice_answer(choice, confidence, QUEUE["options"])
    return interpret_queue(_SPEC.queue, answer)


def _move(queue: QueueOutcome, threshold: float = 0.90):  # type: ignore[no-untyped-def]
    actions = decide_routing(policy(move=threshold, refund=1.0), queue, _CONSULTA)
    [move] = [a for a in actions if a.action is ActionName.MOVER_A_COLA]
    return move


def test_confidence_equal_to_threshold_is_automated() -> None:
    move = _move(_queue("cuenta", 0.90))

    assert move.status is ActionStatus.AUTOMATIZADA
    assert move.value == "cuenta"
    assert move.reasons == ()
    assert (move.threshold, move.risk.value, move.justification) == (0.90, "bajo", "provisional")


def test_below_threshold_goes_to_review_with_reason() -> None:
    move = _move(_queue("cuenta", 0.87))

    assert move.status is ActionStatus.A_REVISION
    assert move.value == "cuenta"
    assert move.confidence == 0.87
    assert move.reasons == (PendingReason.BAJO_UMBRAL,)


def test_escape_is_never_automated_even_with_full_confidence() -> None:
    move = _move(_queue("other", 1.0), threshold=0.0)

    assert move.status is ActionStatus.A_REVISION
    assert move.value == "other"  # lo que respondió el modelo; nunca se asigna como cola
    assert move.reasons == (PendingReason.ESCAPE,)


def test_option_outside_definition_and_missing_answer_go_to_review() -> None:
    outside = interpret_queue(
        _SPEC.queue,
        ChoiceAnswer(choice="envios", confidence=1.0, probabilities={"envios": 1.0}),
    )
    assert _move(outside).reasons == (PendingReason.FUERA,)
    assert _move(outside).value is None

    missing = _move(_queue(None))
    assert missing.status is ActionStatus.A_REVISION
    assert missing.reasons == (PendingReason.SIN_RESPUESTA,)
    assert missing.confidence is None
    assert missing.value is None


def test_service_confidence_is_compared_not_the_recomputed_one() -> None:
    answer = ChoiceAnswer(
        choice="cuenta",
        confidence=0.95,
        probabilities={"cuenta": 0.5, "tecnico": 0.5, "facturacion": 0.0, "other": 0.0},
    )
    outcome = interpret_queue(_SPEC.queue, answer)
    assert outcome.recomputed_confidence is not None and outcome.recomputed_confidence < 0.9

    assert _move(outcome).status is ActionStatus.AUTOMATIZADA


_CONFIDENCES = st.floats(min_value=0, max_value=1, allow_nan=False)
_VALID = st.sampled_from(["facturacion", "tecnico", "cuenta"])


@given(_VALID, _CONFIDENCES, _CONFIDENCES)
def test_nothing_below_threshold_is_automated(
    queue: str, confidence: float, threshold: float
) -> None:
    move = _move(_queue(queue, confidence), threshold)
    if confidence < threshold:
        assert move.status is not ActionStatus.AUTOMATIZADA
    else:
        assert move.status is ActionStatus.AUTOMATIZADA


@given(_CONFIDENCES, _CONFIDENCES)
def test_escape_always_ends_in_review(confidence: float, threshold: float) -> None:
    assert _move(_queue("other", confidence), threshold).status is ActionStatus.A_REVISION


@given(_VALID, _CONFIDENCES, _CONFIDENCES, _CONFIDENCES)
def test_band_is_monotonic(queue: str, low: float, high: float, threshold: float) -> None:
    low, high = sorted((low, high))
    if _move(_queue(queue, low), threshold).status is ActionStatus.AUTOMATIZADA:
        assert _move(_queue(queue, high), threshold).status is ActionStatus.AUTOMATIZADA
