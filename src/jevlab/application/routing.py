"""Caso de uso del enrutado: preguntar, decidir con la política, auditar y encolar (spec 002)."""

from dataclasses import dataclass
from pathlib import Path

from jevlab.domain.decision_spec import ResolvedRequest, RouteSpec
from jevlab.domain.examples import Recording, TicketText
from jevlab.domain.policy import Policy
from jevlab.domain.review import ReviewItem
from jevlab.domain.routing import RoutingResult, decide_routing, decision_entries
from jevlab.domain.triage import Answers, Origin, OriginMode, interpret_queue
from jevlab.ports.clock import Clock
from jevlab.ports.ids import IdGenerator
from jevlab.ports.judge import JudgePort
from jevlab.ports.policy import PolicyLoader
from jevlab.ports.routing_store import RoutingStore
from jevlab.ports.specs import SpecLoader

ROUTE_REQUEST = "soporte/enrutado"


@dataclass(frozen=True)
class Routed:
    """El resultado decidido y, si algo quedó pendiente, el elemento guardado con su número."""

    result: RoutingResult
    item: ReviewItem | None


class RouteTicket:
    def __init__(
        self,
        judge: JudgePort,
        specs: SpecLoader,
        policies: PolicyLoader,
        store: RoutingStore,
        ids: IdGenerator,
        clock: Clock,
    ) -> None:
        self._judge = judge
        self._specs = specs
        self._policies = policies
        self._store = store
        self._ids = ids
        self._clock = clock

    def run_live(self, raw: str, policy_path: Path | None = None) -> Routed:
        """La política se valida antes de cualquier efecto; la longitud, antes de llamar."""
        policy = self._policies.load(policy_path)
        resolved, spec = self._request()
        ticket = TicketText.parse(raw)
        ticket.check_length(spec.max_chars)
        answers = self._judge.ask(resolved, ticket.value)
        origin = Origin(mode=OriginMode.EN_VIVO, model=answers.model)
        return self._decide(policy, resolved, spec, answers, origin, ticket.value)

    def run_recorded(self, recording: Recording, policy_path: Path | None = None) -> Routed:
        policy = self._policies.load(policy_path)
        resolved, spec = self._request()
        answers = self._judge.ask(resolved, recording.text)
        origin = Origin(
            mode=OriginMode.GRABADO,
            model=recording.model,
            recorded_on=recording.recorded_on,
            example=recording.name,
            synthetic=recording.synthetic,
        )
        return self._decide(policy, resolved, spec, answers, origin, recording.text)

    def _request(self) -> tuple[ResolvedRequest, RouteSpec]:
        resolved = self._specs.load_request(ROUTE_REQUEST)
        return resolved, RouteSpec.from_request(resolved)

    def _decide(
        self,
        policy: Policy,
        resolved: ResolvedRequest,
        spec: RouteSpec,
        answers: Answers,
        origin: Origin,
        ticket: str,
    ) -> Routed:
        actions = decide_routing(
            policy,
            interpret_queue(spec.queue, answers.choice("cola")),
            interpret_queue(spec.request_kind, answers.choice("solicitud")),
        )
        result = RoutingResult(
            request_id=self._ids.new_request_id(),
            decided_at=self._clock.now(),
            origin=origin,
            policy=policy.ref,
            spec_versions=resolved.spec_versions(),
            actions=actions,
        )
        item = ReviewItem.from_result(result, ticket)
        saved = self._store.record(result, decision_entries(result), item)
        return Routed(result=result, item=saved)
