"""Fixtures comunes a varias capas de tests."""

import pytest

from jevlab.adapters.yaml_files import YamlRecordingLibrary
from jevlab.domain.examples import Recording

# Las grabaciones reales vienen con el paquete desde T031 de la spec 001. Si faltan, los tests que
# las leen fallan: saltarlos dejaría la CI en verde con las grabaciones borradas.
MISSING_RECORDINGS = "no hay grabaciones reales: regrabar con `uv run poe record` (necesita `.env`)"


@pytest.fixture
def real_recordings() -> list[Recording]:
    recordings = YamlRecordingLibrary().all()
    if not recordings:
        pytest.fail(MISSING_RECORDINGS)
    return recordings
