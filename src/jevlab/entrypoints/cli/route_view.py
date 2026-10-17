"""Salida de `jevlab route` en texto plano (contracts/cli-route.md, docs/standards/cli-ux.md).

Cada dato lleva la etiqueta de su origen (cli-ux.md §6): `IA` (valor y confianza), `política`
(umbral y riesgo) y `regla` (la comparación del código y el motivo del estado).
"""

from jevlab.application.routing import Routed
from jevlab.domain.policy import ActionName, PolicyRef
from jevlab.domain.routing import ActionOutcome, ActionStatus, PendingReason
from jevlab.entrypoints.cli.triage_view import number, render_origin

_SEP = " · "
TITLES = {ActionName.MOVER_A_COLA: "mover a cola", ActionName.REEMBOLSAR: "reembolsar"}
_QUESTIONS = {
    ActionName.MOVER_A_COLA: "IA propone la cola",
    ActionName.REEMBOLSAR: "IA clasifica la solicitud",
}


def render(routed: Routed) -> list[str]:
    result = routed.result
    lines = [
        render_origin(result.origin),
        render_policy(result.policy),
        f"Petición: {result.request_id}",
    ]
    for action in result.actions:
        lines += ["", *render_action(action)]
    if routed.item is not None:
        lines += [
            "",
            f"En la cola de revisión: elemento {routed.item.id}",
            "qué hacer: jevlab review",
        ]
    return lines


def render_policy(policy: PolicyRef) -> str:
    return f"Política: {policy.version}{_SEP}huella {policy.fingerprint}"


def render_action(action: ActionOutcome) -> list[str]:
    status = action.status.value
    if action.status is ActionStatus.AUTOMATIZADA and action.action is ActionName.REEMBOLSAR:
        status += " (simulado)"
    head = f"Acción: {TITLES[action.action]}{_SEP}estado: {status}"
    return [head, *("  " + line for line in render_sources(action))]


def render_sources(action: ActionOutcome) -> list[str]:
    """Las líneas `IA`, `política` y `regla` de una acción, sin sangría."""
    lines = [f"{_QUESTIONS[action.action]}: {_proposal(action)}{_SEP}{_confidence(action)}"]
    if action.status is ActionStatus.SIN_REEMBOLSO:
        # La abstención no aplica umbral (FR-004): no hay línea de política.
        return [*lines, f"regla: sin umbral{_SEP}motivo: {_reasons(action)}"]
    rule = f"umbral {number(action.threshold)} (riesgo {action.risk.value}"
    rule += ", provisional)" if action.provisional else ")"
    lines.append(f"política: {rule}")
    if action.value is None or action.confidence is None:
        check = "sin valor válido"
    else:
        sign = "≥" if action.confidence >= action.threshold else "<"
        check = f"{number(action.confidence)} {sign} {number(action.threshold)}"
    if action.reasons:
        check += f"{_SEP}motivo: {_reasons(action)}"
    elif action.status is ActionStatus.AUTOMATIZADA and action.action is ActionName.REEMBOLSAR:
        check += f"{_SEP}cola facturacion automatizada"
    return [*lines, f"regla: {check}"]


def _proposal(action: ActionOutcome) -> str:
    if action.value is None:
        return "ninguna"
    if PendingReason.SOLICITUD_ESCAPE in action.reasons:
        return f"{action.value} (escape)"
    return action.value


def _confidence(action: ActionOutcome) -> str:
    if action.confidence is None:
        return "confianza no disponible"
    return f"confianza {number(action.confidence)}"


def _reasons(action: ActionOutcome) -> str:
    return "; ".join(r.value for r in action.reasons)
