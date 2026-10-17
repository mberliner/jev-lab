"""Salida de `jevlab review` (contracts/cli-review.md; cli-ux.md §6, prueba de SC-004)."""

from jevlab.application.review import Guide
from jevlab.domain.policy import ActionName
from jevlab.domain.review import Resolution, ReviewItem
from jevlab.entrypoints.cli import review_view
from tests.builders import route_spec
from tests.routing_builders import policy, routing_result

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

    assert lines[:4] == [
        "Pendientes: 1",
        "Peticiones con alguna acción que el código no automatizó; el motivo está en cada «regla».",
        "Las resuelve una persona con los comandos de «qué hacer».",
        "Qué significa cada cola y cada comando: jevlab review guia",
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


def test_guide_takes_queues_from_the_definition_and_thresholds_from_the_policy() -> None:
    rules = policy(move=0.8, refund=0.95, version="0.2.0")
    lines = review_view.render_guide(Guide(queue=route_spec().queue, policy=rules))

    i = lines.index("Colas: qué tickets atiende cada una (definición cola-destino 0.1.0):")
    assert lines[i + 1 : i + 6] == [
        "  cuenta       Acceso.",
        "  facturacion  Cobros.",
        "  tecnico      Fallos.",
        "  other        Ninguna de las anteriores. Es el escape: no se asigna.",
        "",
    ]
    i = lines.index(f"Acciones (política 0.2.0 · huella {rules.fingerprint}):")
    assert lines[i + 1 : i + 3] == [
        "  mover a cola  riesgo bajo · umbral 0,80 (provisional)",
        "  reembolsar    riesgo alto · umbral 0,95 (provisional) · solo con la cola facturacion",
    ]


def test_guide_lists_every_review_command() -> None:
    lines = review_view.render_guide(Guide(queue=route_spec().queue, policy=policy()))

    i = lines.index("Comandos (N es el número del elemento):")
    commands = [line.split("  ")[1] for line in lines[i + 1 :]]
    assert commands == [
        "jevlab review",
        "jevlab review asignar N <cola>",
        "jevlab review descartar N",
        "jevlab review confirmar N",
        "jevlab review rechazar N",
    ]


def test_guide_says_how_the_queue_decides_the_refund() -> None:
    lines = review_view.render_guide(Guide(queue=route_spec().queue, policy=policy(refund=0.95)))

    i = lines.index("La cola decide el reembolso:")
    assert lines[i + 1 : i + 6] == [
        "  facturacion      se puede confirmar o rechazar (en route, se automatiza desde 0,95)",
        "  cuenta, tecnico  no se puede confirmar: asignar una de ellas lo rechaza",
        "  descartar        sin cola: un reembolso pendiente queda rechazado",
        "Un elemento sale de la lista cuando no le quedan acciones pendientes.",
        "Toda resolución queda en la auditoría.",
    ]


def test_ticket_text_is_shown_whole_wrapped_and_quoted() -> None:
    long = _item(6, queue="cuenta", queue_confidence=0.5).model_copy(
        update={"ticket": "palabra " * 30}
    )
    short = _item(7, queue="cuenta", queue_confidence=0.5).model_copy(update={"ticket": "Hola."})

    lines = review_view.render_item(long, _QUEUES)
    text = lines[1 : lines.index("  Acción: mover a cola · estado: a revisión")]
    assert len(text) > 1
    assert text[0].startswith("  «palabra") and text[-1].endswith("palabra»")
    assert all(line.startswith("   palabra") for line in text[1:])
    assert " ".join(line.strip(" «»") for line in text).split() == ["palabra"] * 30
    assert review_view.render_item(short, _QUEUES)[1] == "  «Hola.»"


def test_escape_explains_when_to_assign_and_when_to_discard() -> None:
    lines = review_view.render_item(
        _item(8, queue="other", queue_confidence=1.0, kind="consulta"), _QUEUES
    )

    assert _todo(lines) == [
        "    jevlab review asignar 8 <cola>  # si el ticket sí es de una cola: cuenta, facturacion, tecnico",
        "    jevlab review descartar 8  # si no es de soporte, como propone el modelo",
    ]
