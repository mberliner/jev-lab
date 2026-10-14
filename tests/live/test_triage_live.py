"""Humo `live` de `jevlab triage --en-vivo` con la clave real de `.env`."""

import pytest
from typer.testing import CliRunner

from jevlab.adapters.settings import ProviderSettings
from jevlab.entrypoints.cli.main import app


@pytest.mark.live(max_usd=0.01)
def test_triage_live_with_real_key() -> None:
    if not ProviderSettings().typesafe_api_key.strip():
        pytest.skip("falta TYPESAFE_API_KEY en .env")

    text = "Me habéis cobrado dos veces la cuota de octubre. ¿Podéis devolverme uno de los cargos?"
    result = CliRunner().invoke(app, ["triage", "--en-vivo", text])

    assert result.exit_code == 0, result.output
    assert result.stdout.startswith("Origen: en vivo · ")
