"""Salida de `jevlab review` en texto plano (contracts/cli-review.md, docs/standards/cli-ux.md).

Es el único sitio donde la CLI muestra el texto de un ticket que no acaba de escribir la persona:
entero, entre comillas, porque el Operador lo necesita para decidir (prueba de SC-004).
"""

import textwrap
from collections.abc import Sequence

from jevlab.application.review import Guide
from jevlab.domain.decision_spec import BILLING_QUEUE
from jevlab.domain.policy import ActionName
from jevlab.domain.review import Resolution, ReviewItem
from jevlab.domain.routing import AuditEntry, PendingReason
from jevlab.entrypoints.cli.route_view import TITLES, render_sources
from jevlab.entrypoints.cli.triage_view import number

_SEP = " · "
_TEXT_WIDTH = 88
_ID_WIDTH = 8
_ABOUT = (
    "Peticiones con alguna acción que el código no automatizó; el motivo está en cada «regla».",
    "Las resuelve una persona con los comandos de «qué hacer».",
    "Qué significa cada cola y cada comando: jevlab review guia",
)
_CONDITIONS = {ActionName.REEMBOLSAR: f"solo con la cola {BILLING_QUEUE}"}
_COMMANDS = (
    ("jevlab review", "lista los pendientes y qué hacer en cada uno"),
    ("jevlab review asignar N <cola>", "el ticket pasa a esa cola de soporte (simulado)"),
    ("jevlab review descartar N", "cierra el elemento sin cola"),
    ("jevlab review confirmar N", "confirma el reembolso (simulado)"),
    ("jevlab review rechazar N", "rechaza solo el reembolso"),
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


def render_guide(guide: Guide) -> list[str]:
    """Qué es la cola, qué significa cada cola y cada acción, y qué hace cada comando.

    Las colas salen de la definición `cola-destino` y los umbrales de la política del paquete,
    las mismas que usa `jevlab route`: la guía no repite nada a mano.
    """
    queue, policy = guide.queue, guide.policy
    names = sorted(name for name in queue.options if name != queue.escape)
    width = max(len(name) for name in queue.options)
    lines = [
        "Cola de revisión: peticiones con alguna acción que el código no automatizó.",
        "La IA propone un valor con su confianza; el código lo compara con el umbral de la política.",
        "Si no lo alcanza, la acción espera aquí a que una persona la resuelva. Todo es simulado.",
        "",
        f"Colas: qué tickets atiende cada una (definición {queue.name} {queue.version}):",
    ]
    lines += [f"  {name:<{width}}  {queue.options[name]}" for name in names]
    escape = f"{queue.options[queue.escape]} Es el escape: no se asigna."
    lines += [f"  {queue.escape:<{width}}  {escape}", ""]
    lines.append(f"Acciones (política {policy.version}{_SEP}huella {policy.fingerprint}):")
    width = max(len(title) for title in TITLES.values())
    for name, title in TITLES.items():
        rule = policy.action(name)
        parts = [f"riesgo {rule.riesgo.value}", f"umbral {number(rule.umbral)}"]
        if rule.provisional:
            parts[-1] += " (provisional)"
        if name in _CONDITIONS:
            parts.append(_CONDITIONS[name])
        lines.append(f"  {title:<{width}}  {_SEP.join(parts)}")
    lines += ["Cada elemento muestra la política con la que se decidió.", ""]
    lines += [*_refund_by_queue(names, number(policy.action(ActionName.REEMBOLSAR).umbral)), ""]
    lines.append("Comandos (N es el número del elemento):")
    width = max(len(command) for command, _ in _COMMANDS)
    lines += [f"  {command:<{width}}  {what}" for command, what in _COMMANDS]
    return lines


def _refund_by_queue(queues: Sequence[str], threshold: str) -> list[str]:
    """La regla del reembolso según la cola (FR-006), con las colas de la definición."""
    rows = [
        (
            BILLING_QUEUE,
            f"se puede confirmar o rechazar (en route, se automatiza desde {threshold})",
        ),
        (
            ", ".join(q for q in queues if q != BILLING_QUEUE),
            "no se puede confirmar: asignar una de ellas lo rechaza",
        ),
        ("descartar", "sin cola: un reembolso pendiente queda rechazado"),
    ]
    width = max(len(label) for label, _ in rows)
    return [
        "La cola decide el reembolso:",
        *(f"  {label:<{width}}  {what}" for label, what in rows),
        "Un elemento sale de la lista cuando no le quedan acciones pendientes.",
        "Toda resolución queda en la auditoría.",
    ]


def render_item(item: ReviewItem, queues: Sequence[str]) -> list[str]:
    head = _SEP.join(
        [
            f"[{item.id}] {item.created_at:%Y-%m-%d %H:%M}",
            item.origin.mode.value,
            f"política {item.policy.label()}",
            f"petición {short_id(item.request_id)}",
        ]
    )
    lines = [head, *_quote(item.ticket)]
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


def _quote(text: str) -> list[str]:
    """El texto entero entre comillas, partido en líneas con sangría."""
    wrapped = textwrap.wrap(text, _TEXT_WIDTH) or [""]
    wrapped[0] = "«" + wrapped[0]
    wrapped[-1] += "»"  # puede ser la misma línea que la primera
    return ["  " + wrapped[0], *("   " + line for line in wrapped[1:])]


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
        pending = item.pending_action(ActionName.MOVER_A_COLA)
        if pending is not None and PendingReason.ESCAPE in pending.reasons:
            return [
                f"jevlab review asignar {n} <cola>  # si el ticket sí es de una cola: "
                + ", ".join(queues),
                f"jevlab review descartar {n}  # si no es de soporte, como propone el modelo",
            ]
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
