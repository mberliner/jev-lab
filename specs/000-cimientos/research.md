# Investigación: Cimientos de jev-lab

Fase 0 de `/speckit-plan`. Cada apartado resuelve una incógnita del contexto técnico con la forma
decisión, motivo y alternativas. Versiones consultadas en PyPI y GitHub el 2026-10-12.

## R1. Comprobación remota de TypeSafe

- **Decisión:** `TypeSafeClient(...).models.list()` del SDK oficial (`typesafe-sdk` 0.7.4). Correcto
  si la clave lista al menos un modelo. Si `TYPESAFE_DEFAULT_MODEL` está fijado, debe figurar en la
  lista o ser un alias documentado (`jev-latest`, `jev-preview`).
- **Motivo:** el SDK documenta `models.list()` como «List the models available to the account»
  ([*Synchronous client*](https://docs.typesafe.ai/sdk/python/api/clients/sync.md)). El precio se
  aplica a los tokens de entrada de `/v1/systemone` ([*Models*](https://docs.typesafe.ai/models.md)),
  así que listar modelos no consume tokens. Errores: `TypeSafeAPIError` (con `.status`) para
  respuestas HTTP y `TypeSafeAPIConnectionError` para red o *timeout*
  ([*Exceptions*](https://docs.typesafe.ai/sdk/python/api/exceptions.md)); bastan para distinguir
  clave inválida (401/403) de red no disponible.
- **Alternativas:** una llamada mínima a `system_one` (cuesta tokens y es una pregunta al modelo,
  fuera de alcance); un GET HTTP propio (duplica el SDK).

## R2. Comprobación remota de Azure OpenAI

- **Decisión:** `AzureOpenAI` de `openai` (3.29.0) con `chat.completions.create` de un mensaje fijo
  y `max_completion_tokens=16`. Correcto si responde sin error; no se muestra el contenido.
- **Motivo:** es la única forma de comprobar a la vez endpoint, clave, nombre del deployment y
  versión de API. Listar modelos no confirma que exista el deployment.
- **Alternativas:** `max_tokens=1` (no lo aceptan los modelos de razonamiento recientes).

## R3. El SDK de TypeSafe usa `httpx2`

- **Hallazgo:** `typesafe-sdk` depende de `httpx2>=2.0.0`, no de `httpx`. `respx` (previsto en
  `docs/standards/testing.md` §1 para HTTP) y `vcrpy` interceptan `httpx`.
- **Decisión para la 000:** los tests de contrato del adaptador de TypeSafe usan el parámetro
  `transport` del cliente con un transporte simulado de `httpx2`, sin `respx`. Las *cassettes*
  quedan fuera de alcance (spec, YAGNI).
- **Pendiente para la 001:** comprobar si `vcrpy`/`pytest-recording` graban `httpx2`; si no, ajustar
  el estándar de testing. Anotado en `docs/ideas.md`.

## R4. Dónde vive `jevlab doctor` en la arquitectura hexagonal

- **Decisión:** caso de uso `CheckEnvironment` en `application/`, modelo del informe en `domain/`,
  tres puertos (`LocalEnvironment`, `ModelCatalog`, `GeneratorProbe`) con adaptadores reales y
  fakes, y el comando Typer en `entrypoints/cli/`. Detalle en `data-model.md` y en la sección
  «Arquitectura» del plan.
- **Motivo:** es la primera pieza real del esqueleto y lo valida de punta a punta, con la regla de
  dependencias ya activa. La lógica que decide (estados, código de salida) es pura y se prueba sin
  red (Constitución §I y §III).
- **Alternativas:** un script suelto en `scripts/` (no ejercita el esqueleto ni `import-linter`).

## R5. Nombre de la opción remota

- **Decisión:** `jevlab doctor --remote`. Mensajes en español.
- **Motivo:** los comandos del roadmap están en inglés (`triage`, `review`, `eval`); la opción sigue
  el mismo idioma. El estándar `cli-ux.md` llega con la spec 001 y puede revisarlo.

## R6. Tareas multiplataforma

- **Decisión:** `poethepoet` (0.48.0) en `pyproject.toml`; cada comprobación propia es un módulo
  Python en `scripts/checks/`, ejecutado como `uv run poe <tarea>`.
- **Motivo:** mismo comando en Linux y Windows sin bash ni cmd (FR-002, Constitución §VI).
- **Alternativas:** `make` o `just` (dependen de herramientas externas en Windows).

## R7. Pre-commit y CI con las mismas comprobaciones

- **Decisión:**
  - `pre-commit` (4.6.2) con `default_install_hook_types: [pre-commit, commit-msg]`.
  - Ganchos `repo: local` que llaman a `uv run poe <tarea>` (`language: system`), salvo gitleaks,
    que usa su gancho oficial (v8.30.1).
  - La suite completa con cobertura corre en cada commit (aclaración de la spec).
  - CI: GitHub Actions, matriz `ubuntu-latest` y `windows-latest`, `astral-sh/setup-uv`,
    `uv sync --locked` y `uv run pre-commit run --all-files`. Sin *secrets* (spec, Assumptions).
- **Motivo:** una sola definición de cada puerta, invocada igual desde pre-commit, CI y cualquier
  agente (FR-009, ADR-0002).
- **Alternativas:** duplicar comandos en el workflow (dos fuentes que divergen).

## R8. Comprobaciones de presets sin la CLI de Spec Kit

- **Decisión:** `scripts/checks/presets.py` lee los archivos versionados y no ejecuta `specify`:
  - copia instalada: cada `presets/<id>/` es igual a `.specify/presets/<id>/`;
  - «Tests are OPTIONAL» no aparece en `.specify/presets/*/templates/tasks-template.md`, en
    `.specify/templates/tasks-template.md` solo si la sustituye un preset `replace`, ni en las
    skills `speckit-tasks` de los dos agentes;
  - paridad: el cuerpo (sin *frontmatter*) de cada skill sustituida por un preset es igual en
    `.claude/skills/` y `.agents/skills/` (hoy solo difieren en el *frontmatter*);
  - bit de ejecución: `git ls-files -s .specify/scripts/bash/` da modo `100755`, también en Windows.
- **Motivo:** la CLI es una prerelease (1.1.4.dev0) que la CI no necesita instalar.
- **Alternativas:** `specify preset resolve` en CI (dependencia y red innecesarias).

## R9. Red bloqueada y cobertura

- **Decisión:** `pytest` (9.1.1) con `pytest-socket` (0.8.1, `--disable-socket
  --allow-unix-socket`), marcas `integration` y `live`, y `pytest-cov` (7.1.0):
  - `poe test`: toda la suite salvo `live`.
  - `poe cov`: `-m "not integration and not live"` con `--cov-fail-under=80` y después
    `coverage report --include="src/jevlab/domain/*" --fail-under=95`.
  - `poe live`: `-m live --force-enable-socket`.
- **Motivo:** `docs/standards/testing.md` §2 a §4.
- **Riesgo conocido:** con `domain/` casi vacío, el 95 % se cumple con poco código; los umbrales
  ganan sentido desde la spec 001.

## R10. Comprobaciones de redacción, mensaje de commit y rutas

- **Decisión:** tres módulos en `scripts/checks/`:
  - `writing.py`: emojis y pictogramas en `.md`, y caracteres de caja y flechas fuera de bloques de
    código (`docs/standards/writing.md`).
  - `commit_msg.py`: Conventional Commits y ausencia de `Co-Authored-By` y `Generated with`
    (`docs/standards/version-control.md`).
  - `paths.py`: rutas absolutas de máquina (`/home/`, `/datum`, `C:\Users\`…) en archivos
    versionados, y ausencia de enlaces simbólicos.
- **Motivo:** no hay herramienta estándar para estas reglas propias; un script corto y probado es
  lo más simple.

## R11. `CLAUDE.md` importa solo `AGENTS.md`

- **Decisión:** `scripts/checks/agents.py` comprueba que `CLAUDE.md`, sin líneas vacías, es
  exactamente `@AGENTS.md`.

## R12. Logs del SDK por defecto

- **Decisión:** al arrancar, la CLI fija el logger `typesafe_sdk` en `WARNING` salvo que
  `TYPESAFE_LOG_LEVEL` esté definido en el entorno local. Un test lo comprueba
  (Constitución §V, `docs/standards/security.md` §2).

## R13. Creación del repositorio público

- **Decisión:** el mantenedor crea el repositorio vacío y público en github.com con la interfaz web
  (sin `gh`, que no está instalado) y añade el remoto con `git remote add origin` y `git push`. Se
  documenta en `docs/setup.md`. La licencia es Apache-2.0 (`LICENSE`, aclaración de la spec).

## R14. Dependencias

| Paquete | Versión | Uso |
| --- | --- | --- |
| `typesafe-sdk` | 0.7.4 | Catálogo de modelos (R1) |
| `openai` | 3.29.0 | Comprobación de Azure (R2) |
| `pydantic` / `pydantic-settings` | 2.14.1 / 2.15.0 | Modelos de dominio y lectura de `.env` |
| `typer` | 0.27.3 | CLI |
| Desarrollo: `pytest`, `pytest-socket`, `pytest-cov`, `hypothesis` | 9.1.1, 0.8.1, 7.1.0, 6.169.0 | Tests |
| Desarrollo: `ruff`, `mypy`, `import-linter`, `poethepoet`, `pre-commit` | 0.17.0, 2.4.0, 2.15, 0.48.0, 4.6.2 | Puertas y tareas |

`python-dotenv` no hace falta: `pydantic-settings` lee `.env`. `vcrpy` y `pytest-recording` se
añaden en la 001, cuando haya *cassettes* (R3).
