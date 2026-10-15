"""US4: cambiar el umbral en una copia de la política, sin tocar código (SC-005, FR-009a, FR-010)."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from jevlab.entrypoints.cli.main import app
from tests.builders import POLICY
from tests.integration.route_examples import queue_confidence, with_tag

pytestmark = pytest.mark.integration


def _policy(path: Path, version: str, move: float, refund: float = 0.97) -> Path:
    acciones = {
        "mover-a-cola": POLICY["acciones"]["mover-a-cola"] | {"umbral": move},
        "reembolsar": POLICY["acciones"]["reembolsar"] | {"umbral": refund},
    }
    path.write_text(yaml.safe_dump({"version": version, "acciones": acciones}), encoding="utf-8")
    return path


def test_lowering_the_threshold_changes_the_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "estado"
    monkeypatch.setenv("JEVLAB_STATE_DIR", str(state))
    runner = CliRunner()
    example = with_tag("mover-a-revision")
    # Umbral igual a la confianza grabada: se automatiza porque la regla es «>=».
    lax = _policy(tmp_path / "laxa.yaml", "0.2.0", queue_confidence(example))

    initial = runner.invoke(app, ["route", "--ejemplo", example.name])
    changed = runner.invoke(app, ["route", "--ejemplo", example.name, "--politica", str(lax)])

    assert initial.exit_code == 0 and changed.exit_code == 0, changed.output
    initial_lines, changed_lines = initial.stdout.splitlines(), changed.stdout.splitlines()
    assert any(line.endswith(" · a revisión") for line in initial_lines if "Mover a cola" in line)
    assert any(line.endswith(" · automatizada") for line in changed_lines if "Mover a cola" in line)
    assert initial_lines[1].startswith("Política: 0.1.0 · huella ")
    assert changed_lines[1].startswith("Política: 0.2.0 · huella ")
    assert initial_lines[1].split()[-1] != changed_lines[1].split()[-1]

    with closing(sqlite3.connect(state / "estado.sqlite3")) as connection, connection:
        versions = connection.execute(
            "SELECT DISTINCT policy_version, policy_fingerprint FROM audit"
        ).fetchall()
    assert len(versions) == 2
    assert {v for v, _ in versions} == {"0.1.0", "0.2.0"}


def test_non_monotonic_policy_stops_before_any_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "estado"
    monkeypatch.setenv("JEVLAB_STATE_DIR", str(state))
    broken = _policy(tmp_path / "rota.yaml", "0.1.0", move=0.90, refund=0.85)

    result = CliRunner().invoke(
        app, ["route", "--ejemplo", with_tag("mover-a-revision").name, "--politica", str(broken)]
    )

    assert result.exit_code == 1
    assert "es menor que el de mover-a-cola" in result.stderr
    assert not (state / "estado.sqlite3").exists()
