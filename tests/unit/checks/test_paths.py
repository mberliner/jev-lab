import os
from pathlib import Path

import pytest

from checks.paths import check_paths, main
from tests.unit.checks.conftest import Git, write

# Las rutas de ejemplo se construyen por partes para que este archivo no las contenga literalmente.
_HOME = "/" + "home" + "/usuario/proyecto"
_MAC = "/" + "Users" + "/usuario/proyecto"
_WIN = "C:" + "\\" + "Users" + "\\usuario\\proyecto"
_ROOT = "/" + "root" + "/proyecto"


def test_relative_paths_pass(repo: Path, git: Git) -> None:
    write(repo, "docs/a.md", "Ver docs/setup.md y ./scripts/checks/paths.py\n")
    git("add", "-A")
    assert check_paths(repo) == []
    assert main(["--root", str(repo)]) == 0


@pytest.mark.parametrize("path", [_HOME, _MAC, _WIN, _ROOT])
def test_machine_paths_are_rejected(repo: Path, git: Git, path: str) -> None:
    write(repo, "docs/a.md", f"linea\nver {path}/x\n")
    git("add", "-A")
    errors = check_paths(repo)
    assert len(errors) == 1
    assert errors[0].startswith("docs/a.md:2: ")


def test_url_with_home_segment_is_not_a_machine_path(repo: Path, git: Git) -> None:
    write(repo, "a.md", "https://example.com" + _HOME + "\n")
    git("add", "-A")
    assert check_paths(repo) == []


def test_absolute_path_of_the_repository_is_rejected(repo: Path, git: Git) -> None:
    write(repo, "config.toml", f'ruta = "{repo.resolve().as_posix()}/datos"\n')
    git("add", "-A")
    assert len(check_paths(repo)) == 1


def test_untracked_but_not_ignored_files_are_checked(repo: Path) -> None:
    write(repo, "nuevo.md", f"{_HOME}\n")
    assert len(check_paths(repo)) == 1


def test_ignored_files_are_skipped(repo: Path) -> None:
    write(repo, ".gitignore", "local/\n")
    write(repo, "local/notas.md", f"{_HOME}\n")
    assert check_paths(repo) == []


def test_binary_files_are_skipped(repo: Path, git: Git) -> None:
    (repo / "imagen.png").write_bytes(b"\x89PNG\x00" + _HOME.encode())
    git("add", "-A")
    assert check_paths(repo) == []


@pytest.mark.skipif(os.name == "nt", reason="crear enlaces simbólicos en Windows exige permisos")
def test_symlink_is_rejected(repo: Path, git: Git, capsys: pytest.CaptureFixture[str]) -> None:
    write(repo, "AGENTS.md", "instrucciones\n")
    (repo / "CLAUDE.md").symlink_to("AGENTS.md")
    git("add", "-A")
    errors = check_paths(repo)
    assert len(errors) == 1
    assert "CLAUDE.md" in errors[0]
    assert "simbólico" in errors[0]
    assert main(["--root", str(repo)]) == 1
    assert "CLAUDE.md" in capsys.readouterr().err


def test_symlink_in_index_is_rejected_even_if_checked_out_as_file(repo: Path, git: Git) -> None:
    blob = git("hash-object", "-w", "--stdin", input_text="AGENTS.md")
    git("update-index", "--add", "--cacheinfo", f"120000,{blob.strip()},enlace.md")
    errors = check_paths(repo)
    assert any("enlace.md" in e for e in errors)
