"""Regla del reembolso (research.md R4; FR-006, FR-013; Constitución §II).

El reembolso se automatiza solo con la solicitud `reembolso` por encima de su umbral y la cola
automatizada a `facturacion`; si la solicitud no es `reembolso`, la abstención es explícita.
"""

from hypothesis import given
from hypothesis import strategies as st

from jevlab.domain.policy import ActionName
from jevlab.domain.routing import ActionOutcome, ActionStatus, PendingReason, decide_routing
from jevlab.domain.triage import ChoiceAnswer, interpret_queue
from tests.builders import QUEUE, REQUEST_KIND, choice_answer, route_spec
from tests.routing_builders import policy, routing_result

_SPEC = route_spec()


def _refund(
    queue: str | None = "facturacion",
    queue_confidence: float = 1.0,
    kind: str | None = "reembolso",
    kind_confidence: float = 0.98,
    move: float = 0.90,
    refund: float = 0.97,
) -> ActionOutcome:
    result = routing_result(
        queue, queue_confidence, kind, kind_confidence, rules=policy(move=move, refund=refund)
    )
    found = result.action(ActionName.REEMBOLSAR)
    assert found is not None
    return found


def test_refund_with_enough_confidence_and_billing_queue_is_automated() -> None:
    refund = _refund()

    assert refund.status is ActionStatus.AUTOMATIZADA
    assert refund.value == "reembolso"
    assert (refund.confidence, refund.threshold, refund.risk.value) == (0.98, 0.97, "alto")
    assert refund.reasons == ()


def test_refund_below_threshold_awaits_confirmation() -> None:
    refund = _refund(kind_confidence=0.93)

    assert refund.status is ActionStatus.PENDIENTE
    assert refund.reasons == (PendingReason.BAJO_UMBRAL,)


def test_refund_without_billing_queue_automated_awaits_confirmation() -> None:
    for queue, confidence in (
        ("facturacion", 0.5),
        ("other", 1.0),
        ("tecnico", 1.0),
        ("cuenta", 1.0),
    ):
        refund = _refund(queue=queue, queue_confidence=confidence)
        assert refund.status is ActionStatus.PENDIENTE, queue
        assert refund.reasons == (PendingReason.COLA_NO_FACTURACION,), queue


def test_both_causes_give_both_reasons_in_order() -> None:
    refund = _refund(queue="cuenta", kind_confidence=0.5)
    assert refund.reasons == (PendingReason.BAJO_UMBRAL, PendingReason.COLA_NO_FACTURACION)


def test_other_requests_are_an_explicit_abstention() -> None:
    for kind in ("consulta", "incidencia"):
        refund = _refund(kind=kind, kind_confidence=0.92)
        assert refund.status is ActionStatus.SIN_REEMBOLSO
        assert (refund.value, refund.confidence) == (kind, 0.92)
        assert refund.reasons == (PendingReason.NO_REEMBOLSO,)

    escape = _refund(kind="other", kind_confidence=0.65)
    assert escape.status is ActionStatus.SIN_REEMBOLSO
    assert escape.reasons == (PendingReason.SOLICITUD_ESCAPE,)

    missing = _refund(kind=None)
    assert missing.status is ActionStatus.SIN_REEMBOLSO
    assert missing.confidence is None
    assert missing.reasons == (PendingReason.SIN_RESPUESTA,)


def test_outside_definition_is_an_abstention() -> None:
    queue = interpret_queue(_SPEC.queue, choice_answer("facturacion", 1.0, QUEUE["options"]))
    kind = interpret_queue(
        _SPEC.request_kind,
        ChoiceAnswer(choice="devolucion", confidence=0.99, probabilities={"devolucion": 0.99}),
    )
    [_, refund] = decide_routing(policy(), queue, kind)
    assert refund.status is ActionStatus.SIN_REEMBOLSO
    assert refund.reasons == (PendingReason.FUERA,)


def test_abstention_does_not_need_review() -> None:
    assert not routing_result("cuenta", 1.0, "consulta", 0.9).needs_review
    assert routing_result("cuenta", 1.0, "reembolso", 0.5).needs_review
    assert routing_result("cuenta", 0.5, "consulta", 0.9).needs_review


_CONFIDENCES = st.floats(min_value=0, max_value=1, allow_nan=False)
_QUEUES = st.sampled_from(list(QUEUE["options"]))
_KINDS = st.sampled_from(list(REQUEST_KIND["options"]))


@given(_QUEUES, _CONFIDENCES, _KINDS, _CONFIDENCES, _CONFIDENCES, _CONFIDENCES)
def test_no_refund_without_billing_queue_or_below_threshold(
    queue: str, queue_confidence: float, kind: str, kind_confidence: float, a: float, b: float
) -> None:
    move, refund_threshold = sorted((a, b))
    result = routing_result(
        queue,
        queue_confidence,
        kind,
        kind_confidence,
        rules=policy(move=move, refund=refund_threshold),
    )
    moved = result.action(ActionName.MOVER_A_COLA)
    refund = result.action(ActionName.REEMBOLSAR)
    assert moved is not None and refund is not None
    if refund.status is ActionStatus.AUTOMATIZADA:
        assert moved.status is ActionStatus.AUTOMATIZADA and moved.value == "facturacion"
        assert kind == "reembolso" and kind_confidence >= refund_threshold
    if kind == "other":
        assert refund.status is ActionStatus.SIN_REEMBOLSO


@given(_CONFIDENCES, _CONFIDENCES, _CONFIDENCES)
def test_refund_band_is_monotonic(low: float, high: float, threshold: float) -> None:
    low, high = sorted((low, high))
    if _refund(kind_confidence=low, refund=threshold, move=0).status is ActionStatus.AUTOMATIZADA:
        assert _refund(kind_confidence=high, refund=threshold, move=0).status is (
            ActionStatus.AUTOMATIZADA
        )
