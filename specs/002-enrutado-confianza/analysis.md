# Análisis: Enrutado con confianza según riesgo

Informe de `/speckit-analyze` sobre `spec.md`, `plan.md` y `tasks.md` (con `data-model.md`,
`research.md`, `contracts/` y `quickstart.md`), contrastado con la constitución v0.3.1.

**Fecha**: 2026-10-14 · **Estado**: corregidos C1, I1, U1, U2, U4 y F5; el resto, pendiente

## Hallazgos

| ID | Categoría | Severidad | Ubicación | Resumen | Recomendación | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | Constitución (§II) | HIGH | plan.md, «Diseño de decisiones»; contracts/cli-route.md, «Reglas»; data-model.md, `RoutingResult.actions` | El escape (o la falta de respuesta) de `solicitud` acaba en «no se propone reembolso» sin rastro: la salida omite la línea `Reembolsar` y la auditoría no registra nada. §II pide revisión o **abstención explícita**, y `decision-design.md` §7 pide mostrar el resultado y la confianza de cada decisión. | Mostrar siempre la solicitud, por ejemplo `Solicitud: other · confianza 0,65 · sin reembolso`, o registrar la abstención en la auditoría. Si se considera suficiente que el código decida «sin reembolso», justificarlo en el plan. | Corregido: `reembolsar` pasa a estar siempre en el resultado; con una solicitud distinta de `reembolso` queda `sin reembolso` (abstención explícita), se muestra y se audita, y no va a revisión (spec US2-4 y FR-011, data-model, plan, R4, cli-route, T033-T036, T039). |
| I1 | Inconsistencia | HIGH | data-model.md, «Transiciones»; T014 (`save_resolution(item, entry)`); spec US3 escenario 5 | `asignar` con otra cola y `descartar` resuelven dos acciones a la vez (la cola, y el reembolso queda `rechazada`), pero cada transición produce **un** `AuditEntry` con un solo `action`. El rechazo en cascada del reembolso no queda en la auditoría, y el escenario 5 de la US3 lo exige. | Que `resolve` devuelva una tupla de `AuditEntry` (una por acción resuelta) y `save_resolution(item, entries)`; añadirlo a T038 y T009. | Corregido: `resolve` devuelve una `AuditEntry` por acción resuelta y `save_resolution(item, entries)` las guarda en una transacción (data-model, cli-review, T009, T014, T038, T039, T042). |
| U1 | Infraespecificación | HIGH | T041; research R8 | T041 pide «`confirmar` antes de asignar en un elemento con cola y reembolso pendientes» con grabaciones reales, pero ninguno de los tres ejemplos garantiza ese caso; R8 reconoce que el reembolso con la cola sin automatizar no tiene ejemplo grabado. | Cubrir ese paso con `InMemoryRoutingStore` en T039/T040, o añadir a `covers` un ejemplo grabado que lo produzca y comprobarlo en T048. | Corregido: el paso sale de T041 y pasa a T040 con un elemento sintético guardado en un SQLite temporal, que cubre también el rechazo en cascada. |
| U2 | Infraespecificación | MEDIUM | T022, T023, T041, T046, quickstart US3 y US4 | Varias tareas dependen de valores de grabaciones que todavía no existen y que `covers` no declara. `cobro-duplicado` necesita `solicitud` ≥ 0,97, pero T022 obliga a mantener el mismo texto que el triaje y T023 prohíbe reescribirlo. `reembolso-ambiguo` necesita la cola automatizada a `facturacion` (T041 y quickstart). `instruccion-incrustada` necesita la cola entre 0,80 y 0,90 en la grabación nueva (T046); la cifra de 0,87 sale de la grabación del triaje. | Declarar en T022 los requisitos de cada ejemplo, comprobarlos en T048 y decidir qué se hace si `cobro-duplicado` no llega: un ejemplo nuevo de reembolso claro en lugar de reescribir el compartido. | Corregido: cada ejemplo declara en `covers` todo lo que se espera de él y T048 lo comprueba; tests, demos y quickstart eligen ejemplos por etiqueta y leen las confianzas de la grabación; los textos de la 001 se comparten sin cambios (`tests/live/examples.py`) y los casos que no cubran van a ejemplos nuevos; nuevo adversarial `reembolso-incrustado`, que no se reescribe para que pase; grabación separada con `poe record-route` (spec FR-014, SC-006, supuestos y corte vertical; plan; R8; T002, T022, T023, T028, T035, T041, T046, T048, T054; quickstart). |
| U4 | Infraespecificación | MEDIUM | spec US4 escenario 2; spec «Corte vertical», US4 | Detectado al resolver U2: la demo de la US4 subía el umbral por encima de la confianza de `cobro-duplicado`, pero con una confianza de 1,0 ningún umbral válido (≤ 1) lo supera, así que el resultado no puede cambiar. | Invertir la demo: rebajar el umbral hasta la confianza grabada del ejemplo de «cola a revisión». | Corregido: escenario 2 de la US4 y tabla «Corte vertical» invertidos (y T046 y quickstart, por U2). |
| I2 | Inconsistencia | MEDIUM | data-model.md, `AuditEntry` y «Persistencia» | Una `AuditEntry` de resolución exige `spec_versions`, pero `review_item` no lo guarda, así que `ResolveReview` no puede rellenarlo. | Añadir `spec_versions` a `review_item` (y a `ReviewItem`), o hacer el campo opcional en las resoluciones. | Pendiente |
| U3 | Infraespecificación | MEDIUM | data-model.md, `ReviewItem.id` y `AuditEntry.review_item`; T030, T043 | El `id` del elemento lo asigna SQLite al guardar, pero las `AuditEntry` de decisión, que deben llevar `review_item`, se construyen antes, en `RouteTicket`. No se dice quién rellena ese campo. | Indicar que `store.record` asigna el `id` y lo propaga a las entradas, y que `ReviewItem.id` es opcional hasta que se guarda; comprobarlo en T009. | Pendiente |
| F1 | Orden de tareas | MEDIUM | T006; Phase 2 | T006 hace que `tests/fakes.py` importe `Answers`, `ResolvedRequest`, `Policy`, `InvalidPolicy` y `RoutingStore`, que no existen hasta T012, T014, T016 y T019. Como los tests de la 001 importan `fakes.py`, toda la suite deja de recogerse hasta entonces, y el checkpoint «la 001 sigue en verde» se vuelve opaco. | Partir T006: adaptar `FakeJudge` y `StaticSpecLoader` junto a T012-T013 y añadir los fakes nuevos tras T014-T016, o importar lo nuevo solo desde módulos de test nuevos. | Pendiente |
| F2 | Inconsistencia | LOW | T034, T045 | Llevan `[P]`, pero dicen ir «en serie» con T026 y con T025/T027 porque tocan los mismos archivos. | Quitar `[P]` a T034 y T045. | Pendiente |
| F3 | Inconsistencia | LOW | T007 | Cita FR-016 para «el texto viaja solo en `state`»; FR-016 trata del estado local fuera del repositorio. | Citar la Constitución §I (estado mínimo) o quitar la referencia. | Pendiente |
| F4 | Deriva terminológica | LOW | spec US1 escenario 2; data-model `PendingReason`; `src/jevlab/domain/triage.py` | El ejemplo de la spec (`cuenta · confianza 0,87 · no se mueve: umbral 0,90`) no sigue el formato del contrato (`a revisión · confianza 0,87 < umbral 0,90`). `PendingReason` dice «fuera de la definición», mientras que la 001 usa «respuesta fuera de la definición». | Alinear el ejemplo de la spec con el contrato y reutilizar los textos de motivo de la 001. | Pendiente |
| F5 | Ambigüedad | LOW | spec, «Corte vertical», US1 y US2 | Quedan marcadores sin resolver (`<reembolso claro>`, `<reembolso ambiguo>`), y la demo de la US1 usa `cobro-duplicado` mientras que tasks y quickstart usan `cambio-de-correo`. | Sustituirlos por `cobro-duplicado` y `reembolso-ambiguo`, y unificar el ejemplo de la US1. | Corregido: la tabla «Corte vertical» usa los ejemplos previstos por etiqueta, y T023 fija los definitivos tras grabar. |
| F6 | Deriva terminológica | LOW | spec FR-009, US4; research R3 | La spec habla de `policy.yaml` y el archivo real es `policies/soporte/enrutado.yaml`; R3 lo explica, pero la spec no. | Una nota en la spec, o usar el nombre real. | Pendiente |
| E1 | Cobertura | LOW | plan, «Performance Goals» | «`route` grabado y `review` en menos de 1 s» no tiene tarea que lo mida (T052 solo anota el tiempo de la suite). | Anotar los tiempos en T053/T055, o rebajar la meta a orientativa. | Pendiente |
| E2 | Cobertura | LOW | spec, «Edge Cases»; FR-013 | Sin test explícito para «el mismo ticket dos veces da dos elementos». La monotonía «si una confianza se automatiza, cualquier mayor también» solo se prueba para `mover-a-cola` (T024), no para `reembolsar` (T033). | Añadir los dos casos a T039 y T033. | Pendiente |
| E3 | Cobertura | LOW | SC-004 | «El Operador resuelve un elemento en menos de 1 minuto siguiendo la lección» no tiene ninguna comprobación. | Cronometrarlo en T055 y anotarlo. | Pendiente |

