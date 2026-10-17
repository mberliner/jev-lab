"""Humo `live` de `jevlab route --en-vivo` con la clave real de `.env` (spec 002)."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from typer.testing import CliRunner

from jevlab.adapters.settings import ProviderSettings
from jevlab.entrypoints.cli.main import app


@pytest.mark.live(max_usd=0.01)
def test_route_live_with_real_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if not ProviderSettings().typesafe_api_key.strip():
        pytest.skip("falta TYPESAFE_API_KEY en .env")
    monkeypatch.setenv("JEVLAB_STATE_DIR", str(tmp_path))

    text = "No puedo entrar en mi cuenta desde que cambié la contraseña. ¿Me ayudáis?"
    result = CliRunner().invoke(app, ["route", "--en-vivo", text])

    assert result.exit_code == 0, result.output
    assert result.stdout.startswith("Origen: en vivo · ")
    request_id = result.stdout.splitlines()[2].removeprefix("Petición: ")
    with closing(sqlite3.connect(tmp_path / "estado.sqlite3")) as connection, connection:
        rows = connection.execute("SELECT request_id FROM audit").fetchall()
    assert rows == [(request_id,), (request_id,)]
