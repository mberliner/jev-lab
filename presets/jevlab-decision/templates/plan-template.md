## Diseño de decisiones (jev-lab)

> Deriva de: Constitución §I, §II, §III y §IV · Estándar: `docs/standards/decision-design.md`

Una fila por decisión de la spec. Si la spec dice «no aplica», esta sección también.

| Decisión | `DecisionSpec` (ruta y versión) | Modelo fijado | Estado mínimo enviado | Umbrales (archivo) | Justificación del umbral |
| --- | --- | --- | --- | --- | --- |
| [nombre-corto] | [`src/jevlab/specs/<dominio>/<decision>.yaml`, `0.1.0`] | [modelo y versión] | [campos y por qué bastan] | [ruta del YAML] | [evaluación que lo justifica \| provisional] |

- **Revisión de I**: ¿alguna pregunta pide al modelo una cifra, una fecha, un permiso o más de una
  idea? [no \| sí: cómo se corrige].
- **Escape y respuesta inválida**: [cómo se implementan la revisión o la abstención de la spec].
- **Salida**: [interfaz y estándar de su formato: `docs/standards/cli-ux.md` (§6, origen de cada
  dato y `qué hacer:`), `api-errors.md` \| no aplica].
