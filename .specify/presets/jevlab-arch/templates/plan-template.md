## Arquitectura (jev-lab)

> Deriva de: Constitución §III · Estándar: `docs/standards/architecture.md`

| Pieza nueva o cambiada | Capa | Depende de | Cómo se prueba aislada |
| --- | --- | --- | --- |
| [`NombreDeLaPieza`] | [domain \| application \| ports \| adapters \| entrypoints] | [puertos o piezas que usa] | [fake, contrato con cassette, `CliRunner`…] |

- **Efectos externos**: [cada uso de red, disco, reloj, azar o IDs, y el puerto por el que pasa].
- **Puertos nuevos**: [puerto, adaptador real y fake para los tests].
- **Una sola definición**: [consumidores que cargan el mismo `DecisionSpec` y test que lo
  comprueba; «no aplica» si la feature no tiene decisiones].
