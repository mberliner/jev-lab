"""Puerto del entorno local que comprueba `jevlab doctor`."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PythonInfo:
    """Lo que se sabe del `python3` de Spec Kit; `version` es None si no existe o no responde."""

    executable: str
    version: tuple[int, int, int] | None = None
    yaml_version: str | None = None
    yaml_via_override: bool = False


class LocalEnvironment(Protocol):
    def speckit_python(self) -> PythonInfo: ...

    def project_python(self) -> tuple[int, int, int]: ...

    def missing_env_keys(self) -> list[str]: ...
