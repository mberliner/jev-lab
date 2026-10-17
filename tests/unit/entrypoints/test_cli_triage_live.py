"""`jevlab triage --en-vivo` con el juez sustituido (FR-013, FR-013a, FR-014)."""

from contextlib import nullcontext
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

import jevlab.entrypoints.cli.main as cli
from jevlab.domain.diagnostics import ProviderRejected, ProviderUnavailable
from tests.builders import answers, triage_request
from tests.fakes import FakeJudge, StaticSpecLoader

# Valor sintético con forma de clave: el test comprueba que nunca aparece en la salida.
_SECRET = "ts-valor-secreto-0123456789"  # gitleaks:allow
_TEXT = "La aplicación no arranca desde esta mañana."


def _invoke(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    args: list[str],
    judge: FakeJudge | None = None,
    key: str | None = _SECRET,
) -> tuple[Result, FakeJudge, list[str]]:
    judge = judge or FakeJudge(default=answers(model="jev-1.13.0"))
    opened: list[str] = []

    def live(api_key: str) -> nullcontext[FakeJudge]:
        opened.append(api_key)
        return nullcontext(judge)

    monkeypatch.chdir(tmp_path)  # sin .env
    if key is None:
        monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    else:
        monkeypatch.setenv("TYPESAFE_API_KEY", key)
    monkeypatch.setattr(cli, "build_spec_loader", lambda: StaticSpecLoader(triage_request()))
    monkeypatch.setattr(cli, "live_judge", live)
    result = CliRunner().invoke(cli.app, ["triage", "--en-vivo", *args])
    return result, judge, opened


def test_live_calls_once_and_says_so(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    result, judge, opened = _invoke(monkeypatch, tmp_path, [_TEXT])

    assert result.exit_code == 0, result.output
    assert opened == [_SECRET]
    assert len(judge.calls) == 1
    assert result.stdout.splitlines()[0] == "Origen: en vivo · jev-1.13.0"
    assert _SECRET not in result.output


@pytest.mark.parametrize("args", [[], ["--ejemplo", "cobro-duplicado"], [_TEXT, "--ejemplo", "x"]])
def test_live_needs_text_and_no_example(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, args: list[str]
) -> None:
    result, judge, opened = _invoke(monkeypatch, tmp_path, args)
    assert result.exit_code == 2
    assert opened == []
    assert judge.calls == []


@pytest.mark.parametrize("key", [None, "", "   "])
def test_missing_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, key: str | None) -> None:
    result, _, opened = _invoke(monkeypatch, tmp_path, [_TEXT], key=key)

    assert result.exit_code == 1
    assert (
        result.stderr.strip() == "error: falta TYPESAFE_API_KEY; ver .env.example y jevlab doctor"
    )
    assert opened == []


def test_too_long_is_rejected_before_calling(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result, judge, _ = _invoke(monkeypatch, tmp_path, ["x" * 4001])

    assert result.exit_code == 2
    assert result.stderr.strip() == "error: el ticket tiene 4.001 caracteres; el máximo es 4.000"
    assert "xxxxxxxxxx" not in result.output
    assert judge.calls == []


def test_exactly_the_limit_is_accepted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    result, judge, _ = _invoke(monkeypatch, tmp_path, ["x" * 4000])
    assert result.exit_code == 0, result.output
    assert len(judge.calls) == 1


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (
            ProviderUnavailable("TypeSafe no respondió a tiempo (10 s)"),
            "TypeSafe no respondió a tiempo (10 s)",
        ),
        (
            ProviderUnavailable("TypeSafe no disponible (503) tras 3 intentos"),
            "TypeSafe no disponible (503) tras 3 intentos",
        ),
        (ProviderRejected(401), "TypeSafe rechazó la petición (401)"),
    ],
)
def test_service_errors_without_payload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, error: Exception, message: str
) -> None:
    result, _, _ = _invoke(monkeypatch, tmp_path, [_TEXT], judge=FakeJudge(error=error))

    assert result.exit_code == 1
    assert result.stderr.strip() == f"error: {message}"
    assert _TEXT not in result.output
    assert _SECRET not in result.output


def test_live_judge_builds_the_real_client_once() -> None:
    with cli.live_judge("clave-sintetica") as judge:
        assert judge.last_exchange() is None
