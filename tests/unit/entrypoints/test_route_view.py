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

    assert "Mover a cola: facturacion · automatizada" in lines
    assert "  confianza 1,00 ≥ umbral 0,90 (riesgo bajo, provisional)" in lines
    assert "Reembolsar: reembolso · automatizada (simulado)" in lines
    assert (
        "  confianza 0,98 ≥ umbral 0,97 (riesgo alto, provisional) · cola facturacion automatizada"
    ) in lines
    assert not any(line.startswith("En la cola de revisión") for line in lines)
    assert not any("motivo" in line for line in lines)


def test_queue_below_threshold_goes_to_review_with_reason() -> None:
    lines = _render(1, queue="cuenta", queue_confidence=0.87, kind="consulta", kind_confidence=0.9)

    i = lines.index("Mover a cola: cuenta · a revisión")
    assert lines[i + 1] == "  confianza 0,87 < umbral 0,90 (riesgo bajo, provisional)"
    assert lines[i + 2] == "  motivo: confianza por debajo del umbral"
    assert lines[-1] == "En la cola de revisión: elemento 1 (jevlab review)"
    assert lines[-2] == ""


def test_escape_has_no_queue() -> None:
    lines = _render(2, queue="other", queue_confidence=1.0, kind="consulta")

    i = lines.index("Mover a cola: sin cola · a revisión")
    assert lines[i + 2] == "  motivo: el ticket no encaja en ninguna cola"


def test_missing_queue_answer_has_no_confidence() -> None:
    lines = _render(3, queue=None, kind="consulta")

    i = lines.index("Mover a cola: sin cola · a revisión")
    assert lines[i + 1] == "  confianza no disponible · umbral 0,90 (riesgo bajo, provisional)"
    assert lines[i + 2] == "  motivo: sin respuesta válida"


def test_pending_refund_shows_reasons() -> None:
    lines = _render(4, queue="cuenta", kind="reembolso", kind_confidence=0.81)

    i = lines.index("Reembolsar: reembolso · pendiente de confirmación")
    assert lines[i + 1] == "  confianza 0,81 < umbral 0,97 (riesgo alto, provisional)"
    assert lines[i + 2] == (
        "  motivo: confianza por debajo del umbral; la cola no se automatizó a facturacion"
    )


def test_no_refund_is_an_explicit_abstention_without_threshold() -> None:
    lines = _render(queue="cuenta", kind="consulta", kind_confidence=0.92)
    i = lines.index("Reembolsar: sin reembolso · solicitud consulta · confianza 0,92")
    assert lines[i + 1] == "  motivo: la solicitud no es reembolso"
    assert "umbral 0,97" not in "\n".join(lines)

    escape = _render(queue="cuenta", kind="other", kind_confidence=0.65)
    assert "Reembolsar: sin reembolso · solicitud other (escape) · confianza 0,65" in escape

    missing = _render(queue="cuenta", kind=None)
    assert (
        "Reembolsar: sin reembolso · solicitud sin respuesta válida · confianza no disponible"
        in missing
    )


def test_not_provisional_threshold_does_not_say_so() -> None:
    acciones = dict(POLICY["acciones"])
    acciones["mover-a-cola"] = acciones["mover-a-cola"] | {"justificacion": "evaluación 004"}
    evaluated = parse_policy({"version": "0.2.0", "acciones": acciones}, "evaluada.yaml")

    lines = _render(rules=evaluated)

    assert "  confianza 1,00 ≥ umbral 0,90 (riesgo bajo)" in lines


def test_recorded_date_is_shown() -> None:
    assert date(2026, 10, 20).isoformat() in _render()[0]
    assert _SEP in _render()[0]
