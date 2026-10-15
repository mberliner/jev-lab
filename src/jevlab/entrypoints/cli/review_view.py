"""Salida de `jevlab review` en texto plano (contracts/cli-review.md, docs/standards/cli-ux.md).

Es el único sitio donde la CLI muestra el texto de un ticket que no acaba de escribir la persona,
recortado y entre comillas.
"""

from collections.abc import Sequence

from jevlab.domain.policy import ActionName
from jevlab.domain.review import Resolution, ReviewAction, ReviewItem
from jevlab.domain.routing import AuditEntry
from jevlab.entrypoints.cli.triage_view import number

_SEP = " · "
_TEXT_WIDTH = 72
_ID_WIDTH = 8
_TITLES = {ActionName.MOVER_A_COLA: "Mover a cola", ActionName.REEMBOLSAR: "Reembolsar"}


def short_id(request_id: str) -> str:
    return request_id if len(request_id) <= _ID_WIDTH else request_id[:_ID_WIDTH] + "…"


def render_pending(items: Sequence[ReviewItem]) -> list[str]:
    lines = [f"Pendientes: {len(items)}"]
    for item in items:
        lines += ["", *render_item(item)]
    return lines


def render_item(item: ReviewItem) -> list[str]:
    head = _SEP.join(
        [
            f"[{item.id}] {item.created_at:%Y-%m-%d %H:%M}",
            item.origin.mode.value,
            f"política {item.policy.label()}",
            f"petición {short_id(item.request_id)}",
        ]
    )
    text = item.ticket
    if len(text) > _TEXT_WIDTH:
        text = text[:_TEXT_WIDTH] + "…"
    lines = [head, f"  «{text}»"]
    if item.queue is not None:
        assigned = item.action(ActionName.MOVER_A_COLA)
        how = "asignada" if assigned is not None else "automatizada"
        lines.append(f"  Cola: {item.queue} ({how})")
    for action in item.actions:
        if action.resolution is None:
            lines += _render_action(action)
    return lines


def _render_action(action: ReviewAction) -> list[str]:
    threshold = f"umbral {number(action.threshold)}"
    if action.confidence is None:
        comparison = f"confianza no disponible{_SEP}{threshold}"
    else:
        sign = "≥" if action.confidence >= action.threshold else "<"
        comparison = f"confianza {number(action.confidence)} {sign} {threshold}"
    value = action.value or "sin cola"
    lines = [f"  {_TITLES[action.action]}: {value}{_SEP}{action.status.value}{_SEP}{comparison}"]
    if action.reasons:
        lines.append(f"    motivo: {'; '.join(r.value for r in action.reasons)}")
    return lines


def render_resolution(item: ReviewItem, entries: Sequence[AuditEntry]) -> list[str]:
    parts: list[str] = []
    for entry in entries:
        outcome = Resolution(entry.outcome)
        if entry.action is ActionName.MOVER_A_COLA:
            if outcome is Resolution.ASIGNADA:
                parts.append(f"cola {entry.value} asignada")
            else:
                parts.append("descartado")
        elif outcome is Resolution.CONFIRMADA:
            parts.append(f"reembolso confirmado (simulado){_SEP}cola {item.queue}")
        elif entry.reasons:
            parts.append("reembolso rechazado (la cola no es facturacion)")
        else:
            parts.append("reembolso rechazado")
    lines = [f"Elemento {item.id}: {_SEP.join(parts)}"]
    if item.pending:
        lines.append(
            f"Elemento {item.id}: sigue pendiente el reembolso (jevlab review confirmar "
            f"{item.id} o jevlab review rechazar {item.id})"
        )
    else:
        lines.append(f"Elemento {item.id} resuelto: sin acciones pendientes")
    return lines
