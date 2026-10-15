"""Definiciones, política y grabaciones en YAML dentro del paquete (research R10 de la 001, R3 de
la 002).

Solo leen, escriben y traducen nombres; validar es cosa del dominio.
"""

from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any

import yaml
from pydantic import TypeAdapter

from jevlab.domain.decision_spec import DecisionSpec, RequestSpec, ResolvedRequest
from jevlab.domain.diagnostics import InvalidPolicy
from jevlab.domain.examples import Recording
from jevlab.domain.policy import Policy, parse_policy

_DECISION: TypeAdapter[DecisionSpec] = TypeAdapter(DecisionSpec)
_SYNTHETIC = "sintetico"


def _read(path: Traversable) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class YamlSpecLoader:
    def __init__(self, root: Traversable | None = None) -> None:
        self._root = root if root is not None else files("jevlab") / "specs"

    def load_request(self, name: str) -> ResolvedRequest:
        """`name` es `<dominio>/<petición>`; las decisiones viven en la misma carpeta."""
        domain, request_name = name.split("/")
        folder = self._root / domain
        request = RequestSpec.model_validate(
            _read(folder / f"{request_name}.yaml") | {"name": request_name}
        )
        decisions = {
            decision: _DECISION.validate_python(
                _read(folder / f"{decision}.yaml") | {"name": decision}
            )
            for decision in request.questions.values()
        }
        return ResolvedRequest.resolve(request, decisions)


class YamlPolicyLoader:
    """Lee la política del paquete o la de otro archivo (`--politica`); el dominio la valida."""

    def __init__(self, default: Traversable | None = None) -> None:
        self._default = (
            default if default is not None else files("jevlab") / "policies/soporte/enrutado.yaml"
        )

    def load(self, path: Path | None) -> Policy:
        source: Traversable = self._default if path is None else path
        try:
            data = _read(source)
        except (OSError, UnicodeDecodeError, yaml.YAMLError):
            raise InvalidPolicy.unreadable(str(source)) from None
        return parse_policy(data, source.name)


class YamlRecordingLibrary:
    def __init__(self, root: Traversable | None = None) -> None:
        self._root = root if root is not None else files("jevlab") / "recordings/soporte/triaje"

    @classmethod
    def packaged(cls, request: str, domain: str = "soporte") -> "YamlRecordingLibrary":
        """Las grabaciones de una petición del paquete: `recordings/<dominio>/<petición>`."""
        return cls(files("jevlab") / "recordings" / domain / request)

    def all(self) -> list[Recording]:
        if not self._root.is_dir():
            return []
        paths = sorted(
            (p for p in self._root.iterdir() if p.name.endswith(".yaml")), key=lambda p: p.name
        )
        return [self._load(path) for path in paths]

    def save(self, recording: Recording) -> None:
        if not isinstance(self._root, Path):
            raise TypeError("solo se graba en una carpeta del sistema de archivos")
        data = recording.model_dump(mode="json")
        content = {
            "name": data["name"],
            "text": data["text"],
            "origen": _SYNTHETIC,
            "covers": data["covers"],
            "model": data["model"],
            "recorded_on": recording.recorded_on,
            "spec_versions": data["spec_versions"],
            "request": data["request"],
            "response": data["response"],
        }
        self._root.mkdir(parents=True, exist_ok=True)
        with (self._root / f"{recording.name}.yaml").open("w", encoding="utf-8", newline="\n") as f:
            yaml.safe_dump(content, f, allow_unicode=True, sort_keys=False, width=100)

    def _load(self, path: Traversable) -> Recording:
        data = _read(path)
        stem = path.name.removesuffix(".yaml")
        if data.get("name") != stem:
            raise ValueError(f"{path.name}: el nombre no coincide con el archivo ({stem})")
        origin = data.pop("origen", None)
        if origin != _SYNTHETIC:
            raise ValueError(f"{path.name}: origen {origin!r}; esta feature solo admite sintetico")
        return Recording.model_validate(data | {"synthetic": True})
