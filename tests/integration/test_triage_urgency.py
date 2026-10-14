"""US2: urgencia explícita con adaptadores reales y grabaciones reales."""

import pytest
from typer.testing import CliRunner

from jevlab.domain.examples import Recording
from jevlab.entrypoints.cli.main import app

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("example", "word"),
    [("servicio-caido", "sí"), ("cobro-duplicado", "no"), ("urgencia-ambigua", "incierto")],
)
def test_urgency_verdict(real_recordings: list[Recording], example: str, word: str) -> None:
    result = CliRunner().invoke(app, ["triage", "--ejemplo", example])

    assert result.exit_code == 0, result.output
    assert f"Urgencia explícita: {word} · probabilidad " in result.stdout
    assert "  incierto entre 0,30 y 0,70 (provisional)" in result.stdout
