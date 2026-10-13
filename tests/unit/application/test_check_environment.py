import pytest

from jevlab.application.check_environment import CheckEnvironment
from jevlab.domain.diagnostics import (
    CheckResult,
    CheckStatus,
    ProviderRejected,
    ProviderUnavailable,
    Scope,
)
from jevlab.ports.environment import PythonInfo
from tests.fakes import FakeGeneratorProbe, FakeLocalEnvironment, FakeModelCatalog


def _run(
    remote: bool = False,
    local: FakeLocalEnvironment | None = None,
    catalog: FakeModelCatalog | None = None,
    generator: FakeGeneratorProbe | None = None,
) -> dict[str, CheckResult]:
    use_case = CheckEnvironment(
        local=local or FakeLocalEnvironment(),
        catalog=catalog or FakeModelCatalog(),
        generator=generator or FakeGeneratorProbe(),
    )
    report = use_case.run(remote=remote)
    return {r.name: r for r in report.results}


def test_results_come_in_fixed_order() -> None:
    use_case = CheckEnvironment(
        local=FakeLocalEnvironment(), catalog=FakeModelCatalog(), generator=FakeGeneratorProbe()
    )
    report = use_case.run(remote=True)

    assert [r.name for r in report.results] == [
        "speckit-python",
        "project-python",
        "env-keys",
        "typesafe",
        "azure",
    ]
    assert report.remote_requested is True
    assert report.exit_code() == 0


def test_without_remote_no_provider_is_called() -> None:
    catalog, generator = FakeModelCatalog(), FakeGeneratorProbe()
    use_case = CheckEnvironment(local=FakeLocalEnvironment(), catalog=catalog, generator=generator)

    report = use_case.run(remote=False)

    assert [r.scope for r in report.results] == [Scope.LOCAL] * 3
    assert catalog.calls == 0
    assert generator.calls == 0


def test_complete_local_environment_is_ok() -> None:
    results = _run()
    assert all(r.status is CheckStatus.OK for r in results.values())
    assert "3.8.10" in results["speckit-python"].detail
    assert "5.3.1" in results["speckit-python"].detail
    assert "3.13.11" in results["project-python"].detail


def test_missing_python3_fails_with_link_instructions() -> None:
    local = FakeLocalEnvironment(speckit=PythonInfo(executable="python3"))
    result = _run(local=local)["speckit-python"]
    assert result.status is CheckStatus.FAIL
    assert result.fix is not None
    assert "python3.exe" in result.fix


def test_old_python3_fails() -> None:
    old = PythonInfo(executable="python3", version=(3, 7, 3), yaml_version="5.1")
    result = _run(local=FakeLocalEnvironment(speckit=old))["speckit-python"]
    assert result.status is CheckStatus.FAIL
    assert "3.7.3" in result.detail


def test_python3_without_yaml_fails_with_pyyaml_instructions() -> None:
    no_yaml = PythonInfo(executable="python3", version=(3, 8, 10))
    result = _run(local=FakeLocalEnvironment(speckit=no_yaml))["speckit-python"]
    assert result.status is CheckStatus.FAIL
    assert result.fix is not None
    assert "PyYAML" in result.fix
    assert "SPECKIT_PYTHON_EXECUTABLE" in result.fix


def test_yaml_through_override_is_ok_and_reported() -> None:
    info = PythonInfo(
        executable="python3", version=(3, 8, 10), yaml_version="6.0.3", yaml_via_override=True
    )
    result = _run(local=FakeLocalEnvironment(speckit=info))["speckit-python"]
    assert result.status is CheckStatus.OK
    assert "SPECKIT_PYTHON_EXECUTABLE" in result.detail


def test_wrong_project_python_fails_with_uv_sync() -> None:
    result = _run(local=FakeLocalEnvironment(project=(3, 12, 1)))["project-python"]
    assert result.status is CheckStatus.FAIL
    assert result.fix is not None
    assert "uv sync" in result.fix


def test_missing_keys_are_named_without_values() -> None:
    local = FakeLocalEnvironment(missing_keys=["AZURE_OPENAI_API_KEY", "TYPESAFE_API_KEY"])
    result = _run(local=local)["env-keys"]
    assert result.status is CheckStatus.FAIL
    assert "AZURE_OPENAI_API_KEY" in result.detail
    assert "TYPESAFE_API_KEY" in result.detail
    assert result.fix is not None
    assert ".env.example" in result.fix


def test_typesafe_lists_models() -> None:
    result = _run(remote=True)["typesafe"]
    assert result.status is CheckStatus.OK
    assert "jev-1.13" in result.detail


@pytest.mark.parametrize("default", ["jev-1.13", "jev-latest", "jev-preview"])
def test_default_model_in_list_or_documented_alias_is_ok(default: str) -> None:
    catalog = FakeModelCatalog(models=["jev-1.13"], default=default)
    assert _run(remote=True, catalog=catalog)["typesafe"].status is CheckStatus.OK


def test_unknown_default_model_fails() -> None:
    catalog = FakeModelCatalog(models=["jev-1.13"], default="jev-0.1")
    result = _run(remote=True, catalog=catalog)["typesafe"]
    assert result.status is CheckStatus.FAIL
    assert "jev-0.1" in result.detail
    assert result.fix is not None
    assert "TYPESAFE_DEFAULT_MODEL" in result.fix


def test_empty_model_list_fails() -> None:
    result = _run(remote=True, catalog=FakeModelCatalog(models=[]))["typesafe"]
    assert result.status is CheckStatus.FAIL


@pytest.mark.parametrize("name", ["typesafe", "azure"])
def test_unavailable_provider_is_reported_as_unavailable(name: str) -> None:
    error = ProviderUnavailable("sin conexión")
    results = _run(
        remote=True,
        catalog=FakeModelCatalog(error=error),
        generator=FakeGeneratorProbe(error=error),
    )
    result = results[name]
    assert result.status is CheckStatus.UNAVAILABLE
    assert result.fix is not None
    assert "--remote" in result.fix


@pytest.mark.parametrize(
    ("status", "hint"),
    [
        (401, "TYPESAFE_API_KEY"),
        (403, "TYPESAFE_API_KEY"),
        (404, "TYPESAFE_DEFAULT_MODEL"),
        (None, "TYPESAFE_API_KEY"),
        (400, "400"),
    ],
)
def test_typesafe_rejection_fix_depends_on_status(status: int | None, hint: str) -> None:
    catalog = FakeModelCatalog(error=ProviderRejected(status))
    result = _run(remote=True, catalog=catalog)["typesafe"]
    assert result.status is CheckStatus.FAIL
    assert result.fix is not None
    assert hint in result.fix + result.detail


@pytest.mark.parametrize(
    ("status", "hint"),
    [
        (401, "AZURE_OPENAI_API_KEY"),
        (403, "AZURE_OPENAI_API_KEY"),
        (404, "AZURE_OPENAI_DEPLOYMENT"),
        (None, "AZURE_OPENAI_ENDPOINT"),
        (400, "400"),
    ],
)
def test_azure_rejection_fix_depends_on_status(status: int | None, hint: str) -> None:
    generator = FakeGeneratorProbe(error=ProviderRejected(status))
    result = _run(remote=True, generator=generator)["azure"]
    assert result.status is CheckStatus.FAIL
    assert result.fix is not None
    assert hint in result.fix + result.detail


def test_azure_ok_when_deployment_answers() -> None:
    assert _run(remote=True)["azure"].status is CheckStatus.OK
