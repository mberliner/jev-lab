# jev-lab: instrucciones para agentes

Fuente única de instrucciones para cualquier agente de código (Claude Code, Antigravity u otro).
Todo lo necesario para trabajar está en el repo: no hay que
depender de memorias, rutas ni configuración externas.

## Qué es

Laboratorio progresivo para aprender y demostrar Jev (TypeSafe), un modelo de decisión tipada
(Choice, Score, Noul), desde lo básico hasta técnicas de producción. Se desarrolla con
Spec-Driven Development (Spec Kit).

## Documentos fundamentales

| Documento | Para qué |
| --- | --- |
| `docs/roadmap.md` | **Plan vigente y estado actual**: empezar por «Estado actual y cómo retomar» |
| `.specify/memory/constitution.md` | Principios no negociables (v0.3.0, ratificada) |
| `docs/personas.md` | Perfiles de usuario a los que sirve cada feature |
| `docs/ideas.md` | Ideas abiertas para specs futuras (sobre todo de las retros); revisar al planificar una spec |
| `docs/governance.md` | Dónde vive cada regla común: constitución -> presets propios -> estándares |
| `specs/NNN-*/` | Artefactos SDD de cada feature |
| `docs/setup.md` | Puesta en marcha en Linux y Windows (se crea en la spec 000) |

## Flujo de trabajo (Spec Kit)

`/speckit-constitution` -> `/speckit-specify` -> `/speckit-clarify` -> `/speckit-plan` ->
`/speckit-tasks` -> `/speckit-analyze` -> `/speckit-implement`.

- Skills para Claude Code en `.claude/skills/` y para Antigravity en `.agents/skills/`. Las dos
  comparten `.specify/` y `specs/`.
- Los scripts de Spec Kit son Python (`.specify/scripts/python/`) y se ejecutan con `python3` ≥ 3.8.
- Para actualizar Spec Kit se sigue `docs/governance.md` §5, «Actualizar Spec Kit»: los presets
  propios con `replace` no reciben las mejoras de la base sin intervención manual.

## Entorno

- **Python del proyecto: 3.13, gestionado por uv.** El código del proyecto se ejecuta siempre con
  `uv run …`, nunca con `python3`, que puede ser un Python de sistema antiguo.
- **`python3` del sistema (≥ 3.8):** lo usan solo los scripts de Spec Kit.
- **Windows:** si solo existen `python`/`py`, crear el enlace `python3.exe` -> `python.exe` (ver
  `docs/setup.md`).
- Multiplataforma (Linux y Windows): sin symlinks, `pathlib`, UTF-8 explícito, finales de línea
  según `.gitattributes`.

## Reglas básicas (resumen; manda la constitución)

- El modelo juzga, el código decide: aritmética, fechas, conteos, permisos e invariantes van en código.
- Cada Choice incluye una opción de escape (`other`/`none`).
- Toda acción automatizable pasa por la confianza, con umbrales por riesgo.
- Secretos solo en `.env` (nunca en el repo); logs sin bodies ni datos personales.
- Código y textos originales; datos externos solo con licencia válida y citados. Solo se citan la
  documentación oficial de TypeSafe y fuentes primarias.
- Hooks y comandos solo con implementación neutral: la lógica va en tareas del repo y existe igual
  para todos los agentes, o no se usa. Las puertas de calidad son pre-commit y CI.
- Documentación sin emojis ni pictogramas; caracteres de caja y flechas solo en bloques de código
  (`docs/standards/writing.md`).
- Commits en formato Conventional Commits y sin firmas ni atribuciones de agentes
  (`Co-Authored-By`, `Generated with`), también en PRs (`docs/standards/version-control.md`).
