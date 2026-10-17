"""Salida de `jevlab review` en texto plano (contracts/cli-review.md, docs/standards/cli-ux.md).

Es el único sitio donde la CLI muestra el texto de un ticket que no acaba de escribir la persona,
recortado y entre comillas.
"""

from collections.abc import Sequence

from jevlab.domain.decision_spec import BILLING_QUEUE
from jevlab.domain.policy import ActionName
from jevlab.domain.review import Resolution, ReviewItem
from jevlab.domain.routing import AuditEntry
from jevlab.entrypoints.cli.route_view import TITLES, render_sources

_SEP = " · "
_TEXT_WIDTH = 72
_ID_WIDTH = 8
_ABOUT = (
    "Peticiones con alguna acción que el código no automatizó; el motivo está en cada «regla».",
    "Las resuelve una persona con los comandos de «qué hacer».",
)


def short_id(request_id: str) -> str:
    return request_id if len(request_id) <= _ID_WIDTH else request_id[:_ID_WIDTH] + "…"


def render_pending(items: Sequence[ReviewItem], queues: Sequence[str]) -> list[str]:
    """`queues` son las colas válidas de `cola-destino`, para el comando `asignar`."""
    lines = [f"Pendientes: {len(items)}"]
    if items:
        lines += _ABOUT
    for item in items:
        lines += ["", *render_item(item, queues)]
    return lines


def render_item(item: ReviewItem, queues: Sequence[str]) -> list[str]:
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
        how = "asignada por una persona" if assigned is not None else "automatizada"
        lines.append(f"  Cola: {item.queue}{_SEP}{how}")
    for action in item.actions:
        if action.resolution is None:
            lines.append(f"  Acción: {TITLES[action.action]}{_SEP}estado: {action.status.value}")
            lines += ["    " + line for line in render_sources(action)]
    lines.append("  qué hacer:")
    lines += ["    " + command for command in todo(item, queues)]
    return lines


def todo(item: ReviewItem, queues: Sequence[str]) -> list[str]:
    """Los comandos que resuelven lo pendiente del elemento (transiciones de `resolve`)."""
    n = item.id
    move = item.pending_action(ActionName.MOVER_A_COLA) is not None
    refund = item.pending_action(ActionName.REEMBOLSAR) is not None
    if move and refund:
        others = " o ".join(q for q in queues if q != BILLING_QUEUE)
        return [
            f"jevlab review asignar {n} {BILLING_QUEUE}  # después, confirmar {n} o rechazar {n}",
            f"jevlab review asignar {n} <cola>  # {others}; rechaza el reembolso",
            f"jevlab review descartar {n}  # rechaza también el reembolso",
            f"jevlab review rechazar {n}  # solo el reembolso",
        ]
    if move:
        return [
            f"jevlab review asignar {n} <cola>  # colas: {', '.join(queues)}",
            f"jevlab review descartar {n}",
        ]
    if item.queue == BILLING_QUEUE:
        return [f"jevlab review confirmar {n}", f"jevlab review rechazar {n}"]
    return [f"jevlab review rechazar {n}  # sin la cola {BILLING_QUEUE} no se puede confirmar"]


def render_resolution(
    item: ReviewItem, entries: Sequence[AuditEntry], queues: Sequence[str]
) -> list[str]:
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
        lines += [f"Elemento {item.id}: sigue pendiente el reembolso", "qué hacer:"]
        lines += ["  " + command for command in todo(item, queues)]
    else:
        lines.append(f"Elemento {item.id} resuelto: sin acciones pendientes")
    return lines
