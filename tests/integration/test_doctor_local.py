"""US2: `jevlab doctor` con los adaptadores locales reales (escenario principal)."""

import os
import stat
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from jevlab.entrypoints.cli.main import app

pytestmark = pytest.mark.integration

_EXAMPLE = "TYPESAFE_API_KEY=\nTYPESAFE_DEFAULT_MODEL=jev-latest\nAZURE_OPENAI_API_KEY=\n"


def _python3_on_path(directory: Path) -> str:
    """Un `python3` que delega en el intérprete de los tests, que tiene PyYAML."""
    directory.mkdir()
    if sys.platform == "win32":
        (directory / "python3.cmd").write_text(f'@"{sys.executable}" %*\r\n', encoding="utf-8")
    else:
        path = directory / "python3"
        path.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return str(directory)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for key in ("TYPESAFE_API_KEY", "TYPESAFE_DEFAULT_MODEL", "AZURE_OPENAI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("SPECKIT_PYTHON_EXECUTABLE", raising=False)
    bin_dir = _python3_on_path(tmp_path / "bin")
    monkeypatch.setenv("PATH", bin_dir + os.pathsep + os.environ["PATH"])
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".env.example").write_text(_EXAMPLE, encoding="utf-8")
    monkeypatch.chdir(root)
    return root


def test_doctor_passes_with_complete_env(project: Path) -> None:
    (project / ".env").write_text(
        "TYPESAFE_API_KEY=clave-a\nAZURE_OPENAI_API_KEY=clave-b\n", encoding="utf-8"
    )

    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 0, result.output
    assert "clave-a" not in result.output


def test_doctor_fails_with_empty_key(project: Path) -> None:
    (project / ".env").write_text(
        "TYPESAFE_API_KEY=clave-a\nAZURE_OPENAI_API_KEY=\n", encoding="utf-8"
    )

    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "[fail] env-keys        faltan: AZURE_OPENAI_API_KEY" in result.output
