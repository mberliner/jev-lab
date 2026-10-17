"""Salida de `jevlab route` (contracts/cli-route.md; FR-004, SC-002)."""

from datetime import date

from jevlab.application.routing import Routed
from jevlab.domain.policy import parse_policy
from jevlab.domain.review import ReviewItem
from jevlab.domain.triage import Origin, OriginMode
from jevlab.entrypoints.cli import route_view
from tests.builders import POLICY
from tests.routing_builders import policy, routing_result

_SEP = " · "


def _render(item_id: int | None = None, **kwargs: object) -> list[str]:
    result = routing_result(**kwargs)  # type: ignore[arg-type]
    item = None
    if item_id is not None:
        created = ReviewItem.from_result(result, "texto")
        assert created is not None
        item = created.model_copy(update={"id": item_id})
    return route_view.render(Routed(result=result, item=item))


def test_header_has_origin_policy_and_request_first() -> None:
    lines = _render()
    fingerprint = policy().fingerprint

    assert lines[0] == (
        "Origen: grabado · ejemplo cobro-duplicado (ticket sintético) · jev-1.13.0 · 2026-10-20"
    )
    assert lines[1] == f"Política: 0.1.0 · huella {fingerprint}"
    assert lines[2] == "Petición: req-0001"
    assert lines[3] == ""


def test_live_origin() -> None:
    result = routing_result().model_copy(
        update={"origin": Origin(mode=OriginMode.EN_VIVO, model="jev-1.13.0")}
    )
    assert route_view.render(Routed(result=result, item=None))[0] == "Origen: en vivo · jev-1.13.0"


def test_automated_queue_and_refund() -> None:
    lines = _render()

    i = lines.index("Acción: mover a cola · estado: automatizada")
    assert lines[i + 1 : i + 4] == [
        "  IA propone la cola: facturacion · confianza 1,00",
        "  política: umbral 0,90 (riesgo bajo, provisional)",
        "  regla: 1,00 ≥ 0,90",
    ]
    j = lines.index("Acción: reembolsar · estado: automatizada (simulado)")
    assert lines[j + 1 : j + 4] == [
        "  IA clasifica la solicitud: reembolso · confianza 0,98",
        "  política: umbral 0,97 (riesgo alto, provisional)",
        "  regla: 0,98 ≥ 0,97 · cola facturacion automatizada",
    ]
    assert not any(line.startswith("En la cola de revisión") for line in lines)
    assert not any("motivo" in line or "qué hacer" in line for line in lines)


def test_values_are_never_written_after_the_action_name() -> None:
    """La prueba de SC-004: `Mover a cola: cuenta` no decía que `cuenta` era la propuesta."""
    lines = _render(1, queue="cuenta", queue_confidence=0.87, kind="reembolso", kind_confidence=0.8)
    assert not any(line.startswith(("Mover a cola", "Reembolsar")) for line in lines)


def test_queue_below_threshold_goes_to_review_with_reason() -> None:
    lines = _render(1, queue="cuenta", queue_confidence=0.87, kind="consulta", kind_confidence=0.9)

    i = lines.index("Acción: mover a cola · estado: a revisión")
    assert lines[i + 1 : i + 4] == [
        "  IA propone la cola: cuenta · confianza 0,87",
        "  política: umbral 0,90 (riesgo bajo, provisional)",
        "  regla: 0,87 < 0,90 · motivo: confianza por debajo del umbral",
    ]
    assert lines[-3:] == ["", "En la cola de revisión: elemento 1", "qué hacer: jevlab review"]


def test_escape_has_no_queue() -> None:
    lines = _render(2, queue="other", queue_confidence=1.0, kind="consulta")

    i = lines.index("Acción: mover a cola · estado: a revisión")
    assert lines[i + 1] == "  IA propone la cola: ninguna · confianza 1,00"
    assert lines[i + 3] == "  regla: sin valor válido · motivo: el ticket no encaja en ninguna cola"


def test_missing_queue_answer_has_no_confidence() -> None:
    lines = _render(3, queue=None, kind="consulta")

    i = lines.index("Acción: mover a cola · estado: a revisión")
    assert lines[i + 1] == "  IA propone la cola: ninguna · confianza no disponible"
    assert lines[i + 3] == "  regla: sin valor válido · motivo: sin respuesta válida"


def test_pending_refund_shows_reasons() -> None:
    lines = _render(4, queue="cuenta", kind="reembolso", kind_confidence=0.81)

    i = lines.index("Acción: reembolsar · estado: pendiente de confirmación")
    assert lines[i + 1] == "  IA clasifica la solicitud: reembolso · confianza 0,81"
    assert lines[i + 3] == (
        "  regla: 0,81 < 0,97 · motivo: confianza por debajo del umbral; "
        "la cola no se automatizó a facturacion"
    )


def test_no_refund_is_an_explicit_abstention_without_threshold() -> None:
    lines = _render(queue="cuenta", kind="consulta", kind_confidence=0.92)
    i = lines.index("Acción: reembolsar · estado: sin reembolso")
    assert lines[i + 1 : i + 3] == [
        "  IA clasifica la solicitud: consulta · confianza 0,92",
        "  regla: sin umbral · motivo: la solicitud no es reembolso",
    ]
    assert "umbral 0,97" not in "\n".join(lines)

    escape = _render(queue="cuenta", kind="other", kind_confidence=0.65)
    assert "  IA clasifica la solicitud: other (escape) · confianza 0,65" in escape
    assert "  regla: sin umbral · motivo: la solicitud no encaja en ninguna opción" in escape

    missing = _render(queue="cuenta", kind=None)
    assert "  IA clasifica la solicitud: ninguna · confianza no disponible" in missing
    assert "  regla: sin umbral · motivo: sin respuesta válida" in missing


def test_not_provisional_threshold_does_not_say_so() -> None:
    acciones = dict(POLICY["acciones"])
    acciones["mover-a-cola"] = acciones["mover-a-cola"] | {"justificacion": "evaluación 004"}
    evaluated = parse_policy({"version": "0.2.0", "acciones": acciones}, "evaluada.yaml")

    lines = _render(rules=evaluated)

    assert "  política: umbral 0,90 (riesgo bajo)" in lines


def test_recorded_date_is_shown() -> None:
    assert date(2026, 10, 20).isoformat() in _render()[0]
    assert _SEP in _render()[0]
