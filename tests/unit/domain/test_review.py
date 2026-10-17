"""Cola de revisión: creación y transiciones (data-model.md, «Cola de revisión», «Transiciones»)."""

from datetime import UTC, datetime

import pytest

from jevlab.domain.policy import ActionName
from jevlab.domain.review import (
    AlreadyResolved,
    RefundNeedsBillingQueue,
    Resolution,
    ReviewCommand,
    ReviewItem,
    UnknownQueue,
    resolve,
)
from jevlab.domain.routing import ActionStatus, PendingReason
from tests.routing_builders import routing_result

_QUEUES = ("cuenta", "facturacion", "tecnico")
_NOW = datetime(2026, 10, 20, 11, 0, tzinfo=UTC)
_TICKET = "Creo que se me cobró algo que no reconozco."


def _item(item_id: int = 4, **kwargs: object) -> ReviewItem:
    created = ReviewItem.from_result(routing_result(**kwargs), _TICKET)  # type: ignore[arg-type]
    assert created is not None
    return created.model_copy(update={"id": item_id})


def _status(item: ReviewItem, name: ActionName) -> Resolution | None:
    found = item.action(name)
    assert found is not None
    return found.resolution


def test_no_item_when_nothing_needs_review() -> None:
    assert ReviewItem.from_result(routing_result(), _TICKET) is None
    assert ReviewItem.from_result(routing_result("cuenta", 1.0, "consulta", 0.9), _TICKET) is None


def test_item_holds_only_pending_actions_and_the_automated_queue() -> None:
    result = routing_result("facturacion", 1.0, "reembolso", 0.81)
    item = ReviewItem.from_result(result, _TICKET)

    assert item is not None
    assert item.id is None
    assert [a.action for a in item.actions] == [ActionName.REEMBOLSAR]
    assert item.actions[0].status is ActionStatus.PENDIENTE
    assert item.queue == "facturacion"
    assert (item.request_id, item.ticket, item.policy) == (
        result.request_id,
        _TICKET,
        result.policy,
    )
    assert item.spec_versions == result.spec_versions
    assert item.pending


def test_abstention_never_enters_the_item() -> None:
    item = ReviewItem.from_result(routing_result("cuenta", 0.5, "consulta", 0.9), _TICKET)
    assert item is not None
    assert [a.action for a in item.actions] == [ActionName.MOVER_A_COLA]
    assert item.queue is None


def test_assign_resolves_the_queue() -> None:
    item = _item(queue="cuenta", queue_confidence=0.87, kind="consulta")

    resolved, entries = resolve(item, ReviewCommand.ASIGNAR, _QUEUES, _NOW, queue="cuenta")

    assert resolved.queue == "cuenta"
    assert _status(resolved, ActionName.MOVER_A_COLA) is Resolution.ASIGNADA
    assert not resolved.pending
    [entry] = entries
    assert (entry.kind, entry.action, entry.value, entry.outcome) == (
        "resolucion",
        ActionName.MOVER_A_COLA,
        "cuenta",
        "asignada",
    )
    assert (entry.request_id, entry.review_item, entry.at) == (item.request_id, 4, _NOW)
    assert entry.spec_versions == item.spec_versions
    assert entry.policy == item.policy
    assert entry.confidence is None and entry.threshold is None


def test_assign_other_queue_rejects_pending_refund_with_its_own_entry() -> None:
    item = _item(queue="facturacion", queue_confidence=0.5, kind="reembolso", kind_confidence=0.99)

    resolved, entries = resolve(item, ReviewCommand.ASIGNAR, _QUEUES, _NOW, queue="tecnico")

    assert _status(resolved, ActionName.REEMBOLSAR) is Resolution.RECHAZADA
    assert not resolved.pending
    assert [(e.action, e.outcome) for e in entries] == [
        (ActionName.MOVER_A_COLA, "asignada"),
        (ActionName.REEMBOLSAR, "rechazada"),
    ]
    assert entries[1].reasons == (PendingReason.COLA_NO_FACTURACION,)


def test_assign_billing_keeps_the_refund_pending() -> None:
    item = _item(queue="facturacion", queue_confidence=0.5, kind="reembolso", kind_confidence=0.99)

    resolved, entries = resolve(item, ReviewCommand.ASIGNAR, _QUEUES, _NOW, queue="facturacion")

    assert _status(resolved, ActionName.REEMBOLSAR) is None
    assert resolved.pending
    assert len(entries) == 1


def test_discard_closes_every_pending_action() -> None:
    item = _item(queue="cuenta", queue_confidence=0.5, kind="reembolso", kind_confidence=0.99)

    resolved, entries = resolve(item, ReviewCommand.DESCARTAR, _QUEUES, _NOW)

    assert _status(resolved, ActionName.MOVER_A_COLA) is Resolution.DESCARTADA
    assert _status(resolved, ActionName.REEMBOLSAR) is Resolution.RECHAZADA
    assert [e.outcome for e in entries] == ["descartada", "rechazada"]
    assert not resolved.pending


def test_confirm_needs_billing_queue() -> None:
    item = _item(queue="facturacion", queue_confidence=0.5, kind="reembolso", kind_confidence=0.99)

    with pytest.raises(RefundNeedsBillingQueue) as error:
        resolve(item, ReviewCommand.CONFIRMAR, _QUEUES, _NOW)
    assert str(error.value) == (
        "para confirmar el reembolso, primero asigna la cola facturacion "
        "(jevlab review asignar 4 facturacion)"
    )


def test_confirm_and_reject_resolve_the_refund() -> None:
    item = _item(queue="facturacion", queue_confidence=1.0, kind="reembolso", kind_confidence=0.81)

    confirmed, [entry] = resolve(item, ReviewCommand.CONFIRMAR, _QUEUES, _NOW)
    assert _status(confirmed, ActionName.REEMBOLSAR) is Resolution.CONFIRMADA
    assert (entry.action, entry.value, entry.outcome) == (
        ActionName.REEMBOLSAR,
        "reembolso",
        "confirmada",
    )
    assert not confirmed.pending

    rejected, _ = resolve(item, ReviewCommand.RECHAZAR, _QUEUES, _NOW)
    assert _status(rejected, ActionName.REEMBOLSAR) is Resolution.RECHAZADA


def test_already_resolved_or_absent_action_fails() -> None:
    item = _item(queue="facturacion", queue_confidence=1.0, kind="reembolso", kind_confidence=0.81)
    with pytest.raises(AlreadyResolved, match="no tiene la cola pendiente"):
        resolve(item, ReviewCommand.ASIGNAR, _QUEUES, _NOW, queue="cuenta")

    done, _ = resolve(item, ReviewCommand.RECHAZAR, _QUEUES, _NOW)
    with pytest.raises(AlreadyResolved) as error:
        resolve(done, ReviewCommand.CONFIRMAR, _QUEUES, _NOW)
    assert str(error.value) == "el elemento 4 no tiene un reembolso pendiente"
    with pytest.raises(AlreadyResolved, match="no tiene acciones pendientes"):
        resolve(done, ReviewCommand.DESCARTAR, _QUEUES, _NOW)


@pytest.mark.parametrize("queue", ["envios", "other", None])
def test_unknown_queue_or_escape_lists_valid_queues(queue: str | None) -> None:
    item = _item(queue="cuenta", queue_confidence=0.5, kind="consulta")
    with pytest.raises(UnknownQueue) as error:
        resolve(item, ReviewCommand.ASIGNAR, _QUEUES, _NOW, queue=queue)
    assert str(error.value) == "cola desconocida; colas: cuenta, facturacion, tecnico"
