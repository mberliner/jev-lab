"""Política de enrutado: umbrales por riesgo, versionados fuera del código (spec 002).

data-model.md, «Política»; research.md R3. Validar y calcular la huella es puro: leer el archivo
es del adaptador.
"""

import hashlib
import json
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from jevlab.domain.decision_spec import Justification, Version
from jevlab.domain.diagnostics import InvalidPolicy


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Risk(StrEnum):
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"

    @property
    def rank(self) -> int:
        return list(Risk).index(self)


class ActionName(StrEnum):
    MOVER_A_COLA = "mover-a-cola"
    REEMBOLSAR = "reembolsar"


PROVISIONAL = "provisional"


class ActionPolicy(_Frozen):
    riesgo: Risk
    umbral: Annotated[float, Field(ge=0, le=1)]
    justificacion: Justification

    @property
    def provisional(self) -> bool:
        return self.justificacion.strip() == PROVISIONAL


class PolicyRef(_Frozen):
    """Lo que se muestra y se guarda: la versión semver y la huella del contenido (FR-009a)."""

    version: str
    fingerprint: str

    def label(self) -> str:
        return f"{self.version}/{self.fingerprint}"


def _number(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


class Policy(_Frozen):
    version: Version
    acciones: dict[ActionName, ActionPolicy]

    @model_validator(mode="after")
    def _check_actions(self) -> Self:
        missing = [name.value for name in ActionName if name not in self.acciones]
        if missing:
            raise ValueError(f"acciones: falta {', '.join(missing)}")
        for a_name, a in self.acciones.items():
            for b_name, b in self.acciones.items():
                if a.riesgo.rank > b.riesgo.rank and a.umbral < b.umbral:
                    raise ValueError(
                        f"acciones.{a_name.value}.umbral {_number(a.umbral)} es menor que el de "
                        f"{b_name.value} {_number(b.umbral)} con más riesgo"
                    )
        return self

    def action(self, name: ActionName) -> ActionPolicy:
        return self.acciones[name]

    @property
    def fingerprint(self) -> str:
        """8 hexadecimales del SHA-256 del JSON canónico de la política validada (research R3).

        No cambia con el orden de las claves, los comentarios ni los finales de línea del archivo.
        """
        canonical = json.dumps(
            self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:8]

    @property
    def ref(self) -> PolicyRef:
        return PolicyRef(version=self.version, fingerprint=self.fingerprint)


def _reason(error: ValidationError) -> str:
    """Campo y motivo de cada error, sin el valor recibido: solo lo que dice qué está mal."""
    parts = []
    for detail in error.errors(include_input=False, include_url=False):
        location = ".".join(str(part) for part in detail["loc"])
        message = str(detail["msg"]).removeprefix("Value error, ")
        if detail["type"] == "extra_forbidden":
            message = "campo desconocido"
        parts.append(f"{location}: {message}" if location else message)
    return "; ".join(parts)


def parse_policy(data: object, source: str) -> Policy:
    """Valida la política entera; cualquier fallo es `InvalidPolicy`, que no automatiza nada."""
    if not isinstance(data, dict):
        raise InvalidPolicy.invalid(source, "el archivo no es un mapa con version y acciones")
    try:
        return Policy.model_validate(data)
    except ValidationError as error:
        raise InvalidPolicy.invalid(source, _reason(error)) from None