## Cobertura

| Requisito | ¿Tarea? | Tareas | Notas |
| --- | --- | --- | --- |
| FR-001 | Sí | T027, T032, suite de la 001 en T013 | |
| FR-002 | Sí | T027, T032 | |
| FR-003 | Sí | T024, T029 | |
| FR-004 | Sí | T026, T031, T034 | |
| FR-005 | Sí | T026, T034, T040 | |
| FR-006 | Sí | T033, T036 | |
| FR-007 | Sí | T039, T043 | |
| FR-008 | Sí | T038-T044 | Ver I1 |
| FR-009 | Sí | T005, T016, T017 | |
| FR-009a | Sí | T005, T045, T046 | |
| FR-010 | Sí | T005, T008, T045, T047 | |
| FR-011 | Sí | T025, T028, T030 | Ver U3 |
| FR-012 | Sí | T009, T020 | |
| FR-013 | Sí | T005, T024, T033 | Ver E2 |
| FR-014 | Sí | T015, T022, T023, T048 | Ver U2 |
| FR-015 | Sí | T027, T040 | |
| FR-016 | Sí | T010, T020, T053 | |
| SC-001 | Sí | T024, T033 | |
| SC-002 | Sí | T026, T034 | |
| SC-003 | Sí | T009, T028 | Ver I1, I2 |
| SC-005 | Sí | T046 | |
| SC-006 | Sí | T022, T048 | Ver U2 |

SC-004 se excluye del cómputo: es un resultado con personas (ver E3).

**Tareas sin requisito asociado:** ninguna. Las de setup (T001, T002), polish (T049-T053) y cierre
(T054-T056) son de soporte o de §VII.

## Métricas

- Requisitos: 22 (17 FR y 5 SC con trabajo construible)
- Tareas: 56
- Cobertura: 100 % (22/22 con al menos una tarea)
- Ambigüedades: 2 (F5, E1)
- Duplicaciones: 0
- Problemas críticos: 0 (C1 roza §II; se clasifica HIGH porque el código decide la abstención y
  solo falta hacerla visible)

## Siguientes pasos

Sin hallazgos críticos. Antes de `/speckit-implement` conviene resolver C1, I1 y U1, que afectan
a la constitución, a un escenario de aceptación y a un test de integración que no se puede
escribir tal cual, y anotar en T022 los requisitos de cada grabación (U2). El resto se puede
corregir editando `data-model.md` y `tasks.md` sin volver a `/speckit-plan`.
