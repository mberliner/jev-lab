"""Contrato de SystemLocalEnvironment con archivos y ejecutables de prueba en tmp_path."""

import json
import os
import stat
import sys
from pathlib import Path

import pytest

from jevlab.adapters.local_environment import SystemLocalEnvironment

_KEYS = ("TYPESAFE_API_KEY", "TYPESAFE_DEFAULT_MODEL", "AZURE_OPENAI_API_KEY")
_EXAMPLE = (
    "# comentario\nTYPESAFE_API_KEY=\nTYPESAFE_DEFAULT_MODEL=jev-latest\nAZURE_OPENAI_API_KEY=\n"
)


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (*_KEYS, "SPECKIT_PYTHON_EXECUTABLE", "SPECKIT_PYTHON"):
        monkeypatch.delenv(key, raising=False)


def _fake_python(directory: Path, name: str, version: list[int], yaml: str | None) -> str:
    """Ejecutable de prueba que responde a la sonda como lo haría un python3 real."""
    answer = json.dumps({"version": version, "yaml": yaml})
    if sys.platform == "win32":
        path = directory / f"{name}.cmd"
        path.write_text(f"@echo {answer}\r\n", encoding="utf-8")
    else:
        path = directory / name
        path.write_text(f"#!/bin/sh\necho '{answer}'\n", encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return str(path)


def _env(tmp_path: Path, python3: str = "python3") -> SystemLocalEnvironment:
    (tmp_path / ".env.example").write_text(_EXAMPLE, encoding="utf-8")
    return SystemLocalEnvironment(root=tmp_path, python3=python3)


def test_complete_env_file_has_no_missing_keys(tmp_path: Path) -> None:
    env = _env(tmp_path)
    (tmp_path / ".env").write_text("TYPESAFE_API_KEY=a\nAZURE_OPENAI_API_KEY=b\n", encoding="utf-8")
    assert env.missing_env_keys() == []


def test_without_env_file_keys_without_default_are_missing(tmp_path: Path) -> None:
    env = _env(tmp_path)
    assert env.missing_env_keys() == ["TYPESAFE_API_KEY", "AZURE_OPENAI_API_KEY"]


def test_empty_key_is_missing(tmp_path: Path) -> None:
    env = _env(tmp_path)
    (tmp_path / ".env").write_text(
        "TYPESAFE_API_KEY=a\nAZURE_OPENAI_API_KEY=  \n", encoding="utf-8"
    )
    assert env.missing_env_keys() == ["AZURE_OPENAI_API_KEY"]


def test_process_environment_counts_as_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = _env(tmp_path)
    monkeypatch.setenv("TYPESAFE_API_KEY", "a")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "b")
    assert env.missing_env_keys() == []


def test_without_env_example_reports_it(tmp_path: Path) -> None:
    env = SystemLocalEnvironment(root=tmp_path)
    assert env.missing_env_keys() == [".env.example"]


def test_project_python_is_the_running_interpreter(tmp_path: Path) -> None:
    assert _env(tmp_path).project_python() == tuple(sys.version_info[:3])


def test_speckit_python_with_yaml(tmp_path: Path) -> None:
    python3 = _fake_python(tmp_path, "python3", [3, 8, 10], "5.3.1")
    info = _env(tmp_path, python3).speckit_python()
    assert info.version == (3, 8, 10)
    assert info.yaml_version == "5.3.1"
    assert info.yaml_via_override is False


def test_missing_python3(tmp_path: Path) -> None:
    info = _env(tmp_path, str(tmp_path / "no-existe")).speckit_python()
    assert info.version is None


def test_python3_that_is_not_python(tmp_path: Path) -> None:
    if sys.platform == "win32":
        path = tmp_path / "python3.cmd"
        path.write_text("@echo hola\r\n", encoding="utf-8")
    else:
        path = tmp_path / "python3"
        path.write_text("#!/bin/sh\necho hola\n", encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
    assert _env(tmp_path, str(path)).speckit_python().version is None


def test_old_python3(tmp_path: Path) -> None:
    python3 = _fake_python(tmp_path, "python3", [3, 7, 3], "5.1")
    assert _env(tmp_path, python3).speckit_python().version == (3, 7, 3)


def test_python3_without_yaml_and_no_override(tmp_path: Path) -> None:
    python3 = _fake_python(tmp_path, "python3", [3, 8, 10], None)
    info = _env(tmp_path, python3).speckit_python()
    assert info.version == (3, 8, 10)
    assert info.yaml_version is None


def test_yaml_from_speckit_python_executable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    python3 = _fake_python(tmp_path, "python3", [3, 8, 10], None)
    override = _fake_python(tmp_path, "tool-python", [3, 13, 11], "6.0.3")
    monkeypatch.setenv("SPECKIT_PYTHON_EXECUTABLE", override)

    info = _env(tmp_path, python3).speckit_python()

    assert info.version == (3, 8, 10)
    assert info.yaml_version == "6.0.3"
    assert info.yaml_via_override is True


def test_python3_of_the_virtualenv_is_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    venv_bin = Path(sys.prefix, "Scripts" if sys.platform == "win32" else "bin")
    system_bin = tmp_path / "system-bin"
    system_bin.mkdir()
    _fake_python(system_bin, "python3", [3, 8, 10], "5.3.1")
    monkeypatch.setattr(sys, "base_prefix", str(tmp_path / "base"))
    monkeypatch.setenv("PATH", os.pathsep.join([str(venv_bin), str(system_bin)]))

    assert _env(tmp_path).speckit_python().version == (3, 8, 10)


def test_real_interpreter_is_probed(tmp_path: Path) -> None:
    info = _env(tmp_path, sys.executable).speckit_python()
    assert info.version == tuple(sys.version_info[:3])
    assert info.executable == os.fspath(sys.executable)
