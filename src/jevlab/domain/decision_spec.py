"""Definiciones versionadas de decisión y de petición (data-model.md, «Definiciones»).

Cada decisión vive en su archivo; la petición agrupa las que viajan juntas
(docs/standards/architecture.md §6). Aquí solo se valida: leer los archivos es del adaptador.
"""

import re
from collections.abc import Mapping
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator, model_validator

_SEMVER = re.compile(r"\d+\.\d+\.\d+")
_MOVING_ALIASES = frozenset({"jev-latest", "jev-preview"})
_ESCAPES = frozenset({"other", "none"})


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


def _check_version(value: str) -> str:
    if not _SEMVER.fullmatch(value):
        raise ValueError(f"versión no semver: {value}")
    return value


def _check_justification(value: str) -> str:
    if not value.strip():
        raise ValueError("la justificación es «provisional» o la referencia a una evaluación")
    return value


Version = Annotated[str, AfterValidator(_check_version)]
Justification = Annotated[str, AfterValidator(_check_justification)]


class _Decision(_Frozen):
    name: str
    version: Version
    model: str
    instructions: str = Field(min_length=1)

    @field_validator("model")
    @classmethod
    def _pinned_model(cls, value: str) -> str:
        if value in _MOVING_ALIASES or not value:
            raise ValueError(f"modelo no fijado: {value!r}; usa un identificador como jev-1.13.0")
        return value


class ChoiceSpec(_Decision):
    primitive: Literal["choice"]
    options: dict[str, str]
    escape: str

    @model_validator(mode="after")
    def _check_escape(self) -> Self:
        if self.escape not in _ESCAPES:
            raise ValueError("el escape es other o none")
        if self.escape not in self.options:
            raise ValueError("el escape tiene que ser una de las opciones")
        if len(self.options) < 2:
            raise ValueError("al menos dos opciones contando el escape")
        return self


class UncertainBand(_Frozen):
    low: float
    high: float
    justification: Justification

    @model_validator(mode="after")
    def _check_order(self) -> Self:
        if not 0 <= self.low <= self.high <= 1:
            raise ValueError("la banda cumple 0 <= low <= high <= 1")
        return self


class NoulSpec(_Decision):
    primitive: Literal["noul"]
    criteria_true: str
    criteria_false: str
    uncertain_band: UncertainBand


class Level(_Frozen):
    name: str
    description: str


class Threshold(_Frozen):
    level: str
    justification: Justification


class ScoreSpec(_Decision):
    primitive: Literal["score"]
    levels: tuple[Level, ...]
    threshold: Threshold

    @model_validator(mode="after")
    def _check_levels(self) -> Self:
        if len(self.levels) < 2:
            raise ValueError("al menos dos niveles")
        if self.threshold.level not in self.level_names:
            raise ValueError(f"el umbral {self.threshold.level!r} no es un nivel")
        return self

    @property
    def level_names(self) -> tuple[str, ...]:
        return tuple(level.name for level in self.levels)

    def position(self, level: str) -> int:
        """Posición del nivel desde 0: el valor con el que se compara el `score`."""
        return self.level_names.index(level)

    @property
    def threshold_position(self) -> int:
        return self.position(self.threshold.level)


DecisionSpec = Annotated[ChoiceSpec | NoulSpec | ScoreSpec, Field(discriminator="primitive")]


class RequestSpec(_Frozen):
    name: str
    version: Version
    max_chars: int = Field(gt=0)
    questions: dict[str, str]

    @field_validator("questions")
    @classmethod
    def _no_repeated_decision(cls, value: dict[str, str]) -> dict[str, str]:
        if len(set(value.values())) != len(value):
            raise ValueError("una decisión aparece en más de una pregunta")
        return value


