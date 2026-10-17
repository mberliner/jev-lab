"""Casos de uso TriageTicket y RecordExamples con fakes (data-model.md, «Puertos»)."""

from datetime import date

import pytest

from jevlab.application.triage import RecordExamples, TriageTicket
from jevlab.domain.examples import EmptyTicket, ExampleTicket, Exchange, TicketTooLong
from jevlab.domain.triage import OriginMode
from tests.builders import answers, recording, triage_request
from tests.fakes import FakeJudge, FrozenClock, InMemoryRecordingLibrary, StaticSpecLoader


def _use_case(judge: FakeJudge, max_chars: int = 4000) -> TriageTicket:
    return TriageTicket(judge=judge, specs=StaticSpecLoader(triage_request(max_chars)))


def test_live_asks_once_with_normalized_text_and_live_origin() -> None:
    judge = FakeJudge(default=answers(model="jev-1.13.0"))

    result = _use_case(judge).run_live("  Me  cobraron  dos veces ")

    assert [ticket for _, ticket in judge.calls] == ["Me cobraron dos veces"]
    assert judge.calls[0][0] == triage_request()
    assert result.origin.mode is OriginMode.EN_VIVO
    assert result.origin.model == "jev-1.13.0"
    assert result.origin.recorded_on is None
    assert result.origin.example is None


def test_live_checks_length_before_calling() -> None:
    judge = FakeJudge(default=answers())

    with pytest.raises(TicketTooLong):
        _use_case(judge, max_chars=10).run_live("a" * 11)
    with pytest.raises(EmptyTicket):
        _use_case(judge).run_live("   ")
    assert judge.calls == []


def test_recorded_sends_the_recording_text_and_its_origin() -> None:
    judge = FakeJudge(default=answers())
    example = recording(text="Texto grabado.")

    result = _use_case(judge).run_recorded(example)

    assert [ticket for _, ticket in judge.calls] == ["Texto grabado."]
    assert result.origin.mode is OriginMode.GRABADO
    assert result.origin.example == "cobro-duplicado"
    assert result.origin.recorded_on == date(2026, 10, 20)
    assert result.origin.synthetic is True


def test_record_examples_saves_one_recording_per_example() -> None:
    exchange = Exchange.model_validate(
        {"request": {"state": "Cobro doble."}, "response": {"status": 200, "body": {"a": 1}}}
    )
    judge = FakeJudge(default=answers(model="jev-1.13.0"), exchanges={"Cobro doble.": exchange})
    library = InMemoryRecordingLibrary()

    saved = RecordExamples(judge=judge, library=library, clock=FrozenClock(date(2026, 11, 2))).run(
        triage_request(),
        [ExampleTicket(name="cobro-doble", text="  Cobro   doble. ", covers=("x",))],
    )

    [stored] = library.all()
    assert saved == [stored]
    assert stored.name == "cobro-doble"
    assert stored.text == "Cobro doble."
    assert stored.model == "jev-1.13.0"
    assert stored.recorded_on == date(2026, 11, 2)
    assert stored.spec_versions == triage_request().spec_versions()
    assert stored.request == exchange.request
    assert stored.response == exchange.response
    assert stored.covers == ("x",)


def test_record_examples_fails_without_captured_exchange() -> None:
    judge = FakeJudge(default=answers())
    with pytest.raises(RuntimeError):
        RecordExamples(judge=judge, library=InMemoryRecordingLibrary(), clock=FrozenClock()).run(
            triage_request(), [ExampleTicket(name="a", text="b", covers=())]
        )
