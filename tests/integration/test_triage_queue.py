"""US1: cola, distribución y confianza con adaptadores reales y grabaciones reales."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from jevlab.domain.examples import Recording
from jevlab.entrypoints.cli.main import app

pytestmark = pytest.mark.integration


def test_queue_and_escape_from_another_directory(
    real_recordings: list[Recording], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    billing = runner.invoke(app, ["triage", "--ejemplo", "cobro-duplicado"])
    assert billing.exit_code == 0, billing.output
    lines = billing.stdout.splitlines()
    assert lines[0].startswith("Origen: grabado · ejemplo cobro-duplicado")
    queue = lines.index(next(line for line in lines if line.startswith("Cola: ")))
    assert lines[queue].startswith("Cola: facturacion · confianza ")
    rows = lines[queue + 1 : queue + 5]
    assert sorted(row.split()[0] for row in rows) == ["cuenta", "facturacion", "other", "tecnico"]
    shares = [float(row.split()[1].replace(",", ".")) for row in rows]
    assert shares == sorted(shares, reverse=True)

    escape = runner.invoke(app, ["triage", "--ejemplo", "pregunta-fuera-de-ambito"])
    assert escape.exit_code == 0, escape.output
    assert "Cola: sin cola asignada, requiere revisión manual" in escape.stdout
