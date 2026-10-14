"""Menú de ejemplos de `jevlab triage` sin texto ni nombre (FR-010a, research.md R9)."""

import os
from contextlib import nullcontext

import pytest
from typer.testing import CliRunner, Result

import jevlab.entrypoints.cli.main as cli
from jevlab.domain.examples import Recording
from tests.builders import answers, recording, triage_spec
from tests.fakes import FakeJudge, InMemoryRecordingLibrary, StaticSpecLoader

_EXAMPLES = [
    recording(text="Me habéis cobrado dos veces la cuota de octubre y quiero que me la devolváis."),
    recording(name="servicio-caido", text="Todo caído."),
]


def _invoke(
    monkeypatch: pytest.MonkeyPatch, terminal: bool, typed: str | None
) -> tuple[Result, list[Recording]]:
    judge = FakeJudge(default=answers())
    replayed: list[Recording] = []

    def replay(example: Recording) -> nullcontext[FakeJudge]:
        replayed.append(example)
        return nullcontext(judge)

    monkeypatch.setattr(cli, "build_spec_loader", lambda: StaticSpecLoader(triage_spec()))
    monkeypatch.setattr(cli, "build_recordings", lambda: InMemoryRecordingLibrary(list(_EXAMPLES)))
    monkeypatch.setattr(cli, "replay_judge", replay)
    monkeypatch.setattr(cli, "stdin_is_terminal", lambda: terminal)
    return CliRunner().invoke(cli.app, ["triage"], input=typed), replayed


def test_menu_lists_examples_and_triages_the_chosen_one(monkeypatch: pytest.MonkeyPatch) -> None:
    result, replayed = _invoke(monkeypatch, terminal=True, typed="2\n")

    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    assert lines[0].startswith("1. cobro-duplicado  Me habéis cobrado dos veces la cuota")
    assert lines[0].endswith("…")
    assert lines[1] == "2. servicio-caido  Todo caído."
    assert [r.name for r in replayed] == ["servicio-caido"]
    assert any(line.startswith("Origen: grabado · ejemplo servicio-caido") for line in lines)


@pytest.mark.parametrize("typed", ["9\n", "dos\n", "0\n", None])
def test_invalid_answer_or_interruption_ends_without_triage(
    monkeypatch: pytest.MonkeyPatch, typed: str | None
) -> None:
    result, replayed = _invoke(monkeypatch, terminal=True, typed=typed)

    assert result.exit_code == 1
    assert result.stderr.strip() == "sin triaje: no se eligió ningún ejemplo"
    assert "Traceback" not in result.output
    assert replayed == []


def test_without_terminal_lists_examples_and_exits_with_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, replayed = _invoke(monkeypatch, terminal=False, typed="1\n")

    assert result.exit_code == 2
    assert result.stderr.strip() == (
        "error: falta TEXTO o --ejemplo; ejemplos: cobro-duplicado, servicio-caido"
    )
    assert replayed == []


def test_null_device_is_not_a_terminal() -> None:
    # En Windows, `isatty()` es cierto para `NUL`; el menú no debe salir con la entrada redirigida.
    with open(os.devnull, encoding="utf-8") as null:
        assert not cli.is_terminal(null)
