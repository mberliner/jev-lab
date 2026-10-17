"""US1: mover a cola solo con confianza suficiente, con grabaciones y adaptadores reales."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from typer.testing import CliRunner

from jevlab.entrypoints.cli.main import app
from tests.integration.route_examples import with_tag

pytestmark = pytest.mark.integration


def test_queue_is_moved_only_with_enough_confidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JEVLAB_STATE_DIR", str(tmp_path / "estado"))
    runner = CliRunner()
    outputs = {}
    for tag in ("mover-automatizada", "mover-a-revision", "mover-escape"):
        result = runner.invoke(app, ["route", "--ejemplo", with_tag(tag).name])
        assert result.exit_code == 0, result.output
        outputs[tag] = result.stdout.splitlines()

    automated = outputs["mover-automatizada"]
    assert "Acción: mover a cola · estado: automatizada" in automated

    review = outputs["mover-a-revision"]
    i = review.index("Acción: mover a cola · estado: a revisión")
    assert review[i + 1].startswith("  IA propone la cola: ")
    assert review[i + 2].startswith("  política: umbral 0,90 ")
    assert review[i + 3].endswith(" < 0,90 · motivo: confianza por debajo del umbral")
    assert review[-1] == "qué hacer: jevlab review"

    escape = outputs["mover-escape"]
    i = escape.index("Acción: mover a cola · estado: a revisión")
    assert escape[i + 1].startswith("  IA propone la cola: ninguna · ")

    with closing(sqlite3.connect(tmp_path / "estado" / "estado.sqlite3")) as connection, connection:
        rows = connection.execute(
            "SELECT request_id, action, policy_version, policy_fingerprint FROM audit"
        ).fetchall()
    request_ids = [lines[2].removeprefix("Petición: ") for lines in outputs.values()]
    assert {row[0] for row in rows} == set(request_ids)
    assert {(row[0], row[1]) for row in rows} == {
        (request_id, action)
        for request_id in request_ids
        for action in ("mover-a-cola", "reembolsar")
    }
    fingerprints = {lines[1] for lines in outputs.values()}
    assert len(fingerprints) == 1
    assert {f"Política: {row[2]} · huella {row[3]}" for row in rows} == fingerprints
    texts = [with_tag(tag).text for tag in outputs]
    with closing(sqlite3.connect(tmp_path / "estado" / "estado.sqlite3")) as connection, connection:
        dump = "\n".join(connection.iterdump())
    audit_dump = [line for line in dump.splitlines() if 'INSERT INTO "audit"' in line]
    for text in texts:
        assert all(text[:20] not in line for line in audit_dump)
