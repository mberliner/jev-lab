# Gobernanza de reglas: constitución, presets y estándares

Guía de buenas prácticas para decidir **dónde vive cada regla común a todas las specs** y cómo se
mantiene. Se aplica a cualquier tema transversal: arquitectura, UX, seguridad, evaluación, etc.

Este documento describe el **mecanismo**, no el contenido. Los principios concretos están en la
constitución, y las reglas detalladas, en los presets y estándares de cada tema.

## 1. Las tres capas

Cada tema transversal se gobierna con tres capas. Cada capa tiene una responsabilidad distinta y
remite a la capa superior.

```
Constitución  (tema)  ─ QUÉ debe cumplirse siempre y POR QUÉ
     │ se concreta en
     ▼
Preset        (tema)  ─ QUÉ debe contestar cada artefacto (spec, plan, tasks, checklist)
     │ remite a
     ▼
Estándar      (tema)  ─ CÓMO se hace, con detalle y ejemplos
```

| | Constitución | Preset | Estándar |
| --- | --- | --- | --- |
| **Responsabilidad** | Principios innegociables (MUST/SHOULD) y su motivo | Forzar que cada artefacto SDD trate el tema: secciones, preguntas, tareas y comprobaciones obligatorias | Conocimiento de referencia: convenciones, patrones, ejemplos y antiejemplos |
| **Naturaleza** | Normativa | Estructural | Descriptiva |
| **Alcance** | Todo el proyecto | Un tema; actúa al generar artefactos | Un tema; se consulta al diseñar e implementar |
| **Granularidad** | Un principio por idea, sin tecnología concreta | Una sección por plantilla afectada | Todo el detalle necesario |
| **Ubicación** | `.specify/memory/constitution.md` | `presets/jevlab-<tema>/` (fuente) → `.specify/presets/` (instalado) | `docs/standards/<tema>.md` |
| **Ritmo de cambio** | Raro; enmienda formal | Moderado; al aprender de una spec | Frecuente; evoluciona con el código |
| **Versionado** | Semver de la constitución (ver *Versionado de documentos*) | `version` del `preset.yml` (ídem) | Historial de git |
| **Aprobación** | Humana obligatoria (HITL) | Humana, por PR | PR normal |
| **Cómo se hace cumplir** | Puerta *Constitution Check* del plan; `/speckit-analyze` | El agente no puede generar el artefacto sin la sección; checklist del tema | Revisión de código, lint, tests, `import-linter` |

### Otras piezas (no son capas de reglas)

| Pieza | Para qué | Ubicación |
| --- | --- | --- |
| **ADR** | Registrar **una decisión** con sus alternativas y consecuencias. Explica *por qué* existe un estándar o un principio, pero no es una regla en sí. | `docs/adr/NNNN-<titulo>.md` (MADR) |
| **Artefactos de feature** | Decisiones **locales** a una spec | `specs/NNN-*/` (`research.md`, `plan.md`…) |
| **`AGENTS.md`** | Instrucciones operativas para agentes: comandos, entorno, punteros a esta guía | raíz |

### Precedencia

`constitución` > `preset` > `estándar` > `plan.md` de la feature.

Ninguna capa inferior puede contradecir a una superior. Si un estándar necesita algo que la
constitución prohíbe, se enmienda la constitución o se registra una excepción en la tabla
*Complexity Tracking* del `plan.md` de esa feature, justificada y aprobada.

## 2. Dónde va una regla: criterio de clasificación

Se responden estas preguntas en orden. La primera respuesta "sí" decide la capa.

1. **¿Se puede enunciar sin nombrar una tecnología, una sección de documento ni un archivo, y su
   incumplimiento invalidaría una feature entera?** → **Constitución**.
2. **¿Es algo que *cada* spec, plan o lista de tareas debe declarar, responder o incluir?** →
   **Preset** del tema.
3. **¿Es una convención, un patrón o un ejemplo de cómo hacerlo bien?** → **Estándar** del tema.
4. **¿Es una elección entre alternativas que conviene recordar?** → **ADR** (y, si genera regla, la
   regla va además a su capa).
