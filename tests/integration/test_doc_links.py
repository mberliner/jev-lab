"""US4: los enlaces relativos de la documentación para personas apuntan a archivos existentes."""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
DOCS = (
    "README.md",
    "docs/setup.md",
    "docs/lessons/000-metodo-sdd-y-entorno-reproducible.md",
)
_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_EXTERNAL = ("http://", "https://", "mailto:", "#")


@pytest.mark.parametrize("doc", DOCS)
def test_relative_links_point_to_existing_files(doc: str) -> None:
    path = ROOT / doc
    targets = _LINK.findall(path.read_text(encoding="utf-8"))
    relative = [t.split("#", 1)[0] for t in targets if not t.startswith(_EXTERNAL)]
    broken = [t for t in relative if not (path.parent / t).exists()]
    assert broken == []
