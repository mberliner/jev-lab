"""Salida de `jevlab triage` en texto plano (contracts/cli-triage.md, docs/standards/cli-ux.md)."""

from jevlab.domain.triage import (
    Origin,
    OriginMode,
    PriorityOutcome,
    QueueOutcome,
    TriageResult,
    UrgencyOutcome,
    UrgencyVerdict,
)

_SEP = " · "
_ABSTENTION_QUEUE = "sin cola asignada, requiere revisión manual"


def number(value: float) -> str:
    """Coma decimal y dos decimales (cli-ux.md §2)."""
    return f"{value:.2f}".replace(".", ",")


def render(result: TriageResult) -> list[str]:
    return [
        render_origin(result.origin),
        "",
        *render_queue(result.queue),
        "",
        *render_urgency(result.urgency),
        "",
        *render_priority(result.priority),
    ]


def render_origin(origin: Origin) -> str:
    if origin.mode is OriginMode.EN_VIVO:
        return f"Origen: en vivo{_SEP}{origin.model}"
    example = f"ejemplo {origin.example}"
    if origin.synthetic:
        example += " (ticket sintético)"
    parts = ["Origen: grabado", example, origin.model]
    if origin.recorded_on is not None:
        parts.append(origin.recorded_on.isoformat())
    return _SEP.join(parts)


def render_queue(queue: QueueOutcome) -> list[str]:
    if queue.assigned is not None:
        head = f"Cola: {queue.assigned}"
    else:
        head = f"Cola: {_ABSTENTION_QUEUE} ({queue.abstention_reason})"
    if queue.confidence is not None:
        head += f"{_SEP}confianza {number(queue.confidence)}"
    width = max((len(name) for name, _ in queue.distribution), default=0) + 2
    rows = [f"  {name.ljust(width)}{number(p)}" for name, p in queue.distribution]
    return [head, *rows]


def render_urgency(urgency: UrgencyOutcome) -> list[str]:
    if urgency.verdict is UrgencyVerdict.ABSTENCION or urgency.probability is None:
        return [f"Urgencia explícita: {UrgencyVerdict.ABSTENCION} (sin respuesta válida)"]
    band = urgency.band
    return [
        f"Urgencia explícita: {urgency.verdict}{_SEP}probabilidad {number(urgency.probability)}",
        f"  incierto entre {number(band.low)} y {number(band.high)} ({band.justification})",
    ]


def render_priority(priority: PriorityOutcome) -> list[str]:
    """El valor esperado solo aparece al compararlo con el umbral (FR-008)."""
    if priority.most_likely is None or priority.expected_score is None:
        return ["Prioridad: abstención (sin respuesta válida)"]
    head = f"Prioridad: más probable {priority.most_likely}"
    if priority.confidence is not None:
        head += f"{_SEP}confianza {number(priority.confidence)}"
    width = max(len(name) for _, name, _ in priority.distribution) + 3
    rows = [f"  {i} {name.ljust(width)}{number(p)}" for i, name, p in priority.distribution]
    verdict, sign = ("alcanzado", ">=") if priority.reaches_threshold else ("no alcanzado", "<")
    threshold = (
        f"  umbral {priority.threshold_level} ({priority.threshold_justification}): {verdict}"
        f"{_SEP}valor esperado {number(priority.expected_score)} {sign} "
        f"{priority.threshold_position}"
    )
    return [head, *rows, threshold]
