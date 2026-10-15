"""Ejemplos de enrutado elegidos por su etiqueta de `covers` (research.md R8 de la 002).

Los tests no escriben nombres ni cifras del modelo a mano: buscan el ejemplo que cubre cada caso
y leen su confianza de la grabación.
"""

from jevlab.adapters.typesafe_judge import TypeSafeJudge
from jevlab.adapters.yaml_files import YamlRecordingLibrary, YamlSpecLoader
from jevlab.application.routing import ROUTE_REQUEST
from jevlab.domain.examples import Recording

MISSING = "no hay grabaciones de enrutado: regrabar con `uv run poe record-route` (necesita `.env`)"


def route_recordings() -> list[Recording]:
    recordings = YamlRecordingLibrary.packaged("enrutado").all()
    assert recordings, MISSING
    return recordings


def with_tag(tag: str) -> Recording:
    """El primer ejemplo, por nombre, que declara la etiqueta."""
    for recording in route_recordings():
        if tag in recording.covers:
            return recording
    raise AssertionError(f"ningún ejemplo de enrutado cubre {tag}")


def all_with_tag(tag: str) -> list[Recording]:
    return [r for r in route_recordings() if tag in r.covers]


def queue_confidence(recording: Recording) -> float:
    """Confianza de la cola que devolvió el servicio en esa grabación."""
    request = YamlSpecLoader().load_request(ROUTE_REQUEST)
    with TypeSafeJudge.replay(recording) as judge:
        answer = judge.ask(request, recording.text).choice("cola")
    assert answer is not None
    return answer.confidence
