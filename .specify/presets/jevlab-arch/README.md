# Preset `jevlab-arch`

> Deriva de: Constitución §III · Estándar: `docs/standards/architecture.md` · Gobernanza:
> `docs/governance.md` §4 y §5

Hace que cada plan sitúe sus piezas en la arquitectura hexagonal antes de escribir código.

| Plantilla | Estrategia | Qué añade |
| --- | --- | --- |
| `plan-template` | `append` | Sección «Arquitectura»: capa, dependencias y prueba aislada de cada pieza; efectos externos y su puerto; puertos nuevos con su fake; consumidores de la misma definición |

Decisiones de diseño:
- Solo toca el plan: la spec describe comportamiento y no lleva arquitectura.
- La columna «Cómo se prueba aislada» detecta puertos que faltan: una pieza que no se puede probar
  sin red suele necesitar uno.
- La columna «Depende de» adelanta al plan lo que `import-linter` comprobará en CI.

Instalación: `specify preset add --dev presets/jevlab-arch --priority 30`.
