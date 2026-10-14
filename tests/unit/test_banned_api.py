"""La regla TID251 de ruff prohíbe reloj, azar e IDs fuera de adaptadores y tests (research.md R8)."""

import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]

_SNIPPETS = [
    "import datetime\n\nNOW = datetime.datetime.now()\n",
    "from datetime import date\n\nTODAY = date.today()\n",
    "import time\n\nNOW = time.time()\n",
    "import random\n\nVALUE = random.random()\n",
    "import uuid\n\nID = uuid.uuid4()\n",
]


def _ruff(code: str, path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--no-cache", "--select", "TID251"]
        + ["--stdin-filename", path, "-"],
        input=code,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=_ROOT,
        check=False,
    )


@pytest.mark.parametrize("code", _SNIPPETS)
def test_rule_fires_in_domain(code: str) -> None:
    result = _ruff(code, "src/jevlab/domain/x.py")

    assert result.returncode == 1
    assert "TID251" in result.stdout


@pytest.mark.parametrize("path", ["src/jevlab/adapters/x.py", "tests/x.py"])
@pytest.mark.parametrize("code", _SNIPPETS)
def test_rule_is_ignored_in_adapters_and_tests(code: str, path: str) -> None:
    result = _ruff(code, path)

    assert result.returncode == 0, result.stdout
