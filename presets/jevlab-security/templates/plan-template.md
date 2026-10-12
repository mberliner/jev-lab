## Seguridad (jev-lab)

> Deriva de: Constitución §V · Estándar: `docs/standards/security.md`

| Dato o entrada | Origen | Confiable | Qué se registra (sin *payloads* ni datos personales) |
| --- | --- | --- | --- |
| [texto del ticket] | [usuario \| documento \| API externa \| propio] | [no: se trata como dato \| sí: motivo] | [p. ej. solo ID y resultado] |

- **Secretos nuevos**: [variable de `.env.example` y qué adaptador la usa; «ninguno»].
- **Contenido adversarial**: [casos de inyección que se añaden a los tests o a la evaluación].
