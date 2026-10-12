"""Adaptador del entorno local: `python3` por subproceso, intérprete actual y claves de `.env`."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from jevlab.adapters.settings import ProviderSettings
from jevlab.ports.environment import PythonInfo

# Se ejecuta con el python3 de Spec Kit, que puede ser 3.8. Va en una sola línea porque en Windows
# puede pasar por un lanzador .cmd, y cmd.exe corta los argumentos en el primer salto de línea.
_PROBE = (
    "import json, sys; "
    "y = __import__('yaml').__version__ "
    "if __import__('importlib.util').util.find_spec('yaml') else None; "
    "print(json.dumps({'version': list(sys.version_info[:3]), 'yaml': y}))"
)
_PROBE_TIMEOUT_S = 10
_OVERRIDE_VARS = ("SPECKIT_PYTHON_EXECUTABLE", "SPECKIT_PYTHON")


def _path_outside_venv() -> str:
    """PATH sin la carpeta de ejecutables del entorno virtual activo.

    `uv run` antepone `.venv/bin` (o `.venv\\Scripts`), que tiene su propio `python3`; Spec Kit,
    en cambio, usa el `python3` del sistema.
    """
    path = os.environ.get("PATH", "")
    if sys.prefix == sys.base_prefix:
        return path
    venv_bin = Path(sys.prefix, "Scripts" if sys.platform == "win32" else "bin").resolve()
    kept = [
        entry for entry in path.split(os.pathsep) if entry and Path(entry).resolve() != venv_bin
    ]
    return os.pathsep.join(kept)


def _probe(executable: str) -> tuple[tuple[int, int, int] | None, str | None]:
    resolved = shutil.which(executable, path=_path_outside_venv())
    if resolved is None:
        return None, None
    try:
        completed = subprocess.run(
            [resolved, "-c", _PROBE],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=_PROBE_TIMEOUT_S,
            check=False,
        )
        data = json.loads(completed.stdout.strip().splitlines()[-1])
        major, minor, micro = (int(part) for part in data["version"])
        yaml_version = data["yaml"]
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, IndexError, TypeError):
        return None, None
    return (major, minor, micro), (str(yaml_version) if yaml_version is not None else None)


def _example_keys(path: Path) -> dict[str, str]:
    """Variables de `.env.example` con su valor por defecto (vacío si no lo tiene)."""
    keys: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, _, default = line.partition("=")
            keys[name.strip()] = default.strip()
    return keys


class SystemLocalEnvironment:
    def __init__(self, root: Path, python3: str = "python3") -> None:
        self._root = root
        self._python3 = python3

    def speckit_python(self) -> PythonInfo:
        version, yaml_version = _probe(self._python3)
        info = PythonInfo(executable=self._python3, version=version, yaml_version=yaml_version)
        if version is None or yaml_version is not None:
            return info
        override = next((os.environ[v] for v in _OVERRIDE_VARS if os.environ.get(v)), None)
        if override is None:
            return info
        _, override_yaml = _probe(override)
        if override_yaml is None:
            return info
        return PythonInfo(
            executable=self._python3,
            version=version,
            yaml_version=override_yaml,
            yaml_via_override=True,
        )

    def project_python(self) -> tuple[int, int, int]:
        major, minor, micro = sys.version_info[:3]
        return major, minor, micro

    def missing_env_keys(self) -> list[str]:
        example = self._root / ".env.example"
        if not example.is_file():
            return [".env.example"]
        settings = ProviderSettings(_env_file=self._root / ".env")  # type: ignore[call-arg]
        from_file = {name.upper(): str(value) for name, value in settings.model_dump().items()}
        missing = []
        for name, default in _example_keys(example).items():
            value = os.environ.get(name) or from_file.get(name) or default
            if not value.strip():
                missing.append(name)
        return missing
