"""Contrato de YamlSpecLoader y YamlRecordingLibrary (research.md R10, contracts/recording.md)."""

import shutil
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from jevlab.adapters.yaml_files import YamlPolicyLoader, YamlRecordingLibrary, YamlSpecLoader
from jevlab.domain.decision_spec import RouteSpec, TriageSpec
from jevlab.domain.diagnostics import InvalidPolicy
from jevlab.domain.policy import ActionName, Risk
from tests.builders import POLICY, PRIORITY, QUEUE, REQUEST, URGENCY, recording

_FIXTURES = Path(__file__).parent / "fixtures"


def _write_specs(root: Path, **queue_overrides: object) -> None:
    folder = root / "soporte"
    folder.mkdir(parents=True)
    for data in (QUEUE | queue_overrides, URGENCY, PRIORITY, REQUEST):
        name = data["name"]
        content = {k: v for k, v in data.items() if k != "name"}
        (folder / f"{name}.yaml").write_text(
            yaml.safe_dump(content, allow_unicode=True), encoding="utf-8"
        )


def test_loads_the_real_triage_request() -> None:
    spec = TriageSpec.from_request(YamlSpecLoader().load_request("soporte/triaje"))

    assert spec.model == "jev-1.13.0"
    assert spec.max_chars == 4000
    assert list(spec.queue.options) == ["facturacion", "tecnico", "cuenta", "other"]
    assert spec.urgency.uncertain_band.justification == "provisional"
    assert spec.priority.threshold.level == "alta"
    assert set(spec.spec_versions()) == {
        "triaje",
        "cola-destino",
        "urgencia-explicita",
        "prioridad",
    }


def test_loads_from_another_root(tmp_path: Path) -> None:
    _write_specs(tmp_path)
    resolved = YamlSpecLoader(tmp_path).load_request("soporte/triaje")
    assert resolved.questions()["cola"].name == "cola-destino"


def test_invalid_definition_is_a_domain_validation_error(tmp_path: Path) -> None:
    _write_specs(tmp_path, escape="ninguna")
    with pytest.raises(ValidationError):
        YamlSpecLoader(tmp_path).load_request("soporte/triaje")


def test_reads_synthetic_recording_fixture(tmp_path: Path) -> None:
    shutil.copy(_FIXTURES / "grabacion-sintetica.yaml", tmp_path)

    [loaded] = YamlRecordingLibrary(tmp_path).all()

    assert loaded.name == "grabacion-sintetica"
    assert loaded.synthetic is True
    assert loaded.recorded_on.isoformat() == "2026-10-20"
    assert loaded.covers == ("cola-facturacion", "urgencia-no")


def test_save_and_all_round_trip_in_utf8(tmp_path: Path) -> None:
    library = YamlRecordingLibrary(tmp_path)
    original = recording(text="Cobro duplicado en el señor Muñoz.")

    library.save(original)

    path = tmp_path / "cobro-duplicado.yaml"
    raw = path.read_text(encoding="utf-8")
    assert "origen: sintetico" in raw
    assert "synthetic" not in raw
    assert "Muñoz" in raw
    assert library.all() == [original]


def test_other_origin_is_a_read_error(tmp_path: Path) -> None:
    content = (_FIXTURES / "grabacion-sintetica.yaml").read_text(encoding="utf-8")
    (tmp_path / "grabacion-sintetica.yaml").write_text(
        content.replace("origen: sintetico", "origen: real"), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="origen"):
        YamlRecordingLibrary(tmp_path).all()


def test_file_name_must_match_recording_name(tmp_path: Path) -> None:
    shutil.copy(_FIXTURES / "grabacion-sintetica.yaml", tmp_path / "otro-nombre.yaml")
    with pytest.raises(ValueError, match="otro-nombre"):
        YamlRecordingLibrary(tmp_path).all()


