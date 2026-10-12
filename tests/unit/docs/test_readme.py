"""README.md para personas (FR-015)."""

import re
from pathlib import Path

import pytest

README = Path(__file__).resolve().parents[3] / "README.md"
SECTIONS = ("Qué es", "Estado", "Inicio rápido", "Mapa de documentos", "Licencia")


def _sections() -> dict[str, str]:
    text = README.read_text(encoding="utf-8")
    parts = re.split(r"^## +(.+)$", text, flags=re.MULTILINE)
    return {title.strip(): body for title, body in zip(parts[1::2], parts[2::2], strict=True)}


@pytest.mark.parametrize("title", SECTIONS)
def test_readme_has_section(title: str) -> None:
    assert title in _sections()


def test_status_links_to_roadmap() -> None:
    assert "(docs/roadmap.md" in _sections()["Estado"]


def test_quick_start_has_three_or_four_commands_and_links_setup() -> None:
    body = _sections()["Inicio rápido"]
    block = re.search(r"```[^\n]*\n(.*?)```", body, flags=re.DOTALL)
    assert block is not None
    commands = [line for line in block.group(1).splitlines() if line.strip()]
    assert 3 <= len(commands) <= 4
    assert "(docs/setup.md" in body


def test_license_section_links_license_file() -> None:
    body = _sections()["Licencia"]
    assert "Apache-2.0" in body
    assert "(LICENSE)" in body


def test_readme_points_agents_to_agents_md() -> None:
    assert "(AGENTS.md)" in README.read_text(encoding="utf-8")
