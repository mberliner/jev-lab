"""Respuestas del juez y su interpretación: lo que decide el código (data-model.md).

El adaptador traduce la respuesta del SDK a estos tipos; una pregunta sin respuesta llega como
`None`. La interpretación es pura y no depende del proveedor.
"""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from jevlab.domain.confidence import choice_confidence, most_likely_position, score_confidence
from jevlab.domain.decision_spec import (
    ChoiceSpec,
    NoulSpec,
    ScoreSpec,
    TriageSpec,
    UncertainBand,
)


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class ChoiceAnswer(_Frozen):
    choice: str
    confidence: float
    probabilities: dict[str, float]


class NoulAnswer(_Frozen):
    probability: float


class ScoreAnswer(_Frozen):
    score: float
    confidence: float
    probabilities: dict[int, float]


AnyAnswer = ChoiceAnswer | NoulAnswer | ScoreAnswer


class Answers(_Frozen):
    """Respuestas de una petición cualquiera: por pregunta, la del SDK traducida o `None`."""

    model: str
    by_question: dict[str, AnyAnswer | None]

    def choice(self, question: str) -> ChoiceAnswer | None:
        answer = self.by_question.get(question)
        return answer if isinstance(answer, ChoiceAnswer) else None


class TriageAnswers(_Frozen):
    model: str
    queue: ChoiceAnswer | None
    urgency: NoulAnswer | None
    priority: ScoreAnswer | None

    @classmethod
    def from_answers(cls, answers: Answers) -> "TriageAnswers":
        """Una pregunta sin respuesta, o con la de otra primitiva, llega como `None`."""
        urgency = answers.by_question.get("urgencia")
        priority = answers.by_question.get("prioridad")
        return cls(
            model=answers.model,
            queue=answers.choice("cola"),
            urgency=urgency if isinstance(urgency, NoulAnswer) else None,
            priority=priority if isinstance(priority, ScoreAnswer) else None,
        )


class OriginMode(StrEnum):
    GRABADO = "grabado"
    EN_VIVO = "en vivo"


class Origin(_Frozen):
    mode: OriginMode
    model: str
    recorded_on: date | None = None
    example: str | None = None
    synthetic: bool = False


ESCAPE_REASON = "el ticket no encaja en ninguna cola"
OUTSIDE_REASON = "respuesta fuera de la definición"
MISSING_REASON = "sin respuesta válida"


class QueueOutcome(_Frozen):
    """`assigned` es None si falta la respuesta, si es ajena a la definición o si es el escape.

    `choice` es la opción que devolvió el servicio, tal cual (None sin respuesta).
    """

    assigned: str | None
    abstention_reason: str | None
    distribution: tuple[tuple[str, float], ...]
    confidence: float | None
    recomputed_confidence: float | None
    choice: str | None = None


def interpret_queue(spec: ChoiceSpec, answer: ChoiceAnswer | None) -> QueueOutcome:
    if answer is None:
        return QueueOutcome(
            assigned=None,
            abstention_reason=MISSING_REASON,
            distribution=(),
            confidence=None,
            recomputed_confidence=None,
        )
    if answer.choice not in spec.options:
        assigned, reason = None, OUTSIDE_REASON
    elif answer.choice == spec.escape:
        assigned, reason = None, ESCAPE_REASON
    else:
        assigned, reason = answer.choice, None
    # De mayor a menor; un empate conserva el orden de la definición y después el de llegada.
    order: dict[str, int] = {}
    for name in [*spec.options, *answer.probabilities]:
        order.setdefault(name, len(order))
    distribution = sorted(answer.probabilities.items(), key=lambda kv: (-kv[1], order[kv[0]]))
    return QueueOutcome(
        assigned=assigned,
        choice=answer.choice,
        abstention_reason=reason,
        distribution=tuple(distribution),
        confidence=answer.confidence,
        recomputed_confidence=(
            choice_confidence(answer.probabilities) if len(answer.probabilities) >= 2 else None
        ),
    )


class UrgencyVerdict(StrEnum):
    SI = "sí"
    NO = "no"
    INCIERTO = "incierto"
    ABSTENCION = "abstención"


class UrgencyOutcome(_Frozen):
    """Un Noul es una probabilidad de «sí»: los valores intermedios son duda, no un grado."""

    verdict: UrgencyVerdict
    probability: float | None
    band: UncertainBand


def interpret_urgency(spec: NoulSpec, answer: NoulAnswer | None) -> UrgencyOutcome:
    band = spec.uncertain_band
    if answer is None:
        return UrgencyOutcome(verdict=UrgencyVerdict.ABSTENCION, probability=None, band=band)
    p = answer.probability
    if p < band.low:
        verdict = UrgencyVerdict.NO
    elif p > band.high:
        verdict = UrgencyVerdict.SI
    else:
        verdict = UrgencyVerdict.INCIERTO
    return UrgencyOutcome(verdict=verdict, probability=p, band=band)


class PriorityOutcome(_Frozen):
    """El Score solo se compara con el umbral; su valor no es una magnitud (*Jaggedness*).

    `most_likely` es None (abstención) si falta la respuesta o trae posiciones fuera de la leyenda.
    """

    most_likely: str | None
    distribution: tuple[tuple[int, str, float], ...]
    confidence: float | None
    recomputed_confidence: float | None
    expected_score: float | None
    threshold_level: str
    threshold_position: int
    threshold_justification: str
    reaches_threshold: bool | None


def interpret_priority(spec: ScoreSpec, answer: ScoreAnswer | None) -> PriorityOutcome:
    names = spec.level_names
    abstention = PriorityOutcome(
        most_likely=None,
        distribution=(),
        confidence=None,
        recomputed_confidence=None,
        expected_score=None,
        threshold_level=spec.threshold.level,
        threshold_position=spec.threshold_position,
        threshold_justification=spec.threshold.justification,
        reaches_threshold=None,
    )
    if answer is None or not answer.probabilities:
        return abstention
    if not set(answer.probabilities) <= set(range(len(names))):
        return abstention
    probabilities = [answer.probabilities.get(i, 0.0) for i in range(len(names))]
    return abstention.model_copy(
        update={
            "most_likely": names[most_likely_position(probabilities)],
            "distribution": tuple((i, names[i], p) for i, p in enumerate(probabilities)),
            "confidence": answer.confidence,
            "recomputed_confidence": score_confidence(probabilities),
            "expected_score": answer.score,
            "reaches_threshold": answer.score >= spec.threshold_position,
        }
    )


class TriageResult(_Frozen):
    """Lo que muestra la CLI: cada decisión interpretada y el origen."""

    origin: Origin
    queue: QueueOutcome
    urgency: UrgencyOutcome
    priority: PriorityOutcome


def interpret(spec: TriageSpec, answers: TriageAnswers, origin: Origin) -> TriageResult:
    return TriageResult(
        origin=origin,
        queue=interpret_queue(spec.queue, answers.queue),
        urgency=interpret_urgency(spec.urgency, answers.urgency),
        priority=interpret_priority(spec.priority, answers.priority),
    )
