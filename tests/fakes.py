"""Fakes en memoria de los puertos (docs/standards/architecture.md §3)."""

from dataclasses import dataclass, field
from datetime import date

from jevlab.domain.decision_spec import TriageSpec
from jevlab.domain.examples import Exchange, Recording
from jevlab.domain.triage import TriageAnswers
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


@dataclass
class FakeJudge:
    """Responde lo programado para cada texto (o `default`) y registra las llamadas."""

    default: TriageAnswers | None = None
    by_text: dict[str, TriageAnswers] = field(default_factory=dict)
    exchanges: dict[str, Exchange] = field(default_factory=dict)
    error: Exception | None = None
    calls: list[tuple[TriageSpec, str]] = field(default_factory=list)
    last: str | None = None

    def ask(self, spec: TriageSpec, ticket: str) -> TriageAnswers:
        self.calls.append((spec, ticket))
        if self.error is not None:
            raise self.error
        answers = self.by_text.get(ticket, self.default)
        if answers is None:
            raise AssertionError("FakeJudge sin respuesta programada para ese texto")
        self.last = ticket
        return answers

    def last_exchange(self) -> Exchange | None:
        return None if self.last is None else self.exchanges.get(self.last)


@dataclass
class InMemoryRecordingLibrary:
    recordings: list[Recording] = field(default_factory=list)

    def all(self) -> list[Recording]:
        return sorted(self.recordings, key=lambda r: r.name)

    def save(self, recording: Recording) -> None:
        self.recordings = [r for r in self.recordings if r.name != recording.name] + [recording]


@dataclass
class FrozenClock:
    day: date = date(2026, 10, 20)

    def today(self) -> date:
        return self.day


@dataclass
class StaticSpecLoader:
    spec: TriageSpec
    requested: list[str] = field(default_factory=list)

    def load_request(self, name: str) -> TriageSpec:
        self.requested.append(name)
        return self.spec
