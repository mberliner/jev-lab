# Plan: `jev-lab`, laboratorio progresivo de Jev (TypeSafe) con SDD y Spec Kit

## Context

Queremos un proyecto **propio** de aprendizaje con rigor, que vaya de lo básico a técnicas de producción. Pone el foco en lo que distingue a Jev:
- las distribuciones y la confianza como eje de decisión;
- la opción de escape en cada Choice;
- la calibración con datos propios;
- la resiliencia y la observabilidad;
- el conocimiento explícito de sus modos de fallo y sus mitigaciones. Se apoya en la documentación oficial de TypeSafe y en fuentes primarias de prestigio, y se gestiona con **Spec-Driven Development (Spec Kit)**.

**Decisiones del usuario**
- Stack: **Python + SDK oficial `typesafe-sdk`** (uv).
- Claves: **TypeSafe + Azure OpenAI** (el baseline comparativo es Azure).
- **Proyecto autocontenido y agnóstico:** el repo arranca y funciona aislado, sin depender de rutas, memorias ni configuración externas. Todo lo fundamental (plan, constitución, instrucciones para agentes, puesta en marcha) vive en el repo. Este documento, `docs/roadmap.md`, es el plan vigente.
- **Contenido original:** código, escenarios, datos y textos son propios. Solo se citan la documentación oficial de TypeSafe y otras fuentes primarias.
- Spec Kit: ya instalado con `uv tool install specify-cli`.
- **Cada spec (salvo la 000) debe ser un corte vertical hasta el usuario, de unas 4 historias de usuario.**

**Base de la documentación oficial**
- *Jaggedness* de jev-1.13: **13 limitaciones documentadas**, entre ellas conteo, representaciones numéricas, matemáticas sobre Score, instrucciones contradictorias y sesgo por orden de opciones.
- Fórmula oficial de confianza:
  - Choice: `(p_max − 1/n)/(1 − 1/n)`;
  - Score: basada en la distancia ponderada a la moda;
  - Noul: no trae confianza; se sugiere `|2p−1|`.
- El SDK de Python ofrece:
  - `TypeSafeClient` / `AsyncTypeSafeClient`;
  - `Noul` / `Choice` / `Score`, y `response_model` con Pydantic;
  - `RetryPolicy`, `TypeSafeAPIError(.status, .request_id)`;
  - variables `TYPESAFE_API_KEY`, `TYPESAFE_DEFAULT_MODEL` y `TYPESAFE_LOG_LEVEL`.
  - **Riesgo:** en nivel `debug` registra los *bodies* en los logs.
- Guía "How to build":
  - el control queda en el código;
  - preguntas atómicas;
  - estado mínimo con rutas entre backticks;
  - muchas preguntas en una sola llamada;
  - la composición se hace en código;
  - los umbrales se eligen trazando confianza frente a acierto con datos propios.
- Hay un *agent skill* oficial para Claude Code (`claude plugin install typesafe@typesafe-ai`). Es útil como ayuda mientras desarrollamos, no es una dependencia.

---

## Criterios de diseño de las specs

1. **Corte vertical:** cada spec es una capacidad de dominio que atraviesa todas las capas: diseño de preguntas → cliente SDK → política en código → interfaz (CLI o API) → tests → lección. Entrega algo ejecutable a un usuario concreto.
2. **Progresión de producción:** las técnicas de producción crecen de menor a mayor, spec a spec.
3. **Tamaño:** 4 historias P1–P4 por spec, cada una probable y demostrable por sí sola, en el formato de `spec.md` de Spec Kit.

**Usuarios (personas)**
- **Aprendiz:** desarrollador que estudia Jev con la CLI y las lecciones.
- **Operador:** atiende la cola de revisión y ajusta umbrales.
- **Integrador:** consume la API desde otro sistema.

---

## Funcionamiento igual en Claude Code y Antigravity (`agy`)

