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


# Pregunta de la petición de triaje y primitiva que espera (spec, «Decisiones Jev»).
_TRIAGE_QUESTIONS: dict[str, type[_Decision]] = {
    "cola": ChoiceSpec,
    "urgencia": NoulSpec,
    "prioridad": ScoreSpec,
}


class TriageSpec(_Frozen):
    """La petición de triaje ya resuelta: sus tres decisiones validadas y el modelo común."""

    request: RequestSpec
    queue: ChoiceSpec
    urgency: NoulSpec
    priority: ScoreSpec

    @classmethod
    def resolve(cls, request: RequestSpec, decisions: Mapping[str, DecisionSpec]) -> Self:
        if set(request.questions) != set(_TRIAGE_QUESTIONS):
            raise ValueError(f"el triaje pregunta {sorted(_TRIAGE_QUESTIONS)}")
        resolved: dict[str, DecisionSpec] = {}
        for question, decision_name in request.questions.items():
            decision = decisions.get(decision_name)
            if decision is None:
                raise ValueError(f"no existe la decisión {decision_name}")
            if not isinstance(decision, _TRIAGE_QUESTIONS[question]):
                raise TypeError(
                    f"la pregunta {question} no admite la primitiva {decision.primitive}"
                )
            resolved[question] = decision
        if len({d.model for d in resolved.values()}) != 1:
            raise ValueError("todas las decisiones de una petición comparten modelo")
        return cls.model_validate(
            {
                "request": request,
                "queue": resolved["cola"],
                "urgency": resolved["urgencia"],
                "priority": resolved["prioridad"],
            }
        )

    @property
    def model(self) -> str:
        return self.queue.model

    @property
    def max_chars(self) -> int:
        return self.request.max_chars

    def questions(self) -> dict[str, DecisionSpec]:
        """Nombre de pregunta -> decisión, en el orden de la petición."""
        by_name: dict[str, DecisionSpec] = {
            "cola": self.queue,
            "urgencia": self.urgency,
            "prioridad": self.priority,
        }
        return {question: by_name[question] for question in self.request.questions}

    def spec_versions(self) -> dict[str, str]:
        versions = {self.request.name: self.request.version}
        versions |= {d.name: d.version for d in self.questions().values()}
        return versions
