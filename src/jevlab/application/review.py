"""Casos de uso de la cola de revisión: listar y resolver (spec 002, US3; FR-008)."""

from dataclasses import dataclass

from jevlab.application.routing import ROUTE_REQUEST
from jevlab.domain.decision_spec import ChoiceSpec, RouteSpec
from jevlab.domain.policy import Policy
from jevlab.domain.review import ReviewCommand, ReviewItem, ReviewItemNotFound, resolve
from jevlab.domain.routing import AuditEntry
from jevlab.ports.clock import Clock
from jevlab.ports.policy import PolicyLoader
from jevlab.ports.routing_store import RoutingStore
from jevlab.ports.specs import SpecLoader


class RouteQueues:
    """Las colas a las que el Operador puede asignar, de la definición `cola-destino`."""

    def __init__(self, specs: SpecLoader) -> None:
        self._specs = specs

    def run(self) -> tuple[str, ...]:
        return RouteSpec.from_request(self._specs.load_request(ROUTE_REQUEST)).valid_queues()


@dataclass(frozen=True)
class Guide:
    """Lo que explica `jevlab review guia`: las colas de `cola-destino` y la política vigente."""

    queue: ChoiceSpec
    policy: Policy


class ReviewGuide:
    """Lee la guía de las mismas fuentes que usan `route` y `review`, sin el archivo de estado."""

    def __init__(self, specs: SpecLoader, policies: PolicyLoader) -> None:
        self._specs = specs
        self._policies = policies

    def run(self) -> Guide:
        spec = RouteSpec.from_request(self._specs.load_request(ROUTE_REQUEST))
        return Guide(queue=spec.queue, policy=self._policies.load(None))


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
        queues = RouteQueues(self._specs).run()
        resolved, entries = resolve(item, command, queues, self._clock.now(), queue=queue)
        self._store.save_resolution(resolved, entries)
        return resolved, entries
