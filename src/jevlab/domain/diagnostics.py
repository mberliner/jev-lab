"""Informe de `jevlab doctor` y errores de los proveedores (data-model.md de 000 y 001)."""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator


class CheckStatus(StrEnum):
    OK = "ok"
    FAIL = "fail"
    UNAVAILABLE = "unavailable"


class Scope(StrEnum):
    LOCAL = "local"
    REMOTE = "remote"


class CheckResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    scope: Scope
    status: CheckStatus
    detail: str
    fix: str | None = None

    @model_validator(mode="after")
    def _check_rules(self) -> Self:
        if self.scope is Scope.LOCAL and self.status is CheckStatus.UNAVAILABLE:
            raise ValueError("una comprobación local no puede quedar no disponible")
        if self.status is not CheckStatus.OK and not self.fix:
            raise ValueError("fix es obligatorio si el estado no es ok")
        return self


class DoctorReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    results: tuple[CheckResult, ...]
    remote_requested: bool

    def exit_code(self) -> int:
        if any(r.status is CheckStatus.FAIL for r in self.results):
            return 1
        if self.remote_requested and any(
            r.scope is Scope.REMOTE and r.status is CheckStatus.UNAVAILABLE for r in self.results
        ):
            return 1
        return 0


class ProviderUnavailable(Exception):
    """El proveedor no respondió: red, DNS, tiempo de espera o 5xx tras reintentos."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class ProviderRejected(Exception):
    """El proveedor rechazó la petición; `status` es None si falta configuración local."""

    def __init__(self, status: int | None) -> None:
        super().__init__(status)
        self.status = status


class InvalidProviderResponse(Exception):
    """El SDK no pudo decodificar la respuesta; el mensaje no lleva el cuerpo."""

    def __init__(self) -> None:
        super().__init__("TypeSafe devolvió una respuesta no válida")


class RecordingOutdated(Exception):
    """La petición que genera la definición actual no coincide con la grabada."""

    def __init__(self, name: str) -> None:
        super().__init__(
            f"la grabación {name} no corresponde a la definición actual; hay que regrabar"
        )
        self.name = name


class MissingApiKey(Exception):
    def __init__(self) -> None:
        super().__init__("falta TYPESAFE_API_KEY; ver .env.example y jevlab doctor")


class InvalidPolicy(Exception):
    """La política no se puede usar: no se lee o no es válida. No automatiza nada (FR-010).

    El mensaje dice el archivo, el campo y el motivo, nunca el contenido del archivo.
    """

    @classmethod
    def unreadable(cls, path: str) -> "InvalidPolicy":
        return cls(f"no se puede leer la política {path}")

    @classmethod
    def invalid(cls, source: str, reason: str) -> "InvalidPolicy":
        return cls(f"política no válida ({source}): {reason}")


class StateUnreadable(Exception):
    """El archivo de estado local no es de esta versión de jevlab o no es una base SQLite."""

    def __init__(self, path: str) -> None:
        super().__init__(f"el archivo de estado {path} no es de esta versión de jevlab")
        self.path = path
