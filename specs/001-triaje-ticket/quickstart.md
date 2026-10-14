# Guía de validación: Triaje de un ticket de soporte

Escenarios para demostrar cada historia una vez implementada. La salida exacta y los códigos de
salida están en [contracts/cli-triage.md](contracts/cli-triage.md); el formato de las grabaciones,
en [contracts/recording.md](contracts/recording.md).

## Requisitos

- Entorno de la spec 000 instalado (`uv sync`, `docs/setup.md`).
- Para la US1-US4 en modo grabado: nada más, ni red ni `.env`.
- Para `--en-vivo` y para regrabar: `.env` con `TYPESAFE_API_KEY` (T037 de la spec 000).

## US1: cola, distribución y confianza

| Paso | Resultado esperado |
| --- | --- |
| `uv run jevlab triage --ejemplo cobro-duplicado` | `Cola: facturacion`, la distribución de las cuatro opciones de mayor a menor y la confianza; código 0 |
| `uv run jevlab triage --ejemplo pregunta-fuera-de-ambito` | `Cola: sin cola asignada, requiere revisión manual`; código 0 |
| `uv run poe test` | Pasa el test que recalcula la confianza de cada grabación (FR-006) |

## US2: urgencia explícita

| Paso | Resultado esperado |
| --- | --- |
| `uv run jevlab triage --ejemplo servicio-caido` | `Urgencia explícita: sí` con la probabilidad |
| `uv run jevlab triage --ejemplo cobro-duplicado` | `Urgencia explícita: no` |
| `uv run jevlab triage --ejemplo urgencia-ambigua` | `Urgencia explícita: incierto`, con la banda 0,30 a 0,70 (provisional) |

## US3: prioridad y umbral

| Paso | Resultado esperado |
| --- | --- |
| `uv run jevlab triage --ejemplo servicio-caido` | Niveles con nombre y probabilidad, nivel más probable, confianza y `umbral alta (provisional): alcanzado` |
| `uv run jevlab triage --ejemplo cambio-de-correo` | `umbral alta (provisional): no alcanzado` |

## US4: sin red ni coste

| Paso | Resultado esperado |
| --- | --- |
| Sin red y sin `.env`: `uv run jevlab triage "<texto de cobro-duplicado>"` | Misma salida que con `--ejemplo`; primera línea `Origen: grabado` con modelo y fecha |
| `uv run jevlab triage` en una terminal | Menú numerado; al elegir un número, su triaje |
| `uv run jevlab triage "un texto sin grabación"` | Error con la lista de ejemplos; código 2; sin conexión |
| Con `.env`: `uv run jevlab triage --en-vivo "<texto>"` | `Origen: en vivo` y el modelo; código 0 |
| Con `.env`: `uv run poe record` | Regraba los ejemplos con el tope de `JEVLAB_LIVE_BUDGET_USD`; cada archivo con `model` y `recorded_on` |

## Puertas

| Paso | Resultado esperado |
| --- | --- |
| `uv run poe check` | Pasa, incluida la regla de ruff que prohíbe reloj, azar e IDs fuera de `adapters/` y `tests/` |
| En Git Bash: `uv run jevlab triage --ejemplo cobro-duplicado \| cat` | Tildes y «·» correctos |
