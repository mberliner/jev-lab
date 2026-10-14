"""Contrato de YamlSpecLoader y YamlRecordingLibrary (research.md R10, contracts/recording.md)."""

import shutil
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from jevlab.adapters.yaml_files import YamlRecordingLibrary, YamlSpecLoader
from tests.builders import PRIORITY, QUEUE, REQUEST, URGENCY, recording

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
    spec = YamlSpecLoader().load_request("soporte/triaje")

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
    assert YamlSpecLoader(tmp_path).load_request("soporte/triaje").queue.name == "cola-destino"


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
