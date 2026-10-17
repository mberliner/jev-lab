"""`jevlab triage` en modo grabado con adaptadores sustituidos (contracts/cli-triage.md)."""

from contextlib import nullcontext

import pytest
from typer.testing import CliRunner, Result

import jevlab.entrypoints.cli.main as cli
from jevlab.domain.diagnostics import RecordingOutdated
from jevlab.domain.examples import Recording
from tests.builders import answers, recording, triage_request
from tests.fakes import FakeJudge, InMemoryRecordingLibrary, StaticSpecLoader

_TEXT = "Me habéis cobrado dos veces la cuota."
_EXAMPLES = [recording(text=_TEXT), recording(name="servicio-caido", text="Todo caído.")]


def _invoke(
    monkeypatch: pytest.MonkeyPatch, args: list[str], judge: FakeJudge | None = None
) -> tuple[Result, FakeJudge, list[Recording]]:
    judge = judge or FakeJudge(default=answers())
    replayed: list[Recording] = []

    def replay(example: Recording) -> nullcontext[FakeJudge]:
        replayed.append(example)
        return nullcontext(judge)

    monkeypatch.setattr(cli, "build_spec_loader", lambda: StaticSpecLoader(triage_request()))
    monkeypatch.setattr(cli, "build_recordings", lambda: InMemoryRecordingLibrary(list(_EXAMPLES)))
    monkeypatch.setattr(cli, "replay_judge", replay)
    return CliRunner().invoke(cli.app, ["triage", *args]), judge, replayed


def test_by_text_replays_the_matching_example(monkeypatch: pytest.MonkeyPatch) -> None:
    result, judge, replayed = _invoke(monkeypatch, ["  Me habéis  cobrado dos veces la cuota. "])

    assert result.exit_code == 0, result.output
    assert [r.name for r in replayed] == ["cobro-duplicado"]
    assert [ticket for _, ticket in judge.calls] == [_TEXT]
    lines = result.stdout.splitlines()
    assert lines[0].startswith("Origen: grabado · ejemplo cobro-duplicado")
    assert "Cola: facturacion · confianza 0,84" in lines


def test_by_name(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _, replayed = _invoke(monkeypatch, ["--ejemplo", "servicio-caido"])
    assert result.exit_code == 0, result.output
    assert [r.name for r in replayed] == ["servicio-caido"]


def test_text_and_name_together_is_a_usage_error(monkeypatch: pytest.MonkeyPatch) -> None:
    result, judge, _ = _invoke(monkeypatch, [_TEXT, "--ejemplo", "servicio-caido"])
    assert result.exit_code == 2
    assert judge.calls == []


def test_empty_text_is_a_usage_error(monkeypatch: pytest.MonkeyPatch) -> None:
    result, judge, _ = _invoke(monkeypatch, ["   "])
    assert result.exit_code == 2
    assert result.stderr.strip() == "error: el ticket está vacío"
    assert judge.calls == []


@pytest.mark.parametrize("args", [["un texto secreto sin grabación"], ["--ejemplo", "no-existe"]])
def test_without_recording_lists_examples(monkeypatch: pytest.MonkeyPatch, args: list[str]) -> None:
    result, judge, _ = _invoke(monkeypatch, args)

    assert result.exit_code == 2
    assert result.stderr.strip() == (
        "error: no hay grabación para ese ticket; ejemplos: cobro-duplicado, servicio-caido"
    )
    assert "secreto" not in result.output
    assert judge.calls == []


def test_outdated_recording_fails_with_code_1(monkeypatch: pytest.MonkeyPatch) -> None:
    judge = FakeJudge(error=RecordingOutdated("cobro-duplicado"))
    result, _, _ = _invoke(monkeypatch, ["--ejemplo", "cobro-duplicado"], judge=judge)

    assert result.exit_code == 1
    assert result.stderr.strip() == (
        "error: la grabación cobro-duplicado no corresponde a la definición actual; "
        "hay que regrabar"
    )
    assert _TEXT not in result.output
