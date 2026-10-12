## Decisiones Jev (jev-lab) *(mandatory si la feature pregunta al modelo)*

> Deriva de: Constitución §I, §II y §IV · Estándar: `docs/standards/decision-design.md`

Si la feature no pregunta al modelo: «no aplica» y se borra el resto de la sección.

| Decisión | Pregunta (una idea, literal) | Primitiva | Opciones + escape | Acción automatizable y riesgo | Destino del escape |
| --- | --- | --- | --- | --- | --- |
| [nombre-corto] | [«¿…?»] | [Choice \| Score \| Noul] | [`a`, `b`, `other`] | [qué se hace solo; riesgo bajo \| medio \| alto] | [revisión \| abstención] |

- **Lo que decide el código**: [cifras, fechas, conteos, permisos e invariantes de la feature que
  no se preguntan al modelo].
- **Qué ve cada persona**: [resultado, confianza, motivo del escalado, «no disponible», grabado o
  sintético; por persona de `docs/personas.md`].
