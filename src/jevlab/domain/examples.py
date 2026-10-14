"""Texto del ticket, ejemplos grabados y su selección (data-model.md, research.md R9).

Ningún error de este módulo incluye el texto del ticket (FR-014).
"""

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalize(text: str) -> str:
    """NFC, sin espacios al principio ni al final y con los repetidos reducidos a uno."""
    return " ".join(unicodedata.normalize("NFC", text).split())


class EmptyTicket(Exception):
    def __init__(self) -> None:
        super().__init__("el ticket está vacío")


class TicketTooLong(Exception):
    def __init__(self, length: int, max_chars: int) -> None:
        super().__init__(
            f"el ticket tiene {_thousands(length)} caracteres; el máximo es {_thousands(max_chars)}"
        )
        self.length = length
        self.max_chars = max_chars


def _thousands(value: int) -> str:
    return f"{value:,}".replace(",", ".")


@dataclass(frozen=True)
class TicketText:
    """Texto del ticket ya normalizado; solo esto viaja al modelo (FR-016)."""

    value: str

    @classmethod
    def parse(cls, raw: str) -> Self:
        value = normalize(raw)
        if not value:
            raise EmptyTicket()
        return cls(value)

    def check_length(self, max_chars: int) -> None:
        if len(self.value) > max_chars:
            raise TicketTooLong(len(self.value), max_chars)


class RecordedResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: int
    body: dict[str, Any]


class Exchange(BaseModel):
    """Cuerpo de la petición y estado y cuerpo de la respuesta, sin cabeceras."""

    model_config = ConfigDict(frozen=True)

    request: dict[str, Any]
    response: RecordedResponse


_NAME = re.compile(r"[a-z0-9-]+")


class Recording(Exchange):
    """Respuesta real del servicio para un ticket de ejemplo (contracts/recording.md)."""

    name: str
    text: str
    synthetic: bool
    covers: tuple[str, ...] = ()
    model: str = Field(min_length=1)
    recorded_on: date
    spec_versions: dict[str, str]

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        if not _NAME.fullmatch(value):
            raise ValueError("el nombre usa solo [a-z0-9-]")
        return value

    @field_validator("text")
    @classmethod
    def _check_text(cls, value: str) -> str:
        if not value or normalize(value) != value:
            raise ValueError("el texto de una grabación se guarda normalizado")
        return value

    @field_validator("synthetic")
    @classmethod
    def _check_synthetic(cls, value: bool) -> bool:
        if not value:
            raise ValueError("los tickets de ejemplo de esta feature son sintéticos")
        return value


@dataclass(frozen=True)
class ExampleTicket:
    """Ticket de ejemplo que se va a grabar: nombre, texto y caso que pretende cubrir."""

    name: str
    text: str
    covers: tuple[str, ...]


def list_names(names: Sequence[str]) -> str:
    return ", ".join(names) if names else "ninguno; hay que grabarlos con uv run poe record"


class ExampleNotFound(Exception):
    def __init__(self, names: Sequence[str]) -> None:
        self.names = tuple(names)
        super().__init__("no hay grabación para ese ticket; ejemplos: " + list_names(self.names))


def select_example(
    recordings: Sequence[Recording], name: str | None = None, text: str | None = None
) -> Recording:
    """Por nombre exacto o por texto normalizado."""
    if name is None and text is None:
        raise ValueError("hace falta el nombre o el texto del ejemplo")
    wanted = None if text is None else normalize(text)
    for recording in recordings:
        if (name is not None and recording.name == name) or recording.text == wanted:
            return recording
    raise ExampleNotFound([r.name for r in recordings])
