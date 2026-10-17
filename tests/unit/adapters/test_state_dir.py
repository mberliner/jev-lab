"""Dónde vive el estado local (research.md R5; FR-016)."""

from pathlib import Path

import pytest

from jevlab.adapters.sqlite_store import STATE_FILE, state_dir, state_file


def test_env_variable_wins_and_folder_is_created(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "otro" / "estado"
    monkeypatch.setenv("JEVLAB_STATE_DIR", str(target))

    assert state_dir() == target
    assert target.is_dir()
    assert state_file() == target / STATE_FILE
    assert STATE_FILE == "estado.sqlite3"


def test_windows_uses_localappdata(tmp_path: Path) -> None:
    env = {"LOCALAPPDATA": str(tmp_path / "Local")}
    assert state_dir(env, "win32") == tmp_path / "Local" / "jevlab"


def test_windows_without_localappdata_uses_home(tmp_path: Path) -> None:
    assert state_dir({}, "win32", tmp_path) == tmp_path / "AppData" / "Local" / "jevlab"


def test_linux_uses_xdg_state_home(tmp_path: Path) -> None:
    env = {"XDG_STATE_HOME": str(tmp_path / "state")}
    assert state_dir(env, "linux") == tmp_path / "state" / "jevlab"


def test_linux_without_xdg_uses_local_state(tmp_path: Path) -> None:
    assert state_dir({}, "linux", tmp_path) == tmp_path / ".local" / "state" / "jevlab"
    assert (tmp_path / ".local" / "state" / "jevlab").is_dir()
