## Reglas de jev-lab para la fase de convergencia

> Deriva de: Constitución §IV y §VII · Proceso: `docs/governance.md` §7, «Ciclo de convergencia»

Al escribir la fase `## Phase N: Convergence` en `tasks.md`, además de lo anterior:

- **Test primero.** Cada cambio de comportamiento lleva su tarea de test antes de la de
  implementación, y el test debe fallar antes del cambio (`docs/standards/testing.md`). Se siguen
  las mismas reglas que en `/speckit-tasks`: los tests son obligatorios.
- **Lo que enseña y valida.** Si cambia una salida, un comando o un flujo que ve una persona, se
  añade una tarea para actualizar `quickstart.md`, la lección de la spec
  (`docs/lessons/NNN-*.md`) y, si cambia un comando, `AGENTS.md`.
- **Motivo en la cabecera.** La cabecera de la fase dice qué la motivó, entre paréntesis: la
  prueba, el repaso o la retro, y la fecha. Por ejemplo,
  `## Phase 9: Convergence (segunda prueba de SC-004, 2026-10-17)`.
- **Prueba que se repite.** Si la fase la motivó una prueba de un criterio de éxito, su última
  tarea es repetir esa prueba y anotar el resultado en la tarea de aceptación de la fase final.
