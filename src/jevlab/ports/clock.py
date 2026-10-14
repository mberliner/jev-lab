"""Puerto del reloj: el único acceso a la fecha fuera de los adaptadores (research.md R8)."""

from datetime import date
from typing import Protocol


class Clock(Protocol):
    def today(self) -> date: ...
