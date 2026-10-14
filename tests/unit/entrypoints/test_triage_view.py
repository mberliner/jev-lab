"""Vista de `jevlab triage` (contracts/cli-triage.md, «Salida»)."""

from datetime import date

import pytest

from jevlab.domain.triage import (
    ChoiceAnswer,
    NoulAnswer,
    Origin,
    OriginMode,
    ScoreAnswer,
    interpret_priority,
    interpret_queue,
    interpret_urgency,
)
from jevlab.entrypoints.cli.triage_view import (
    number,
    render_origin,
    render_priority,
    render_queue,
    render_urgency,
)
from tests.builders import triage_spec

_SPEC = triage_spec()


def test_recorded_origin_line() -> None:
    origin = Origin(
        mode=OriginMode.GRABADO,
        model="jev-1.13.0",
        recorded_on=date(2026, 10, 20),
        example="cobro-duplicado",
        synthetic=True,
    )
    assert render_origin(origin) == (
        "Origen: grabado · ejemplo cobro-duplicado (ticket sintético) · jev-1.13.0 · 2026-10-20"
    )


def test_live_origin_line() -> None:
    origin = Origin(mode=OriginMode.EN_VIVO, model="jev-1.13.0")
    assert render_origin(origin) == "Origen: en vivo · jev-1.13.0"


def test_assigned_queue_block() -> None:
    answer = ChoiceAnswer(
        choice="facturacion",
        confidence=0.84,
        probabilities={"facturacion": 0.88, "tecnico": 0.06, "cuenta": 0.04, "other": 0.02},
    )
    assert render_queue(interpret_queue(_SPEC.queue, answer)) == [
        "Cola: facturacion · confianza 0,84",
        "  facturacion  0,88",
        "  tecnico      0,06",
        "  cuenta       0,04",
        "  other        0,02",
    ]


def test_escape_block_says_no_queue_and_keeps_distribution() -> None:
    answer = ChoiceAnswer(
        choice="other",
        confidence=0.6,
        probabilities={"facturacion": 0.1, "tecnico": 0.1, "cuenta": 0.1, "other": 0.7},
    )
    lines = render_queue(interpret_queue(_SPEC.queue, answer))
    assert lines[0] == (
        "Cola: sin cola asignada, requiere revisión manual "
        "(el ticket no encaja en ninguna cola) · confianza 0,60"
    )
    assert lines[1] == "  other        0,70"
    assert len(lines) == 5


def test_missing_answer_block() -> None:
    assert render_queue(interpret_queue(_SPEC.queue, None)) == [
        "Cola: sin cola asignada, requiere revisión manual (sin respuesta válida)"
    ]


@pytest.mark.parametrize(("probability", "word"), [(0.12, "no"), (0.5, "incierto"), (0.93, "sí")])
def test_urgency_block(probability: float, word: str) -> None:
    outcome = interpret_urgency(_SPEC.urgency, NoulAnswer(probability=probability))
    assert render_urgency(outcome) == [
        f"Urgencia explícita: {word} · probabilidad {number(probability)}",
        "  incierto entre 0,30 y 0,70 (provisional)",
    ]


def test_urgency_abstention_and_never_medio() -> None:
    assert render_urgency(interpret_urgency(_SPEC.urgency, None)) == [
        "Urgencia explícita: abstención (sin respuesta válida)"
    ]
    for p in (0.3, 0.5, 0.7):
        text = "\n".join(
            render_urgency(interpret_urgency(_SPEC.urgency, NoulAnswer(probability=p)))
        )
        assert "medio" not in text


def test_priority_block_below_threshold() -> None:
    answer = ScoreAnswer(
        score=1.1, confidence=0.41, probabilities={0: 0.2, 1: 0.55, 2: 0.2, 3: 0.05}
    )
    assert render_priority(interpret_priority(_SPEC.priority, answer)) == [
        "Prioridad: más probable media · confianza 0,41",
        "  0 baja      0,20",
        "  1 media     0,55",
        "  2 alta      0,20",
        "  3 critica   0,05",
        "  umbral alta (provisional): no alcanzado · valor esperado 1,10 < 2",
    ]


def test_priority_block_reaching_threshold_shows_score_only_there() -> None:
    answer = ScoreAnswer(
        score=2.4, confidence=0.6, probabilities={0: 0.05, 1: 0.1, 2: 0.25, 3: 0.6}
    )
    lines = render_priority(interpret_priority(_SPEC.priority, answer))
    assert lines[-1] == "  umbral alta (provisional): alcanzado · valor esperado 2,40 >= 2"
    assert sum("2,40" in line for line in lines) == 1
    assert not any("%" in line for line in lines)


def test_priority_abstention() -> None:
    assert render_priority(interpret_priority(_SPEC.priority, None)) == [
        "Prioridad: abstención (sin respuesta válida)"
    ]
