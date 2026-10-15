"""Puerto del reloj: el único acceso a la fecha y la hora fuera de los adaptadores.

Research R8 de la 001 y R6 de la 002.
"""

from datetime import date, datetime
from typing import Protocol


class Clock(Protocol):
    def today(self) -> date: ...

    def now(self) -> datetime:
        """Hora actual en UTC, con zona."""
        ...
