import json
from pathlib import Path

import pytest

from checks.presets import check_presets, main
from tests.unit.checks.conftest import Git, write

_TASKS_TESTING = """schema_version: "1.0"
preset:
  id: "jevlab-testing"
provides:
  templates:
    - type: "template"
      name: "tasks-template"
      file: "templates/tasks-template.md"
      strategy: "replace"
    - type: "command"
      name: "speckit.tasks"
      file: "commands/speckit.tasks.md"
      strategy: "replace"
"""
_SPECKIT_MANIFEST = ".specify/integrations/speckit.manifest.json"
_SKILL_BODY = "# Speckit Tasks Skill\n\nLos tests son obligatorios.\n"


def _skill(front: str, body: str = _SKILL_BODY) -> str:
    return f"---\nname: speckit-tasks\n{front}---\n\n{body}"


@pytest.fixture
def project(repo: Path, git: Git) -> Path:
    """Repositorio mínimo coherente: fuente, copia instalada, registro, skills y manifiesto."""
    for base in ("presets/jevlab-testing", ".specify/presets/jevlab-testing"):
        write(repo, f"{base}/preset.yml", _TASKS_TESTING)
        write(repo, f"{base}/templates/tasks-template.md", "# Tareas\n\nTests MANDATORY.\n")
        write(repo, f"{base}/commands/speckit.tasks.md", "comando\n")
    registry = {
        "presets": {
            "jevlab-testing": {
                "priority": 90,
                "registered_skills": {"claude": ["speckit-tasks"], "agy": ["speckit-tasks"]},
            }
        }
    }
    write(repo, ".specify/presets/.registry", json.dumps(registry))
    write(repo, ".specify/templates/tasks-template.md", "**Tests**: Tests are OPTIONAL\n")
    write(repo, ".claude/skills/speckit-tasks/SKILL.md", _skill("user-invocable: true\n"))
    write(repo, ".agents/skills/speckit-tasks/SKILL.md", _skill("compatibility: x\n"))
    write(
        repo, _SPECKIT_MANIFEST, json.dumps({"files": {".specify/scripts/python/common.py": "x"}})
    )
    git("add", "-A")
    return repo


def test_consistent_project_passes(project: Path) -> None:
    assert check_presets(project) == []
    assert main(["--root", str(project)]) == 0


def test_installed_copy_differs_from_source(project: Path) -> None:
    write(project, ".specify/presets/jevlab-testing/commands/speckit.tasks.md", "otro\n")
    errors = check_presets(project)
    assert len(errors) == 1
    assert "jevlab-testing" in errors[0]
    assert "commands/speckit.tasks.md" in errors[0]


def test_composed_command_in_installed_copy_is_not_extra(project: Path) -> None:
    # Spec Kit escribe en la copia instalada el comando compuesto de un preset con `append`.
    write(project, ".specify/presets/jevlab-testing/.composed/speckit.converge.md", "compuesto\n")
    assert check_presets(project) == []


def test_file_missing_in_installed_copy(project: Path) -> None:
    (project / ".specify/presets/jevlab-testing/commands/speckit.tasks.md").unlink()
    assert any("speckit.tasks.md" in e for e in check_presets(project))


def test_tests_optional_in_preset_template(project: Path) -> None:
    for base in ("presets/jevlab-testing", ".specify/presets/jevlab-testing"):
        write(project, f"{base}/templates/tasks-template.md", "Tests are OPTIONAL\n")
    errors = check_presets(project)
    assert len(errors) == 1
    assert "Tests are OPTIONAL" in errors[0]


def test_base_template_counts_when_no_replace_preset(project: Path) -> None:
    for base in ("presets/jevlab-testing", ".specify/presets/jevlab-testing"):
        manifest = _TASKS_TESTING.replace('strategy: "replace"', 'strategy: "append"', 1)
        write(project, f"{base}/preset.yml", manifest)
    errors = check_presets(project)
    assert any(".specify/templates/tasks-template.md" in e for e in errors)


@pytest.mark.parametrize("agent", [".claude", ".agents"])
def test_tests_optional_back_in_an_agent_skill(project: Path, agent: str) -> None:
    write(
        project,
        f"{agent}/skills/speckit-tasks/SKILL.md",
        _skill("x: y\n", "Tests are OPTIONAL\n"),
    )
    errors = check_presets(project)
    assert any(agent in e and "Tests are OPTIONAL" in e for e in errors)


def test_skill_bodies_differ_between_agents(project: Path) -> None:
    write(project, ".agents/skills/speckit-tasks/SKILL.md", _skill("x: y\n", "otro cuerpo\n"))
    errors = check_presets(project)
    assert len(errors) == 1
    assert "speckit-tasks" in errors[0]
    assert "paridad" in errors[0]


def test_command_registered_in_one_agent_only(project: Path) -> None:
    registry = {
        "presets": {
            "jevlab-testing": {"registered_skills": {"claude": ["speckit-tasks"], "agy": []}}
        }
    }
    write(project, ".specify/presets/.registry", json.dumps(registry))
    errors = check_presets(project)
    assert any("agy" in e for e in errors)


@pytest.mark.parametrize("venv", [".venv/bin/python", ".venv/Scripts/python.exe"])
def test_skill_using_the_virtualenv_python(project: Path, venv: str) -> None:
    body = f"Run `{venv} .specify/scripts/python/setup_tasks.py --json`\n"
    for agent in (".claude", ".agents"):
        write(project, f"{agent}/skills/speckit-tasks/SKILL.md", _skill("x: y\n", body))
    errors = check_presets(project)
    assert len(errors) == 2
    assert all(".venv" in e for e in errors)


@pytest.mark.parametrize("script", ["bash/common.sh", "powershell/common.ps1"])
def test_shell_script_versioned(project: Path, git: Git, script: str) -> None:
    write(project, f".specify/scripts/{script}", "# script\n")
    git("add", "-f", f".specify/scripts/{script}")
    errors = check_presets(project)
    assert len(errors) == 1
    assert script in errors[0]
    assert "solo Python" in errors[0]


@pytest.mark.parametrize("script", ["bash/common.sh", "powershell/common.ps1"])
def test_shell_script_in_speckit_manifest(project: Path, script: str) -> None:
    files = {".specify/scripts/python/common.py": "x", f".specify/scripts/{script}": "y"}
    write(project, _SPECKIT_MANIFEST, json.dumps({"files": files}))
    errors = check_presets(project)
    assert len(errors) == 1
    assert _SPECKIT_MANIFEST in errors[0]
    assert script in errors[0]
