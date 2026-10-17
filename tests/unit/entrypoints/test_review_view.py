"""Salida de `jevlab review` (contracts/cli-review.md; cli-ux.md §6, prueba de SC-004)."""

from jevlab.domain.policy import ActionName
from jevlab.domain.review import Resolution, ReviewItem
from jevlab.entrypoints.cli import review_view
from tests.routing_builders import routing_result

_QUEUES = ("cuenta", "facturacion", "tecnico")


def _item(item_id: int = 1, **kwargs: object) -> ReviewItem:
    created = ReviewItem.from_result(routing_result(**kwargs), "texto")  # type: ignore[arg-type]
    assert created is not None
    return created.model_copy(update={"id": item_id})


def _todo(lines: list[str]) -> list[str]:
    """Las líneas de comandos que siguen a `qué hacer:`."""
    i = lines.index("  qué hacer:")
    return lines[i + 1 :]


def test_header_says_what_the_queue_is_and_who_resolves_it() -> None:
    lines = review_view.render_pending([_item(queue="cuenta", queue_confidence=0.5)], _QUEUES)

    assert lines[:3] == [
        "Pendientes: 1",
        "Peticiones con alguna acción que el código no automatizó; el motivo está en cada «regla».",
        "Las resuelve una persona con los comandos de «qué hacer».",
    ]


def test_empty_queue_has_no_explanation() -> None:
    assert review_view.render_pending([], _QUEUES) == ["Pendientes: 0"]


def test_pending_queue_labels_each_source_and_lists_the_queues() -> None:
    lines = review_view.render_item(
        _item(queue="cuenta", queue_confidence=0.87, kind="consulta"), _QUEUES
    )

    i = lines.index("  Acción: mover a cola · estado: a revisión")
    assert lines[i + 1 : i + 4] == [
        "    IA propone la cola: cuenta · confianza 0,87",
        "    política: umbral 0,90 (riesgo bajo, provisional)",
        "    regla: 0,87 < 0,90 · motivo: confianza por debajo del umbral",
    ]
    assert _todo(lines) == [
        "    jevlab review asignar 1 <cola>  # colas: cuenta, facturacion, tecnico",
        "    jevlab review descartar 1",
    ]


def test_pending_refund_with_billing_queue() -> None:
    lines = review_view.render_item(_item(2, kind="reembolso", kind_confidence=0.87), _QUEUES)

    assert "  Cola: facturacion · automatizada" in lines
    assert "  Acción: reembolsar · estado: pendiente de confirmación" in lines
    assert "    IA clasifica la solicitud: reembolso · confianza 0,87" in lines
    assert _todo(lines) == ["    jevlab review confirmar 2", "    jevlab review rechazar 2"]


def test_pending_refund_with_another_automated_queue_can_only_be_rejected() -> None:
    lines = review_view.render_item(
        _item(3, queue="cuenta", kind="reembolso", kind_confidence=0.99), _QUEUES
    )

    assert "  Cola: cuenta · automatizada" in lines
    assert _todo(lines) == [
        "    jevlab review rechazar 3  # sin la cola facturacion no se puede confirmar"
    ]


def test_queue_and_refund_pending() -> None:
    lines = review_view.render_item(
        _item(4, queue="facturacion", queue_confidence=0.5, kind="reembolso"), _QUEUES
    )

    assert _todo(lines) == [
        "    jevlab review asignar 4 facturacion  # después, confirmar 4 o rechazar 4",
        "    jevlab review asignar 4 <cola>  # cuenta o tecnico; rechaza el reembolso",
        "    jevlab review descartar 4  # rechaza también el reembolso",
        "    jevlab review rechazar 4  # solo el reembolso",
    ]


def test_assigned_queue_says_a_person_did_it() -> None:
    item = _item(5, queue="facturacion", queue_confidence=0.5, kind="reembolso")
    actions = tuple(
        a.model_copy(update={"resolution": Resolution.ASIGNADA})
        if a.action is ActionName.MOVER_A_COLA
        else a
        for a in item.actions
    )
    assigned = item.model_copy(update={"actions": actions, "queue": "facturacion"})

    lines = review_view.render_item(assigned, _QUEUES)

    assert "  Cola: facturacion · asignada por una persona" in lines
    assert _todo(lines) == ["    jevlab review confirmar 5", "    jevlab review rechazar 5"]
