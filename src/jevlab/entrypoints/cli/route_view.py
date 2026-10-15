"""Salida de `jevlab route` en texto plano (contracts/cli-route.md, docs/standards/cli-ux.md)."""

from jevlab.application.routing import Routed
from jevlab.domain.policy import ActionName, PolicyRef
from jevlab.domain.routing import ActionOutcome, ActionStatus, PendingReason
from jevlab.entrypoints.cli.triage_view import number, render_origin

_SEP = " · "
_TITLES = {ActionName.MOVER_A_COLA: "Mover a cola", ActionName.REEMBOLSAR: "Reembolsar"}


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
        lines += ["", f"En la cola de revisión: elemento {routed.item.id} (jevlab review)"]
    return lines


def render_policy(policy: PolicyRef) -> str:
    return f"Política: {policy.version}{_SEP}huella {policy.fingerprint}"


def render_action(action: ActionOutcome) -> list[str]:
    title = _TITLES[action.action]
    if action.status is ActionStatus.SIN_REEMBOLSO:
        return render_abstention(title, action)
    value = action.value or "sin cola"
    status = action.status.value
    if action.status is ActionStatus.AUTOMATIZADA and action.action is ActionName.REEMBOLSAR:
        status += " (simulado)"
    lines = [f"{title}: {value}{_SEP}{status}", "  " + _comparison(action)]
    if action.status is ActionStatus.AUTOMATIZADA and action.action is ActionName.REEMBOLSAR:
        lines[-1] += f"{_SEP}cola facturacion automatizada"
    if action.reasons:
        lines.append(f"  motivo: {'; '.join(r.value for r in action.reasons)}")
    return lines


def render_abstention(title: str, action: ActionOutcome) -> list[str]:
    """Sin reembolso: el valor y la confianza de la solicitud y el motivo, sin umbral (FR-004)."""
    if action.value is None:
        reason = action.reasons[0] if action.reasons else PendingReason.SIN_RESPUESTA
        kind = f"solicitud {reason.value}"
    elif PendingReason.SOLICITUD_ESCAPE in action.reasons:
        kind = f"solicitud {action.value} (escape)"
    else:
        kind = f"solicitud {action.value}"
    confidence = (
        "confianza no disponible"
        if action.confidence is None
        else f"confianza {number(action.confidence)}"
    )
    lines = [f"{title}: {action.status.value}{_SEP}{kind}{_SEP}{confidence}"]
    if action.value is not None:
        lines.append(f"  motivo: {'; '.join(r.value for r in action.reasons)}")
    return lines


def _comparison(action: ActionOutcome) -> str:
    rule = f"umbral {number(action.threshold)} (riesgo {action.risk.value}"
    rule += ", provisional)" if action.provisional else ")"
    if action.confidence is None:
        return f"confianza no disponible{_SEP}{rule}"
    sign = "≥" if action.confidence >= action.threshold else "<"
    return f"confianza {number(action.confidence)} {sign} {rule}"
