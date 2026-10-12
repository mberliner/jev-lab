# Preset `jevlab-security`

> Deriva de: Constitución §V · Estándar: `docs/standards/security.md` · Gobernanza:
> `docs/governance.md` §4 y §5

Hace que cada plan decida, antes de escribir código, qué datos no son confiables y qué se escribe
en los logs.

| Plantilla | Estrategia | Qué añade |
| --- | --- | --- |
| `plan-template` | `append` | Sección «Seguridad»: origen, confianza y registro de cada dato; secretos nuevos; casos adversariales |

Decisiones de diseño:
- Solo toca el plan: la spec describe comportamiento, y la transparencia ante la persona ya está en
  `jevlab-decision`.
- Las columnas «Origen» y «Confiable» hacen explícito qué contenido nunca se trata como
  instrucción; «Qué se registra» obliga a decidir el log antes de escribirlo.

Instalación: `specify preset add --dev presets/jevlab-security --priority 40`.
