# Preset `jevlab-testing`

> Deriva de: Constitución §IV · Estándar: `docs/standards/testing.md` · Gobernanza:
> `docs/governance.md` §4 y §5

Spec Kit trata los tests como opcionales («Tests are OPTIONAL»), en la plantilla de tareas y en el
comando que la usa. Eso contradice IV («Todo comportamiento MUST tener tests»). Este preset
sustituye las dos piezas y añade la misma regla a la fase de convergencia.

| Pieza | Estrategia | Base copiada |
| --- | --- | --- |
| `tasks-template` | `replace` | `.specify/templates/tasks-template.md` de Spec Kit 1.1.4.dev0 |
| `speckit.tasks` (comando) | `replace` | `core_pack/commands/tasks.md` de Spec Kit 1.1.4.dev0 (formato fuente, con marcadores) |
| `speckit.converge` (comando) | `append` | Ninguna: solo el fragmento «Reglas de jev-lab para la fase de convergencia» |

## Por qué `replace`

`append`, `prepend` y `wrap` solo añaden texto; no pueden quitar «OPTIONAL». Es el único preset del
proyecto con `replace` (regla 1 de `docs/governance.md` §5).

`speckit.converge` no dice que los tests sean opcionales; solo le falta exigirlos al escribir la
fase de convergencia. Basta con añadir texto, así que usa `append` y recibe las mejoras de la base
al reinstalar el preset. El fragmento añade también la tarea de poner al día `quickstart.md` y la
lección (§VII): es la misma fase y separarla en otro preset obligaría a componer dos fragmentos
sobre un comando para una sola regla del ciclo (`docs/governance.md` §7, «Ciclo de convergencia»).

## Qué cambia respecto a la base

Solo las líneas que hacían opcionales los tests y los símbolos que prohíbe
`docs/standards/writing.md`; el resto es copia literal:

- Plantilla: la nota «Tests» (tests obligatorios, primero y en rojo; pruebas `live` opcionales,
  marcadas y con tope de coste), los títulos «Tests for User Story N», y tres menciones
  «(if requested)», «(if included)» y «(if tests requested)».
- Comando: la regla «Tests are OPTIONAL» y cuatro menciones «(if requested)» / «If tests
  requested».
- Plantilla y comando (v0.2.0): la mezcla de tests por historia de `docs/standards/testing.md` §2.
  En los ejemplos de cada historia, el test de contrato pasa a tests unitarios y el de
  integración cubre el escenario de aceptación principal.
- Plantilla y comando (v0.2.1): sin emojis ni flechas (`docs/standards/writing.md`). Se quita el
  símbolo de los ejemplos «CORRECT»/«WRONG», de «CRITICAL» y de «MVP», que ya llevan la palabra,
  y la flecha Unicode pasa a `->`. Al trasladar mejoras de una base nueva, repetir la sustitución;
  `uv run poe check-writing` avisa si se escapa alguno.

## Mantenimiento

- Prioridad 90, la más baja: los fragmentos `append` de otros presets se componen sobre esta copia.
- Al actualizar Spec Kit se sigue `docs/governance.md` §5, «Actualizar Spec Kit»: comparar la
  nueva base con la copiada, trasladar sus mejoras, actualizar la versión de la tabla y subir
  `version`.

Instalación: `specify preset add --dev presets/jevlab-testing --priority 90` y, como trae un
comando, el paso por cada agente de `docs/governance.md` §5, «Instalar o cambiar un preset».
