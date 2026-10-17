"""`jevlab route` con CliRunner (contracts/cli-route.md; FR-001, FR-002, FR-010, FR-015).

Grabaciones reales del paquete y estado en una carpeta temporal; en vivo, un juez falso.
"""

import logging
import sqlite3
from contextlib import closing, nullcontext
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner, Result

import jevlab.entrypoints.cli.main as cli
from jevlab.domain.diagnostics import ProviderUnavailable
from tests.builders import POLICY, route_answers
from tests.fakes import FakeJudge

_SECRET = "ts-valor-secreto-0123456789"  # gitleaks:allow
_LIVE_TEXT = "Quiero que me devolváis el cargo duplicado de la cuota de octubre."


@pytest.fixture
def state(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    folder = tmp_path / "estado"
    monkeypatch.setenv("JEVLAB_STATE_DIR", str(folder))
    monkeypatch.setattr(cli, "stdin_is_terminal", lambda: False)
    return folder / "estado.sqlite3"


def _route(*args: str) -> Result:
    return CliRunner().invoke(cli.app, ["route", *args])


def _audit(path: Path) -> list[tuple[object, ...]]:
    with closing(sqlite3.connect(path)) as connection, connection:
        return connection.execute(
            "SELECT request_id, action, outcome, policy_version, policy_fingerprint FROM audit"
        ).fetchall()


def test_by_name_routes_and_audits(state: Path) -> None:
    result = _route("--ejemplo", "cambio-de-correo")

    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    assert lines[0].startswith("Origen: grabado · ejemplo cambio-de-correo (ticket sintético)")
    assert lines[1].startswith("Política: 0.1.0 · huella ")
    request_id = lines[2].removeprefix("Petición: ")
    assert "Acción: mover a cola · estado: automatizada" in lines
    assert any(line.startswith("  IA propone la cola: cuenta · ") for line in lines)
    rows = _audit(state)
    assert {row[0] for row in rows} == {request_id}
    assert [row[1:3] for row in rows] == [
        ("mover-a-cola", "automatizada"),
        ("reembolsar", "sin reembolso"),
    ]


def test_by_text_selects_the_recording(state: Path) -> None:
    text = "  Quiero cambiar el correo electrónico asociado a mi cuenta.  No corre prisa. "
    result = _route(text)
    assert result.exit_code == 0, result.output
    assert "ejemplo cambio-de-correo" in result.stdout.splitlines()[0]


def test_pending_result_still_exits_zero_and_names_the_item(state: Path) -> None:
    result = _route("--ejemplo", "instruccion-incrustada")
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines()[-2:] == [
        "En la cola de revisión: elemento 1",
        "qué hacer: jevlab review",
    ]


def test_usage_errors_are_code_two(state: Path) -> None:
    both = _route("texto", "--ejemplo", "cobro-duplicado")
    assert both.exit_code == 2
    assert both.stderr.strip() == "error: TEXTO y --ejemplo son excluyentes"

    unknown = _route("--ejemplo", "no-existe")
    assert unknown.exit_code == 2
    assert unknown.stderr.startswith("error: no hay grabación para ese ticket; ejemplos: ")

    empty = _route("   ")
    assert (empty.exit_code, empty.stderr.strip()) == (2, "error: el ticket está vacío")

    live_without_text = _route("--en-vivo", "--ejemplo", "cobro-duplicado")
    assert live_without_text.exit_code == 2

    assert not state.exists()


def test_without_terminal_lists_examples(state: Path) -> None:
    result = _route()
    assert result.exit_code == 2
    assert "reembolso-ambiguo" in result.stderr
    assert "sin enrutado" not in result.stderr


def test_other_policy_by_path(state: Path, tmp_path: Path) -> None:
    acciones = dict(POLICY["acciones"])
    acciones["mover-a-cola"] = acciones["mover-a-cola"] | {"umbral": 0.5}
    path = tmp_path / "politica.yaml"
    path.write_text(yaml.safe_dump({"version": "0.2.0", "acciones": acciones}), encoding="utf-8")

    result = _route("--ejemplo", "instruccion-incrustada", "--politica", str(path))

    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines()[1].startswith("Política: 0.2.0 · huella ")
    assert "Acción: mover a cola · estado: automatizada" in result.stdout
    assert "  IA propone la cola: cuenta · " in result.stdout


def test_invalid_policy_is_code_one_and_writes_nothing(state: Path, tmp_path: Path) -> None:
    acciones = dict(POLICY["acciones"])
    acciones["reembolsar"] = acciones["reembolsar"] | {"umbral": 0.85}
    path = tmp_path / "laxa.yaml"
    path.write_text(yaml.safe_dump({"version": "0.1.0", "acciones": acciones}), encoding="utf-8")

    result = _route("--ejemplo", "instruccion-incrustada", "--politica", str(path))

    assert result.exit_code == 1
    assert result.stderr.strip() == (
        "error: política no válida (laxa.yaml): acciones.reembolsar.umbral 0,85 es menor que "
        "el de mover-a-cola 0,90 con más riesgo"
    )
    assert "Ignora" not in result.stderr
    assert not state.exists()

    missing = _route("--ejemplo", "cobro-duplicado", "--politica", str(tmp_path / "nada.yaml"))
    assert missing.exit_code == 1
    assert missing.stderr.strip() == f"error: no se puede leer la política {tmp_path / 'nada.yaml'}"


def test_state_from_another_version_is_code_one(state: Path) -> None:
    state.parent.mkdir(parents=True)
    with closing(sqlite3.connect(state)) as connection, connection:
        connection.execute("PRAGMA user_version = 9")

    result = _route("--ejemplo", "cobro-duplicado")

    assert result.exit_code == 1
    assert result.stderr.strip() == (
        f"error: el archivo de estado {state} no es de esta versión de jevlab"
    )


def _live(monkeypatch: pytest.MonkeyPatch, judge: FakeJudge) -> None:
    monkeypatch.setenv("TYPESAFE_API_KEY", _SECRET)
    monkeypatch.setattr(cli, "live_judge", lambda _key: nullcontext(judge))


def test_live_routes_with_live_origin(state: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    judge = FakeJudge(default=route_answers())
    _live(monkeypatch, judge)

    result = _route(_LIVE_TEXT, "--en-vivo")

    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines()[0] == "Origen: en vivo · jev-1.13.0"
    assert [ticket for _, ticket in judge.calls] == [_LIVE_TEXT]
    assert len(_audit(state)) == 2


def test_live_errors_never_show_the_ticket(state: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _live(monkeypatch, FakeJudge(error=ProviderUnavailable("sin conexión con TypeSafe")))

    result = _route(_LIVE_TEXT, "--en-vivo")

    assert result.exit_code == 1
    assert result.stderr.strip() == "error: sin conexión con TypeSafe"
    assert "devolváis" not in result.output
    assert not state.exists() or _audit(state) == []


def test_info_log_has_metadata_only(state: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)

    result = _route("--ejemplo", "reembolso-ambiguo")

    assert result.exit_code == 0, result.output
    [record] = [r for r in caplog.records if r.name == "jevlab"]
    message = record.getMessage()
    request_id = result.stdout.splitlines()[2].removeprefix("Petición: ")
    assert message.startswith(f"route peticion={request_id} modo=grabado ejemplo=reembolso-ambiguo")
    assert "modelo=jev-1.13.0 politica=0.1.0/" in message
    assert message.endswith("mover-a-cola=automatizada reembolsar=pendiente-de-confirmacion")
    assert "cargo" not in message and "euros" not in message
