"""US3: prioridad y umbral con adaptadores reales y grabaciones reales."""

import pytest
from typer.testing import CliRunner

from jevlab.domain.examples import Recording
from jevlab.entrypoints.cli.main import app

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("example", "verdict"), [("servicio-caido", "alcanzado"), ("cambio-de-correo", "no alcanzado")]
)
def test_priority_threshold(real_recordings: list[Recording], example: str, verdict: str) -> None:
    result = CliRunner().invoke(app, ["triage", "--ejemplo", example])

    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    assert any(line.startswith("Prioridad: más probable ") for line in lines)
    assert [line.split()[1] for line in lines if line[:4] in {"  0 ", "  1 ", "  2 ", "  3 "}] == [
        "baja",
        "media",
        "alta",
        "critica",
    ]
    assert any(line.startswith(f"  umbral alta (provisional): {verdict} · ") for line in lines)
    assert "%" not in result.stdout
