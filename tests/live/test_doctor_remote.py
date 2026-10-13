"""Humo `live` de `jevlab doctor --remote` con las claves reales de `.env`."""

import pytest
from typer.testing import CliRunner

from jevlab.adapters.settings import ProviderSettings
from jevlab.entrypoints.cli.main import app

_REQUIRED = (
    "typesafe_api_key",
    "azure_openai_endpoint",
    "azure_openai_api_key",
    "azure_openai_deployment",
    "azure_openai_api_version",
)


@pytest.mark.live(max_usd=0.01)
def test_doctor_remote_with_real_keys() -> None:
    settings = ProviderSettings()
    missing = [name.upper() for name in _REQUIRED if not getattr(settings, name).strip()]
    if missing:
        pytest.skip("faltan claves en .env: " + ", ".join(missing))

    result = CliRunner().invoke(app, ["doctor", "--remote"])

    assert result.exit_code == 0, result.output
    assert "[ok]   typesafe" in result.output
    assert "[ok]   azure" in result.output