def test_loads_the_real_route_request() -> None:
    spec = RouteSpec.from_request(YamlSpecLoader().load_request("soporte/enrutado"))

    assert spec.model == "jev-1.13.0"
    assert spec.max_chars == 4000
    assert list(spec.request_kind.options) == ["reembolso", "consulta", "incidencia", "other"]
    assert spec.request_kind.escape == "other"
    assert spec.spec_versions() == {
        "enrutado": "0.1.0",
        "cola-destino": "0.1.0",
        "solicitud": "0.1.0",
    }


def test_triage_and_route_share_one_queue_definition() -> None:
    loader = YamlSpecLoader()
    triage = loader.load_request("soporte/triaje").questions()["cola"]
    route = loader.load_request("soporte/enrutado").questions()["cola"]
    assert triage == route


def test_recording_library_per_request(tmp_path: Path) -> None:
    packaged = YamlRecordingLibrary.packaged("enrutado")
    assert all(r.spec_versions.get("enrutado") for r in packaged.all())

    library = YamlRecordingLibrary(tmp_path / "soporte" / "enrutado")
    original = recording(name="reembolso-ambiguo", covers=("reembolso-pendiente",))
    library.save(original)
    assert library.all() == [original]


def _write_policy(path: Path, data: object) -> Path:
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return path


def test_loads_the_real_policy() -> None:
    policy = YamlPolicyLoader().load(None)

    move = policy.action(ActionName.MOVER_A_COLA)
    refund = policy.action(ActionName.REEMBOLSAR)
    assert policy.version == "0.1.0"
    assert (move.riesgo, move.umbral, move.provisional) == (Risk.BAJO, 0.90, True)
    assert (refund.riesgo, refund.umbral, refund.provisional) == (Risk.ALTO, 0.97, True)


def test_loads_a_policy_by_path(tmp_path: Path) -> None:
    data = POLICY | {"version": "0.2.0"}
    policy = YamlPolicyLoader().load(_write_policy(tmp_path / "politica.yaml", data))
    assert policy.version == "0.2.0"


def test_comments_and_line_endings_do_not_change_the_fingerprint(tmp_path: Path) -> None:
    plain = _write_policy(tmp_path / "a.yaml", POLICY)
    commented = tmp_path / "b.yaml"
    crlf = "\r\n"
    text = "# comentario" + crlf + plain.read_text(encoding="utf-8").replace("\n", crlf)
    commented.write_bytes(text.encode("utf-8"))
    loader = YamlPolicyLoader()
    assert loader.load(plain).fingerprint == loader.load(commented).fingerprint


def test_missing_policy_says_which_file(tmp_path: Path) -> None:
    missing = tmp_path / "no-existe.yaml"
    with pytest.raises(InvalidPolicy) as error:
        YamlPolicyLoader().load(missing)
    assert str(error.value) == f"no se puede leer la política {missing}"


def test_unparsable_policy_is_unreadable(tmp_path: Path) -> None:
    broken = tmp_path / "rota.yaml"
    broken.write_text("version: [0.1.0\nsecreto-del-archivo", encoding="utf-8")
    with pytest.raises(InvalidPolicy) as error:
        YamlPolicyLoader().load(broken)
    assert str(error.value) == f"no se puede leer la política {broken}"
    assert "secreto" not in str(error.value)


def test_invalid_policy_names_file_and_field_without_content(tmp_path: Path) -> None:
    acciones = dict(POLICY["acciones"])
    acciones["reembolsar"] = acciones["reembolsar"] | {"umbral": 0.85}
    path = _write_policy(tmp_path / "laxa.yaml", {"version": "0.1.0", "acciones": acciones})

    with pytest.raises(InvalidPolicy) as error:
        YamlPolicyLoader().load(path)

    assert str(error.value) == (
        "política no válida (laxa.yaml): acciones.reembolsar.umbral 0,85 es menor que el de "
        "mover-a-cola 0,90 con más riesgo"
    )
