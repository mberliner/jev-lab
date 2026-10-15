"""Casos de uso de la cola de revisión: listar y resolver (spec 002, US3; FR-008)."""

from jevlab.application.routing import ROUTE_REQUEST
from jevlab.domain.decision_spec import RouteSpec
from jevlab.domain.review import ReviewCommand, ReviewItem, ReviewItemNotFound, resolve
from jevlab.domain.routing import AuditEntry
from jevlab.ports.clock import Clock
from jevlab.ports.routing_store import RoutingStore
from jevlab.ports.specs import SpecLoader


class ListPending:
    def __init__(self, store: RoutingStore) -> None:
        self._store = store

    def run(self) -> list[ReviewItem]:
        return self._store.pending()


class ResolveReview:
    def __init__(self, store: RoutingStore, specs: SpecLoader, clock: Clock) -> None:
        self._store = store
        self._specs = specs
        self._clock = clock

    def run(
        self, item_id: int, command: ReviewCommand, queue: str | None = None
    ) -> tuple[ReviewItem, tuple[AuditEntry, ...]]:
        """Las colas válidas salen de la definición `cola-destino`, la misma que usa el modelo."""
        item = self._store.get(item_id)
        if item is None:
            raise ReviewItemNotFound(item_id)
        queues = RouteSpec.from_request(self._specs.load_request(ROUTE_REQUEST)).valid_queues()
        resolved, entries = resolve(item, command, queues, self._clock.now(), queue=queue)
        self._store.save_resolution(resolved, entries)
        return resolved, entries
