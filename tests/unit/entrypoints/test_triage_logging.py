"""Logs de `jevlab triage`: una línea `info` con metadatos y resultados, sin payloads (FR-015)."""

import logging
from contextlib import nullcontext
from pathlib import Path

import pytest
from typer.testing import CliRunner

import jevlab.entrypoints.cli.main as cli
from jevlab.domain.diagnostics import ProviderUnavailable
from tests.builders import answers, recording, triage_spec
from tests.fakes import FakeJudge, InMemoryRecordingLibrary, StaticSpecLoader

_SECRET = "ts-valor-secreto-0123456789"  # gitleaks:allow
_TEXT = "Me habéis cobrado dos veces la cuota de octubre."


def _setup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, judge: FakeJudge) -> None:
    def open_judge(_: object) -> nullcontext[FakeJudge]:
        return nullcontext(judge)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TYPESAFE_API_KEY", _SECRET)
    monkeypatch.setattr(cli, "build_spec_loader", lambda: StaticSpecLoader(triage_spec()))
    monkeypatch.setattr(
        cli, "build_recordings", lambda: InMemoryRecordingLibrary([recording(text=_TEXT)])
    )
    monkeypatch.setattr(cli, "replay_judge", open_judge)
    monkeypatch.setattr(cli, "live_judge", open_judge)


def _records(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name.startswith(("jevlab", "typesafe_sdk"))]


def _assert_clean(text: str) -> None:
    assert "habéis" not in text
    assert _SECRET not in text
    assert "probabilities" not in text
    assert "0,88" not in text and "0.88" not in text


def test_recorded_run_logs_one_info_line(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    _setup(monkeypatch, tmp_path, FakeJudge(default=answers()))
    caplog.set_level(logging.INFO)

    result = CliRunner().invoke(cli.app, ["triage", "--ejemplo", "cobro-duplicado"])

    assert result.exit_code == 0, result.output
    [record] = _records(caplog)
    assert record.levelno == logging.INFO
    assert record.name == "jevlab"
    assert record.getMessage() == (
        "triage modo=grabado ejemplo=cobro-duplicado modelo=jev-1.13.0 cola=facturacion "
        "urgencia=no prioridad=media umbral=no"
    )
    _assert_clean(caplog.text + result.stderr)


def test_live_error_logs_metadata_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    down = ProviderUnavailable("TypeSafe no disponible (503) tras 3 intentos")
    _setup(monkeypatch, tmp_path, FakeJudge(error=down))
    caplog.set_level(logging.INFO)

    result = CliRunner().invoke(cli.app, ["triage", "--en-vivo", _TEXT])

    assert result.exit_code == 1
    [record] = _records(caplog)
    assert record.getMessage() == "triage modo=en-vivo error=ProviderUnavailable"
    _assert_clean(caplog.text + result.stderr)


def test_abstentions_are_logged_as_such(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    blank = answers().model_copy(update={"queue": None, "urgency": None, "priority": None})
    _setup(monkeypatch, tmp_path, FakeJudge(default=blank))
    caplog.set_level(logging.INFO)

    CliRunner().invoke(cli.app, ["triage", "--ejemplo", "cobro-duplicado"])

    [record] = _records(caplog)
    assert record.getMessage().endswith(
        "cola=abstencion urgencia=abstencion prioridad=abstencion umbral=-"
    )
