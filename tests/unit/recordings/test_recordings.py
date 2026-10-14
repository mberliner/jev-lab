"""Comprobaciones sobre las grabaciones reales (contracts/recording.md, SC-006, FR-012).

Cada grabación se reproduce con la definición actual por el mismo decodificador que en vivo.
"""

import os
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from jevlab.adapters.typesafe_judge import TypeSafeJudge
from jevlab.adapters.yaml_files import YamlSpecLoader
from jevlab.application.triage import TRIAGE_REQUEST
from jevlab.domain.examples import Recording
from jevlab.domain.triage import (
    ESCAPE_REASON,
    Origin,
    OriginMode,
    TriageResult,
    UrgencyVerdict,
    interpret,
)

_FOLDER = Path(__file__).resolve().parents[3] / "src/jevlab/recordings/soporte/triaje"
_AUTH_KEYS = {"authorization", "x-api-key", "api-key", "api_key", "cookie"}

Check = Callable[[TriageResult], bool]

# Lo que declara `covers` y cómo se comprueba con el resultado interpretado.
_COVERS: dict[str, Check] = {
    "cola-facturacion": lambda r: r.queue.assigned == "facturacion",
    "cola-tecnico": lambda r: r.queue.assigned == "tecnico",
    "cola-cuenta": lambda r: r.queue.assigned == "cuenta",
    "cola-other": lambda r: r.queue.abstention_reason == ESCAPE_REASON,
    "urgencia-si": lambda r: r.urgency.verdict is UrgencyVerdict.SI,
    "urgencia-no": lambda r: r.urgency.verdict is UrgencyVerdict.NO,
    "urgencia-incierto": lambda r: r.urgency.verdict is UrgencyVerdict.INCIERTO,
    "prioridad-alcanza-umbral": lambda r: r.priority.reaches_threshold is True,
    "prioridad-no-alcanza-umbral": lambda r: r.priority.reaches_threshold is False,
    "adversarial": lambda r: True,
}

# SC-006: al menos un ejemplo por cola, uno que termina en other y uno por resultado del Noul.
_REQUIRED = (
    "cola-facturacion",
    "cola-tecnico",
    "cola-cuenta",
    "cola-other",
    "urgencia-si",
    "urgencia-no",
    "urgencia-incierto",
)


def _results(recordings: list[Recording]) -> dict[str, TriageResult]:
    spec = YamlSpecLoader().load_request(TRIAGE_REQUEST)
    results = {}
    for recording in recordings:
        # Reproducir con la definición actual falla con RecordingOutdated si cambió.
        with TypeSafeJudge.replay(recording) as judge:
            answers = judge.ask(spec, recording.text)
        origin = Origin(mode=OriginMode.GRABADO, model=recording.model)
        results[recording.name] = interpret(spec, answers, origin)
    return results


def _keys(node: Any) -> set[str]:
    if isinstance(node, dict):
        return {str(k).lower() for k in node} | set().union(*(_keys(v) for v in node.values()))
    if isinstance(node, list):
        return set().union(*(_keys(v) for v in node))
    return set()


def test_metadata_and_origin(real_recordings: list[Recording]) -> None:
    for path in sorted(_FOLDER.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["origen"] == "sintetico", path.name
        assert data["model"], path.name
        assert data["recorded_on"], path.name


def test_no_authentication_material(real_recordings: list[Recording]) -> None:
    secret = os.environ.get("TYPESAFE_API_KEY", "").strip()
    for path in sorted(_FOLDER.glob("*.yaml")):
        raw = path.read_text(encoding="utf-8")
        assert not _keys(yaml.safe_load(raw)) & _AUTH_KEYS, path.name
        assert "bearer " not in raw.lower(), path.name
        if secret:
            assert secret not in raw, path.name


def test_examples_cover_sc_006_and_what_they_declare(real_recordings: list[Recording]) -> None:
    results = _results(real_recordings)

    covered = {tag for tag in _REQUIRED if any(_COVERS[tag](r) for r in results.values())}
    assert covered == set(_REQUIRED), f"faltan: {sorted(set(_REQUIRED) - covered)}"

    for recording in real_recordings:
        missed = [t for t in recording.covers if not _COVERS[t](results[recording.name])]
        if missed:
            warnings.warn(
                f"{recording.name} no cubre lo que declara: {', '.join(missed)}", stacklevel=1
            )
