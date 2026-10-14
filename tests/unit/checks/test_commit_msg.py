from pathlib import Path

import pytest

from checks.commit_msg import check_message, main
from tests.unit.checks.conftest import Git, write


@pytest.mark.parametrize(
    "message",
    [
        "feat(presets): añadir jevlab-arch",
        "docs: corregir enlaces",
        "fix(cli)!: cambiar el código de salida\n\nBREAKING CHANGE: ahora sale con 2",
        "chore(spec-001): ordenar\n\n- viñeta uno\n- viñeta dos\n",
        "test(domain): propiedades\n# comentario de git que se ignora\n",
    ],
)
def test_valid_messages_pass(message: str) -> None:
    assert check_message(message) == []


@pytest.mark.parametrize(
    "message",
    [
        "Actualizo varias cosas",
        "feature(cli): tipo inválido",
        "feat(cli) falta los dos puntos",
        "feat(cli):sin espacio",
        "feat(): ámbito vacío",
        "",
    ],
)
def test_invalid_header_is_rejected(message: str) -> None:
    errors = check_message(message)
    assert errors
    assert "version-control.md" in errors[0]


@pytest.mark.parametrize(
    "footer",
    ["Co-Authored-By: Agente <a@b.c>", "co-authored-by: x", "Generated with [Herramienta](x)"],
)
def test_agent_attribution_is_rejected(footer: str) -> None:
    errors = check_message(f"feat(cli): algo\n\n{footer}\n")
    assert len(errors) == 1
    assert "§2" in errors[0]


def test_main_reads_message_file(tmp_path: Path) -> None:
    ok = write(tmp_path, "OK_MSG", "docs: texto\n")
    bad = write(tmp_path, "BAD_MSG", "docs: texto\n\nCo-Authored-By: x\n")
    assert main([str(ok)]) == 0
    assert main([str(bad)]) == 1


def test_main_checks_a_range_of_commits(
    repo: Path, git: Git, capsys: pytest.CaptureFixture[str]
) -> None:
    git("config", "user.email", "prueba@example.invalid")
    git("config", "user.name", "Prueba")
    git("commit", "-q", "--allow-empty", "-m", "chore: inicio")
    first = git("rev-parse", "HEAD").strip()
    git("commit", "-q", "--allow-empty", "-m", "docs: bien")
    assert main(["--root", str(repo), "--range", f"{first}..HEAD"]) == 0
    git("commit", "-q", "--allow-empty", "-m", "mal mensaje")
    assert main(["--root", str(repo), "--range", f"{first}..HEAD"]) == 1
    assert "mal mensaje" in capsys.readouterr().err
    assert main(["--root", str(repo), "--range", "HEAD~1..HEAD"]) == 1


def test_range_from_zero_sha_or_single_rev_checks_whole_history(repo: Path, git: Git) -> None:
    git("config", "user.email", "prueba@example.invalid")
    git("config", "user.name", "Prueba")
    git("commit", "-q", "--allow-empty", "-m", "sin formato")
    git("commit", "-q", "--allow-empty", "-m", "docs: bien")
    assert main(["--root", str(repo), "--range", "0" * 40 + "..HEAD"]) == 1
    assert main(["--root", str(repo), "--range", "HEAD"]) == 1


def test_range_from_unknown_sha_checks_whole_history(repo: Path, git: Git) -> None:
    # Tras un push forzado, el inicio del rango es un commit que ya no existe en el clon.
    git("config", "user.email", "prueba@example.invalid")
    git("config", "user.name", "Prueba")
    git("commit", "-q", "--allow-empty", "-m", "sin formato")
    git("commit", "-q", "--allow-empty", "-m", "docs: bien")
    assert main(["--root", str(repo), "--range", "1" * 40 + "..HEAD"]) == 1


def test_merge_commits_are_skipped(repo: Path, git: Git) -> None:
    git("config", "user.email", "prueba@example.invalid")
    git("config", "user.name", "Prueba")
    git("commit", "-q", "--allow-empty", "-m", "chore: inicio")
    git("checkout", "-q", "-b", "rama")
    git("commit", "-q", "--allow-empty", "-m", "feat: en rama")
    git("checkout", "-q", "-")
    git("commit", "-q", "--allow-empty", "-m", "fix: en principal")
    git("merge", "-q", "--no-ff", "--no-edit", "rama")
    assert main(["--root", str(repo), "--range", "HEAD"]) == 0
