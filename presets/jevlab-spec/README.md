# Preset `jevlab-spec`

> Deriva de: Constitución §VII · Estándar: no necesita · Gobernanza: `docs/governance.md` §4 y §5

Hace que cada feature cumpla «Cortes verticales que enseñan».

| Plantilla | Estrategia | Qué añade |
| --- | --- | --- |
| `spec-template` | `append` | Sección «Corte vertical y lección»: persona, capacidad de extremo a extremo, demostración por historia, número de historias, fuera de alcance y lección |
| `tasks-template` | `append` | Fase final de cierre: lección, demostración de cada historia y retro |

Lo que la plantilla base ya cubre y no se repite: historias priorizadas, *Independent Test* por
historia y escenarios Given/When/Then.

Decisiones de diseño:
- El cierre va en `tasks.md` y no en una checklist: `/speckit-implement` usa las checklists como
  puerta **antes** de implementar, cuando la lección aún no puede existir.
- La retro no tiene archivo propio: sus respuestas van en el commit de cierre y cada «sí» abre su
  cambio o se anota en `docs/ideas.md`.
- Los fragmentos solo enlazan documentos estables (`docs/personas.md`, `docs/ideas.md`), nunca el
  roadmap, porque acaban copiados en cada `spec.md` y `tasks.md` generado.
- Como `jevlab-testing` sustituye `tasks-template` (`replace`), este preset necesita más prioridad
  que él para que su fragmento se componga.

Instalación: `specify preset add --dev presets/jevlab-spec --priority <n>`.
