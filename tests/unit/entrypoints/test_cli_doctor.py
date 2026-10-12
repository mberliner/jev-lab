"""Salida y códigos de `jevlab doctor` (specs/000-cimientos/contracts/cli-doctor.md)."""

import pytest
from typer.testing import CliRunner, Result

import jevlab.entrypoints.cli.main as cli
from jevlab.domain.diagnostics import ProviderRejected, ProviderUnavailable
from tests.fakes import FakeGeneratorProbe, FakeLocalEnvironment, FakeModelCatalog

# Valor sintético con forma de clave: el test comprueba que nunca aparece en la salida.
_SECRET = "ts-valor-secreto-0123456789"  # gitleaks:allow


def _invoke(
    monkeypatch: pytest.MonkeyPatch,
    args: list[str],
    local: FakeLocalEnvironment | None = None,
    catalog: FakeModelCatalog | None = None,
    generator: FakeGeneratorProbe | None = None,
) -> Result:
    adapters = (
        local or FakeLocalEnvironment(),
        catalog or FakeModelCatalog(),
        generator or FakeGeneratorProbe(),
    )
    monkeypatch.setattr(cli, "build_adapters", lambda: adapters)
    monkeypatch.setenv("TYPESAFE_API_KEY", _SECRET)
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", _SECRET)
    return CliRunner().invoke(cli.app, args)


def test_all_local_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _invoke(monkeypatch, ["doctor"])

    assert result.exit_code == 0
    lines = result.output.splitlines()
    assert lines[0].startswith("[ok]   speckit-python  ")
    assert lines[1].startswith("[ok]   project-python  ")
    assert lines[2].startswith("[ok]   env-keys        ")
    assert lines[-1] == "Resultado: todo correcto"
    assert len(lines) == 4


def test_missing_key_fails_with_fix_line(monkeypatch: pytest.MonkeyPatch) -> None:
    local = FakeLocalEnvironment(missing_keys=["AZURE_OPENAI_API_KEY"])

    result = _invoke(monkeypatch, ["doctor"], local=local)

    assert result.exit_code == 1
    lines = result.output.splitlines()
    assert lines[2] == "[fail] env-keys        faltan: AZURE_OPENAI_API_KEY"
    assert lines[3].startswith("       arreglo: ")
    assert lines[-1] == "Resultado: 1 falla"


def test_remote_unavailable_shows_nd_and_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    down = ProviderUnavailable("sin conexion")

    result = _invoke(
        monkeypatch,
        ["doctor", "--remote"],
        catalog=FakeModelCatalog(error=down),
        generator=FakeGeneratorProbe(error=down),
    )

    assert result.exit_code == 1
    assert "[n/d]  typesafe        no disponible: sin conexion" in result.output
    assert "[n/d]  azure           no disponible: sin conexion" in result.output
    assert result.output.splitlines()[-1] == "Resultado: 2 no disponibles"


def test_remote_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _invoke(monkeypatch, ["doctor", "--remote"])

    assert result.exit_code == 0
    assert "[ok]   typesafe        " in result.output
    assert "[ok]   azure           " in result.output


def test_mixed_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _invoke(
        monkeypatch,
        ["doctor", "--remote"],
        local=FakeLocalEnvironment(missing_keys=["TYPESAFE_API_KEY"]),
        catalog=FakeModelCatalog(error=ProviderRejected(401)),
        generator=FakeGeneratorProbe(error=ProviderUnavailable("sin conexion")),
    )

    assert result.exit_code == 1
    assert result.output.splitlines()[-1] == "Resultado: 2 fallas, 1 no disponible"


def test_output_is_ascii_and_has_no_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _invoke(
        monkeypatch,
        ["doctor", "--remote"],
        local=FakeLocalEnvironment(missing_keys=["TYPESAFE_API_KEY"]),
        catalog=FakeModelCatalog(error=ProviderRejected(401)),
        generator=FakeGeneratorProbe(error=ProviderRejected(404)),
    )

    assert _SECRET not in result.output
    assert result.output.isascii()


def test_without_remote_providers_are_not_called(monkeypatch: pytest.MonkeyPatch) -> None:
    catalog, generator = FakeModelCatalog(), FakeGeneratorProbe()

    _invoke(monkeypatch, ["doctor"], catalog=catalog, generator=generator)

    assert catalog.calls == 0
    assert generator.calls == 0
