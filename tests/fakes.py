"""Fakes en memoria de los puertos (docs/standards/architecture.md §3)."""

from dataclasses import dataclass, field

from jevlab.ports.environment import PythonInfo


@dataclass
class FakeLocalEnvironment:
    speckit: PythonInfo = field(
        default_factory=lambda: PythonInfo(
            executable="python3", version=(3, 8, 10), yaml_version="5.3.1"
        )
    )
    project: tuple[int, int, int] = (3, 13, 11)
    missing_keys: list[str] = field(default_factory=list)

    def speckit_python(self) -> PythonInfo:
        return self.speckit

    def project_python(self) -> tuple[int, int, int]:
        return self.project

    def missing_env_keys(self) -> list[str]:
        return list(self.missing_keys)


@dataclass
class FakeModelCatalog:
    """Devuelve la lista programada o lanza el error programado."""

    models: list[str] = field(default_factory=lambda: ["jev-1.13", "jev-latest"])
    default: str = "jev-latest"
    error: Exception | None = None
    calls: int = 0

    def list_models(self) -> list[str]:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return list(self.models)

    def default_model(self) -> str:
        return self.default


@dataclass
class FakeGeneratorProbe:
    error: Exception | None = None
    calls: int = 0

    def ping(self) -> None:
        self.calls += 1
        if self.error is not None:
            raise self.error
