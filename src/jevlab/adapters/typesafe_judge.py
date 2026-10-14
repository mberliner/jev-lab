"""Juez de TypeSafe: una petición `system_one` con las tres preguntas (research.md R1, R2 y R6).

Un solo cliente por ejecución, que se cierra al salir del `with`. Los errores se traducen al
dominio con el tipo y el estado HTTP, nunca con el cuerpo ni el texto del ticket (FR-014).
"""

from types import TracebackType
from typing import Self

import httpx2
from typesafe_sdk import (
    Choice,
    Noul,
    Question,
    RetryPolicy,
    Score,
    TypeSafeAPIConnectionError,
    TypeSafeAPIError,
    TypeSafeAPIResponseValidationError,
    TypeSafeAPITimeoutError,
    TypeSafeClient,
    TypeSafeError,
)
from typesafe_sdk import ChoiceAnswer as SdkChoiceAnswer
from typesafe_sdk import NoulAnswer as SdkNoulAnswer
from typesafe_sdk import ScoreAnswer as SdkScoreAnswer

from jevlab.adapters.recording_transport import RecordingTransport, ReplayTransport
from jevlab.domain.decision_spec import ChoiceSpec, DecisionSpec, NoulSpec, TriageSpec
from jevlab.domain.diagnostics import (
    InvalidProviderResponse,
    ProviderRejected,
    ProviderUnavailable,
)
from jevlab.domain.examples import Exchange, Recording
from jevlab.domain.triage import ChoiceAnswer, NoulAnswer, ScoreAnswer, TriageAnswers

TIMEOUT_S = 10.0
# El SDK exige una clave no vacía; en reproducción nunca sale de la máquina.
_REPLAY_KEY = "reproduccion-sin-red"
_TRANSIENT = {408, 429}


class TypeSafeJudge:
    def __init__(
        self, client: TypeSafeClient, retry: RetryPolicy, recorder: RecordingTransport | None = None
    ) -> None:
        self._client = client
        self._attempts = retry.max_retries + 1
        self._recorder = recorder

    @classmethod
    def live(
        cls,
        api_key: str,
        transport: httpx2.BaseTransport | None = None,
        retry: RetryPolicy | None = None,
        record: bool = False,
    ) -> Self:
        """Cliente real con la política de reintentos por defecto del SDK y *timeout* de 10 s."""
        policy = retry if retry is not None else RetryPolicy()
        recorder = RecordingTransport(transport or httpx2.HTTPTransport()) if record else None
        client = TypeSafeClient(
            api_key=api_key, retry=policy, timeout=TIMEOUT_S, transport=recorder or transport
        )
        return cls(client, policy, recorder)

    @classmethod
    def replay(cls, recording: Recording) -> Self:
        """Mismo cliente y mismo decodificador que en vivo, sobre la respuesta grabada."""
        policy = RetryPolicy(max_retries=0)
        client = TypeSafeClient(
            api_key=_REPLAY_KEY,
            retry=policy,
            timeout=TIMEOUT_S,
            transport=ReplayTransport(recording),
        )
        return cls(client, policy)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._client.close()

    def last_exchange(self) -> Exchange | None:
        return None if self._recorder is None else self._recorder.last_exchange()

    def ask(self, spec: TriageSpec, ticket: str) -> TriageAnswers:
        questions = {name: _question(d) for name, d in spec.questions().items()}
        try:
            response = self._client.system_one(state=ticket, questions=questions, model=spec.model)
        except TypeSafeAPITimeoutError as error:
            raise ProviderUnavailable(
                f"TypeSafe no respondió a tiempo ({TIMEOUT_S:g} s)"
            ) from error
        except TypeSafeAPIConnectionError as error:
            raise ProviderUnavailable("sin conexión con TypeSafe") from error
        except TypeSafeAPIResponseValidationError as error:
            raise InvalidProviderResponse() from error
        except TypeSafeAPIError as error:
            if error.status >= 500 or error.status in _TRANSIENT:
                raise ProviderUnavailable(
                    f"TypeSafe no disponible ({error.status}) tras {self._attempts} intentos"
                ) from error
            raise ProviderRejected(error.status) from error
        except TypeSafeError as error:
            raise InvalidProviderResponse() from error
        answers = response.answers
        queue, urgency, priority = (answers.get(name) for name in ("cola", "urgencia", "prioridad"))
        return TriageAnswers(
            model=response.model,
            queue=(
                ChoiceAnswer(
                    choice=queue.choice,
                    confidence=queue.confidence,
                    probabilities=dict(queue.probabilities),
                )
                if isinstance(queue, SdkChoiceAnswer)
                else None
            ),
            urgency=(
                NoulAnswer(probability=urgency.noul) if isinstance(urgency, SdkNoulAnswer) else None
            ),
            priority=(
                ScoreAnswer(
                    score=priority.score,
                    confidence=priority.confidence,
                    probabilities=dict(priority.probabilities),
                )
                if isinstance(priority, SdkScoreAnswer)
                else None
            ),
        )


def _question(decision: DecisionSpec) -> Question:
    if isinstance(decision, ChoiceSpec):
        return Choice(instructions=decision.instructions, criteria=dict(decision.options))
    if isinstance(decision, NoulSpec):
        return Noul(
            instructions=decision.instructions,
            criteria={"true": decision.criteria_true, "false": decision.criteria_false},
        )
    return Score(
        instructions=decision.instructions,
        criteria=[f"{level.name}: {level.description}" for level in decision.levels],
    )
