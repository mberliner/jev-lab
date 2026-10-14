"""Fixtures comunes a varias capas de tests."""

import pytest

from jevlab.adapters.yaml_files import YamlRecordingLibrary
from jevlab.domain.examples import Recording

# Las grabaciones reales llegan con T031 de la spec 001, que necesita TYPESAFE_API_KEY. Hasta
# entonces, los tests que las leen se saltan con este motivo, visible en el resumen de pytest.
PENDING_RECORDINGS = "sin grabaciones reales todavía: pendiente `uv run poe record` (T031 de 001)"


@pytest.fixture
def real_recordings() -> list[Recording]:
    recordings = YamlRecordingLibrary().all()
    if not recordings:
        pytest.skip(PENDING_RECORDINGS)
    return recordings
