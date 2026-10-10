# jev-lab: instrucciones para agentes

Fuente única de instrucciones para cualquier agente de código (Claude Code, Antigravity u otro).
`CLAUDE.md` solo importa este archivo. Todo lo necesario para trabajar está en el repo: no hay que
depender de memorias, rutas ni configuración externas.

> Estado: **arranque (spec 000 en curso)**. Este archivo se completa durante la spec 000.

## Qué es

Laboratorio progresivo para aprender y demostrar Jev (TypeSafe), un modelo de decisión tipada
(Choice, Score, Noul), desde lo básico hasta técnicas de producción. Se desarrolla con
Spec-Driven Development (Spec Kit).

## Documentos fundamentales

| Documento | Para qué |
| --- | --- |
| `docs/roadmap.md` | **Plan vigente**: arquitectura, specs 000–007 y verificación |
| `.specify/memory/constitution.md` | Principios no negociables (en ratificación, proceso HITL) |
| `specs/NNN-*/` | Artefactos SDD de cada feature |
| `docs/setup.md` | Puesta en marcha en Linux y Windows (se crea en la spec 000) |

## Flujo de trabajo (Spec Kit)

`/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` →
`/speckit-tasks` → `/speckit-analyze` → `/speckit-implement`.

- Skills para Claude Code en `.claude/skills/` y para Antigravity en `.agents/skills/`. Las dos
  comparten `.specify/` y `specs/`.
- Los scripts de Spec Kit son Python (`.specify/scripts/python/`) y se ejecutan con `python3` ≥ 3.8.

## Entorno

- **Python del proyecto: 3.13, gestionado por uv.** El código del proyecto se ejecuta siempre con
  `uv run …`, nunca con `python3`, que puede ser un Python de sistema antiguo.
- **`python3` del sistema (≥ 3.8):** lo usan solo los scripts de Spec Kit.
- **Windows:** si solo existen `python`/`py`, crear el enlace `python3.exe` → `python.exe` (ver
  `docs/setup.md`).
- Multiplataforma (Linux y Windows): sin symlinks, `pathlib`, UTF-8 explícito, finales de línea
  según `.gitattributes`.

## Reglas básicas (resumen provisional; manda la constitución ratificada)

- El modelo juzga, el código decide: aritmética, fechas, conteos, permisos e invariantes van en código.
- Cada Choice incluye una opción de escape (`other`/`none`).
- Toda acción automatizable pasa por la confianza, con umbrales por riesgo.
- Secretos solo en `.env` (nunca en el repo); logs sin bodies ni datos personales.
- Contenido original; solo se citan la documentación oficial de TypeSafe y fuentes primarias.
- Nada de hooks ni comandos exclusivos de un agente: las puertas de calidad son pre-commit y CI.
