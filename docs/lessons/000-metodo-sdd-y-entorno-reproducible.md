# Lección 000: el método SDD y un entorno reproducible

> Spec: [000, Cimientos](../../specs/000-cimientos/spec.md) · Persona: usuario inicial de Jev ·
> Requisito previo: tener el proyecto instalado según [la guía de puesta en marcha](../setup.md)

Esta lección no trata todavía de Jev. Explica cómo se construye jev-lab: cómo se pasa de una idea a
código con Spec Kit, dónde vive cada regla y por qué el entorno funciona igual en cualquier máquina
y con cualquier agente. Las specs siguientes dan todo esto por sabido.

## Qué se aprende

1. El flujo de Spec-Driven Development con Spec Kit.
2. Las capas de reglas (constitución, presets, estándares y ADRs) y cómo se rastrea una regla
   hasta su principio.
3. Cómo se aplica un preset, paso a paso, con el caso de `jevlab-testing`.
4. El entorno de dos intérpretes y cómo lo comprueba `jevlab doctor`.
5. Qué suele fallar y cómo se mitiga.

## 1. El flujo de Spec Kit

Cada funcionalidad recorre los mismos comandos, en este orden. Cada uno produce un artefacto en
`specs/NNN-nombre/` que el siguiente usa como entrada:

```
/speckit-specify   -> spec.md        qué y para quién: historias, requisitos, criterios de éxito
/speckit-clarify   -> spec.md        hasta 5 preguntas para cerrar ambigüedades
/speckit-plan      -> plan.md, research.md, data-model.md, contracts/, quickstart.md
/speckit-tasks     -> tasks.md       tareas ordenadas por historia, tests primero
/speckit-analyze   -> (informe)      coherencia entre spec, plan, tareas y constitución
/speckit-implement -> código         ejecuta las tareas y las marca como hechas
```

Ideas clave:

- **La spec no habla de tecnología.** Dice qué necesita la persona y cómo se comprueba. El plan
  decide cómo.
- **Cada historia se demuestra sola.** La spec 000 tiene cuatro: instalar desde un clon limpio,
  `jevlab doctor`, las puertas de calidad y esta lección. Cada una tiene su comando de
  demostración en la tabla «Corte vertical y lección» de su spec.
- **Las decisiones las aprueba una persona.** El agente propone; las aclaraciones y los hallazgos
  del análisis se resuelven con la persona antes de implementar.

Para verlo en un caso real, basta con leer en orden los artefactos de
[specs/000-cimientos/](../../specs/000-cimientos/spec.md).

## 2. Dónde vive cada regla

Una regla común a todas las specs vive en una de tres capas. Cada capa remite a la superior:

| Capa | Responde a | Dónde |
| --- | --- | --- |
| Constitución | Qué debe cumplirse siempre y por qué | [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) |
| Preset | Qué debe contestar cada spec, plan o lista de tareas | `presets/jevlab-<tema>/` |
| Estándar | Cómo se hace, con ejemplos y antiejemplos | `docs/standards/<tema>.md` |

Los ADR (`docs/adr/`) registran una decisión con sus alternativas; explican por qué existe una
regla, pero no son una regla. El criterio para clasificar una regla nueva está en
[docs/governance.md](../governance.md), apartado 2.

**Cómo se rastrea una regla.** Ejemplo: «los tests se escriben antes que la implementación».

```
tasks.md de la spec 000      "Tests for User Story 1 (write first, must FAIL ...)"
  <- plantilla de tareas     presets/jevlab-testing/templates/tasks-template.md
  <- estándar                docs/standards/testing.md §5, «Tests antes que la implementación»
  <- principio               Constitución IV, «Evidencia antes que afirmación»
```

Cada sección que añade un preset empieza con una línea `> Deriva de: Constitución §…`, y cada
estándar con `> Concreta: Constitución §…`. Si una regla no se puede rastrear hasta un principio,
sobra la regla o falta el principio.

## 3. Aplicar un preset paso a paso: `jevlab-testing`

Spec Kit trae una plantilla de tareas que dice «Tests are OPTIONAL». Eso contradice la
Constitución IV. El preset [`jevlab-testing`](../../presets/jevlab-testing/README.md) lo corrige.

**Por qué `replace`.** Las estrategias `append`, `prepend` y `wrap` solo añaden texto; no pueden
quitar una frase. `jevlab-testing` sustituye la plantilla (`tasks-template`) y el comando de
tareas (`speckit.tasks`) por copias propias. El precio: las mejoras futuras de Spec Kit en esas
dos piezas no llegan solas (ver «Actualizar Spec Kit» en
[docs/governance.md](../governance.md), apartado 5).

**Composición por prioridad.** Varios presets tocan la misma plantilla. Un número de prioridad
menor gana precedencia, y los fragmentos `append` se añaden sobre la capa base:

```
tasks-template resuelta = jevlab-testing (replace, prioridad 90)   <- capa base
                        + jevlab-spec    (append,  prioridad 10)   <- fase final de cierre
```

Por eso el preset con `replace` lleva el número más alto: así los demás se componen encima.

