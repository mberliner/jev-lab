"""Puerto del estado local: auditoría y cola de revisión (data-model.md, «Persistencia»).

Los adaptadores traducen un archivo ilegible o de otra versión a `StateUnreadable`.
"""

from collections.abc import Sequence
from typing import Protocol

from jevlab.domain.review import ReviewItem
from jevlab.domain.routing import AuditEntry, RoutingResult


class RoutingStore(Protocol):
    def record(
        self, result: RoutingResult, entries: Sequence[AuditEntry], item: ReviewItem | None
    ) -> ReviewItem | None:
        """En una transacción: el elemento (si lo hay), con el `id` que se le asigna, y las
        entradas de auditoría de la petición con ese `review_item`. Devuelve el elemento guardado.
        """
        ...

    def pending(self) -> list[ReviewItem]:
        """Elementos con alguna acción sin resolver, del más antiguo al más reciente."""
        ...

    def get(self, item_id: int) -> ReviewItem | None: ...

    def save_resolution(self, item: ReviewItem, entries: Sequence[AuditEntry]) -> None:
        """El elemento actualizado y todas las entradas de la resolución, en una transacción."""
        ...