class ResolvedRequest(_Frozen):
    """Una petición con sus decisiones validadas por nombre de pregunta y un único modelo.

    Es lo que viaja al juez; `TriageSpec` y `RouteSpec` comprueban su forma concreta.
    """

    request: RequestSpec
    decisions: dict[str, DecisionSpec]

    @classmethod
    def resolve(cls, request: RequestSpec, available: Mapping[str, DecisionSpec]) -> Self:
        resolved: dict[str, DecisionSpec] = {}
        for question, decision_name in request.questions.items():
            decision = available.get(decision_name)
            if decision is None:
                raise ValueError(f"no existe la decisión {decision_name}")
            resolved[question] = decision
        if len({d.model for d in resolved.values()}) != 1:
            raise ValueError("todas las decisiones de una petición comparten modelo")
        return cls(request=request, decisions=resolved)

    @property
    def name(self) -> str:
        return self.request.name

    @property
    def model(self) -> str:
        return next(iter(self.decisions.values())).model

    @property
    def max_chars(self) -> int:
        return self.request.max_chars

    def questions(self) -> dict[str, DecisionSpec]:
        """Nombre de pregunta -> decisión, en el orden de la petición."""
        return {question: self.decisions[question] for question in self.request.questions}

    def spec_versions(self) -> dict[str, str]:
        versions = {self.request.name: self.request.version}
        versions |= {d.name: d.version for d in self.questions().values()}
        return versions


def _check_shape(
    resolved: ResolvedRequest, label: str, expected: Mapping[str, type[_Decision]]
) -> None:
    if set(resolved.decisions) != set(expected):
        raise ValueError(f"el {label} pregunta {sorted(expected)}")
    for question, decision in resolved.decisions.items():
        if not isinstance(decision, expected[question]):
            raise TypeError(f"la pregunta {question} no admite la primitiva {decision.primitive}")


class _RequestView(_Frozen):
    """Forma concreta de una petición: delega en la petición resuelta."""

    request: ResolvedRequest

    @property
    def model(self) -> str:
        return self.request.model

    @property
    def max_chars(self) -> int:
        return self.request.max_chars

    def questions(self) -> dict[str, DecisionSpec]:
        return self.request.questions()

    def spec_versions(self) -> dict[str, str]:
        return self.request.spec_versions()


# Pregunta de la petición de triaje y primitiva que espera (spec 001, «Decisiones Jev»).
_TRIAGE_QUESTIONS: dict[str, type[_Decision]] = {
    "cola": ChoiceSpec,
    "urgencia": NoulSpec,
    "prioridad": ScoreSpec,
}


class TriageSpec(_RequestView):
    """La petición de triaje: sus tres decisiones validadas."""

    queue: ChoiceSpec
    urgency: NoulSpec
    priority: ScoreSpec

    @classmethod
    def from_request(cls, resolved: ResolvedRequest) -> Self:
        _check_shape(resolved, "triaje", _TRIAGE_QUESTIONS)
        return cls.model_validate(
            {
                "request": resolved,
                "queue": resolved.decisions["cola"],
                "urgency": resolved.decisions["urgencia"],
                "priority": resolved.decisions["prioridad"],
            }
        )


# Opciones que nombra la regla del reembolso (spec 002, FR-006): las comprueba la definición.
BILLING_QUEUE = "facturacion"
REFUND = "reembolso"

_ROUTE_QUESTIONS: dict[str, type[_Decision]] = {"cola": ChoiceSpec, "solicitud": ChoiceSpec}


class RouteSpec(_RequestView):
    """La petición de enrutado: la cola de la 001 y la solicitud del cliente (spec 002)."""

    queue: ChoiceSpec
    request_kind: ChoiceSpec

    @classmethod
    def from_request(cls, resolved: ResolvedRequest) -> Self:
        _check_shape(resolved, "enrutado", _ROUTE_QUESTIONS)
        queue, kind = resolved.decisions["cola"], resolved.decisions["solicitud"]
        assert isinstance(queue, ChoiceSpec) and isinstance(kind, ChoiceSpec)
        if BILLING_QUEUE not in queue.options:
            raise ValueError(f"la cola necesita la opción {BILLING_QUEUE}")
        if REFUND not in kind.options:
            raise ValueError(f"la solicitud necesita la opción {REFUND}")
        return cls(request=resolved, queue=queue, request_kind=kind)

    def valid_queues(self) -> tuple[str, ...]:
        """Colas a las que el Operador puede asignar: todas menos el escape, en orden."""
        return tuple(sorted(name for name in self.queue.options if name != self.queue.escape))
