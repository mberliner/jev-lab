"""US2: el reembolso exige más confianza y la cola facturacion automatizada (FR-006)."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from typer.testing import CliRunner

from jevlab.entrypoints.cli.main import app
from tests.integration.route_examples import all_with_tag, with_tag

pytestmark = pytest.mark.integration


def test_refund_by_risk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "estado"
    monkeypatch.setenv("JEVLAB_STATE_DIR", str(state))
    runner = CliRunner()

    def route(name: str) -> list[str]:
        result = runner.invoke(app, ["route", "--ejemplo", name])
        assert result.exit_code == 0, result.output
        return result.stdout.splitlines()

    automated = route(with_tag("reembolso-automatizado").name)
    assert "Reembolsar: reembolso · automatizada (simulado)" in automated
    assert not any(line.startswith("En la cola de revisión") for line in automated)

    pending = route(with_tag("reembolso-pendiente").name)
    assert "Reembolsar: reembolso · pendiente de confirmación" in pending

    abstention = route(with_tag("reembolso-abstencion").name)
    assert any(line.startswith("Reembolsar: sin reembolso · solicitud ") for line in abstention)
    assert not any(line.startswith("En la cola de revisión") for line in abstention)

    for recording in all_with_tag("sin-reembolso-adversarial"):
        assert "Reembolsar: reembolso · automatizada (simulado)" not in route(recording.name)

    with closing(sqlite3.connect(state / "estado.sqlite3")) as connection, connection:
        refunds = connection.execute(
            "SELECT risk, threshold FROM audit WHERE action = 'reembolsar'"
        ).fetchall()
    assert refunds and set(refunds) == {("alto", 0.97)}
