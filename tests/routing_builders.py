"""Política y resultados de enrutado construidos en los tests (spec 002).

Aparte de `tests/builders.py` para que los tests de la 000 y la 001 no dependan de la 002.
"""

from datetime import UTC, date, datetime
from typing import Any

from jevlab.domain.policy import Policy, parse_policy
from jevlab.domain.review import ReviewItem
from jevlab.domain.routing import AuditEntry, RoutingResult, decide_routing, decision_entries
from jevlab.domain.triage import Origin, OriginMode, interpret_queue
from tests.builders import MODEL, POLICY, route_answers, route_spec


def policy(move: float = 0.90, refund: float = 0.97, version: str = "0.1.0") -> Policy:
    acciones = {
        "mover-a-cola": POLICY["acciones"]["mover-a-cola"] | {"umbral": move},
        "reembolsar": POLICY["acciones"]["reembolsar"] | {"umbral": refund},
    }
    return parse_policy({"version": version, "acciones": acciones}, "politica-de-test.yaml")


RECORDED = Origin(
    mode=OriginMode.GRABADO,
    model=MODEL,
    recorded_on=date(2026, 10, 20),
    example="cobro-duplicado",
    synthetic=True,
)
DECIDED_AT = datetime(2026, 10, 20, 10, 2, tzinfo=UTC)


def routing_result(
    queue: str | None = "facturacion",
    queue_confidence: float = 1.0,
    kind: str | None = "reembolso",
    kind_confidence: float = 0.98,
    request_id: str = "req-0001",
    rules: Policy | None = None,
) -> RoutingResult:
    """Resultado de enrutado decidido por el dominio a partir de respuestas construidas."""
    spec = route_spec()
    given = route_answers(queue, queue_confidence, kind, kind_confidence)
    rules = rules or policy()
    actions = decide_routing(
        rules,
        interpret_queue(spec.queue, given.choice("cola")),
        interpret_queue(spec.request_kind, given.choice("solicitud")),
    )
    return RoutingResult(
        request_id=request_id,
        decided_at=DECIDED_AT,
        origin=RECORDED,
        policy=rules.ref,
        spec_versions=spec.spec_versions(),
        actions=actions,
    )


def routed(
    ticket: str = "Me habéis cobrado dos veces.", **kwargs: Any
) -> tuple[RoutingResult, tuple[AuditEntry, ...], ReviewItem | None]:
    result = routing_result(**kwargs)
    return result, decision_entries(result), ReviewItem.from_result(result, ticket)
