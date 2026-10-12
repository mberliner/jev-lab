# Implementation Plan: Cimientos de jev-lab

**Branch**: `000-cimientos` | **Date**: 2026-10-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/000-cimientos/spec.md`

## Summary

Crear el proyecto Python 3.13 con uv y el esqueleto hexagonal vacío, validado de punta a punta por
una única pieza real: `jevlab doctor`, que comprueba el entorno en local y, con `--remote`, el
acceso a TypeSafe (`models.list()`) y a Azure OpenAI. Alrededor, las puertas de calidad como
tareas `poe` invocadas igual desde pre-commit y desde la CI de GitHub Actions (Linux y Windows), y
la documentación para personas: `docs/setup.md`, `README.md`, `LICENSE` (Apache-2.0) y la lección
000. Detalle de las decisiones en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.13 (uv 0.9.18) para el proyecto; `python3` ≥ 3.8 con PyYAML solo
para Spec Kit.

**Primary Dependencies**: `typesafe-sdk` 0.7.4, `openai` 3.29.0, `pydantic` 2.14.1,
`pydantic-settings` 2.15.0, `typer` 0.27.3 (research R14).

**Storage**: N/A (nada se persiste).

**Testing**: `pytest` 9.1.1, `pytest-socket` 0.8.1, `pytest-cov` 7.1.0, `hypothesis` 6.169.0;
marcas `integration` y `live` (`docs/standards/testing.md`).

**Target Platform**: Linux y Windows (CI `ubuntu-latest` y `windows-latest`).

**Project Type**: CLI (paquete `jevlab` instalable con uv).

**Performance Goals**: suite por defecto en menos de 1 minuto (SC-002), porque corre en cada
commit.

**Constraints**: sin red en la suite por defecto; sin *secrets* en la CI de esta spec; sin enlaces
simbólicos; UTF-8 y `pathlib`; repositorio público.

**Scale/Scope**: un paquete, cinco capas, un comando de CLI y siete puertas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple el plan | Estado |
| --- | --- | --- |
| I. El modelo juzga, el código decide | No se pregunta nada al modelo; el código de salida y los estados se calculan en dominio puro | Cumple |
| II. Escape y confianza | No hay decisiones ni acciones automatizables | No aplica |
| III. Una definición, aislada del proveedor | Dominio sin E/S; TypeSafe y Azure detrás de puertos con fakes; `import-linter` activo desde el primer commit | Cumple |
| IV. Evidencia antes que afirmación | Tests primero; suite sin red ni claves; humo `live` marcado y opcional; respuestas simuladas etiquetadas como sintéticas | Cumple |
| V. Seguridad y privacidad | Secretos solo en `.env`; gitleaks; `doctor` no muestra claves ni respuestas; logger del SDK en `WARNING` con test (R12) | Cumple |
| VI. Autocontenido, neutral y original | Puertas como tareas del repo, iguales en pre-commit, CI y agentes; CI Linux y Windows; comprobación de rutas absolutas y de `CLAUDE.md` | Cumple |
| VII. Cortes verticales que enseñan | Spec de cimientos (excepción de corte vertical); 4 historias demostrables; lección 000 | Cumple |
| Flujo y puertas | Lint, tipos, tests, dependencias y secretos en pre-commit y CI | Cumple |

Re-evaluación tras el diseño (fase 1): sin cambios. No hay excepciones que registrar.

## Project Structure

### Documentation (this feature)

```text
specs/000-cimientos/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli-doctor.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
src/jevlab/
├── __init__.py
├── domain/
│   └── diagnostics.py         # CheckStatus, Scope, CheckResult, DoctorReport, errores de proveedor
├── application/
│   └── check_environment.py   # CheckEnvironment
├── ports/
│   ├── environment.py         # LocalEnvironment
│   └── providers.py           # ModelCatalog, GeneratorProbe
├── adapters/
│   ├── local_environment.py   # python3 por subproceso, sys.version_info, .env con pydantic-settings
│   ├── typesafe_catalog.py    # TypeSafeClient.models.list()
│   └── azure_probe.py         # AzureOpenAI, llamada mínima
└── entrypoints/
    └── cli/
        └── main.py            # app Typer `jevlab`, comando `doctor`, cableado y logger del SDK

scripts/checks/                # puertas propias, una por módulo
├── writing.py
├── commit_msg.py
├── presets.py
├── paths.py
└── agents.py

tests/
├── fakes.py                   # FakeLocalEnvironment, FakeModelCatalog, FakeGeneratorProbe
├── unit/                      # dominio (con hypothesis), aplicación, CLI, scripts/checks
├── contract/                  # adaptadores con transportes simulados (respuestas sintéticas)
├── integration/               # un test por historia
└── live/                      # humo de `jevlab doctor --remote`

