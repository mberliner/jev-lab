"""Fakes en memoria de los puertos del enrutado (spec 002).

Viven aparte de `tests/fakes.py` para que los tests de la 000 y la 001 no dependan de ellos.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from jevlab.domain.diagnostics import InvalidPolicy
from jevlab.domain.policy import Policy
from jevlab.domain.review import ReviewItem
from jevlab.domain.routing import AuditEntry, RoutingResult


@dataclass
class InMemoryRoutingStore:
    """Mismo contrato que `SqliteRoutingStore` (data-model.md, «Persistencia»)."""

    audit: list[AuditEntry] = field(default_factory=list)
    items: dict[int, ReviewItem] = field(default_factory=dict)
    results: list[RoutingResult] = field(default_factory=list)
    next_id: int = 1

    def record(
        self, result: RoutingResult, entries: Sequence[AuditEntry], item: ReviewItem | None
    ) -> ReviewItem | None:
        saved = None
        if item is not None:
            saved = item.model_copy(update={"id": self.next_id})
            self.items[self.next_id] = saved
            self.next_id += 1
        self.results.append(result)
        self.audit.extend(
            e if saved is None else e.model_copy(update={"review_item": saved.id}) for e in entries
        )
        return saved

    def pending(self) -> list[ReviewItem]:
        return [item for _, item in sorted(self.items.items()) if item.pending]

    def get(self, item_id: int) -> ReviewItem | None:
        return self.items.get(item_id)

    def save_resolution(self, item: ReviewItem, entries: Sequence[AuditEntry]) -> None:
        assert item.id is not None
        self.items[item.id] = item
        self.audit.extend(entries)


@dataclass
class SequentialIds:
    count: int = 0

    def new_request_id(self) -> str:
        self.count += 1
        return f"req-{self.count:04d}"


@dataclass
class StaticPolicyLoader:
    """Devuelve la política dada o lanza el error dado; registra las rutas pedidas."""

    policy: Policy | None = None
    error: InvalidPolicy | None = None
    requested: list[Path | None] = field(default_factory=list)

    def load(self, path: Path | None) -> Policy:
        self.requested.append(path)
        if self.error is not None:
            raise self.error
        assert self.policy is not None
        return self.policy