5. **¿Solo afecta a una feature?** → artefactos de esa spec. No es una regla común.

Ejemplos:

| Regla | Capa | Motivo |
| --- | --- | --- |
| "El dominio no hace I/O; todo efecto pasa por un puerto" | Constitución | Invariante del proyecto, sin tecnología concreta |
| "Cada plan lista los puertos nuevos o afectados y sus adaptadores" | Preset `arch` | Obliga a cada `plan.md` a contestar algo |
| "Los puertos son `typing.Protocol` y se nombran `<Algo>Port`" | Estándar `architecture` | Convención de implementación |
| "Elegimos hexagonal frente a capas clásicas" | ADR | Decisión con alternativas |
| "Toda decisión expuesta al usuario muestra resultado, confianza y motivo de escalado" | Constitución | Invariante de experiencia |
| "Cada spec describe los estados auto/revisión/escape por persona" | Preset `ux` | Sección obligatoria de `spec.md` |
| "Formato de error de la API: `{code, message, request_id}`" | Estándar `api-errors` | Detalle de implementación |

## 3. Trazabilidad entre capas

Cada regla de un preset o un estándar debe poder rastrearse hasta un principio. Si no se puede,
esa regla sobra o falta un principio.

- Los principios de la constitución llevan número romano estable (`I`, `II`, …). No se reutilizan
  números de principios eliminados.
- Cada sección que añade un preset empieza con una línea de origen:
  `> Deriva de: Constitución §III · Estándar: docs/standards/cli-ux.md`
- Cada estándar empieza con una cabecera que indica los principios que concreta y el preset que lo
  exige.
- `/speckit-analyze` y la checklist del tema comprueban que cada artefacto cubre las secciones del
  preset.

## 4. Organización por tema

Un tema existe cuando tiene al menos un principio en la constitución. A partir de ahí puede tener
preset, estándar o ambos, según lo necesite.

| Tema | Principio(s) | Preset | Estándar(es) | Estado |
| --- | --- | --- | --- | --- |
| Arquitectura | *(tras ratificar)* | `jevlab-arch` | `architecture.md` | previsto en 000 |
| UX (CLI/API) | *(tras ratificar)* | `jevlab-ux` | `cli-ux.md`, `api-errors.md` | previsto en 000 |
| Decisión Jev (escape, umbrales, calibración) | *(tras ratificar)* | `jevlab-decision` | `decision-design.md` | previsto en 000 |
| Testing | *(tras ratificar)* | *(por decidir)* | `testing.md` | pendiente |
| Seguridad | *(tras ratificar)* | *(por decidir)* | `security.md` | pendiente |

Esta tabla se actualiza al crear o retirar un tema.

## 5. Presets propios: convenciones

Los presets de este proyecto son **propios y viven en el repo**. No se instalan presets del
catálogo comunitario.

### Estructura

```
presets/jevlab-<tema>/          # fuente versionada (la que se edita)
├── preset.yml                  # manifiesto
├── README.md                   # qué añade, de qué principios deriva
└── templates/
    ├── plan-template.md        # solo el fragmento que se añade
    └── spec-template.md
```

Se instala con `specify preset add --dev presets/jevlab-<tema> --priority <n>`. Eso lo deja en
`.specify/presets/`, que también se versiona para que un clon nuevo funcione sin pasos extra.

### Reglas

1. **Componer, no sustituir.** Se usa `strategy: append` (o `prepend`/`wrap`) sobre la plantilla
   base. `replace` solo se usa si hay un motivo escrito en el README del preset. Así varios presets
   conviven en la misma plantilla y las mejoras de Spec Kit se siguen recibiendo.
2. **Un preset por tema.** Un preset no mezcla arquitectura con UX. Así cada tema se puede activar,
   desactivar o versionar por separado.
3. **Fragmentos cortos que exigen y enlazan.** El fragmento plantea las preguntas o la tabla que hay
   que rellenar y enlaza al estándar. No copia el estándar.
4. **Prioridad explícita.** El orden de composición se fija con `--priority` y se documenta en la
   tabla del apartado 4.
