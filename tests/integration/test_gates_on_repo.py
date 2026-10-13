"""US3: las puertas propias pasan sobre el propio repositorio (escenario principal)."""

from pathlib import Path
from types import ModuleType

import pytest

from checks import agents, commit_msg, paths, presets, writing

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("gate", [writing, presets, paths, agents])
def test_gate_passes_on_this_repository(gate: ModuleType) -> None:
    assert gate.main(["--root", str(ROOT)]) == 0


def test_commit_history_follows_the_convention() -> None:
    assert commit_msg.main(["--root", str(ROOT), "--range", "HEAD"]) == 0
