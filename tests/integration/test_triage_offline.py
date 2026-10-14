"""US4: modo grabado sin red, sin claves y sin `.env`, reproducible (SC-004)."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from jevlab.domain.examples import Recording
from jevlab.entrypoints.cli.main import app

pytestmark = pytest.mark.integration


def test_every_example_replays_offline_and_identically(
    real_recordings: list[Recording], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    for name in ("TYPESAFE_API_KEY", "TYPESAFE_DEFAULT_MODEL", "TYPESAFE_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    runner = CliRunner()

    for recording in real_recordings:
        by_name = runner.invoke(app, ["triage", "--ejemplo", recording.name])
        assert by_name.exit_code == 0, by_name.output
        first = by_name.stdout.splitlines()[0]
        assert first == (
            f"Origen: grabado · ejemplo {recording.name} (ticket sintético) · "
            f"{recording.model} · {recording.recorded_on.isoformat()}"
        )
        messy = "  " + recording.text.replace(" ", "   ", 1) + " "
        for args in ([recording.text], [messy], ["--ejemplo", recording.name]):
            again = runner.invoke(app, ["triage", *args])
            assert again.exit_code == 0, again.output
            assert again.stdout == by_name.stdout


def test_text_without_recording_lists_examples(
    real_recordings: list[Recording], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["triage", "un texto sin grabación"])

    assert result.exit_code == 2
    assert "no hay grabación para ese ticket; ejemplos: " in result.stderr
    for recording in real_recordings:
        assert recording.name in result.stderr