5. **Sin overrides.** No se usa `.specify/templates/overrides/`: sustituye la plantilla entera y
   rompería la composición por temas.
6. **Sin dependencias de un agente.** Los fragmentos son Markdown neutro. Funcionan igual con Claude
   Code y Antigravity.

### Nota técnica

La composición de plantillas con `preset.yml` necesita **PyYAML en el `python3` que ejecuta los
scripts de Spec Kit**. Si no está disponible (habitual en Windows), se puede apuntar
`SPECKIT_PYTHON_EXECUTABLE` a un intérprete que lo tenga, por ejemplo el del `uv tool` de
`specify-cli`. `docs/setup.md` documenta cómo.

## 6. Estándares: convenciones

- Un archivo por tema (o subtema) en `docs/standards/`.
- Cabecera fija:
  ```
  > Concreta: Constitución §… · Exigido por: preset jevlab-<tema> · ADRs: NNNN
  ```
- Contenido: convenciones con su motivo, un ejemplo correcto, un antiejemplo y cómo se verifica
  (test, lint o revisión).
- Lo que se pueda comprobar automáticamente se automatiza (lint, `import-linter`, tests), y el
  estándar indica qué herramienta lo hace.

## 7. Ciclo de cambio

| Cambio | Proceso | Propagación |
| --- | --- | --- |
| **Constitución** | `/speckit-constitution` → *Sync Impact Report* → aprobación humana → commit `docs(constitution): …` con bump semver | Revisar los presets afectados (el *Sync Impact Report* los lista) |
| **Preset** | PR con bump de `version` en `preset.yml` y reinstalación (`specify preset update` o `add --dev`) | Afecta a los artefactos que se generen a partir de ese momento |
| **Estándar** | PR normal | Inmediata; el código existente se adapta en la siguiente spec que lo toque |
| **Specs ya cerradas** | No se reescriben. En la retro de cierre de cada spec se anota si una regla nueva obliga a una tarea de adaptación | La tarea entra en una spec futura |

Una retro breve al cerrar cada spec responde tres preguntas: ¿algún principio estorbó?, ¿faltó
alguno?, ¿alguna sección de preset se rellenó por rellenar? Cada respuesta "sí" abre un cambio en
la capa que corresponda.

### Versionado de documentos

Se aplica a todo documento o artefacto del proyecto versionado con semver: constitución, presets,
estándares versionados y definiciones de decisión.

- **Versión inicial: `0.3.0` como máximo.** Nunca se empieza en `1.0.0`. Los valores `0.1.0` y
  `0.2.0` sirven para borradores tempranos.
- **Fase `0.x` (maduración):** un cambio incompatible (eliminar o redefinir algo) sube MINOR; el
  resto sube PATCH. Ratificar un documento no lo saca de `0.x`.
- **`1.0.0` (estable):** solo por decisión humana explícita, cuando el documento ha superado al
  menos una spec completa sin cambios incompatibles. A partir de ahí rigen las reglas semver
  normales (MAJOR/MINOR/PATCH).

## 8. Antipatrones

- **Constitución como manual:** principios con nombres de librerías, versiones o rutas. Eso va en
  estándares o en `AGENTS.md`. Excepción acotada: los **enunciados** de los principios no nombran
  rutas ni herramientas, pero las secciones de proceso (alcance, flujo, gobernanza) y las líneas
  de *Verificación* sí pueden nombrar las herramientas del proceso SDD, como esta guía,
  `plan.md`, *Constitution Check*, *Complexity Tracking* o `/speckit-analyze`. Si cambian, la
  enmienda es PATCH.
- **Preset legislador:** un fragmento de plantilla que introduce una regla que no está en la
  constitución.
- **Estándar duplicado en el preset:** el detalle se copia en la plantilla y deja de coincidir con
  el estándar.
- **Override monolítico:** una plantilla sustituida entera que mezcla todos los temas.
- **Regla huérfana:** una regla sin principio de origen, o un principio que no se verifica de
  ninguna forma.
- **Presets ajenos:** reglas de terceros que nadie ha decidido en este proyecto.
