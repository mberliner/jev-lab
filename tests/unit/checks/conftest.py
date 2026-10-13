import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

Git = Callable[..., str]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Repositorio Git vacío en tmp_path; los archivos se añaden al índice con `git`."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


@pytest.fixture
def git(repo: Path) -> Git:
    def run(*args: str, input_text: str | None = None) -> str:
        completed = subprocess.run(
            ["git", "-C", str(repo), *args],
            input=input_text,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return completed.stdout

    return run


def write(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return path
