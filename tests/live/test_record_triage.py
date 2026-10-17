"""Grabación de los ejemplos de triaje con TypeSafe real (research.md R11, contracts/recording.md).

Con `JEVLAB_RECORD=1` (`uv run poe record-triage`) escribe en `src/jevlab/recordings/soporte/triaje/`;
sin ella graba en una carpeta temporal y solo comprueba el proceso.

Los tickets son propios y sintéticos; la respuesta es real.
"""

import os
from pathlib import Path

import pytest

from jevlab.adapters.settings import ProviderSettings
from jevlab.adapters.system_clock import SystemClock
from jevlab.adapters.typesafe_judge import TypeSafeJudge
from jevlab.adapters.yaml_files import YamlRecordingLibrary, YamlSpecLoader
from jevlab.application.triage import TRIAGE_REQUEST, RecordExamples
from jevlab.domain.examples import ExampleTicket
from tests.live.examples import TEXTS

_TARGET = Path(__file__).resolve().parents[2] / "src/jevlab/recordings/soporte/triaje"

EXAMPLES = [
    ExampleTicket(
        name="cobro-duplicado",
        text=TEXTS["cobro-duplicado"],
        covers=("cola-facturacion", "urgencia-no"),
    ),
    ExampleTicket(
        name="servicio-caido",
        text=TEXTS["servicio-caido"],
        covers=("cola-tecnico", "urgencia-si", "prioridad-alcanza-umbral"),
    ),
    ExampleTicket(
        name="cambio-de-correo",
        text=TEXTS["cambio-de-correo"],
        covers=("cola-cuenta", "prioridad-no-alcanza-umbral"),
    ),
    ExampleTicket(
        name="pregunta-fuera-de-ambito",
        text=TEXTS["pregunta-fuera-de-ambito"],
        covers=("cola-other",),
    ),
    ExampleTicket(
        name="urgencia-ambigua",
        text=TEXTS["urgencia-ambigua"],
        covers=("urgencia-incierto",),
    ),
    ExampleTicket(
        name="instruccion-incrustada",
        text=TEXTS["instruccion-incrustada"],
        covers=("adversarial",),
    ),
]


@pytest.mark.live(max_usd=0.01)
def test_record_triage_examples(tmp_path: Path) -> None:
    api_key = ProviderSettings().typesafe_api_key.strip()
    if not api_key:
        pytest.skip("falta TYPESAFE_API_KEY en .env")
    target = _TARGET if os.environ.get("JEVLAB_RECORD") == "1" else tmp_path
    library = YamlRecordingLibrary(target)
    spec = YamlSpecLoader().load_request(TRIAGE_REQUEST)

    with TypeSafeJudge.live(api_key, record=True) as judge:
        saved = RecordExamples(judge=judge, library=library, clock=SystemClock()).run(
            spec, EXAMPLES
        )

    assert [r.name for r in library.all()] == sorted(e.name for e in EXAMPLES)
    for recording in saved:
        assert recording.model
        assert recording.response.status == 200
