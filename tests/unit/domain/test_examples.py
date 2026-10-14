"""Normalización del ticket, ejemplos grabados y su selección (data-model.md)."""

import unicodedata
from datetime import date
from typing import Any

import pytest
from pydantic import ValidationError

from jevlab.domain.examples import (
    EmptyTicket,
    ExampleNotFound,
    Recording,
    TicketText,
    TicketTooLong,
    normalize,
    select_example,
)


def recording(**overrides: Any) -> Recording:
    data: dict[str, Any] = {
        "name": "cobro-duplicado",
        "text": "Me habéis cobrado dos veces la cuota de octubre.",
        "synthetic": True,
        "covers": ["cola-facturacion"],
        "model": "jev-1.13.0",
        "recorded_on": date(2026, 10, 20),
        "spec_versions": {"triaje": "0.1.0"},
        "request": {"state": "x"},
        "response": {"status": 200, "body": {"model": "jev-1.13.0"}},
    }
    return Recording.model_validate(data | overrides)


def test_normalize_trims_collapses_and_composes() -> None:
    decomposed = unicodedata.normalize("NFD", "  habéis   cobrado\n dos  ")
    assert normalize(decomposed) == "habéis cobrado dos"


def test_empty_ticket() -> None:
    for raw in ("", "   ", "\n\t"):
        with pytest.raises(EmptyTicket):
            TicketText.parse(raw)


def test_ticket_length_limit_is_inclusive() -> None:
    TicketText.parse("a" * 4000).check_length(4000)
    with pytest.raises(TicketTooLong) as error:
        TicketText.parse("a" * 4001).check_length(4000)
    assert (error.value.length, error.value.max_chars) == (4001, 4000)
    assert "a" * 10 not in str(error.value)


def test_select_by_name_and_by_normalized_text() -> None:
    examples = [recording(), recording(name="servicio-caido", text="Todo caído.")]

    assert select_example(examples, name="servicio-caido").name == "servicio-caido"
    decomposed = unicodedata.normalize(
        "NFD", "  Me habéis  cobrado dos veces la cuota de octubre. "
    )
    assert select_example(examples, text=decomposed).name == "cobro-duplicado"


def test_not_found_lists_names_without_the_text() -> None:
    examples = [recording(), recording(name="servicio-caido", text="Todo caído.")]

    with pytest.raises(ExampleNotFound) as error:
        select_example(examples, text="un texto secreto sin grabación")
    assert error.value.names == ("cobro-duplicado", "servicio-caido")
    assert "secreto" not in str(error.value)
    assert "cobro-duplicado, servicio-caido" in str(error.value)

    with pytest.raises(ExampleNotFound):
        select_example(examples, name="no-existe")


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": "Cobro_Duplicado"},
        {"model": ""},
        {"synthetic": False},
        {"text": "Me  habéis cobrado"},
        {"text": " "},
    ],
)
def test_recording_rules(overrides: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        recording(**overrides)


def test_recording_requires_date() -> None:
    data = recording().model_dump()
    del data["recorded_on"]
    with pytest.raises(ValidationError):
        Recording.model_validate(data)


def test_not_found_without_recordings_says_how_to_record() -> None:
    with pytest.raises(ExampleNotFound) as error:
        select_example([], text="algo")
    assert str(error.value).endswith("ejemplos: ninguno; hay que grabarlos con uv run poe record")
