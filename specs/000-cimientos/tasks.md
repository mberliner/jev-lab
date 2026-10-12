---

description: "Lista de tareas de la spec 000: Cimientos de jev-lab"
---

# Tasks: Cimientos de jev-lab

**Input**: Design documents from `specs/000-cimientos/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-doctor.md,
quickstart.md

**Tests**: MANDATORY (jev-lab, Constitution IV). Every user story includes test tasks, written
before its implementation tasks and failing before implementing. Tests against real services are
optional, marked `live`, and declare a cost cap. Test mix per story (docs/standards/testing.md §2):
unit tests first, enough to reach coverage; one `integration` test for the main acceptance
scenario; contract tests only if the story adds or changes an adapter.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing
of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 a US4)
- Rutas relativas a la raíz del repositorio; estructura de `plan.md`, «Project Structure»
- Versiones de dependencias: `research.md` R14. Reglas de cada capa: `docs/standards/architecture.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: proyecto uv instalable, configuración de herramientas y tareas `poe`.

- [ ] T001 Crear `pyproject.toml` con `uv init --package --name jevlab` (paquete en `src/jevlab/`), `requires-python = ">=3.13,<3.14"`, `.python-version` con `3.13`, dependencias de `research.md` R14 (`typesafe-sdk`, `openai`, `pydantic`, `pydantic-settings`, `typer`) y grupo `dev` (`pytest`, `pytest-socket`, `pytest-cov`, `hypothesis`, `ruff`, `mypy`, `import-linter`, `poethepoet`, `pre-commit`)
- [ ] T002 [P] Crear los paquetes vacíos de las cinco capas: `src/jevlab/domain/__init__.py`, `src/jevlab/application/__init__.py`, `src/jevlab/ports/__init__.py`, `src/jevlab/adapters/__init__.py`, `src/jevlab/entrypoints/__init__.py` y `src/jevlab/entrypoints/cli/__init__.py`
- [ ] T003 [P] Crear `tests/unit/`, `tests/contract/`, `tests/integration/` y `tests/live/`, y configurar pytest en `pyproject.toml`: marcas `integration` y `live`, `addopts = "--disable-socket --allow-unix-socket -m 'not live'"`, `pythonpath = ["scripts"]`, `testpaths = ["tests"]`
- [ ] T004 [P] Configurar en `pyproject.toml` `ruff` (reglas por defecto más `I`, `UP`, `B`; formato) y `mypy` (`strict = true`, `files = ["src", "scripts", "tests"]`)
- [ ] T005 [P] Crear `.env.example` con `TYPESAFE_API_KEY=`, `TYPESAFE_DEFAULT_MODEL=jev-latest`, `AZURE_OPENAI_ENDPOINT=`, `AZURE_OPENAI_API_KEY=`, `AZURE_OPENAI_DEPLOYMENT=` y `AZURE_OPENAI_API_VERSION=`, y comprobar que `.gitignore` excluye `.env`
- [ ] T006 [P] Crear `LICENSE` con el texto oficial de Apache-2.0 (https://www.apache.org/licenses/LICENSE-2.0.txt) y la línea de copyright del mantenedor; declarar `license = "Apache-2.0"` en `pyproject.toml`
- [ ] T007 Declarar las tareas `poe` de `plan.md`, «Puertas de calidad», en `pyproject.toml`: `lint`, `typecheck`, `lint-imports`, `test`, `cov` (dos pasos: `pytest -m "not integration and not live" --cov=jevlab --cov=checks --cov-fail-under=80` y `coverage report --include="src/jevlab/domain/*" --fail-under=95`), `test-integration`, `live` (`pytest -m live --force-enable-socket`), `check-writing`, `check-commit-msg`, `check-presets`, `check-paths`, `check-agents` y `check` (secuencia sin `test` ni `check-commit-msg`)
- [ ] T008 Ejecutar `uv lock` y `uv sync` y versionar `uv.lock`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: la regla de dependencias activa antes de escribir código de capas.

- [ ] T009 Crear `.importlinter` con: contrato de capas `jevlab.entrypoints`, `jevlab.application`, `jevlab.domain`; contrato que impide a `jevlab.domain` importar `jevlab.adapters`, `jevlab.ports`, `jevlab.application`, `jevlab.entrypoints`, `typesafe_sdk` y `openai`; contrato que impide a `jevlab.application` importar `jevlab.adapters`, `typesafe_sdk` y `openai` (`docs/standards/architecture.md` §1 y §2)
- [ ] T010 Comprobar que `uv run poe lint`, `uv run poe typecheck` y `uv run poe lint-imports` pasan sobre el esqueleto vacío

**Checkpoint**: esqueleto instalable con la regla de dependencias comprobada.

---

## Phase 3: User Story 1 - Poner en marcha el proyecto desde un clon limpio (Priority: P1) MVP

**Goal**: desde un clon limpio, en Linux o en Windows, con solo `docs/setup.md`, la suite por
defecto pasa sin red ni claves.

**Independent Test**: en un clon nuevo, seguir `docs/setup.md` y ejecutar `uv run poe test` con la
red desactivada.

### Tests for User Story 1 (write first, must FAIL before implementation)

- [ ] T011 [P] [US1] Test unitario que abre un socket TCP y espera `pytest_socket.SocketBlockedError` en `tests/unit/test_network_blocked.py`
- [ ] T012 [P] [US1] Test unitario de `jevlab --version` con `typer.testing.CliRunner` (sale con 0 e imprime la versión del paquete) en `tests/unit/entrypoints/test_cli_version.py`
- [ ] T013 [P] [US1] Test de integración (marca `integration`) del escenario principal: con un entorno sin variables de TypeSafe ni Azure y sin `.env`, `python -m jevlab --version` en subproceso sale con 0, en `tests/integration/test_clean_start.py`

### Implementation for User Story 1

- [ ] T014 [US1] Crear la app Typer `jevlab` con la opción `--version` en `src/jevlab/entrypoints/cli/main.py`, `src/jevlab/__main__.py` y `[project.scripts] jevlab = "jevlab.entrypoints.cli.main:app"` en `pyproject.toml`
- [ ] T015 [US1] Escribir `docs/setup.md` (FR-014): requisitos; uv y Python 3.13; `python3` ≥ 3.8 con PyYAML para Spec Kit y `SPECKIT_PYTHON_EXECUTABLE` (`docs/governance.md` §5, nota técnica); el enlace duro `python3.exe` en Windows; Git Bash; `uv sync`, `uv run poe test` y `uv run pre-commit install`; `.env` desde `.env.example`; los dos agentes y los pasos de paridad que hoy están en `docs/roadmap.md`, «Funcionamiento igual en Claude Code y Antigravity»; la creación del repositorio público en GitHub (`research.md` R13)
- [ ] T016 [US1] Sustituir el procedimiento de la sección «Funcionamiento igual en Claude Code y Antigravity» de `docs/roadmap.md` por un enlace a `docs/setup.md` y a ADR-0002
- [ ] T017 [US1] Validar la US1 en Linux con `quickstart.md`, «US1», en un clon nuevo con la red desactivada

**Checkpoint**: la US1 se demuestra sola (Windows se valida en CI, US3).

---

## Phase 4: User Story 2 - Comprobar el entorno con `jevlab doctor` (Priority: P2)

**Goal**: `jevlab doctor` muestra cada comprobación con su estado y arreglo; `--remote` añade
TypeSafe y Azure (`contracts/cli-doctor.md`).

**Independent Test**: simular cada requisito ausente y comprobar estado, arreglo y código de
salida; con claves reales, el humo `live`.

### Tests for User Story 2 (write first, must FAIL before implementation)

- [ ] T018 [P] [US2] Crear los fakes `FakeLocalEnvironment`, `FakeModelCatalog` (lista programable o error `ProviderUnavailable`/`ProviderRejected`) y `FakeGeneratorProbe` en `tests/fakes.py`, con las firmas de los puertos de `plan.md`, «Arquitectura»
- [ ] T019 [P] [US2] Tests unitarios y de propiedades (`hypothesis`) de `src/jevlab/domain/diagnostics.py` en `tests/unit/domain/test_diagnostics.py`: `exit_code()` es 1 si algún resultado es `fail`; es 1 si `remote_requested` y algún remoto es `unavailable`; es 0 en otro caso; un `CheckResult` con `scope=local` no admite `unavailable`; `fix` es obligatorio si `status` no es `ok`
- [ ] T020 [P] [US2] Tests unitarios de `CheckEnvironment` con los fakes en `tests/unit/application/test_check_environment.py`: orden fijo de resultados (`speckit-python`, `project-python`, `env-keys`, `typesafe`, `azure`); sin `remote` no se llama a `ModelCatalog` ni a `GeneratorProbe`; `ProviderUnavailable` da `unavailable`; `ProviderRejected` da `fail` con arreglo según el código (401/403 clave, 404 modelo o deployment); el modelo por defecto debe estar en la lista o ser `jev-latest` o `jev-preview`
- [ ] T021 [P] [US2] Tests unitarios del comando `doctor` con `CliRunner` y fakes inyectados en `tests/unit/entrypoints/test_cli_doctor.py`: formato de `contracts/cli-doctor.md` (`[ok]`, `[fail]`, `[n/d]`, línea `arreglo:`, resumen), códigos de salida y que ningún valor de clave aparece en la salida
- [ ] T022 [P] [US2] Test unitario de que, sin `TYPESAFE_LOG_LEVEL`, la CLI deja el logger `typesafe_sdk` en `WARNING` y una llamada simulada no emite el *payload* en los logs capturados, en `tests/unit/entrypoints/test_sdk_logging.py` (`research.md` R12)
- [ ] T023 [P] [US2] Test de contrato de `SystemLocalEnvironment` en `tests/contract/test_local_environment.py`: `.env` temporal completo, sin archivo y con una clave vacía; `python3` ausente, de versión < 3.8 y sin `yaml` mediante `SPECKIT_PYTHON_EXECUTABLE` apuntando a un ejecutable de prueba generado en `tmp_path`
- [ ] T024 [P] [US2] Test de contrato de `TypeSafeModelCatalog` con un transporte simulado de `httpx2` pasado por el parámetro `transport` de `TypeSafeClient`, en `tests/contract/test_typesafe_catalog.py`: lista de modelos, 401 y error de conexión. Respuestas sintéticas etiquetadas como tales (`research.md` R1 y R3)
- [ ] T025 [P] [US2] Test de contrato de `AzureGeneratorProbe` con `httpx.MockTransport` en el `http_client` de `AzureOpenAI`, en `tests/contract/test_azure_probe.py`: respuesta correcta, 401, 404 y error de conexión. Respuestas sintéticas etiquetadas (`research.md` R2)
- [ ] T026 [P] [US2] Test de integración (marca `integration`) del escenario principal en `tests/integration/test_doctor_local.py`: CLI con adaptadores locales reales, `.env` temporal completo y otro con una clave vacía; códigos de salida 0 y 1 y sin red
- [ ] T027 [P] [US2] Mecanismo de tope de coste de los tests `live` en `tests/live/conftest.py`: cada test declara `@pytest.mark.live(max_usd=...)`; la sesión se aborta antes de empezar si la suma de los topes seleccionados supera `JEVLAB_LIVE_BUDGET_USD` (por defecto `0.10`). Test unitario del cálculo en `tests/unit/test_live_budget.py` (`docs/standards/testing.md` §6)
- [ ] T028 [US2] Humo `live` de `jevlab doctor --remote` con claves reales y `max_usd=0.01` en `tests/live/test_doctor_remote.py`

### Implementation for User Story 2

- [ ] T029 [US2] Implementar en `src/jevlab/domain/diagnostics.py` los modelos inmutables de `data-model.md`: `CheckStatus` (`ok`, `fail`, `unavailable`), `Scope` (`local`, `remote`), `CheckResult` («Una comprobación `local` nunca es `unavailable`»; `fix` «Obligatorio si `status` no es `ok`»), `DoctorReport` con `exit_code()`, y los errores `ProviderUnavailable` y `ProviderRejected` (con `status`)
- [ ] T030 [P] [US2] Definir el puerto `LocalEnvironment` (`speckit_python()`, `project_python()`, `missing_env_keys()`) en `src/jevlab/ports/environment.py`
- [ ] T031 [P] [US2] Definir los puertos `ModelCatalog` (`list_models() -> list[str]`) y `GeneratorProbe` (`ping() -> None`) en `src/jevlab/ports/providers.py`, como `typing.Protocol`
- [ ] T032 [US2] Implementar `CheckEnvironment(local, catalog, generator).run(remote: bool) -> DoctorReport` en `src/jevlab/application/check_environment.py`
- [ ] T033 [P] [US2] Implementar `SystemLocalEnvironment` en `src/jevlab/adapters/local_environment.py`: `python3` (o `SPECKIT_PYTHON_EXECUTABLE`) por subproceso con `-c` para versión e import de `yaml`; `sys.version_info`; variables requeridas leídas de `.env.example` y su presencia en `.env` o en el entorno con `pydantic-settings`, sin guardar valores
- [ ] T034 [P] [US2] Implementar `TypeSafeModelCatalog` en `src/jevlab/adapters/typesafe_catalog.py`: `TypeSafeClient.models.list()`; `TypeSafeAPIConnectionError` y 5xx a `ProviderUnavailable`; 401, 403 y 404 a `ProviderRejected`
- [ ] T035 [P] [US2] Implementar `AzureGeneratorProbe` en `src/jevlab/adapters/azure_probe.py`: `AzureOpenAI` con las variables de `.env`, `chat.completions.create` de un mensaje fijo con `max_completion_tokens=16`; mismo mapeo de errores; no conserva el contenido de la respuesta
- [ ] T036 [US2] Añadir el comando `doctor` con la opción `--remote` en `src/jevlab/entrypoints/cli/main.py`: cableado de `CheckEnvironment` con los adaptadores reales (sustituibles en los tests), salida de `contracts/cli-doctor.md`, código de salida de `DoctorReport.exit_code()` y logger `typesafe_sdk` en `WARNING` salvo `TYPESAFE_LOG_LEVEL`
- [ ] T037 [US2] Validar la US2 con `quickstart.md`, «US2», incluido `uv run poe live` con claves reales

**Checkpoint**: `jevlab doctor` funciona solo; la US1 sigue en verde.

---

## Phase 5: User Story 3 - Puertas de calidad en cada commit y en CI (Priority: P3)

**Goal**: cada regla de FR-007 se comprueba igual en pre-commit y en CI, en Linux y Windows, y los
dos agentes trabajan sobre los mismos artefactos.

**Independent Test**: introducir cada violación de `quickstart.md`, «US3», y comprobar que su
puerta la rechaza; `/speckit-specify` de prueba en cada agente.

### Tests for User Story 3 (write first, must FAIL before implementation)

- [ ] T038 [P] [US3] Tests unitarios de `scripts/checks/writing.py` en `tests/unit/checks/test_writing.py`: rechaza un emoji y una flecha o carácter de caja fuera de bloques de código; los acepta dentro de bloques de código; el mensaje nombra la regla, el archivo y la línea (FR-008)
- [ ] T039 [P] [US3] Tests unitarios de `scripts/checks/commit_msg.py` en `tests/unit/checks/test_commit_msg.py`: acepta `feat(presets): …`; rechaza un tipo inválido, una línea `Co-Authored-By:` y `Generated with` (`docs/standards/version-control.md`)
- [ ] T040 [P] [US3] Tests unitarios de `scripts/checks/presets.py` sobre un repositorio de prueba en `tmp_path`, en `tests/unit/checks/test_presets.py`: copia instalada distinta de la fuente; «Tests are OPTIONAL» en una plantilla de preset o en una skill `speckit-tasks`; cuerpos de skill distintos entre `.claude/skills/` y `.agents/skills/` (el *frontmatter* puede diferir); script de `.specify/scripts/bash/` sin modo `100755` en el índice de Git (`research.md` R8)
- [ ] T041 [P] [US3] Tests unitarios de `scripts/checks/paths.py` en `tests/unit/checks/test_paths.py`: rechaza `/home/<usuario>/`, `/datum1/` y `C:\Users\` en un archivo versionado y un enlace simbólico; acepta rutas relativas
- [ ] T042 [P] [US3] Tests unitarios de `scripts/checks/agents.py` en `tests/unit/checks/test_agents.py`: acepta `CLAUDE.md` con solo `@AGENTS.md`; rechaza cualquier otra línea
- [ ] T043 [P] [US3] Test de integración (marca `integration`) del escenario principal en `tests/integration/test_gates_on_repo.py`: las cinco comprobaciones de `scripts/checks/` pasan sobre el propio repositorio

### Implementation for User Story 3

- [ ] T044 [P] [US3] Implementar `scripts/checks/writing.py` (`research.md` R10) con `main(argv) -> int`
- [ ] T045 [P] [US3] Implementar `scripts/checks/commit_msg.py` (`research.md` R10): recibe la ruta del mensaje (gancho `commit-msg`) o, con `--range <a>..<b>`, comprueba los commits de ese rango con `git log`
- [ ] T046 [P] [US3] Implementar `scripts/checks/presets.py` (`research.md` R8), leyendo `.specify/presets/.registry` para saber qué comandos sustituye cada preset
- [ ] T047 [P] [US3] Implementar `scripts/checks/paths.py` (`research.md` R10) sobre `git ls-files`
- [ ] T048 [P] [US3] Implementar `scripts/checks/agents.py` (`research.md` R11)
- [ ] T049 [US3] Crear `.pre-commit-config.yaml` (`research.md` R7): `default_install_hook_types: [pre-commit, commit-msg]`; ganchos `repo: local` con `language: system`, `pass_filenames: false` y `always_run: true` que ejecutan `uv run poe check` y, en la fase `commit-msg`, `uv run poe check-commit-msg`; gancho oficial de gitleaks `v8.30.1`
- [ ] T050 [US3] Crear `.github/workflows/ci.yml`: disparadores `push` y `pull_request` (nunca `pull_request_target`); `permissions: contents: read`; matriz `ubuntu-latest` y `windows-latest`; `astral-sh/setup-uv`; `uv sync --locked`; `uv run pre-commit run --all-files`; en `push` y `pull_request`, `uv run poe check-commit-msg --range` sobre los commits nuevos; sin *secrets* (`docs/standards/security.md` §5)
- [ ] T051 [US3] Comprobar cada violación de `quickstart.md`, «US3», en local y deshacerla
- [ ] T052 [US3] Crear el repositorio público en GitHub (manual, mantenedor: `research.md` R13), añadir el remoto, hacer `git push` y comprobar la CI en verde en Linux y Windows
- [ ] T053 [US3] Ejecutar `/speckit-specify` de prueba en Claude Code y en Antigravity sobre una rama desechable, comprobar que los dos usan la plantilla resuelta con las secciones de los presets y borrar la rama

**Checkpoint**: las puertas protegen todo cambio posterior.

---

## Phase 6: User Story 4 - Entender el método con el README y la lección (Priority: P4)

**Goal**: una persona sin contexto entiende qué es jev-lab y cómo se construye.

**Independent Test**: con `README.md`, `docs/setup.md` y la lección, explicar el flujo SDD y
aplicar el procedimiento de un preset.

### Tests for User Story 4 (write first, must FAIL before implementation)

- [ ] T054 [P] [US4] Test unitario de `README.md` en `tests/unit/docs/test_readme.py`: contiene las secciones de FR-015 (qué es, estado con enlace a `docs/roadmap.md`, inicio rápido de 3 o 4 comandos, mapa de documentos, licencia)
- [ ] T055 [P] [US4] Test de integración (marca `integration`) en `tests/integration/test_doc_links.py`: todos los enlaces relativos de `README.md`, `docs/setup.md` y `docs/lessons/000-metodo-sdd-y-entorno-reproducible.md` apuntan a archivos existentes

### Implementation for User Story 4

- [ ] T056 [US4] Escribir `README.md` para personas (FR-015), con enlace a `AGENTS.md` para agentes y a `LICENSE`
- [ ] T057 [US4] Escribir `docs/lessons/000-metodo-sdd-y-entorno-reproducible.md` (FR-016): flujo de Spec Kit; constitución, presets, estándares y ADRs, y cómo se rastrea una regla hasta un principio; aplicación de un preset paso a paso con `jevlab-testing` (`replace`, composición por prioridad, agente único activo, `docs/governance.md` §5); entorno de dos intérpretes; fallos típicos con su mitigación (spec, «Lección»); reutiliza `docs/setup.md` con enlaces en vez de repetirlo

**Checkpoint**: las cuatro historias se demuestran por separado.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T058 [P] Actualizar `AGENTS.md` con los comandos del proyecto (`uv sync`, `uv run poe check`, `uv run jevlab doctor`) y el enlace a `docs/setup.md`
- [ ] T059 [P] Actualizar `docs/governance.md` §4: la columna «Estado» pasa de «previsto en 000» a «creado» en los temas ya hechos, y las comprobaciones automáticas de redacción y control de versiones quedan como hechas
- [ ] T060 Ejecutar `uv run poe check` y `uv run pre-commit run --all-files` en Linux y revisar el tiempo de la suite (SC-002, menos de 1 minuto)
- [ ] T061 Validar `quickstart.md` completo

---

## Fase final: cierre de la feature (jev-lab)

> Deriva de: Constitución §VII y *Governance* (revisión periódica)

- [ ] T062 Revisar la lección escrita en T057 contra lo que se ha implementado: qué se aprende, cómo se ejecuta, qué puede fallar y su mitigación
- [ ] T063 Demostrar cada historia con el comando de la tabla «Corte vertical y lección» de la spec
- [ ] T064 Retro: ¿algún principio estorbó?, ¿faltó alguno?, ¿alguno no se pudo verificar? Respuestas en el commit de cierre; cada «sí» abre su cambio o se anota en `docs/ideas.md`. Actualizar «Estado actual y cómo retomar» en `docs/roadmap.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de Setup; bloquea todas las historias.
- **US1 a US4 (Phases 3-6)**: dependen de Foundational. Orden recomendado por prioridad.
- **Polish y cierre**: dependen de las cuatro historias.

### User Story Dependencies

- **US1 (P1)**: sin dependencias de otras historias.
- **US2 (P2)**: usa la app Typer de T014 (US1).
- **US3 (P3)**: independiente en sus comprobaciones; T049 ejecuta `poe check`, que incluye la
  suite de US1 y US2 si ya existen. T052 (CI en Windows) completa la validación de la US1 en
  Windows.
- **US4 (P4)**: enlaza `docs/setup.md` (T015); el resto es independiente.

### Within Each User Story

- Los tests se escriben y fallan antes de implementar.
- Dominio, después puertos, después aplicación, después adaptadores y, por último, entrypoints.

### Parallel Opportunities

- Setup: T002 a T006.
- US2: T018 a T027 (tests y fakes, archivos distintos); T030, T031, T033, T034 y T035.
- US3: T038 a T043 y T044 a T048.
- US4: T054 y T055.
- US3 y US4 pueden avanzar en paralelo una vez cerrada la US1.

---

## Parallel Example: User Story 2

```bash
# Tests de la US2 en paralelo:
Task: "Tests unitarios y de propiedades de diagnostics en tests/unit/domain/test_diagnostics.py"
Task: "Test de contrato de TypeSafeModelCatalog en tests/contract/test_typesafe_catalog.py"
Task: "Test de contrato de AzureGeneratorProbe en tests/contract/test_azure_probe.py"

# Adaptadores de la US2 en paralelo, tras los puertos:
Task: "SystemLocalEnvironment en src/jevlab/adapters/local_environment.py"
Task: "TypeSafeModelCatalog en src/jevlab/adapters/typesafe_catalog.py"
Task: "AzureGeneratorProbe en src/jevlab/adapters/azure_probe.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 y Phase 2.
2. Phase 3 (US1): clon limpio y suite sin red.
3. Validar la US1 por separado.

### Incremental Delivery

1. Setup y Foundational: esqueleto con regla de dependencias.
2. US1: entorno reproducible (MVP).
3. US2: `jevlab doctor`.
4. US3: puertas en pre-commit y CI; repositorio público.
5. US4: README y lección.
6. Polish y cierre.

---

## Notes

- [P]: archivos distintos y sin dependencias pendientes.
- Commit después de cada tarea o grupo lógico, en Conventional Commits y sin atribuciones de
  agentes.
- T052 y T053 son manuales (cuenta de GitHub del mantenedor y dos agentes).
