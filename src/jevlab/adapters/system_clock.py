"""Reloj del sistema; se usa al grabar para fechar cada grabación."""

from datetime import date


class SystemClock:
    def today(self) -> date:
        return date.today()
