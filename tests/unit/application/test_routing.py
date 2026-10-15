"""Caso de uso RouteTicket con fakes (spec 002; data-model.md, «Resultado» y «Auditoría»)."""

from datetime import date

import pytest

from jevlab.application.routing import ROUTE_REQUEST, RouteTicket
from jevlab.domain.diagnostics import InvalidPolicy
from jevlab.domain.examples import EmptyTicket, TicketTooLong
from jevlab.domain.policy import ActionName
from jevlab.domain.routing import ActionStatus
from jevlab.domain.triage import Answers, OriginMode
from tests.builders import recording, route_answers, route_request
from tests.fakes import FakeJudge, FrozenClock, StaticSpecLoader
from tests.routing_builders import policy
from tests.routing_fakes import InMemoryRoutingStore, SequentialIds, StaticPolicyLoader

_TEXT = "Me habéis cobrado dos veces la cuota de octubre."


def _use_case(
    answers: Answers | None = None,
    max_chars: int = 4000,
    policies: StaticPolicyLoader | None = None,
) -> tuple[RouteTicket, FakeJudge, InMemoryRoutingStore]:
    judge = FakeJudge(default=answers or route_answers())
    store = InMemoryRoutingStore()
    use_case = RouteTicket(
        judge=judge,
        specs=StaticSpecLoader(route_request(max_chars)),
        policies=policies or StaticPolicyLoader(policy()),
        store=store,
        ids=SequentialIds(),
        clock=FrozenClock(),
    )
    return use_case, judge, store


def test_live_asks_once_with_the_route_request_and_normalized_text() -> None:
    use_case, judge, _ = _use_case()

    routed = use_case.run_live("  Me habéis  cobrado dos veces la cuota de octubre. ")

    assert judge.calls == [(route_request(), _TEXT)]
    result = routed.result
    assert result.request_id == "req-0001"
    assert result.decided_at == FrozenClock().now()
    assert result.origin.mode is OriginMode.EN_VIVO
    assert result.policy == policy().ref
    assert result.spec_versions == route_request().spec_versions()
    assert [a.status for a in result.actions] == [
        ActionStatus.AUTOMATIZADA,
        ActionStatus.AUTOMATIZADA,
    ]


def test_loads_the_route_request_and_the_given_policy_path(tmp_path: object) -> None:
    loader = StaticPolicyLoader(policy())
    use_case, _, _ = _use_case(policies=loader)
    specs = use_case._specs
    assert isinstance(specs, StaticSpecLoader)

    use_case.run_recorded(recording(text=_TEXT), policy_path=None)

    assert specs.requested == [ROUTE_REQUEST]
    assert loader.requested == [None]


def test_recorded_uses_the_recording_text_and_origin() -> None:
    use_case, judge, _ = _use_case()

    routed = use_case.run_recorded(recording(text="Texto grabado."))

    assert [ticket for _, ticket in judge.calls] == ["Texto grabado."]
    origin = routed.result.origin
    assert (origin.mode, origin.example, origin.recorded_on) == (
        OriginMode.GRABADO,
        "cobro-duplicado",
        date(2026, 10, 20),
    )


def test_live_checks_length_and_emptiness_before_calling() -> None:
    use_case, judge, store = _use_case(max_chars=10)
    with pytest.raises(TicketTooLong):
        use_case.run_live("a" * 11)
    with pytest.raises(EmptyTicket):
        use_case.run_live("   ")
    assert judge.calls == []
    assert store.audit == []


def test_audits_one_decision_per_action_without_the_ticket() -> None:
    use_case, _, store = _use_case(route_answers("cuenta", 1.0, "consulta", 0.9))

    use_case.run_live(_TEXT)

    assert [(e.kind, e.action, e.outcome) for e in store.audit] == [
        ("decision", ActionName.MOVER_A_COLA, "automatizada"),
        ("decision", ActionName.REEMBOLSAR, "sin reembolso"),
    ]
    move = store.audit[0]
    assert (move.request_id, move.value, move.confidence, move.threshold) == (
        "req-0001",
        "cuenta",
        1.0,
        0.90,
    )
    assert move.policy == policy().ref
    assert move.origin_mode is OriginMode.EN_VIVO
    assert move.model == "jev-1.13.0"
    assert move.review_item is None
    for entry in store.audit:
        assert "cobrado" not in entry.model_dump_json()


def test_nothing_pending_creates_no_item() -> None:
    use_case, _, store = _use_case(route_answers("cuenta", 1.0, "consulta", 0.9))

    routed = use_case.run_live(_TEXT)

    assert routed.item is None
    assert store.items == {}


def test_pending_actions_create_one_item_with_its_number() -> None:
    use_case, _, store = _use_case(route_answers("facturacion", 0.5, "reembolso", 0.5))

    routed = use_case.run_live(_TEXT)

    assert routed.item is not None and routed.item.id == 1
    assert list(store.items) == [1]
    assert [a.action for a in routed.item.actions] == [
        ActionName.MOVER_A_COLA,
        ActionName.REEMBOLSAR,
    ]
    assert routed.item.ticket == _TEXT
    assert {e.review_item for e in store.audit} == {1}


def test_same_text_twice_is_two_requests_and_two_items() -> None:
    use_case, _, store = _use_case(route_answers("cuenta", 0.5, "consulta", 0.9))

    first = use_case.run_live(_TEXT)
    second = use_case.run_live(_TEXT)

    assert first.result.request_id != second.result.request_id
    assert len(store.items) == 2


def test_invalid_policy_neither_asks_nor_writes() -> None:
    error = InvalidPolicy.invalid("laxa.yaml", "acciones.reembolsar.umbral …")
    use_case, judge, store = _use_case(policies=StaticPolicyLoader(error=error))

    with pytest.raises(InvalidPolicy):
        use_case.run_live(_TEXT)
    with pytest.raises(InvalidPolicy):
        use_case.run_recorded(recording(text=_TEXT))

    assert judge.calls == []
    assert store.audit == [] and store.items == {}


def test_two_policies_with_same_version_audit_different_fingerprints() -> None:
    a, _, store_a = _use_case(policies=StaticPolicyLoader(policy(move=0.90)))
    b, _, store_b = _use_case(policies=StaticPolicyLoader(policy(move=0.80)))

    a.run_live(_TEXT)
    b.run_live(_TEXT)

    ref_a, ref_b = store_a.audit[0].policy, store_b.audit[0].policy
    assert ref_a.version == ref_b.version
    assert ref_a.fingerprint != ref_b.fingerprint
