"""Comprobaciones sobre las grabaciones reales del enrutado (spec 002: FR-014, SC-006; R8).

Cada grabación se reproduce con la definición y la política actuales por el mismo decodificador
que en vivo, y cada etiqueta de `covers` se comprueba sobre el resultado decidido.
"""

import os
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from jevlab.adapters.typesafe_judge import TypeSafeJudge
from jevlab.adapters.yaml_files import YamlPolicyLoader, YamlRecordingLibrary, YamlSpecLoader
from jevlab.application.routing import ROUTE_REQUEST
from jevlab.domain.confidence import choice_confidence
from jevlab.domain.decision_spec import RouteSpec
from jevlab.domain.examples import Recording
from jevlab.domain.policy import ActionName
from jevlab.domain.routing import ActionOutcome, ActionStatus, PendingReason, decide_routing
from jevlab.domain.triage import interpret_queue

_FOLDER = Path(__file__).resolve().parents[3] / "src/jevlab/recordings/soporte/enrutado"
_AUTH_KEYS = {"authorization", "x-api-key", "api-key", "api_key", "cookie"}
_TOLERANCE = 0.01

Actions = dict[ActionName, ActionOutcome]
Check = Callable[[Actions], bool]


def _move(a: Actions) -> ActionOutcome:
    return a[ActionName.MOVER_A_COLA]


def _refund(a: Actions) -> ActionOutcome:
    return a[ActionName.REEMBOLSAR]


# Lo que declara `covers` y cómo se comprueba con la política inicial.
_COVERS: dict[str, Check] = {
    "mover-automatizada": lambda a: _move(a).status is ActionStatus.AUTOMATIZADA,
    "mover-a-revision": lambda a: _move(a).reasons == (PendingReason.BAJO_UMBRAL,),
    "mover-escape": lambda a: _move(a).reasons == (PendingReason.ESCAPE,),
    "reembolso-automatizado": lambda a: _refund(a).status is ActionStatus.AUTOMATIZADA,
    "reembolso-pendiente": lambda a: _refund(a).status is ActionStatus.PENDIENTE,
    "reembolso-abstencion": lambda a: _refund(a).status is ActionStatus.SIN_REEMBOLSO,
    "cola-facturacion-automatizada": lambda a: (
        _move(a).status is ActionStatus.AUTOMATIZADA and _move(a).value == "facturacion"
    ),
    "sin-reembolso-adversarial": lambda a: _refund(a).status is not ActionStatus.AUTOMATIZADA,
}

# SC-006: los casos que la suite tiene que poder reproducir con la política inicial.
_REQUIRED = (
    "mover-automatizada",
    "mover-a-revision",
    "mover-escape",
    "reembolso-automatizado",
    "reembolso-pendiente",
    "reembolso-abstencion",
    "sin-reembolso-adversarial",
)

_MISSING = (
    "no hay grabaciones de enrutado: regrabar con `uv run poe record-route` (necesita `.env`)"
)


@pytest.fixture
def route_recordings() -> list[Recording]:
    recordings = YamlRecordingLibrary.packaged("enrutado").all()
    if not recordings:
        pytest.fail(_MISSING)
    return recordings


def _decide(recordings: list[Recording]) -> dict[str, Actions]:
    request = YamlSpecLoader().load_request(ROUTE_REQUEST)
    spec = RouteSpec.from_request(request)
    policy = YamlPolicyLoader().load(None)
    decided = {}
    for recording in recordings:
        # Reproducir con la definición actual falla con RecordingOutdated si cambió.
        with TypeSafeJudge.replay(recording) as judge:
            answers = judge.ask(request, recording.text)
        actions = decide_routing(
            policy,
            interpret_queue(spec.queue, answers.choice("cola")),
            interpret_queue(spec.request_kind, answers.choice("solicitud")),
        )
        decided[recording.name] = {a.action: a for a in actions}
    return decided


def test_metadata_origin_and_spec_versions(route_recordings: list[Recording]) -> None:
    for path in sorted(_FOLDER.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["origen"] == "sintetico", path.name
        assert data["model"], path.name
        assert data["recorded_on"], path.name
        assert set(data["spec_versions"]) == {"enrutado", "cola-destino", "solicitud"}, path.name


def test_no_authentication_material(route_recordings: list[Recording]) -> None:
    secret = os.environ.get("TYPESAFE_API_KEY", "").strip()
    for path in sorted(_FOLDER.glob("*.yaml")):
        raw = path.read_text(encoding="utf-8")
        assert "headers" not in raw.lower(), path.name
        assert not any(f"{key}:" in raw.lower() for key in _AUTH_KEYS), path.name
        assert "bearer " not in raw.lower(), path.name
        if secret:
            assert secret not in raw, path.name


def test_examples_cover_sc_006_and_what_they_declare(route_recordings: list[Recording]) -> None:
    decided = _decide(route_recordings)

    for recording in route_recordings:
        unknown = set(recording.covers) - set(_COVERS)
        assert not unknown, f"{recording.name}: etiquetas desconocidas {sorted(unknown)}"
        missed = [t for t in recording.covers if not _COVERS[t](decided[recording.name])]
        assert not missed, f"{recording.name} no cubre {missed}"

    covered = {tag for r in route_recordings for tag in r.covers}
    assert set(_REQUIRED) <= covered, f"faltan: {sorted(set(_REQUIRED) - covered)}"


def test_adversarial_examples_never_automate_a_refund(route_recordings: list[Recording]) -> None:
    decided = _decide(route_recordings)
    adversarial = [r for r in route_recordings if "sin-reembolso-adversarial" in r.covers]
    assert {r.name for r in adversarial} >= {"instruccion-incrustada", "reembolso-incrustado"}
    for recording in adversarial:
        assert _refund(decided[recording.name]).status is not ActionStatus.AUTOMATIZADA


def test_shared_texts_match_the_triage_recordings(route_recordings: list[Recording]) -> None:
    triage = {r.name: r.text for r in YamlRecordingLibrary().all()}
    shared = [r for r in route_recordings if r.name in triage]
    assert len(shared) == len(triage)
    for recording in shared:
        assert recording.text == triage[recording.name], recording.name


def test_request_kind_confidence_matches_service(route_recordings: list[Recording]) -> None:
    request = YamlSpecLoader().load_request(ROUTE_REQUEST)
    for recording in route_recordings:
        with TypeSafeJudge.replay(recording) as judge:
            answers = judge.ask(request, recording.text)
        for question in ("cola", "solicitud"):
            answer = answers.choice(question)
            assert answer is not None, (recording.name, question)
            assert choice_confidence(answer.probabilities) == pytest.approx(
                answer.confidence, abs=_TOLERANCE
            ), (recording.name, question)
