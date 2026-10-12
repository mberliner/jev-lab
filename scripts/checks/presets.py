"""Puerta de presets: docs/governance.md §5, ADR-0002 y research.md R8.

Lee los archivos versionados; no ejecuta la CLI de Spec Kit. Comprueba:
- la copia instalada de cada preset (`.specify/presets/<id>/`) es igual a su fuente (`presets/<id>/`);
- «Tests are OPTIONAL» no aparece en la plantilla de tareas resuelta ni en las skills de tareas;
- cada skill sustituida por un preset está registrada en los dos agentes y tiene el mismo cuerpo;
- los scripts de `.specify/scripts/bash/` tienen modo 100755 en el índice de Git;
- ninguna skill lanza los scripts con el Python de `.venv/` en vez de `python3`.
"""

import json
from pathlib import Path
from typing import Any

import yaml

from checks._common import git, report, root_parser

AGENTS = {"claude": ".claude/skills", "agy": ".agents/skills"}
FORBIDDEN = "Tests are OPTIONAL"
TASKS_SKILL = "speckit-tasks"
TASKS_TEMPLATE = "tasks-template"
VENV_PYTHONS = (".venv/bin/python", ".venv/Scripts/python")


def _files(directory: Path) -> set[str]:
    return {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}


def _check_copies(root: Path) -> list[str]:
    errors: list[str] = []
    sources = root / "presets"
    if not sources.is_dir():
        return errors
    for source in sorted(p for p in sources.iterdir() if p.is_dir()):
        installed = root / ".specify/presets" / source.name
        where = f".specify/presets/{source.name}"
        if not installed.is_dir():
            errors.append(f"{where}: governance.md §5 (copia instalada): preset sin instalar")
            continue
        source_files, installed_files = _files(source), _files(installed)
        for name in sorted(source_files ^ installed_files):
            side = "falta en la copia instalada" if name in source_files else "sobra"
            errors.append(f"{where}/{name}: governance.md §5 (copia instalada): {side}")
        for name in sorted(source_files & installed_files):
            if (source / name).read_bytes() != (installed / name).read_bytes():
                errors.append(
                    f"{where}/{name}: governance.md §5 (copia instalada): distinta de "
                    f"presets/{source.name}/{name}; reinstala el preset"
                )
    return errors


def _manifest(preset: Path) -> dict[str, Any]:
    data = yaml.safe_load((preset / "preset.yml").read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _tasks_templates(root: Path) -> list[Path]:
    """Capas de la plantilla de tareas resuelta: las de los presets y la base si nadie la sustituye."""
    layers = []
    replaced = False
    installed = root / ".specify/presets"
    presets = sorted(p for p in installed.iterdir() if p.is_dir()) if installed.is_dir() else []
    for preset in presets:
        if not (preset / "preset.yml").is_file():
            continue
        for entry in _manifest(preset).get("provides", {}).get("templates", []):
            if entry.get("type") == "template" and entry.get("name") == TASKS_TEMPLATE:
                layers.append(preset / entry["file"])
                replaced |= entry.get("strategy", "replace") == "replace"
    if not replaced:
        layers.append(root / ".specify/templates/tasks-template.md")
    return layers


def _check_tests_optional(root: Path) -> list[str]:
    errors = []
    skills = [root / directory / TASKS_SKILL / "SKILL.md" for directory in AGENTS.values()]
    for path in [*_tasks_templates(root), *skills]:
        if path.is_file() and FORBIDDEN in path.read_text(encoding="utf-8"):
            errors.append(
                f"{path.relative_to(root).as_posix()}: testing.md §5 (tests obligatorios): "
                f"contiene «{FORBIDDEN}»; reinstala jevlab-testing y pasa por cada agente "
                "(governance.md §5)"
            )
    return errors


def _body(path: Path) -> str:
    """Cuerpo de una skill sin el frontmatter, que cada agente escribe a su manera."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        _, _, rest = text[3:].partition("\n---")
        return rest.lstrip("\n")
    return text


def _check_parity(root: Path) -> list[str]:
    registry_path = root / ".specify/presets/.registry"
    if not registry_path.is_file():
        return []
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    errors = []
    for preset_id, preset in sorted(registry.get("presets", {}).items()):
        registered = preset.get("registered_skills", {})
        skills = sorted({s for names in registered.values() for s in names})
        for skill in skills:
            for agent in AGENTS:
                if skill not in registered.get(agent, []):
                    errors.append(
                        f".specify/presets/.registry: ADR-0002 (paridad): {preset_id} registra "
                        f"{skill} sin {agent}; pasa por cada agente (governance.md §5)"
                    )
            paths = [root / directory / skill / "SKILL.md" for directory in AGENTS.values()]
            if all(p.is_file() for p in paths) and _body(paths[0]) != _body(paths[1]):
                errors.append(
                    f"{skill}: ADR-0002 (paridad): el cuerpo de la skill difiere entre "
                    f"{' y '.join(AGENTS.values())}"
                )
    return errors


def _check_exec_bit(root: Path) -> list[str]:
    errors = []
    for line in git(root, "ls-files", "-s", "-z", ".specify/scripts/bash/").split("\0"):
        if not line:
            continue
        mode, _, rest = line.partition(" ")
        name = rest.split("\t", 1)[1]
        if mode != "100755":
            errors.append(
                f"{name}: governance.md §5 (bit de ejecución): modo {mode}, se espera 100755; "
                "restaura con git checkout -- .specify/scripts/bash/"
            )
    return errors


def _check_skill_interpreter(root: Path) -> list[str]:
    """Spec Kit escribe el Python de `.venv/` en las skills si existe al instalar un preset."""
    errors = []
    for directory in AGENTS.values():
        for path in sorted((root / directory).glob("*/SKILL.md")):
            if any(venv in path.read_text(encoding="utf-8") for venv in VENV_PYTHONS):
                errors.append(
                    f"{path.relative_to(root).as_posix()}: governance.md §5 (dos intérpretes): "
                    "la skill usa el Python de .venv; reinstala el preset con .venv apartado"
                )
    return errors


def check_presets(root: Path) -> list[str]:
    return [
        *_check_copies(root),
        *_check_tests_optional(root),
        *_check_parity(root),
        *_check_exec_bit(root),
        *_check_skill_interpreter(root),
    ]


def main(argv: list[str] | None = None) -> int:
    args = root_parser(__doc__ or "").parse_args(argv)
    return report(check_presets(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
