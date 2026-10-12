"""US1: la CLI arranca sin claves ni .env (escenario principal)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

_PROVIDER_PREFIXES = ("TYPESAFE_", "AZURE_OPENAI_")


def test_cli_starts_without_keys_or_env_file(tmp_path: Path) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith(_PROVIDER_PREFIXES)}

    result = subprocess.run(
        [sys.executable, "-m", "jevlab", "--version"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert not (tmp_path / ".env").exists()
