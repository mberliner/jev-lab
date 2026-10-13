"""Informe de `jevlab doctor`: estados, resultados y código de salida (data-model.md)."""

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