**Agente único activo.** Spec Kit registra los comandos de un preset solo en la integración
activa. Para que Claude Code y Antigravity reciban el mismo comando de tareas, se pasa por cada
agente y se vuelve al de por defecto:

```
specify preset add --dev presets/jevlab-testing --priority 90
specify integration use agy
specify integration use claude
```

**Comprobación.** `uv run poe check-presets` verifica lo que se puede olvidar: que la copia
instalada en `.specify/presets/` es igual a la fuente de `presets/`, que «Tests are OPTIONAL» no
reaparece en la plantilla resuelta ni en las skills, que la skill es igual en los dos agentes y
que no se versionan los scripts de shell que Spec Kit copia junto a los de Python.

## 4. Dos intérpretes, dos papeles

| Intérprete | Quién lo usa | Requisito | Cómo se garantiza |
| --- | --- | --- | --- |
| Python del proyecto | `uv run …`: código, tests y puertas | 3.13 | `.python-version` y `uv sync` |
| `python3` del sistema | Los scripts de Spec Kit, lanzados por el agente | 3.8 o superior, con PyYAML | La guía de puesta en marcha |

Separarlos evita dos problemas: el proyecto no depende del Python que traiga cada sistema, y Spec
Kit funciona con el `python3` que ya existe. La regla práctica: el código del proyecto se ejecuta
siempre con `uv run`, nunca con `python3`.

`uv run jevlab doctor` comprueba los dos, además de las claves de `.env`:

```
[ok]   speckit-python  python3 3.8.10 con PyYAML 5.3.1
[ok]   project-python  Python 3.13.11
[fail] env-keys        faltan: AZURE_OPENAI_API_KEY
       arreglo: copia .env.example a .env y rellena las variables que faltan
Resultado: 1 falla
```

Un detalle que enseña: dentro de `uv run`, el primer `python3` del PATH es el del entorno
virtual. `jevlab doctor` lo salta al buscar el de Spec Kit; si no lo hiciera, informaría de
Python 3.13 aunque el sistema tuviera un 3.7 sin PyYAML.

`jevlab doctor` es también la primera pieza del esqueleto hexagonal: el estado y el código de
salida se deciden en `domain/`, el caso de uso vive en `application/`, y el sistema, TypeSafe y
Azure quedan detrás de puertos con fakes para los tests
([ADR-0001](../adr/0001-arquitectura-hexagonal.md)).

## 5. Qué puede fallar y cómo se mitiga

| Fallo | Síntoma | Mitigación |
| --- | --- | --- |
| `python3` antiguo o inexistente (habitual en Windows) | Los comandos de Spec Kit fallan al arrancar | Enlace `python3.exe` de la guía de puesta en marcha; `jevlab doctor` lo detecta |
| `python3` sin PyYAML | Spec Kit ignora los presets: la plantilla vuelve a la base sin avisar | Instalar PyYAML o definir `SPECKIT_PYTHON_EXECUTABLE`; `jevlab doctor` lo detecta |
| Preset con comandos instalado con un solo agente activo | El otro agente sigue usando la skill base, con «Tests are OPTIONAL» | Pasar por cada agente con `specify integration use`; `poe check-presets` lo detecta |
| `specify integration upgrade --force` | Las skills del agente no activo vuelven a la base | Mismo paso por cada agente; `poe check-presets` lo detecta |
| `integration use` copia los scripts de shell del sistema (`bash/` en Linux, `powershell/` en Windows) | El repo cambia según el sistema de quien instala | Están en `.gitignore` y se quitan sus entradas del manifiesto de Spec Kit; `poe check-presets` lo detecta |
| Instalar un preset con `.venv/` presente | Las skills llaman a `.venv/bin/python` en vez de `python3`, que falla en otra máquina o en Windows | Apartar `.venv/` mientras se instala (`docs/governance.md` §5); `poe check-presets` lo detecta |
| El agente copia un emoji de una skill de Spec Kit a un artefacto | El commit de `spec.md` o `plan.md` falla | Cambiarlo por una palabra; `poe check-writing` señala archivo y línea |
| Finales de línea convertidos en Windows | Diferencias en todo el archivo y scripts rotos | `.gitattributes` fija LF salvo en `*.ps1`, `*.cmd` y `*.bat` |
| Un test que usa la red sin querer | Pasa en una máquina y falla en otra, o gasta dinero | `pytest-socket` bloquea la red en la suite por defecto; lo real va marcado `live` con tope |

Todas las comprobaciones automáticas corren en cada commit (pre-commit) y en la CI de Linux y
Windows, con el mismo comando: `uv run poe check`. Da igual el agente que haya hecho el cambio, o
si no lo hizo ninguno.

## Para practicar

1. Ejecuta `uv run jevlab doctor` sin `.env` y arréglalo siguiendo la línea `arreglo:`.
2. Añade «Tests are OPTIONAL» al final de `.agents/skills/speckit-tasks/SKILL.md`, ejecuta
   `uv run poe check-presets`, lee el mensaje y deshaz el cambio con `git checkout`.
3. Elige una regla de `docs/standards/security.md` y rastréala hasta su principio de la
   constitución, como en el apartado 2.
