# Preset `jevlab-testing`

> Deriva de: Constitución §IV · Estándar: `docs/standards/testing.md` · Gobernanza:
> `docs/governance.md` §4 y §5

Spec Kit trata los tests como opcionales («Tests are OPTIONAL»), en la plantilla de tareas y en el
comando que la usa. Eso contradice IV («Todo comportamiento MUST tener tests»). Este preset
sustituye las dos piezas.

| Pieza | Estrategia | Base copiada |
| --- | --- | --- |
| `tasks-template` | `replace` | `.specify/templates/tasks-template.md` de Spec Kit 1.1.4.dev0 |
| `speckit.tasks` (comando) | `replace` | `core_pack/commands/tasks.md` de Spec Kit 1.1.4.dev0 (formato fuente, con marcadores) |

## Por qué `replace`

`append`, `prepend` y `wrap` solo añaden texto; no pueden quitar «OPTIONAL». Es el único preset del
proyecto con `replace` (regla 1 de `docs/governance.md` §5).

## Qué cambia respecto a la base

Solo las líneas que hacían opcionales los tests; el resto es copia literal:

- Plantilla: la nota «Tests» (tests obligatorios, primero y en rojo; pruebas `live` opcionales,
  marcadas y con tope de coste), los títulos «Tests for User Story N», y tres menciones
  «(if requested)», «(if included)» y «(if tests requested)».
- Comando: la regla «Tests are OPTIONAL» y cuatro menciones «(if requested)» / «If tests
  requested».

## Mantenimiento

- Prioridad 90, la más baja: los fragmentos `append` de otros presets se componen sobre esta copia.
- Al actualizar Spec Kit se sigue `docs/governance.md` §5, «Actualizar Spec Kit»: comparar la
  nueva base con la copiada, trasladar sus mejoras, actualizar la versión de la tabla y subir
  `version`.

Instalación: `specify preset add --dev presets/jevlab-testing --priority 90` y, como trae un
comando, el paso por cada agente de `docs/governance.md` §5, «Instalar o cambiar un preset».
