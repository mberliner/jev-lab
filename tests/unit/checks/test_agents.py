from pathlib import Path

import pytest

from checks.agents import check_agents, main
from tests.unit.checks.conftest import write


@pytest.mark.parametrize("content", ["@AGENTS.md\n", "@AGENTS.md", "\n@AGENTS.md\n\n"])
def test_claude_md_with_only_the_import_passes(tmp_path: Path, content: str) -> None:
    write(tmp_path, "CLAUDE.md", content)
    assert check_agents(tmp_path) == []
    assert main(["--root", str(tmp_path)]) == 0


@pytest.mark.parametrize(
    "content", ["@AGENTS.md\nUsa siempre pytest.\n", "Reglas propias\n", "@OTRO.md\n", ""]
)
def test_any_other_content_fails(tmp_path: Path, content: str) -> None:
    write(tmp_path, "CLAUDE.md", content)
    errors = check_agents(tmp_path)
    assert len(errors) == 1
    assert "CLAUDE.md" in errors[0]
    assert "ADR-0002" in errors[0]


def test_missing_claude_md_fails(tmp_path: Path) -> None:
    assert check_agents(tmp_path)
    assert main(["--root", str(tmp_path)]) == 1
