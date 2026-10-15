"""Casos de uso de la cola de revisión con fakes (spec 002, US3; FR-008)."""

import pytest

from jevlab.application.review import ListPending, ResolveReview
from jevlab.application.routing import ROUTE_REQUEST
from jevlab.domain.policy import ActionName
from jevlab.domain.review import Resolution, ReviewCommand, ReviewItemNotFound, UnknownQueue
from tests.builders import route_request
from tests.fakes import FrozenClock, StaticSpecLoader
from tests.routing_builders import routed
from tests.routing_fakes import InMemoryRoutingStore


def _store_with(*kwargs_list: dict[str, object]) -> InMemoryRoutingStore:
    store = InMemoryRoutingStore()
    for number, kwargs in enumerate(kwargs_list, start=1):
        result, entries, item = routed(request_id=f"req-{number:04d}", **kwargs)  # type: ignore[arg-type]
        store.record(result, entries, item)
    return store


def _resolver(store: InMemoryRoutingStore) -> tuple[ResolveReview, StaticSpecLoader]:
    specs = StaticSpecLoader(route_request())
    return ResolveReview(store=store, specs=specs, clock=FrozenClock()), specs


def test_list_pending_in_order() -> None:
    store = _store_with(
        {"queue": "cuenta", "queue_confidence": 0.5, "kind": "consulta"},
        {"queue": "cuenta", "queue_confidence": 1.0, "kind": "consulta"},
        {"queue": "tecnico", "queue_confidence": 0.5, "kind": "consulta"},
    )

    assert [item.request_id for item in ListPending(store).run()] == ["req-0001", "req-0003"]


def test_resolve_applies_transition_with_route_queues_and_saves_everything() -> None:
    store = _store_with(
        {
            "queue": "facturacion",
            "queue_confidence": 0.5,
            "kind": "reembolso",
            "kind_confidence": 0.99,
        }
    )
    resolver, specs = _resolver(store)
    before = len(store.audit)

    item, entries = resolver.run(1, ReviewCommand.ASIGNAR, queue="tecnico")

    assert specs.requested == [ROUTE_REQUEST]
    assert store.items[1] == item
    assert store.audit[before:] == list(entries)
    refund = item.action(ActionName.REEMBOLSAR)
    assert refund is not None and refund.resolution is Resolution.RECHAZADA
    assert all(e.at == FrozenClock().now() for e in entries)
    assert ListPending(store).run() == []


def test_escape_is_not_an_assignable_queue() -> None:
    store = _store_with({"queue": "cuenta", "queue_confidence": 0.5, "kind": "consulta"})
    resolver, _ = _resolver(store)
    with pytest.raises(UnknownQueue) as error:
        resolver.run(1, ReviewCommand.ASIGNAR, queue="other")
    assert error.value.queues == ("cuenta", "facturacion", "tecnico")


def test_missing_item_fails_without_changes() -> None:
    store = _store_with({"queue": "cuenta", "queue_confidence": 0.5, "kind": "consulta"})
    resolver, _ = _resolver(store)
    before = list(store.audit)

    with pytest.raises(ReviewItemNotFound) as error:
        resolver.run(9, ReviewCommand.DESCARTAR)

    assert str(error.value) == "no existe el elemento 9"
    assert store.audit == before
