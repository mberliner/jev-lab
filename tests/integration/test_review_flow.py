"""US3: lo que no se automatiza llega a la cola y el Operador lo resuelve (FR-007, FR-008)."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from typer.testing import CliRunner

from jevlab.entrypoints.cli.main import app
from tests.integration.route_examples import with_tag

pytestmark = pytest.mark.integration


def test_route_list_resolve_and_persist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "estado"
    monkeypatch.setenv("JEVLAB_STATE_DIR", str(state))
    runner = CliRunner()
    items = {}
    for tag in ("mover-a-revision", "mover-escape", "reembolso-pendiente"):
        recording = with_tag(tag)
        result = runner.invoke(app, ["route", "--ejemplo", recording.name])
        assert result.exit_code == 0, result.output
        named, todo = result.stdout.splitlines()[-2:]
        assert named.startswith("En la cola de revisión: elemento "), tag
        assert todo == "qué hacer: jevlab review", tag
        items[tag] = named.split()[-1]

    listed = runner.invoke(app, ["review"])
    assert listed.stdout.splitlines()[0] == "Pendientes: 3"

    assigned = runner.invoke(app, ["review", "asignar", items["mover-a-revision"], "cuenta"])
    assert assigned.exit_code == 0, assigned.output
    assert "resuelto: sin acciones pendientes" in assigned.stdout

    confirmed = runner.invoke(app, ["review", "confirmar", items["reembolso-pendiente"]])
    assert confirmed.exit_code == 0, confirmed.output
    assert "reembolso confirmado (simulado) · cola facturacion" in confirmed.stdout

    # Otra invocación sobre el mismo archivo: solo queda lo que no se resolvió.
    again = CliRunner().invoke(app, ["review"]).stdout.splitlines()
    assert again[0] == "Pendientes: 1"
    assert again[5].startswith(f"[{items['mover-escape']}] ")
    assert f"    jevlab review descartar {items['mover-escape']}" in again

    with closing(sqlite3.connect(state / "estado.sqlite3")) as connection, connection:
        resolutions = connection.execute(
            "SELECT review_item, action, outcome FROM audit WHERE kind = 'resolucion'"
        ).fetchall()
    assert sorted(resolutions) == sorted(
        [
            (int(items["mover-a-revision"]), "mover-a-cola", "asignada"),
            (int(items["reembolso-pendiente"]), "reembolsar", "confirmada"),
        ]
    )
