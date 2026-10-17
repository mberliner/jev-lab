"""Casos de uso del triaje: clasificar un ticket y grabar los ejemplos."""

from collections.abc import Sequence

from jevlab.domain.decision_spec import ResolvedRequest, TriageSpec
from jevlab.domain.examples import ExampleTicket, Recording, TicketText
from jevlab.domain.triage import Origin, OriginMode, TriageAnswers, TriageResult, interpret
from jevlab.ports.clock import Clock
from jevlab.ports.judge import JudgePort
from jevlab.ports.recordings import RecordingLibrary
from jevlab.ports.specs import SpecLoader

TRIAGE_REQUEST = "soporte/triaje"


class TriageTicket:
    def __init__(self, judge: JudgePort, specs: SpecLoader) -> None:
        self._judge = judge
        self._specs = specs

    def run_live(self, raw: str) -> TriageResult:
        """Normaliza y comprueba la longitud antes de llamar (FR-013a)."""
        resolved = self._specs.load_request(TRIAGE_REQUEST)
        spec = TriageSpec.from_request(resolved)
        ticket = TicketText.parse(raw)
        ticket.check_length(spec.max_chars)
        answers = TriageAnswers.from_answers(self._judge.ask(resolved, ticket.value))
        return interpret(spec, answers, Origin(mode=OriginMode.EN_VIVO, model=answers.model))

    def run_recorded(self, recording: Recording) -> TriageResult:
        """Envía el texto de la grabación: el de la persona solo sirve para elegirla."""
        resolved = self._specs.load_request(TRIAGE_REQUEST)
        spec = TriageSpec.from_request(resolved)
        answers = TriageAnswers.from_answers(self._judge.ask(resolved, recording.text))
        origin = Origin(
            mode=OriginMode.GRABADO,
            model=recording.model,
            recorded_on=recording.recorded_on,
            example=recording.name,
            synthetic=recording.synthetic,
        )
        return interpret(spec, answers, origin)


class RecordExamples:
    def __init__(self, judge: JudgePort, library: RecordingLibrary, clock: Clock) -> None:
        self._judge = judge
        self._library = library
        self._clock = clock

    def run(self, spec: ResolvedRequest, examples: Sequence[ExampleTicket]) -> list[Recording]:
        """Sirve a cualquier petición: graba la respuesta real a cada ejemplo."""
        saved = []
        for example in examples:
            text = TicketText.parse(example.text).value
            answers = self._judge.ask(spec, text)
            exchange = self._judge.last_exchange()
            if exchange is None:
                raise RuntimeError(
                    "el juez no capturó la petición: hace falta grabar el transporte"
                )
            recording = Recording(
                name=example.name,
                text=text,
                synthetic=True,
                covers=example.covers,
                model=answers.model,
                recorded_on=self._clock.today(),
                spec_versions=spec.spec_versions(),
                request=exchange.request,
                response=exchange.response,
            )
            self._library.save(recording)
            saved.append(recording)
        return saved
