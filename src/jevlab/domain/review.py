"""Cola de revisión: lo que no se automatizó y su resolución por el Operador (spec 002).

data-model.md, «Cola de revisión» y «Transiciones». Las reglas son de dominio puro; el almacén
solo traduce filas a estas entidades. Ningún error incluye el texto del ticket.
"""

from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict

from jevlab.domain.decision_spec import BILLING_QUEUE
from jevlab.domain.policy import ActionName, PolicyRef
from jevlab.domain.routing import (
    ActionOutcome,
    ActionStatus,
    AuditEntry,
    PendingReason,
    RoutingResult,
)
from jevlab.domain.triage import Origin


class Resolution(StrEnum):
    ASIGNADA = "asignada"
    DESCARTADA = "descartada"
    CONFIRMADA = "confirmada"
    RECHAZADA = "rechazada"


class ReviewCommand(StrEnum):
    ASIGNAR = "asignar"
    DESCARTAR = "descartar"
    CONFIRMAR = "confirmar"
    RECHAZAR = "rechazar"


class ReviewAction(ActionOutcome):
    resolution: Resolution | None = None


class ReviewItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int | None
    request_id: str
    created_at: datetime
    ticket: str
    origin: Origin
    policy: PolicyRef
    spec_versions: dict[str, str]
    actions: tuple[ReviewAction, ...]
    queue: str | None

    @classmethod
    def from_result(cls, result: RoutingResult, ticket: str) -> Self | None:
        """Un elemento por petición, solo si alguna acción quedó a revisión o pendiente (FR-007)."""
        if not result.needs_review:
            return None
        move = result.action(ActionName.MOVER_A_COLA)
        automated = move is not None and move.status is ActionStatus.AUTOMATIZADA
        return cls(
            id=None,
            request_id=result.request_id,
            created_at=result.decided_at,
            ticket=ticket,
            origin=result.origin,
            policy=result.policy,
            spec_versions=result.spec_versions,
            actions=tuple(
                ReviewAction(**a.model_dump())
                for a in result.actions
                if a.status in (ActionStatus.A_REVISION, ActionStatus.PENDIENTE)
            ),
            queue=move.value if automated and move is not None else None,
        )

    @property
    def pending(self) -> bool:
        return any(a.resolution is None for a in self.actions)

    def action(self, name: ActionName) -> ReviewAction | None:
        return next((a for a in self.actions if a.action is name), None)

    def pending_action(self, name: ActionName) -> ReviewAction | None:
        found = self.action(name)
        return found if found is not None and found.resolution is None else None


class ReviewItemNotFound(Exception):
    def __init__(self, item_id: int) -> None:
        super().__init__(f"no existe el elemento {item_id}")
        self.item_id = item_id


class AlreadyResolved(Exception):
    def __init__(self, item_id: int | None, what: str) -> None:
        super().__init__(f"el elemento {item_id} no tiene {what}")


class UnknownQueue(Exception):
    def __init__(self, queues: Sequence[str]) -> None:
        super().__init__(f"cola desconocida; colas: {', '.join(queues)}")
        self.queues = tuple(queues)


class RefundNeedsBillingQueue(Exception):
    def __init__(self, item_id: int | None) -> None:
        super().__init__(
            f"para confirmar el reembolso, primero asigna la cola {BILLING_QUEUE} "
            f"(jevlab review asignar {item_id} {BILLING_QUEUE})"
        )


def _entry(
    item: ReviewItem,
    action: ReviewAction,
    resolution: Resolution,
    value: str | None,
    now: datetime,
    reasons: tuple[PendingReason, ...] = (),
) -> AuditEntry:
    return AuditEntry(
        request_id=item.request_id,
        at=now,
        kind="resolucion",
        action=action.action,
        value=value,
        confidence=None,
        threshold=None,
        risk=action.risk,
        outcome=resolution.value,
        reasons=reasons,
        policy=item.policy,
        origin_mode=item.origin.mode,
        model=item.origin.model,
        spec_versions=item.spec_versions,
        review_item=item.id,
    )


def resolve(
    item: ReviewItem,
    command: ReviewCommand,
    queues: Sequence[str],
    now: datetime,
    queue: str | None = None,
) -> tuple[ReviewItem, tuple[AuditEntry, ...]]:
    """Aplica una orden del Operador; devuelve el elemento y una entrada por acción resuelta.

    `queues` son las colas válidas de `cola-destino`, sin el escape.
    """
    move = item.pending_action(ActionName.MOVER_A_COLA)
    refund = item.pending_action(ActionName.REEMBOLSAR)
    changes: dict[ActionName, Resolution] = {}
    entries: list[AuditEntry] = []
    new_queue = item.queue

    if command is ReviewCommand.ASIGNAR:
        if move is None:
            raise AlreadyResolved(item.id, "la cola pendiente")
        if queue is None or queue not in queues:
            raise UnknownQueue(queues)
        new_queue = queue
        changes[move.action] = Resolution.ASIGNADA
        entries.append(_entry(item, move, Resolution.ASIGNADA, queue, now))
        if refund is not None and queue != BILLING_QUEUE:
            changes[refund.action] = Resolution.RECHAZADA
            entries.append(
                _entry(
                    item,
                    refund,
                    Resolution.RECHAZADA,
                    refund.value,
                    now,
                    (PendingReason.COLA_NO_FACTURACION,),
                )
            )
    elif command is ReviewCommand.DESCARTAR:
        if not item.pending:
            raise AlreadyResolved(item.id, "acciones pendientes")
        if move is not None:
            changes[move.action] = Resolution.DESCARTADA
            entries.append(_entry(item, move, Resolution.DESCARTADA, None, now))
        if refund is not None:
            changes[refund.action] = Resolution.RECHAZADA
            entries.append(_entry(item, refund, Resolution.RECHAZADA, refund.value, now))
    else:
        if refund is None:
            raise AlreadyResolved(item.id, "un reembolso pendiente")
        if command is ReviewCommand.CONFIRMAR and item.queue != BILLING_QUEUE:
            raise RefundNeedsBillingQueue(item.id)
        resolution = (
            Resolution.CONFIRMADA if command is ReviewCommand.CONFIRMAR else Resolution.RECHAZADA
        )
        changes[refund.action] = resolution
        entries.append(_entry(item, refund, resolution, refund.value, now))

    actions = tuple(
        a.model_copy(update={"resolution": changes[a.action]}) if a.action in changes else a
        for a in item.actions
    )
    return item.model_copy(update={"actions": actions, "queue": new_queue}), tuple(entries)