pyproject.toml                 # dependencias, tareas poe, pytest, coverage, ruff, mypy
.importlinter
.pre-commit-config.yaml
.github/workflows/ci.yml
.env.example
LICENSE
README.md
docs/setup.md
docs/lessons/000-metodo-sdd-y-entorno-reproducible.md
```

**Structure Decision**: un solo paquete con las capas de `docs/standards/architecture.md`. Las
puertas propias viven en `scripts/checks/` y no en `jevlab`, porque son herramientas del
repositorio y no parte de la CLI; se prueban con la misma suite y cuentan en la cobertura global.

### Puertas de calidad

| Tarea `poe` | Qué comprueba | Deriva de |
| --- | --- | --- |
| `lint` | `ruff check` y `ruff format --check` | §VI, flujo |
| `typecheck` | `mypy --strict` sobre `src/` y `scripts/` | `architecture.md` §3 |
| `lint-imports` | Contratos de `.importlinter` | `architecture.md` §1 y §2 |
| `test` | Suite salvo `live`, con la red bloqueada (para uso manual) | `testing.md` §2 y §3 |
| `cov` | Unitarios y de contrato con la red bloqueada; cobertura del 80 % global y del 95 % en `domain/` | `testing.md` §3 y §4 |
| `test-integration` | Tests `integration` con la red bloqueada | `testing.md` §2 |
| `check-writing` | Redacción de los `.md` | `writing.md` |
| `check-commit-msg` | Mensaje de commit (gancho `commit-msg`) | `version-control.md` |
| `check-presets` | Copia instalada, «Tests are OPTIONAL», paridad de skills, bit de ejecución | `governance.md` §5, ADR-0002 |
| `check-paths` | Rutas absolutas de máquina y enlaces simbólicos | §VI |
| `check-agents` | `CLAUDE.md` solo importa `AGENTS.md` | §VI, ADR-0002 |
| `check` | Todas las anteriores salvo `test` y `check-commit-msg`: cada test se ejecuta una sola vez por commit | |

Gitleaks usa su gancho oficial de pre-commit. Pre-commit ejecuta `check` y gitleaks en cada commit
y `check-commit-msg` en el mensaje; la CI ejecuta `pre-commit run --all-files` (research R7).

## Complexity Tracking

Sin excepciones.

## Diseño de decisiones (jev-lab)

> Deriva de: Constitución §I, §II, §III y §IV · Estándar: `docs/standards/decision-design.md`

No aplica: la spec no pregunta nada al modelo.

## Arquitectura (jev-lab)

> Deriva de: Constitución §III · Estándar: `docs/standards/architecture.md`

| Pieza nueva o cambiada | Capa | Depende de | Cómo se prueba aislada |
| --- | --- | --- | --- |
| `CheckStatus`, `Scope`, `CheckResult`, `DoctorReport` | domain | nada | Unitario y de propiedades: código de salida según estados y `remote_requested` |
| `ProviderUnavailable`, `ProviderRejected` | domain | nada | Unitario |
| `LocalEnvironment` | ports | domain | (protocolo) |
| `ModelCatalog`, `GeneratorProbe` | ports | domain | (protocolo) |
| `CheckEnvironment` | application | ports, domain | Unitario con los tres fakes: cada combinación de estados y sin llamadas remotas si no se piden |
| `SystemLocalEnvironment` | adapters | ports | Contrato con un `.env` temporal y un ejecutable `python3` simulado por ruta |
| `TypeSafeModelCatalog` | adapters | ports, `typesafe-sdk` | Contrato con transporte `httpx2` simulado: lista, 401, error de conexión |
| `AzureGeneratorProbe` | adapters | ports, `openai` | Contrato con transporte `httpx` simulado: respuesta, 401, 404, error de conexión |
| `jevlab doctor` | entrypoints | application, adapters | `CliRunner` con fakes: salida y código de salida; integración con adaptadores locales reales |

- **Efectos externos**: subproceso `python3` y lectura de `.env` (por `LocalEnvironment`); red hacia
  TypeSafe (por `ModelCatalog`) y hacia Azure (por `GeneratorProbe`). No hay reloj, azar ni IDs.
- **Puertos nuevos**: `LocalEnvironment`, `ModelCatalog` y `GeneratorProbe`, cada uno con su
  adaptador real y su fake en `tests/fakes.py`.
- **Una sola definición**: no aplica, la feature no tiene decisiones.
- **Contratos de `import-linter`**: capas `entrypoints`, `application`, `domain`; `adapters` y
  `application` solo dependen de `ports` y `domain`; `domain` no importa `typesafe_sdk` ni `openai`.

## Seguridad (jev-lab)

> Deriva de: Constitución §V · Estándar: `docs/standards/security.md`

| Dato o entrada | Origen | Confiable | Qué se registra (sin *payloads* ni datos personales) |
| --- | --- | --- | --- |
| Claves de `.env` | Persona | Sí, pero secreto | Solo el nombre de la variable que falta |
| Lista de modelos de TypeSafe | API externa | No: solo se compara con nombres esperados | Nombres de modelo |
| Respuesta de Azure | API externa | No: solo se mira si hubo error | Nada del contenido; solo el estado |
| Errores HTTP de los SDK | API externa | No | Código de estado y tipo de error, sin cuerpo |

- **Secretos nuevos**: `TYPESAFE_API_KEY`, `TYPESAFE_DEFAULT_MODEL` (no secreto),
  `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT` y
  `AZURE_OPENAI_API_VERSION` en `.env.example`; los leen `TypeSafeModelCatalog`,
  `AzureGeneratorProbe` y `SystemLocalEnvironment` (solo presencia).
- **Contenido adversarial**: no aplica; no se envía contenido externo a ningún modelo.
- **CI pública**: sin *secrets* en esta spec; el workflow solo usa `pull_request` y `push`, nunca
  `pull_request_target` (`security.md` §5).
