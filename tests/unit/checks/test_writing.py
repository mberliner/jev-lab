from pathlib import Path

import pytest

from checks.writing import check_text, main
from tests.unit.checks.conftest import write

FENCE = "`" * 3


def test_plain_text_passes() -> None:
    assert check_text("doc.md", "# Titulo\n\nTexto con -> y [hecho].\n") == []


@pytest.mark.parametrize("symbol", ["✅", "⏳", "⚠️", "\U0001f680", "★"])
def test_emoji_is_rejected_with_rule_file_and_line(symbol: str) -> None:
    errors = check_text("docs/x.md", f"linea uno\nestado {symbol} hecho\n")
    assert len(errors) == 1
    assert errors[0].startswith("docs/x.md:2: ")
    assert "writing.md" in errors[0]
    assert "emoji" in errors[0]


def test_emoji_is_rejected_inside_code_blocks_too() -> None:
    text = f"{FENCE}\n✅\n{FENCE}\n"
    assert len(check_text("x.md", text)) == 1


@pytest.mark.parametrize("symbol", ["→", "─", "│", "▼", "←"])
def test_box_and_arrow_outside_code_block_are_rejected(symbol: str) -> None:
    errors = check_text("x.md", f"a {symbol} b\n")
    assert len(errors) == 1
    assert errors[0].startswith("x.md:1: ")
    assert "writing.md" in errors[0]


@pytest.mark.parametrize("symbol", ["→", "─", "│", "▼", "┌"])
def test_box_and_arrow_inside_code_block_are_accepted(symbol: str) -> None:
    text = f"antes\n{FENCE}text\na {symbol} b\n{FENCE}\ndespues\n"
    assert check_text("x.md", text) == []


def test_indented_and_tilde_fences_count_as_code_blocks() -> None:
    text = "- lista\n  ~~~\n  a → b\n  ~~~\n"
    assert check_text("x.md", text) == []


def test_after_closing_fence_the_rule_applies_again() -> None:
    text = f"{FENCE}\na → b\n{FENCE}\nc → d\n"
    errors = check_text("x.md", text)
    assert len(errors) == 1
    assert errors[0].startswith("x.md:4: ")


def test_main_skips_generated_and_excluded_files(repo: Path) -> None:
    write(repo, "docs/ok.md", "texto\n")
    write(repo, ".specify/templates/t.md", "✅\n")
    write(repo, ".claude/skills/s/SKILL.md", "✅\n")
    write(repo, ".agents/skills/s/SKILL.md", "✅\n")
    write(repo, "docs/standards/writing.md", "✅\n")
    assert main(["--root", str(repo)]) == 0


def test_main_reports_violations(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(repo, "README.md", "hola ✅\n")
    assert main(["--root", str(repo)]) == 1
    assert "README.md:1:" in capsys.readouterr().err