Spec Kit admite varias integraciones en el mismo proyecto. Según la [referencia de integraciones](https://github.github.io/spec-kit/reference/integrations.html):
- claves `claude` → `.claude/skills/` y `agy` → `.agents/skills/`;
- `agy` no está declarada como segura para instalarse junto a otras, así que hace falta `--force`;
- la integración por defecto queda en `.specify/integration.json`.

**Cómo se consigue la paridad:**
1. `specify init . --integration claude` y después `specify integration install agy --force`. Comprobar con `specify integration status --json`. Las dos comparten `.specify/` (constitución, plantillas y scripts) y `specs/`, de modo que **los artefactos SDD son los mismos para los dos agentes**.
2. **Una sola fuente de instrucciones:** `AGENTS.md` (convenciones, comandos, constitución resumida y puesta en marcha). `CLAUDE.md` solo contiene `@AGENTS.md`, sin reglas propias. Antigravity lee `AGENTS.md` y `.agents/`.
3. **Neutralidad de herramientas:** todo flujo se ejecuta con comandos del repo (`uv run poe <tarea>`, multiplataforma), nunca con *hooks* ni comandos exclusivos de un agente. Las puertas de calidad son pre-commit y CI, que se aplican igual uses el agente que uses.
4. **Skill de TypeSafe:** se instala por usuario, no se copia en el repo. En Claude Code va como plugin oficial. En `agy` se instala la misma skill en su directorio de usuario si la licencia lo permite; si no, `AGENTS.md` enlaza la documentación oficial (`docs.typesafe.ai/llms.txt`).
5. **Invocación:** en Claude Code las skills de Spec Kit se llaman `/speckit-*` y en Antigravity también `/speckit-*`. La guía `docs/agents.md` documenta las dos.
6. **Verificación de paridad (CI):** `specify integration status` muestra las dos integraciones; un test comprueba que `CLAUDE.md` solo importa `AGENTS.md`. La spec 000 se valida corriendo `/speckit-specify` de prueba en cada agente.

> Antes de instalar, confirmar con `specify init --help` y `specify integration list` en la versión instalada, porque los flags han cambiado (`--ai` → `--integration`).

## Funcionamiento igual en Windows y Linux

No hay nada que lo impida. Todo el stack es multiplataforma: Python 3.13 (vía uv), uv, SDK `typesafe-sdk` (puro Python/httpx), `openai`, FastAPI, SQLite, pre-commit, Claude Code y Antigravity. Hay que fijar estas convenciones:

| Punto | Convención |
| --- | --- |
| **Scripts de Spec Kit** | **`--script py`** (disponible en Specify CLI 1.1.4): los scripts de Spec Kit son Python y funcionan igual en Windows y Linux, sin depender de bash ni de PowerShell. |
| **Tareas del proyecto** | `poethepoet` declarado en `pyproject.toml` y ejecutado con `uv run poe test` / `lint` / `eval`. Las tareas complejas son scripts Python (`scripts/*.py`), que no dependen de bash ni de cmd. |
| **Finales de línea** | `.gitattributes`: `* text=auto eol=lf`, `*.ps1 eol=crlf`, `*.cmd eol=crlf`, binarios marcados como `binary`. |
| **Enlaces simbólicos** | Ninguno en el repo. `CLAUDE.md` usa `@AGENTS.md` (import, no symlink). |
| **Rutas y ficheros** | `pathlib` siempre; `encoding="utf-8"` explícito; nombres de archivo en minúsculas, sin `:` ni espacios. |
| **Variables de entorno** | `.env` cargado con `pydantic-settings`, sin `export` de shell. |
| **Dos intérpretes, papeles separados** | (a) **Spec Kit** ejecuta sus scripts con `python3` del sistema, ≥ 3.8 (probado con 3.8.10 en Linux; en Windows se añade un enlace duro `python3.exe` → `python.exe` del 3.13 existente). (b) **El proyecto** usa **Python 3.13 gestionado por uv** (`.python-version` = 3.13), en espacio de usuario y sin instalar nada en el sistema; en Windows uv reutiliza el 3.13 instalado. `typesafe-sdk` 0.7.4 requiere ≥ 3.10 y soporta 3.13. |
| **Ejecución de código del proyecto** | Siempre con `uv run …` (tareas `poe`, `scripts/*.py`), nunca con `python3` directo, para no caer en el Python del sistema. |
| **Dependencias** | Solo paquetes con wheels para Windows y Linux (p. ej. sin `uvloop` obligatorio). |
| **Contenedores (007)** | Docker Desktop con WSL2 en Windows; el servicio también arranca sin Docker (`uv run poe api`) con SQLite. |
| **CI** | Matriz `ubuntu-latest` + `windows-latest` para lint, mypy y tests unitarios y de contrato. Docker y *live* solo en Linux. |

## Arquitectura de aplicaciones

**Monolito modular con arquitectura hexagonal (puertos y adaptadores)** en un solo paquete Python, `jevlab`. Encaja con un laboratorio de un solo equipo y un dominio desplegable. Los límites entre módulos se garantizan con una regla de dependencias comprobada en CI (`import-linter`): `entrypoints → application → domain` y `adapters → ports`.

```
                 ┌───────────── Adaptadores de entrega ─────────────┐
                 │  CLI (Typer): jevlab triage|review|eval|jagged|ask │
                 │  API (FastAPI): /triage /guard/* /ask              │
                 └───────────────────────┬───────────────────────────┘
                                         ▼
          Aplicación (casos de uso): TriageTicket · ResolveReview · GuardInput/Output
                                     AnswerQuestion · EvaluateSpec · RunJaggedExperiment
                                         │ usa
                                         ▼
          Dominio (puro, sin I/O): DecisionSpec (estado + preguntas + modelo + versión)
                                   Policy (bandas por riesgo) · confidence · composite
                                         │ define puertos
                                         ▼
 Puertos:   JudgePort          GeneratorPort      ReviewQueuePort  AuditPort  PolicyConfigPort  CachePort
 Adaptad.:  TypeSafeJudge(SDK) AzureGenerator     SQLite→Postgres  JSONL→DB   YAML versionado   memoria→Redis
            CassetteJudge      (Azure OpenAI)
            AzureLLMJudge (baseline)
            FakeJudge (tests)
```

**Ideas clave**
- **`DecisionSpec` es la unidad central.** Es un objeto declarativo y versionado (Pydantic + YAML) con las preguntas, la opción de escape, la política y el modelo fijado. CLI, API, evaluación (004) y laboratorio de fallos (005) **consumen el mismo spec**, así que lo que se evalúa es exactamente lo que se despliega.
- **`JudgePort` aísla al proveedor.** Jev en vivo, las cassettes, el baseline de Azure y los fakes son intercambiables. Esto da tests sin red, comparación justa y modo offline.
- **El dominio es puro.** Política, confianza y composición son funciones sin I/O, lo que permite tests de propiedades.
- **Los efectos están en adaptadores:** cola de revisión, auditoría, caché y telemetría (OTel).

**Testabilidad: la arquitectura está diseñada para tests unitarios**

Cada capa se prueba de forma aislada, de modo que **la gran mayoría de los tests son unitarios, rápidos (< 1 s el conjunto por módulo) y sin red ni claves**.

| Capa | Tipo de test | Cómo se aísla | Ejemplos |
| --- | --- | --- | --- |
| **Dominio** (puro) | Unitario + propiedades (`hypothesis`) | Sin dependencias: funciones y modelos Pydantic | La fórmula de confianza coincide con la oficial; las bandas de política son monótonas; `other` siempre va a revisión; la composición con pesos es correcta; `DecisionSpec` sin escape → error de validación |
| **Aplicación** (casos de uso) | Unitario | Puertos inyectados con *fakes* en memoria (`FakeJudge` con respuestas programables, `InMemoryReviewQueue`, `FrozenClock`) | `TriageTicket` con confianza 0,4 encola revisión y audita; `GuardInput` con inyección = 0,9 bloquea; modo degradado si `JudgePort` lanza error |
| **Adaptadores** | Contrato | Cassettes VCR de respuestas reales; SQLite en memoria; `respx` para HTTP | `TypeSafeJudge` traduce bien la respuesta del SDK a tipos de dominio; mapeo de `TypeSafeAPIError` a errores de dominio; reintentos ante un 429 simulado |
| **Entrypoints** | Unitario/integración ligera | `typer.testing.CliRunner`, `httpx.AsyncClient` + `TestClient` de FastAPI con dependencias sustituidas | Códigos HTTP, validación de entrada, idempotencia, salida de la CLI |
| **Extremo a extremo** | Live (opcional, `-m live`) | Claves reales y tope de coste | Humo diario en CI |

Reglas que lo garantizan:
- **Inyección de dependencias explícita:** los casos de uso reciben puertos por constructor, y no hay singletons ni llamadas globales al SDK.
- **Puertos como `typing.Protocol`:** los fakes cumplen el protocolo y `mypy --strict` lo verifica.
- **El tiempo, el azar y los IDs entran por puertos** (`Clock`, `IdGenerator`), lo que da tests deterministas.
- **Pirámide de tests vigilada en CI:** cobertura ≥ 80 % global y ≥ 95 % en `domain/`; un test unitario que intente abrir red falla (`pytest-socket`).
- **TDD por historia:** `/speckit-tasks` genera primero las tareas de test (rojo), luego la implementación (verde) y después el refactor.

**Aplicaciones desplegables (por spec en que nacen)**

| App | Usuario | Nace | Evoluciona |
| --- | --- | --- | --- |
| `jevlab` CLI | Aprendiz/Operador | 001 | review (002), eval (004), jagged (005), ask (006) |
| `jevlab-api` (FastAPI, asíncrona) | Integrador | 003 | /ask (006), /triage endurecido (007) |
| Informes de evaluación (HTML/MD estáticos) | Operador | 004 | resultados del laboratorio (005) |
| Stack operativo (`docker compose`): api + Postgres + Redis + OTel Collector + Prometheus/Grafana | Operador | 007 | — |

Los adaptadores evolucionan sin tocar el dominio: SQLite y memoria en 002–006 pasan a Postgres y Redis en 007.

## Estructura objetivo

```
jev-lab/
├── AGENTS.md                 # fuente única de instrucciones para agentes
├── CLAUDE.md                 # solo "@AGENTS.md"
├── .specify/                 # Spec Kit compartido: memory/constitution.md, templates, scripts, integration.json
├── .claude/skills/           # skills speckit para Claude Code
├── .agents/skills/           # skills speckit para Antigravity
├── specs/NNN-<feature>/      # spec.md, plan.md, research.md, data-model.md, tasks.md, contracts/
├── src/jevlab/
│   ├── domain/               # DecisionSpec, policy, confidence, composite (puro)
│   ├── application/          # casos de uso
│   ├── ports/                # interfaces (Protocol)
│   ├── adapters/             # typesafe, cassette, azure, sqlite/postgres, yaml, cache, otel
│   ├── entrypoints/{cli,api}/
│   └── specs/<dominio>/*.yaml  # DecisionSpecs versionados
├── lessons/NN-<tema>/README.md
├── data/<dominio>/*.jsonl    # datasets originales + cassettes/
├── tests/{unit,contract,live}/
├── pyproject.toml (tareas poe) · .gitattributes · .importlinter · .github/workflows/ci.yml · Dockerfile · compose.yaml
```

Cada spec añade solo lo que sus historias necesitan (YAGNI); la estructura se completa poco a poco.

## Constitución (`/speckit.constitution`)

1. **El modelo juzga, el código decide.** La aritmética, las fechas, los conteos, los permisos y los interbloqueos nunca se delegan en Jev.
2. **Preguntas atómicas y literales.** Sin negaciones ni indirección; estado mínimo; rutas entre backticks.
3. **Cada Choice tiene una opción de escape** (`other`/`none`), que se envía a revisión.
4. **Toda acción automatizable pasa por la confianza**, con umbrales por riesgo, versionados y justificados con datos.
5. **Honestidad metodológica.** Los fixtures se etiquetan; no se proclaman ganadores; lo desconocido se marca como "no disponible".
6. **Probar antes de afirmar.** Unitarios sin red; contrato con cassettes; *live* opcional y con tope de coste. TDD y cobertura ≥ 80 %.
7. **Seguridad.** Secretos solo en `.env` + gitleaks; logs sin bodies ni datos personales; el estado es dato no confiable.
8. **Contenido original y autocontenido.** Contenido propio; solo fuentes oficiales y primarias. El repo arranca y funciona aislado: lo fundamental vive dentro, sin rutas, memorias ni configuración externas.
9. **Cortes verticales.** Cada feature entrega valor ejecutable a una persona; unas 4 historias independientes.
10. **Pedagogía.** Cada feature trae su lección, con lo que puede fallar.
11. **Neutralidad de agente y de sistema operativo.** Todo funciona igual en Claude Code y Antigravity, y en Windows y Linux: una sola fuente de instrucciones (`AGENTS.md`), tareas `poe`, sin symlinks, y puertas de calidad en pre-commit y CI con matriz Linux/Windows.
12. **Hexagonal.** El dominio es puro; los proveedores van detrás de puertos; un mismo `DecisionSpec` sirve para servir, evaluar y probar.

Esta lista es **un borrador de entrada**; la constitución definitiva sale del proceso HITL siguiente.

### Depuración HITL de la constitución (parte de la spec 000, antes de cualquier otra spec)

Buenas prácticas que se aplican:
- Plantilla de Spec Kit: versión semántica, fechas de ratificación y enmienda, *Sync Impact Report* y la puerta *Constitution Check* de `plan-template`.
- Principios declarativos y verificables.

1. **Borrador:** `/speckit-constitution` con la lista anterior. El agente redacta cada principio con este formato:
   - **Enunciado** con MUST / SHOULD (RFC 2119);
   - **Justificación**, con enlace a la fuente oficial o primaria;
   - **Cómo se verifica**: puerta concreta (test, lint, check de CI, revisión) o, si no es automatizable, pregunta de revisión.
   - Principios sin forma de verificarse → se reformulan o se pasan a "guía" fuera de la constitución.
2. **Revisión humana estructurada, principio a principio.** Se usan preguntas cerradas: mantener / editar / eliminar, y MUST frente a SHOULD. Criterios del checklist:
   - atómico (una sola idea);
   - sin ambigüedad ("rápido" o "seguro" sin métrica no valen);
   - sin solapes ni contradicciones con otros principios;
   - no prescribe detalles de implementación que corresponden a `plan.md`;
   - conjunto pequeño (≤ 12) y priorizado.
3. **Prueba con escenarios (*red-team* de la constitución).** Se contrastan los principios con 4–6 situaciones reales del proyecto y el humano valida cada veredicto. Por ejemplo:
   - ¿la US4 de 001 (cassettes) cumple "probar antes de afirmar"?
   - ¿un Choice de 3 opciones sin `other` se bloquea?
   - ¿un clon nuevo sin memorias del agente puede ejecutar `/speckit-specify` solo con `AGENTS.md`?
   - ¿un hook exclusivo de Claude rompe la neutralidad?
   Se ajusta lo que bloquee de más o deje pasar algo indebido.
4. **Segunda opinión con el otro agente.** Si se redactó en Claude Code, se revisa en Antigravity, o al revés, con el mismo checklist. Las discrepancias las resuelve el humano. Así se valida también la paridad entre agentes.
5. **Ratificación.** El humano aprueba explícitamente:
   - versión `1.0.0` con fecha de ratificación;
   - *Sync Impact Report* revisado, con plantillas `plan`, `spec` y `tasks` alineadas (`/speckit-analyze` sin conflictos);
   - commit propio `docs(constitution): ratify v1.0.0`.
6. **Gobierno de enmiendas** (queda escrito en la propia constitución):
   - cambio por PR con justificación;
   - semver: MAJOR si se elimina o redefine un principio, MINOR si se añade, PATCH si se aclara;
   - aprobación humana obligatoria;
   - revisión de la constitución al cerrar cada spec (retro de 10 min: ¿algún principio estorbó o faltó?).

---

## Specs

En cada spec se recorre `/speckit.specify → clarify → plan → tasks → analyze → implement`, en la rama `NNN-nombre`, con commit por historia.

### 000: Cimientos (no es vertical, por diseño)
- `git init`, `uv init --package` (Python 3.13 vía uv; `.python-version` = 3.13).
- Dependencias: `typesafe-sdk`, `openai`, `pydantic`, `python-dotenv`, `typer`.
- Desarrollo: ruff, mypy, pytest, vcrpy/pytest-recording, pre-commit, gitleaks.
- CI mínima.
- `specify init . --integration claude` + `specify integration install agy --force`, `AGENTS.md` y `CLAUDE.md` (`@AGENTS.md`), y constitución.
- Esqueleto hexagonal vacío (`domain/ports/adapters/entrypoints`) + `import-linter` en CI + tareas `poe` + `.gitattributes` + CI con matriz Linux/Windows.
- `docs/setup.md` con la puesta en marcha en Linux y Windows: uv, Python 3.13, el enlace `python3.exe` en Windows (`New-Item -ItemType HardLink -Path "$dir\python3.exe" -Target "$dir\python.exe"`), Git Bash y los dos agentes.
- `.env.example` con `TYPESAFE_API_KEY` y `AZURE_OPENAI_{ENDPOINT,API_KEY,DEPLOYMENT,API_VERSION}`.
- **Espacio reservado: mecanismos de arquitectura y definiciones globales (según Spec Kit).** Se decide en HITL, después de ratificar la constitución y antes de la spec 001. El objetivo es fijar **dónde viven y cómo se aplican** las decisiones que afectan a todas las specs, para que cada `plan.md` las herede en vez de redefinirlas.
  - *Capas de Spec Kit disponibles:*
    - `.specify/memory/constitution.md`: principios, el "qué es innegociable";
    - `.specify/memory/` con documentos globales adicionales, por ejemplo `architecture.md` (hexagonal, regla de dependencias, puertos), `tech-stack.md` (versiones fijadas), `glossary.md` (DecisionSpec, banda, escape…), `testing-strategy.md` y `security.md`;
    - **plantillas personalizadas** en `.specify/templates/` (`plan-template.md` con *Technical Context* que referencia esos documentos y *Constitution Check* ampliado; `spec-template.md` con personas fijas; `tasks-template.md` con TDD), o mejor como **preset/extensión** de Spec Kit (`specify extension add`) para que sobreviva a `specify integration upgrade`;
    - **ADRs** (`docs/adr/NNNN-*.md`, formato MADR) para decisiones con alternativas;
    - `research.md` y `data-model.md` por feature, solo para lo local.
  - *Preguntas a resolver (HITL):*
    1. ¿Documentos globales en `.specify/memory/` o ADRs, o ambos con reparto claro?
    2. ¿Plantillas editadas directamente o mediante preset o extensión versionada?
    3. ¿Cómo se propaga un cambio global a specs ya cerradas (re-analyze, retro)?
    4. ¿Qué puerta automática lo verifica (`/speckit-analyze`, checklist `/speckit-checklist` de arquitectura, `import-linter`)?
  - *Resultado esperado:* `architecture.md` + ADR-0001 (hexagonal) + ADR-0002 (paridad Claude/agy) + plantillas o preset ajustados, aprobados por el humano.
- **Aceptación:**
  - constitución v1.0.0 ratificada por el humano tras los 6 pasos HITL;
  - mecanismos de definiciones globales acordados y aplicados en las plantillas;
  - pytest y CI en verde;
  - pre-commit activo.
- **Comprobación de humo (no es una historia):** `jevlab doctor` comprueba que `python3` (≥ 3.8) existe para Spec Kit, que el intérprete del proyecto es 3.13, que hay claves, lista los modelos de Jev y llama al deployment de Azure.

### 001: Triaje de un ticket de soporte (Aprendiz)
*Aprende: las tres primitivas y cómo leer la salida nativa.*
- **US1 (P1):** clasifico un ticket con `jevlab triage "<texto>"` y veo la cola elegida, la distribución completa y la `confidence`. Choice con `other`.
- **US2 (P2):** veo si el ticket menciona explícitamente un problema urgente (Noul). Lo que cae en la banda incierta se muestra como "incierto", no como "medio".
- **US3 (P3):** veo la prioridad en una escala ordenada (Score con `legend`), usada solo para comparar con un umbral, no como magnitud.
- **US4 (P4):** repito todo **sin red ni coste** reproduciendo respuestas reales grabadas (cassettes). La salida indica que es una grabación.
- *Producción introducida:* cliente reutilizado, `RetryPolicy` por defecto, timeout, errores sin filtrar datos y logs `info` sin bodies.
- *Verificación:* test de contrato con cassette; `confidence.py` reproduce la fórmula oficial a partir de `probabilities`.

### 002: Enrutado con confianza según riesgo (Aprendiz → Operador)
*Aprende: la confianza como segundo eje de decisión; umbrales por riesgo.*
- **US1 (P1):** un ticket con confianza alta se enruta solo y la CLI explica el motivo (umbral y valor).
- **US2 (P2):** si la acción es destructiva (p. ej. reembolso automático), se exige un umbral más alto; si no se alcanza, se pide confirmación.
- **US3 (P3):** lo que tiene confianza baja o `other` entra en una **cola de revisión** (SQLite). Como Operador la listo y la resuelvo con `jevlab review`.
- **US4 (P4):** como Operador cambio los umbrales en `policy.yaml` versionado, sin tocar código, y la CLI muestra qué versión se aplicó.
- *Producción introducida:* configuración validada con Pydantic, auditoría de decisiones con `request_id` y tests de propiedades (hypothesis) que comprueban que las bandas son monótonas.

### 003: Guardarraíl de un asistente con fan-out y composición (Integrador)
*Aprende: los patrones oficiales de fan-out, composite scoring e intent routing.*
- **US1 (P1):** como Integrador llamo a `POST /guard/input` y, en **una sola llamada** a Jev con varios Noul atómicos (inyección, datos personales, fuera de ámbito), recibo la decisión `allow/review/block`.
- **US2 (P2):** el endpoint enruta la intención: código determinista, Azure OpenAI o persona.
- **US3 (P3):** `POST /guard/output` puntúa la respuesta generada por Azure con varios Score (grounding, relevancia, tono). La composición con pesos se hace en código.
- **US4 (P4):** veo la medida de latencia y coste de 1 llamada frente a N llamadas (`jevlab bench fanout`).
- *Producción introducida:* FastAPI con `AsyncTypeSafeClient` en el *lifespan*, contratos OpenAPI en `contracts/`, límite de tamaño del estado y estado tratado como dato no confiable.

### 004: ¿Puedo fiarme? Evaluación y calibración del triaje (Operador)
*Aprende: evaluar con datos propios y elegir umbrales con evidencia.*
- **US1 (P1):** con `jevlab eval triage` evalúo un dataset etiquetado original (~200 ítems: claros, ambiguos, fuera de dominio y adversariales) y obtengo un informe con macro-F1 y la matriz de confusión.
- **US2 (P2):** el informe incluye la **calibración**: Brier, ECE y diagrama de fiabilidad.
- **US3 (P3):** obtengo la **curva cobertura-precisión** y un umbral recomendado para una precisión objetivo. Se exporta como propuesta de `policy.yaml`, con lo que se cierra el ciclo con la 002.
- **US4 (P4):** comparo con el baseline **Azure OpenAI** (Structured Outputs estricto, mismas preguntas): acierto, latencia p50/p95 y coste por cada 1.000 llamadas. Se advierte que sus "probabilidades" son autodeclaradas.
- *Producción introducida:* datasets versionados, ejecución reproducible (semilla y modelo fijado, p. ej. `jev-1.13`) y test de regresión al cambiar de modelo.

### 005: Laboratorio de modos de fallo (Aprendiz)
*Aprende: dónde falla Jev y cómo se mitiga, con datos propios.* Cada historia es una comparación entre un diseño ingenuo y su mitigación, con `jevlab jagged <grupo>`, y usa el evaluador de la 004.
- **US1 (P1), números y tiempo:** matemáticas, conteo, representaciones numéricas, magnitudes de Score y fechas. La mitigación es extraer componentes con Choice y calcular en código.
- **US2 (P2), redacción:** lectura literal, negación e indirección, instrucciones contradictorias.
- **US3 (P3), sesgo de orden:** test de permutación de opciones y métrica de consistencia. También self-consistency (cookbooks).
- **US4 (P4), contexto:** estado irrelevante o largo (filtro previo y Noul de relevancia) y contenido adversarial. La generación se demuestra con la cascada: candidatos por regex y Jev elige.
- *Resultado:* tabla "fallo → mitigación → Δ medido" generada a partir de los datos.

### 006: Asistente RAG verificado (Aprendiz/Integrador)
*Aprende: Jev dentro de un pipeline generativo; Azure genera y Jev decide.*
- **US1 (P1):** pregunto con `jevlab ask` (y `POST /ask`) sobre un corpus pequeño y original. Solo se usan los pasajes que pasan dos Noul independientes: relevancia e instrucciones incrustadas.
- **US2 (P2):** los pasajes se re-ordenan con Score antes de generar.
- **US3 (P3):** cada cita de la respuesta se verifica contra su pasaje (Choice soportado / contradicho / insuficiente). Las no soportadas se marcan o se retiran.
- **US4 (P4):** si la verificación o el guardarraíl de salida (reutiliza la 003) fallan, recibo una respuesta explícita de abstención ("no puedo responder con garantías").
- *Producción introducida:* presupuesto de tokens por petición, caché por hash de estado y preguntas, y trazas OpenTelemetry por etapa.

### 007: Triaje en producción (Integrador + Operador)
*Aprende: desplegar y operar una decisión tipada con seguridad.* Lleva el dominio de las 001/002/004 a producción.
- **US1 (P1):** como Integrador uso `POST /triage` con idempotencia, *rate limit* por cliente, reintentos con backoff ante 429/5xx, *circuit breaker* y respuesta degradada (todo a revisión) si Jev no está disponible.
- **US2 (P2):** como Operador despliego un cambio en **modo shadow** (observe) y comparo con la política vigente antes de pasar a **enforce**.
- **US3 (P3):** las resoluciones de la cola de revisión vuelven al dataset etiquetado y relanzan `jevlab eval`. Es el ciclo de mejora continua.
- **US4 (P4):** como Operador veo métricas y alertas: latencia, tasa de escalado, distribución de confianza y deriva de `other`. Uso Prometheus/OTel y un dashboard sencillo.
- *Entrega:* Dockerfile, `docker compose`, job *live* nocturno en CI con tope de coste.

**Progresión de técnicas de producción:** 001 cliente/reintentos/logs seguros → 002 configuración versionada y auditoría → 003 API asíncrona y contratos → 004 evaluación reproducible y modelo fijado → 006 presupuesto, caché y trazas → 007 resiliencia, shadow/enforce, retroalimentación y monitorización.

---

## Verificación
- Por spec: `/speckit.analyze` sin inconsistencias graves antes de implementar. Cada US cumple sus escenarios Given/When/Then de `spec.md` y se puede demostrar por separado.
- `uv run ruff check && uv run mypy src && uv run pytest -m "not live" --cov` en verde (≥ 80 %); `uv run pytest -m live` con claves reales.
- Demostración de cada US con la CLI o con `curl` contra la API, tanto con cassettes como en vivo.
- 007: `docker compose up`, un 429 simulado que se resuelve con reintento, y modo degradado si Jev cae.
- **Multiplataforma:** el job de CI en `windows-latest` pasa en verde, y en una máquina Windows `uv sync && uv run poe test` funciona sin pasos extra.
- **Aislamiento:** un clon nuevo en una máquina sin memorias ni configuración previas (Linux o Windows) arranca siguiendo solo `README.md` y `docs/setup.md`, y los agentes encuentran todo lo que necesitan en `AGENTS.md`. Ningún archivo del repo contiene rutas absolutas de una máquina (comprobación en CI).

## Primeros pasos tras aprobar
0. ✅ Hecho: plan en `docs/roadmap.md` (dentro del repo).
1. ✅ Hecho: `specify check` (CLI 1.1.4; Claude Code y Antigravity detectados; `--script py` disponible).
2. ✅ Hecho (pendiente de commit): `mkdir jev-lab && cd jev-lab && git init`, crear primero `.gitattributes` y luego `specify init . --integration claude --script py && specify integration install agy --force && specify integration status`.
3. ✅ `AGENTS.md` mínimo de arranque y `CLAUDE.md` (`@AGENTS.md`), para que cualquier agente abierto en `jev-lab/` tenga el contexto sin memorias externas. Se completan en la spec 000.
4. Abrir el agente **dentro de `jev-lab/`** (Claude Code: `claude`; Antigravity: abrir la carpeta) y ejecutar `/speckit-constitution` con el borrador y luego depuración HITL (pasos 1–6) hasta ratificar la v1.0.0. Luego HITL de mecanismos de arquitectura y definiciones globales. Después, el resto de la spec 000.

---

## Apéndice A: referencias de coste (a verificar)

- Precio orientativo de Jev 1.13: unos **0,042 USD por millón de tokens de entrada**, con salida sin coste. **Hay que confirmarlo en la página oficial de modelos y precios de TypeSafe antes de usarlo** en la 003 (bench de fan-out) y la 004 (coste por cada 1.000 llamadas).
- Azure OpenAI: tomar el precio del deployment concreto en la página oficial de precios de Azure; varía por región y modelo.
- Si un coste no se conoce, se muestra como "no disponible" (constitución, principio 5).

## Apéndice B: banco de ideas para futuras specs

Ideas de dominio para specs posteriores a la 007, o como escenarios alternativos dentro de las existentes. Se apoyan en los *cookbooks* y el *use-case map* oficiales de TypeSafe. Todo el contenido se redacta de cero.

| Dominio | Decisiones candidatas | Primitiva / patrón |
| --- | --- | --- |
| Atención al cliente | Riesgo de baja, intención comercial, motivo de reembolso, sentimiento | Score, Choice + escape |
| Comercio | Atributos de producto, seguridad de marca, señales de demanda como *features* | Choice, Noul, composite |
| Confianza y seguridad | Spam, datos personales, cumplimiento de política propia | Noul con umbrales por riesgo |
| Agentes | Elección de herramienta o *skill*, escalado de modelo, juez con referencia explícita | Choice + `none`, confidence routing |
| Datos y extracción | Selección entre candidatos pre-extraídos, estructura de documento, taxonomía jerárquica (beam search) | Choice; cascada |
| Operaciones | Severidad de incidentes, deduplicación de alertas, triaje de cláusulas | Score, Noul |
| Simulación (didáctica) | Acción discreta con **interbloqueo de seguridad en código** que anula la propuesta | Choice + invariantes en código |

## Apéndice C: ruta de estudio sugerida (lecciones)

1. Las tres primitivas sobre un mismo estado (001)
2. La confianza como segundo eje de decisión (002)
3. Noul con banda de incertidumbre (001 US2, 003)
4. Score y puntuación compuesta (001 US3, 003)
5. Evaluar y calibrar con datos propios (004)
6. Modos de fallo y mitigaciones (005)
7. Jev dentro de RAG y agentes (006)
8. Operar en producción: shadow/enforce y monitorización (007)
