"""Definiciones y respuestas de triaje construidas en los tests, sin leer archivos."""

from datetime import date
from typing import Any

from pydantic import TypeAdapter

from jevlab.domain.decision_spec import (
    DecisionSpec,
    RequestSpec,
    ResolvedRequest,
    RouteSpec,
    TriageSpec,
)
from jevlab.domain.examples import RecordedResponse, Recording
from jevlab.domain.triage import Answers, ChoiceAnswer, NoulAnswer, ScoreAnswer

MODEL = "jev-1.13.0"

QUEUE: dict[str, Any] = {
    "name": "cola-destino",
    "version": "0.1.0",
    "model": MODEL,
    "primitive": "choice",
    "instructions": "¿A qué cola de soporte pertenece este ticket?",
    "options": {
        "facturacion": "Cobros.",
        "tecnico": "Fallos.",
        "cuenta": "Acceso.",
        "other": "Ninguna de las anteriores.",
    },
    "escape": "other",
}

URGENCY: dict[str, Any] = {
    "name": "urgencia-explicita",
    "version": "0.1.0",
    "model": MODEL,
    "primitive": "noul",
    "instructions": "¿El ticket menciona explícitamente un problema urgente?",
    "criteria_true": "Lo dice.",
    "criteria_false": "No lo dice.",
    "uncertain_band": {"low": 0.3, "high": 0.7, "justification": "provisional"},
}

PRIORITY: dict[str, Any] = {
    "name": "prioridad",
    "version": "0.1.0",
    "model": MODEL,
    "primitive": "score",
    "instructions": "¿Qué prioridad de atención necesita este ticket?",
    "levels": [
        {"name": "baja", "description": "Puede esperar."},
        {"name": "media", "description": "Esta semana."},
        {"name": "alta", "description": "Hoy."},
        {"name": "critica", "description": "Ya."},
    ],
    "threshold": {"level": "alta", "justification": "provisional"},
}

REQUEST: dict[str, Any] = {
    "name": "triaje",
    "version": "0.1.0",
    "max_chars": 4000,
    "questions": {
        "cola": "cola-destino",
        "urgencia": "urgencia-explicita",
        "prioridad": "prioridad",
    },
}

REQUEST_KIND: dict[str, Any] = {
    "name": "solicitud",
    "version": "0.1.0",
    "model": MODEL,
    "primitive": "choice",
    "instructions": "¿Qué pide el cliente en este ticket?",
    "options": {
        "reembolso": "Dinero.",
        "consulta": "Ayuda.",
        "incidencia": "Fallo.",
        "other": "Ninguna de las anteriores.",
    },
    "escape": "other",
}

ROUTE_REQUEST: dict[str, Any] = {
    "name": "enrutado",
    "version": "0.1.0",
    "max_chars": 4000,
    "questions": {"cola": "cola-destino", "solicitud": "solicitud"},
}

POLICY: dict[str, Any] = {
    "version": "0.1.0",
    "acciones": {
        "mover-a-cola": {"riesgo": "bajo", "umbral": 0.90, "justificacion": "provisional"},
        "reembolsar": {"riesgo": "alto", "umbral": 0.97, "justificacion": "provisional"},
    },
}

_DECISION: TypeAdapter[DecisionSpec] = TypeAdapter(DecisionSpec)


def _resolve(request: dict[str, Any], decisions: tuple[dict[str, Any], ...]) -> ResolvedRequest:
    parsed = [_DECISION.validate_python(d) for d in decisions]
    return ResolvedRequest.resolve(RequestSpec.model_validate(request), {d.name: d for d in parsed})


def triage_request(max_chars: int = 4000) -> ResolvedRequest:
    return _resolve(REQUEST | {"max_chars": max_chars}, (QUEUE, URGENCY, PRIORITY))


def triage_spec(max_chars: int = 4000) -> TriageSpec:
    return TriageSpec.from_request(triage_request(max_chars))


def route_request(max_chars: int = 4000) -> ResolvedRequest:
    return _resolve(ROUTE_REQUEST | {"max_chars": max_chars}, (QUEUE, REQUEST_KIND))


def route_spec() -> RouteSpec:
    return RouteSpec.from_request(route_request())


def choice_answer(choice: str, confidence: float, options: dict[str, str]) -> ChoiceAnswer:
    """Distribución coherente: la opción elegida concentra lo que no tienen las demás."""
    others = [k for k in options if k != choice]
    rest = round((1 - confidence) / max(len(others), 1), 4) if others else 0.0
    probabilities = {choice: round(1 - rest * len(others), 4)} | {k: rest for k in others}
    return ChoiceAnswer(choice=choice, confidence=confidence, probabilities=probabilities)


def answers(
    queue: str = "facturacion",
    urgency: float | None = 0.12,
    score: float = 1.1,
    model: str = MODEL,
) -> Answers:
    others = [k for k in QUEUE["options"] if k != queue]
    probabilities = {queue: 0.88} | dict(zip(others, (0.06, 0.04, 0.02), strict=False))
    return Answers(
        model=model,
        by_question={
            "cola": ChoiceAnswer(choice=queue, confidence=0.84, probabilities=probabilities),
            "urgencia": None if urgency is None else NoulAnswer(probability=urgency),
            "prioridad": ScoreAnswer(
                score=score, confidence=0.5, probabilities={0: 0.2, 1: 0.55, 2: 0.2, 3: 0.05}
            ),
        },
    )


def route_answers(
    queue: str | None = "facturacion",
    queue_confidence: float = 1.0,
    kind: str | None = "reembolso",
    kind_confidence: float = 0.98,
    model: str = MODEL,
) -> Answers:
    """Respuestas de enrutado; `None` en una pregunta es que falta su respuesta."""
    return Answers(
        model=model,
        by_question={
            "cola": (
                None if queue is None else choice_answer(queue, queue_confidence, QUEUE["options"])
            ),
            "solicitud": (
                None
                if kind is None
                else choice_answer(kind, kind_confidence, REQUEST_KIND["options"])
            ),
        },
    )


def recording(
    name: str = "cobro-duplicado",
    text: str = "Me habéis cobrado dos veces.",
    covers: tuple[str, ...] = (),
) -> Recording:
    return Recording(
        name=name,
        text=text,
        synthetic=True,
        covers=covers,
        model=MODEL,
        recorded_on=date(2026, 10, 20),
        spec_versions={"triaje": "0.1.0"},
        request={"state": text},
        response=RecordedResponse(status=200, body={}),
    )
