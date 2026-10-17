"""Enrutado: qué acciones se automatizan con la política y qué queda en la auditoría (spec 002).

data-model.md, «Resultado del enrutado» y «Auditoría»; research.md R4. Decide el código: la
comparación con el umbral, el escape, la composición del reembolso con la cola y el riesgo.
"""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from jevlab.domain.decision_spec import BILLING_QUEUE, REFUND
from jevlab.domain.policy import ActionName, ActionPolicy, Policy, PolicyRef, Risk
from jevlab.domain.triage import (
    ESCAPE_REASON,
    MISSING_REASON,
    OUTSIDE_REASON,
    Origin,
    OriginMode,
    QueueOutcome,
)


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class ActionStatus(StrEnum):
    AUTOMATIZADA = "automatizada"
    A_REVISION = "a revisión"
    PENDIENTE = "pendiente de confirmación"
    SIN_REEMBOLSO = "sin reembolso"


class PendingReason(StrEnum):
    """Texto de la salida; si hay varios motivos se guardan todos, en este orden."""

    ESCAPE = ESCAPE_REASON
    SOLICITUD_ESCAPE = "la solicitud no encaja en ninguna opción"
    FUERA = OUTSIDE_REASON
    SIN_RESPUESTA = MISSING_REASON
    BAJO_UMBRAL = "confianza por debajo del umbral"
    COLA_NO_FACTURACION = "la cola no se automatizó a facturacion"
    NO_REEMBOLSO = "la solicitud no es reembolso"


_ABSTENTION = {
    ESCAPE_REASON: PendingReason.ESCAPE,
    OUTSIDE_REASON: PendingReason.FUERA,
    MISSING_REASON: PendingReason.SIN_RESPUESTA,
}


class ActionOutcome(_Frozen):
    action: ActionName
    value: str | None
    confidence: float | None
    threshold: float
    risk: Risk
    justification: str
    status: ActionStatus
    reasons: tuple[PendingReason, ...]

    @property
    def provisional(self) -> bool:
        return self.justification.strip() == "provisional"


def _outcome(
    name: ActionName,
    rule: ActionPolicy,
    value: str | None,
    confidence: float | None,
    status: ActionStatus,
    reasons: tuple[PendingReason, ...] = (),
) -> ActionOutcome:
    return ActionOutcome(
        action=name,
        value=value,
        confidence=confidence,
        threshold=rule.umbral,
        risk=rule.riesgo,
        justification=rule.justificacion,
        status=status,
        reasons=reasons,
    )


def _reaches(confidence: float | None, threshold: float) -> bool:
    """Mayor o igual, como en la 001; sin confianza no se alcanza nunca."""
    return confidence is not None and confidence >= threshold


def _decide_move(policy: Policy, queue: QueueOutcome) -> ActionOutcome:
    name = ActionName.MOVER_A_COLA
    rule = policy.action(name)
    if queue.assigned is None:
        reason = _ABSTENTION[queue.abstention_reason or MISSING_REASON]
        # El escape es una respuesta del modelo: se guarda, como en la solicitud; nunca se asigna.
        value = queue.choice if queue.abstention_reason == ESCAPE_REASON else None
        return _outcome(name, rule, value, queue.confidence, ActionStatus.A_REVISION, (reason,))
    if not _reaches(queue.confidence, rule.umbral):
        return _outcome(
            name,
            rule,
            queue.assigned,
            queue.confidence,
            ActionStatus.A_REVISION,
            (PendingReason.BAJO_UMBRAL,),
        )
    return _outcome(name, rule, queue.assigned, queue.confidence, ActionStatus.AUTOMATIZADA)


def _decide_refund(policy: Policy, move: ActionOutcome, kind: QueueOutcome) -> ActionOutcome:
    name = ActionName.REEMBOLSAR
    rule = policy.action(name)
    if kind.assigned != REFUND:
        if kind.abstention_reason == ESCAPE_REASON:
            reason = PendingReason.SOLICITUD_ESCAPE
        elif kind.abstention_reason is not None:
            reason = _ABSTENTION[kind.abstention_reason]
        else:
            reason = PendingReason.NO_REEMBOLSO
        value = kind.choice if kind.abstention_reason in (None, ESCAPE_REASON) else None
        return _outcome(name, rule, value, kind.confidence, ActionStatus.SIN_REEMBOLSO, (reason,))
    reasons: list[PendingReason] = []
    if not _reaches(kind.confidence, rule.umbral):
        reasons.append(PendingReason.BAJO_UMBRAL)
    if move.status is not ActionStatus.AUTOMATIZADA or move.value != BILLING_QUEUE:
        reasons.append(PendingReason.COLA_NO_FACTURACION)
    status = ActionStatus.PENDIENTE if reasons else ActionStatus.AUTOMATIZADA
    return _outcome(name, rule, REFUND, kind.confidence, status, tuple(reasons))


def decide_routing(
    policy: Policy, queue: QueueOutcome, request_kind: QueueOutcome
) -> tuple[ActionOutcome, ActionOutcome]:
    """Función pura: recibe las respuestas ya interpretadas, nunca el texto del ticket."""
    move = _decide_move(policy, queue)
    return move, _decide_refund(policy, move, request_kind)


class RoutingResult(_Frozen):
    request_id: str
    decided_at: datetime
    origin: Origin
    policy: PolicyRef
    spec_versions: dict[str, str]
    actions: tuple[ActionOutcome, ...]

    @property
    def needs_review(self) -> bool:
        """`sin reembolso` es una abstención explícita, no una acción pendiente."""
        return any(
            a.status in (ActionStatus.A_REVISION, ActionStatus.PENDIENTE) for a in self.actions
        )

    def action(self, name: ActionName) -> ActionOutcome | None:
        return next((a for a in self.actions if a.action is name), None)


class AuditEntry(_Frozen):
    """Solo metadatos: nunca el texto del ticket ni la respuesta del servicio (FR-011)."""

    request_id: str
    at: datetime
    kind: Literal["decision", "resolucion"]
    action: ActionName
    value: str | None
    confidence: float | None
    threshold: float | None
    risk: Risk
    outcome: str
    reasons: tuple[PendingReason, ...]
    policy: PolicyRef
    origin_mode: OriginMode
    model: str
    spec_versions: dict[str, str]
    review_item: int | None = None


def decision_entries(result: RoutingResult) -> tuple[AuditEntry, ...]:
    """Una entrada por acción decidida; el almacén rellena `review_item` al guardar."""
    return tuple(
        AuditEntry(
            request_id=result.request_id,
            at=result.decided_at,
            kind="decision",
            action=action.action,
            value=action.value,
            confidence=action.confidence,
            threshold=action.threshold,
            risk=action.risk,
            outcome=action.status.value,
            reasons=action.reasons,
            policy=result.policy,
            origin_mode=result.origin.mode,
            model=result.origin.model,
            spec_versions=result.spec_versions,
        )
        for action in result.actions
    )
