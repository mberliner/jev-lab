---

description: "Lista de tareas de la spec 002: Enrutado con confianza según riesgo"
---

# Tasks: Enrutado con confianza según riesgo

**Input**: Design documents from `specs/002-enrutado-confianza/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-route.md,
contracts/cli-review.md, quickstart.md

**Tests**: MANDATORY (jev-lab, Constitution IV). Every user story includes test tasks, written
before its implementation tasks and failing before implementing. Tests against real services are
optional, marked `live`, and declare a cost cap. Test mix per story (docs/standards/testing.md §2):
unit tests first, enough to reach coverage; one `integration` test for the main acceptance
scenario; contract tests only if the story adds or changes an adapter.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing
of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 a US4)
- Rutas relativas a la raíz del repositorio; estructura de `plan.md`, «Project Structure»
- Reglas de cada capa: `docs/standards/architecture.md`. Salida y códigos:
  `contracts/cli-route.md` y `contracts/cli-review.md`. Entidades y transiciones: `data-model.md`
- La generalización de la petición (research R1), la política, el almacén SQLite y las
  grabaciones del enrutado van en la fase 2: las cuatro historias los usan. Los tests de la 001
  se adaptan a las firmas nuevas y deben seguir pasando sin cambiar lo que comprueban

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: carpetas nuevas del paquete y tarea de grabación.

- [ ] T001 [P] Crear las carpetas nuevas: `src/jevlab/policies/soporte/` y `src/jevlab/recordings/soporte/enrutado/`
- [ ] T002 [P] Ampliar la tarea `record` de `[tool.poe.tasks]` en `pyproject.toml` para que ejecute `tests/live/test_record_triage.py` y `tests/live/test_record_route.py` con `JEVLAB_RECORD=1` (research R8)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: petición genérica, decisión `solicitud`, política, puertos nuevos, almacén SQLite y
grabaciones del enrutado. Todo lo que las cuatro historias comparten.

**CRITICAL**: No user story work can begin until this phase is complete

### Tests de la base (write first, must FAIL before implementation)

- [ ] T003 [P] Ampliar `tests/unit/domain/test_decision_spec.py` (data-model, «Definiciones»): `ResolvedRequest` con una decisión inexistente o con modelos distintos falla; `TriageSpec.from_request` con preguntas distintas de `cola`, `urgencia` y `prioridad` o con otra primitiva falla; `RouteSpec.from_request` exige exactamente `cola` y `solicitud`, las dos Choice; falla si `solicitud` no tiene la opción `reembolso` o `cola` no tiene `facturacion`; `spec_versions()` incluye la petición y cada decisión. Los casos existentes de la 001 se mantienen con las firmas nuevas
- [ ] T004 [P] Tests unitarios de `Answers` en `tests/unit/domain/test_triage_answers.py`: `TriageAnswers` derivada de `Answers` da los mismos `queue`, `urgency` y `priority` que antes; una pregunta ausente o con una respuesta de otra primitiva llega como `None`
- [ ] T005 [P] Tests unitarios y de propiedades (`hypothesis`) de `src/jevlab/domain/policy.py` en `tests/unit/domain/test_policy.py` (data-model, «Política»; FR-010, FR-013): es no válida si falta `mover-a-cola` o `reembolsar`, sobra una acción desconocida, «0 <= umbral <= 1» no se cumple, el riesgo no es `bajo`, `medio` o `alto`, `justificacion` está vacía o la `version` no es semver; monotonía «si `a.riesgo > b.riesgo` entonces `a.umbral >= b.umbral`», con un error que nombra las dos acciones; propiedad: para cualquier par de umbrales y riesgos generados, la política es válida si y solo si se cumple la monotonía; `fingerprint` tiene 8 caracteres hexadecimales, cambia con cualquier umbral, riesgo, justificación o versión y no cambia con el orden de las claves del YAML (research R3)
- [ ] T006 [P] Crear en `tests/fakes.py`: `FakeJudge` con `ask(request, ticket) -> Answers` (respuestas programables por texto o una excepción del dominio); `InMemoryRoutingStore` con las firmas de `RoutingStore` (T014); `SequentialIds` (`req-0001`, `req-0002`…); `FrozenClock.now()` con un `datetime` UTC fijo; `StaticPolicyLoader` que devuelve una `Policy` dada o lanza `InvalidPolicy`. Adaptar `StaticSpecLoader` a `ResolvedRequest`
- [ ] T007 [P] Ampliar `tests/contract/test_typesafe_judge.py` y sus fixtures en `tests/contract/fixtures/`: el juez construye las preguntas desde cualquier `ResolvedRequest`; con la petición `enrutado`, una respuesta válida sintética (`origen: sintetico`) se traduce a `Answers` con `cola` y `solicitud`; el texto viaja solo en `state` (FR-016). Los casos de errores de la 001 siguen pasando con la petición de triaje
- [ ] T008 [P] Ampliar `tests/contract/test_yaml_files.py`: carga `soporte/enrutado` como `ResolvedRequest` válida para `RouteSpec`; `soporte/triaje` y `soporte/enrutado` resuelven la misma `ChoiceSpec` para `cola-destino` (plan, «Una sola definición»); `YamlRecordingLibrary` con raíz `recordings/soporte/enrutado` lee y guarda igual que la de triaje; `YamlPolicyLoader` carga `src/jevlab/policies/soporte/enrutado.yaml` con «`mover-a-cola` riesgo bajo, umbral 0,90; `reembolsar` riesgo alto, umbral 0,97; los dos `provisional`», carga un archivo en `tmp_path` por ruta, y un archivo inexistente, ilegible o no válido da `InvalidPolicy` con la ruta y el motivo, sin el contenido
- [ ] T009 [P] Test de contrato de `SqliteRoutingStore` en `tests/contract/test_sqlite_store.py` con `tmp_path` (data-model, «Persistencia»; research R5): crea el esquema y `PRAGMA user_version = 1` al abrir; un archivo con otra `user_version` da `StateUnreadable` con la ruta; `record(result, entries, item)` guarda la auditoría y el elemento en una sola transacción (si falla la inserción del elemento, no queda auditoría); los datos persisten al cerrar y volver a abrir; `pending()` devuelve los elementos con acciones sin resolver, del más antiguo al más reciente; `get(id)` y `save_resolution(item, entry)` actualizan el elemento y añaden la auditoría juntos; ninguna columna de `audit` contiene el texto del ticket (SC-003); las consultas son parametrizadas (un texto con comillas y `;` se guarda tal cual en `review_item.ticket`)
- [ ] T010 [P] Tests unitarios de `state_dir()` en `tests/unit/adapters/test_state_dir.py` (research R5): con `JEVLAB_STATE_DIR` usa esa carpeta; sin ella, en Windows `%LOCALAPPDATA%\jevlab` y en Linux `$XDG_STATE_HOME/jevlab` o `~/.local/state/jevlab` (con el entorno y la plataforma simulados); crea la carpeta si no existe
- [ ] T011 [P] Ampliar `tests/unit/adapters/test_system_clock.py` con `now()` (un `datetime` con zona UTC) y crear `tests/unit/adapters/test_uuid_ids.py`: `UuidIdGenerator.new_request_id()` devuelve identificadores distintos con forma de UUID

### Implementación de la base

- [ ] T012 Implementar en `src/jevlab/domain/decision_spec.py` `ResolvedRequest` (`request`, `decisions`, modelo común, `model`, `max_chars`, `questions()`, `spec_versions()`), `TriageSpec.from_request` (sustituye a `resolve`) y `RouteSpec.from_request` con las reglas de data-model, «`RouteSpec`»; en `src/jevlab/domain/triage.py`, `Answers` (`model`, `by_question`) y `TriageAnswers.from_answers`. T003 y T004 pasan (depende de T003 y T004)
- [ ] T013 Adaptar los puertos `JudgePort.ask(request: ResolvedRequest, ticket) -> Answers` en `src/jevlab/ports/judge.py` y `SpecLoader.load_request(name) -> ResolvedRequest` en `src/jevlab/ports/specs.py`; adaptar `TypeSafeJudge.ask` en `src/jevlab/adapters/typesafe_judge.py` para decodificar cada respuesta del SDK por su tipo sin nombres de pregunta fijos; `YamlSpecLoader` en `src/jevlab/adapters/yaml_files.py` devuelve `ResolvedRequest`; `TriageTicket` y `RecordExamples` en `src/jevlab/application/triage.py` usan `ResolvedRequest` (`RecordExamples` sirve a cualquier petición). Toda la suite de la 001 y T007 pasan (depende de T006, T007 y T012)
- [ ] T014 [P] Definir como `typing.Protocol` los puertos nuevos: `PolicyLoader.load(path: Path | None) -> Policy` en `src/jevlab/ports/policy.py`; `RoutingStore` (`record(result, entries, item)`, `pending()`, `get(item_id)`, `save_resolution(item, entry)`) en `src/jevlab/ports/routing_store.py`; `IdGenerator.new_request_id() -> str` en `src/jevlab/ports/ids.py`; y `Clock.now() -> datetime` en `src/jevlab/ports/clock.py`
- [ ] T015 [P] Escribir `src/jevlab/specs/soporte/solicitud.yaml` y `src/jevlab/specs/soporte/enrutado.yaml` con el contenido exacto de data-model, «Definiciones YAML nuevas» (`version: 0.1.0`, `model: jev-1.13.0`, `max_chars: 4000`)
- [ ] T016 Implementar en `src/jevlab/domain/policy.py` `Risk` (enum ordenado «`bajo` < `medio` < `alto`»), `ActionName` (`mover-a-cola`, `reembolsar`), `ActionPolicy` («0 <= umbral <= 1»; `justificacion` no vacía), `Policy` (`version` semver; «exactamente `mover-a-cola` y `reembolsar`»; monotonía por riesgo), `fingerprint` (8 hex del SHA-256 del JSON canónico) y `PolicyRef` (`version`, `fingerprint`); añadir `InvalidPolicy(source, reason)` y `StateUnreadable(path)` a `src/jevlab/domain/diagnostics.py`, con mensajes sin contenido del archivo. T005 pasa (depende de T005)
- [ ] T017 [P] Escribir la política inicial `src/jevlab/policies/soporte/enrutado.yaml` con el contenido exacto de data-model, «Política»
- [ ] T018 Implementar `YamlPolicyLoader` en `src/jevlab/adapters/yaml_files.py` (por defecto lee `policies/soporte/enrutado.yaml` del paquete con `importlib.resources`; con ruta, ese archivo) y dar a `YamlRecordingLibrary` la raíz de la petición (`recordings/soporte/<petición>`). T008 pasa (depende de T013, T015, T016 y T017)
- [ ] T019 Crear en `src/jevlab/domain/routing.py` los tipos de data-model, «Resultado del enrutado» y «Auditoría»: `ActionStatus`, `PendingReason` (con el texto de la salida), `ActionOutcome`, `RoutingResult` (`needs_review`) y `AuditEntry`; y en `src/jevlab/domain/review.py`, `ReviewItem`, `ReviewAction` y `Resolution`, sin reglas todavía (depende de T016)
- [ ] T020 Implementar `SqliteRoutingStore` y `state_dir()` en `src/jevlab/adapters/sqlite_store.py` con el esquema de data-model, «Persistencia» (`sqlite3`, `pathlib`, consultas parametrizadas, JSON para `reasons`, `origin` y `spec_versions`, una transacción por `record` y por `save_resolution`). T009 y T010 pasan (depende de T014 y T019)
- [ ] T021 [P] Implementar `UuidIdGenerator` en `src/jevlab/adapters/uuid_ids.py` y `SystemClock.now()` en `src/jevlab/adapters/system_clock.py`. T011 pasa
- [ ] T022 Escribir la grabación del enrutado en `tests/live/test_record_route.py` con `@pytest.mark.live(max_usd=0.01)` (research R8): los seis ejemplos de `tests/live/test_record_triage.py` (importados de allí, mismo nombre y texto) y `reembolso-ambiguo`, un texto propio que insinúa una devolución sin pedirla claramente, con `covers` de SC-006 (`mover-automatizada`, `mover-a-revision`, `mover-escape`, `reembolso-automatizado`, `reembolso-pendiente`); solo escribe con `JEVLAB_RECORD=1`; `RecordExamples` con la petición `enrutado` y `YamlRecordingLibrary` con raíz `src/jevlab/recordings/soporte/enrutado/` (depende de T013 y T018)
- [ ] T023 Grabar con `uv run poe record` (necesita `.env`; tope de la tarea) y revisar cada archivo de `src/jevlab/recordings/soporte/enrutado/`: sin cabeceras, `model` y `recorded_on` presentes. Comprobar con la política inicial que cada ejemplo cae donde pretende su `covers`; si no, reescribir el texto y regrabar, anotándolo aquí (research R8). Las grabaciones de `soporte/triaje/` no deben cambiar (depende de T022)

**Checkpoint**: la suite de la 001 sigue en verde con la petición genérica; política, almacén y
grabaciones del enrutado listos.

---

## Phase 3: User Story 1 - Enrutar solo lo que tiene confianza suficiente, con el motivo (Priority: P1) MVP

**Goal**: `jevlab route` mueve un ticket a su cola solo si la confianza alcanza el umbral de
«mover a cola», explica el motivo y deja la decisión en la auditoría.

**Independent Test**: `uv run jevlab route --ejemplo cambio-de-correo` se automatiza;
`--ejemplo instruccion-incrustada` y `--ejemplo pregunta-fuera-de-ambito` no, con su motivo; la
auditoría tiene una entrada por petición con su identificador.

### Tests for User Story 1 (write first, must FAIL before implementation)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T024 [P] [US1] Tests unitarios y de propiedades (`hypothesis`) de `decide_routing` para `mover-a-cola` en `tests/unit/domain/test_routing_queue.py` (research R4; FR-003, FR-013): con confianza igual al umbral se automatiza (`>=`); por debajo, `a revisión` con «confianza por debajo del umbral»; `other` con confianza 1,0 nunca se automatiza (motivo `escape`); opción fuera de la definición y sin respuesta, `a revisión` con su motivo y `value` `None` («sin cola»); se compara la confianza del servicio, no la recalculada; propiedades: para cualquier política válida y cualquier confianza, nada por debajo del umbral se automatiza, el escape siempre termina en revisión y, si una confianza se automatiza, cualquier confianza mayor también
- [ ] T025 [P] [US1] Tests unitarios de `RouteTicket` en `tests/unit/application/test_routing.py` con `FakeJudge`, `StaticSpecLoader`, `StaticPolicyLoader`, `InMemoryRoutingStore`, `SequentialIds` y `FrozenClock`: pide al juez una sola vez con la petición `enrutado` y el texto normalizado; el `RoutingResult` lleva `request_id`, `decided_at`, `origin`, `PolicyRef` y `spec_versions`; graba en el almacén una `AuditEntry` de tipo `decision` por acción con los campos de data-model, «`AuditEntry`», sin el texto del ticket (FR-011); en vivo comprueba la longitud antes de llamar
- [ ] T026 [P] [US1] Tests de la vista en `tests/unit/entrypoints/test_route_view.py` (`contracts/cli-route.md`): líneas `Origen:`, `Política: <versión> · huella <8 hex>` y `Petición:`; `Mover a cola: <cola> · automatizada` con `confianza 1,00 ≥ umbral 0,90 (riesgo bajo, provisional)`; `a revisión` con `<` y la línea `motivo:`; `sin cola · a revisión` con el motivo de escape; `confianza no disponible` sin respuesta; coma decimal y dos decimales
- [ ] T027 [P] [US1] Tests del comando en `tests/unit/entrypoints/test_cli_route.py` con `CliRunner`, `JEVLAB_STATE_DIR` en `tmp_path` y grabaciones reales: modos y selección iguales a `triage` (texto, `--ejemplo`, sin terminal lista y código 2, opciones incompatibles código 2); código 0 aunque no se automatice; los errores van a `stderr` en una línea y no contienen el texto del ticket; el log `info` de `route` tiene `peticion`, `modo`, `ejemplo`, `modelo`, `politica` y el resultado por acción, sin el texto (FR-015)
- [ ] T028 [P] [US1] Test de integración (marca `integration`) en `tests/integration/test_route_queue.py`: con la red bloqueada, sin `.env` y `JEVLAB_STATE_DIR` temporal, `route --ejemplo cambio-de-correo` sale automatizada, `--ejemplo instruccion-incrustada` sale a revisión con confianza por debajo de 0,90 y `--ejemplo pregunta-fuera-de-ambito` sale `sin cola`; el archivo de estado tiene una entrada de auditoría por petición con su `request_id`, la versión y la huella de la política y sin el texto de ningún ticket

### Implementation for User Story 1

- [ ] T029 [US1] Implementar `decide_routing(policy, queue, request_kind)` en `src/jevlab/domain/routing.py` para `mover-a-cola`, a partir de `interpret_queue` de la 001 y de `PendingReason` en el orden de data-model; el reembolso queda para la US2. T024 pasa (depende de T019)
- [ ] T030 [US1] Implementar `RouteTicket(judge, specs, policies, store, ids, clock)` en `src/jevlab/application/routing.py` con `run_live(raw, policy_path)` y `run_recorded(recording, policy_path)`: carga la política antes de llamar al juez, interpreta, decide, construye las `AuditEntry` y llama a `store.record(result, entries, None)`. T025 pasa (depende de T029)
- [ ] T031 [US1] Implementar `src/jevlab/entrypoints/cli/route_view.py` con el formato de `contracts/cli-route.md`, reutilizando el formato de números y de origen de `triage_view.py`. T026 pasa
- [ ] T032 [US1] Añadir el comando `route` a `src/jevlab/entrypoints/cli/main.py`: cableado de `YamlSpecLoader`, `YamlPolicyLoader`, `SqliteRoutingStore(state_dir())`, `UuidIdGenerator`, `SystemClock`, juez grabado o en vivo y biblioteca `recordings/soporte/enrutado`; selección de ejemplo y menú compartidos con `triage`; `StateUnreadable` termina con código 1; log `info` de `contracts/cli-route.md`. T027 y T028 pasan (depende de T030 y T031)

**Checkpoint**: la US1 funciona y se demuestra sola.

---

## Phase 4: User Story 2 - Exigir más confianza a una acción destructiva (Priority: P2)

**Goal**: el reembolso (simulado) se automatiza solo con confianza ≥ 0,97 en `solicitud` y la
cola automatizada a `facturacion`; si no, queda pendiente de confirmación.

**Independent Test**: `uv run jevlab route --ejemplo cobro-duplicado` reembolsa automáticamente;
`--ejemplo reembolso-ambiguo` deja el reembolso pendiente de confirmación con su motivo.

### Tests for User Story 2 (write first, must FAIL before implementation)

- [ ] T033 [P] [US2] Tests unitarios y de propiedades (`hypothesis`) del reembolso en `tests/unit/domain/test_routing_refund.py` (research R4; FR-006, FR-013): solicitud `reembolso` con confianza ≥ umbral y cola automatizada a `facturacion` se automatiza; con confianza por debajo, `pendiente de confirmación` con «confianza por debajo del umbral»; con confianza suficiente y cola en revisión, con escape o automatizada a `tecnico` o `cuenta`, `pendiente de confirmación` con «la cola no se automatizó a facturacion»; las dos causas a la vez dan los dos motivos en orden; solicitud `consulta`, `incidencia`, `other`, fuera de la definición o sin respuesta no producen la acción `reembolsar`; propiedad: ningún reembolso se automatiza sin la cola automatizada a `facturacion` ni por debajo de su umbral, para cualquier política válida
- [ ] T034 [P] [US2] Ampliar `tests/unit/entrypoints/test_route_view.py`: `Reembolsar: reembolso · automatizada (simulado)` con `riesgo alto` y `cola facturacion automatizada`; `pendiente de confirmación` con su motivo; sin la línea `Reembolsar` si la solicitud no es `reembolso` (en serie con T026)
- [ ] T035 [P] [US2] Test de integración (marca `integration`) en `tests/integration/test_route_refund.py`: sin red, `route --ejemplo cobro-duplicado` automatiza los dos, y `--ejemplo reembolso-ambiguo` deja el reembolso `pendiente de confirmación`; la auditoría tiene una entrada `reembolsar` en cada petición con riesgo `alto` y umbral 0,97

### Implementation for User Story 2

- [ ] T036 [US2] Ampliar `decide_routing` en `src/jevlab/domain/routing.py` con `reembolsar` según research R4. T033 pasa (depende de T029)
- [ ] T037 [US2] Ampliar `src/jevlab/entrypoints/cli/route_view.py` y el log `info` de `route` en `src/jevlab/entrypoints/cli/main.py` con la acción `reembolsar`. T034 y T035 pasan (depende de T036)

**Checkpoint**: las US1 y US2 funcionan y se demuestran por separado.

---

## Phase 5: User Story 3 - Atender la cola de revisión (Priority: P3)

**Goal**: lo que no se automatiza crea un elemento por petición; el Operador lo lista y lo
resuelve con `jevlab review`, y cada resolución queda en la auditoría.

**Independent Test**: enrutar `instruccion-incrustada`, `pregunta-fuera-de-ambito` y
`reembolso-ambiguo`; `uv run jevlab review` los lista; resolver uno lo saca de pendientes y deja
su resolución en la auditoría.

### Tests for User Story 3 (write first, must FAIL before implementation)

- [ ] T038 [P] [US3] Tests unitarios de las transiciones en `tests/unit/domain/test_review.py` (data-model, «Transiciones»): `ReviewItem.from_result` crea un elemento solo si `needs_review`, con las acciones no automatizadas y `queue` igual a la cola automatizada o `None`; `asignar` con una cola de `cola-destino` resuelve `mover-a-cola` y fija `queue`; si la cola no es `facturacion`, el reembolso pendiente queda `rechazada`; `descartar` deja `mover-a-cola` `descartada` y el reembolso `rechazada`; `confirmar` exige `queue == facturacion` o lanza `RefundNeedsBillingQueue`; `rechazar` resuelve el reembolso; una acción ya resuelta o un elemento sin pendientes lanza `AlreadyResolved`; una cola desconocida o el escape lanza `UnknownQueue` con las colas válidas; cada transición devuelve una `AuditEntry` de tipo `resolucion` con el `request_id` original; `pending` es falso cuando no quedan acciones sin resolver
- [ ] T039 [P] [US3] Ampliar `tests/unit/application/test_routing.py` y crear `tests/unit/application/test_review.py` con fakes: `RouteTicket` crea un único elemento por petición cuando alguna acción no se automatiza y ninguno cuando todo se automatiza (FR-007); `ListPending` devuelve los pendientes en orden; `ResolveReview` carga el elemento, aplica la transición con las colas de `cola-destino` y guarda resolución y auditoría juntas; un elemento inexistente lanza `ReviewItemNotFound`
- [ ] T040 [P] [US3] Tests de la vista y del comando en `tests/unit/entrypoints/test_review_view.py` y `tests/unit/entrypoints/test_cli_review.py` (`contracts/cli-review.md`): `Pendientes: N` y cada elemento con fecha, origen, política, petición, texto recortado a 72 caracteres con `…` y una línea por acción; `Pendientes: 0`; mensajes de resolución; códigos 2 para elemento inexistente, acción ya resuelta, cola desconocida y confirmación sin `facturacion` (con el mensaje que sugiere `jevlab review asignar`); ningún error contiene el texto del ticket; log `info` de `review` sin el texto; la ruta `route` muestra `En la cola de revisión: elemento N (jevlab review)`
- [ ] T041 [P] [US3] Test de integración (marca `integration`) en `tests/integration/test_review_flow.py`: sin red y con `JEVLAB_STATE_DIR` temporal, enrutar los tres ejemplos de la prueba independiente, listar, `asignar <id> cuenta` en `instruccion-incrustada`, `confirmar` antes de asignar en un elemento con cola y reembolso pendientes da código 2, `confirmar` en `reembolso-ambiguo` (cola `facturacion` automatizada) funciona, y una nueva invocación de `review` (otro proceso lógico sobre el mismo archivo) solo lista lo que queda

### Implementation for User Story 3

- [ ] T042 [US3] Implementar en `src/jevlab/domain/review.py` `ReviewItem.from_result`, `resolve(item, command, queues, now)` y los errores `RefundNeedsBillingQueue`, `AlreadyResolved`, `UnknownQueue` y `ReviewItemNotFound`. T038 pasa (depende de T019)
- [ ] T043 [US3] Ampliar `RouteTicket` en `src/jevlab/application/routing.py` para crear el elemento y pasarlo a `store.record`; implementar `ListPending(store)` y `ResolveReview(store, specs, clock)` en `src/jevlab/application/review.py`. T039 pasa (depende de T030 y T042)
- [ ] T044 [US3] Implementar `src/jevlab/entrypoints/cli/review_view.py` y el grupo `review` en `src/jevlab/entrypoints/cli/main.py` (lista sin subcomando; `asignar ID COLA`, `descartar ID`, `confirmar ID`, `rechazar ID`) con los códigos de `contracts/cli-review.md`; añadir la línea del elemento a `route_view.py`. T040 y T041 pasan (depende de T043)

**Checkpoint**: las US1 a US3 funcionan; el Operador atiende la cola.

---

## Phase 6: User Story 4 - Cambiar los umbrales en una política versionada (Priority: P4)

**Goal**: el Operador cambia los umbrales en un archivo de política, sin tocar código; cada salida
y cada registro muestran la versión y la huella aplicadas, y una política no válida no automatiza
nada.

**Independent Test**: enrutar `instruccion-incrustada` con la política inicial y con una copia de
umbral 0,80 y versión 0.2.0 (`--politica`): el resultado cambia, y la versión y la huella también;
una copia no monótona termina con código 1.

### Tests for User Story 4 (write first, must FAIL before implementation)

- [ ] T045 [P] [US4] Tests unitarios en `tests/unit/application/test_routing.py` y `tests/unit/entrypoints/test_cli_route.py`: con `InvalidPolicy`, `RouteTicket` no llama al juez ni escribe en el almacén; `route --politica <ruta>` usa ese archivo; una política no válida o inexistente termina con código 1 y el mensaje de `contracts/cli-route.md`, que nombra el campo y no contiene el texto del ticket; dos políticas con la misma versión semver y un umbral distinto muestran y auditan huellas distintas (US4, escenario 5)
- [ ] T046 [P] [US4] Test de integración (marca `integration`) en `tests/integration/test_route_policy.py`: sin red, `route --ejemplo instruccion-incrustada` con la política inicial va a revisión; con una copia en `tmp_path` con `mover-a-cola.umbral: 0.80` y `version: 0.2.0` se automatiza, y la salida y la auditoría muestran `0.2.0` y otra huella; una copia con `reembolsar.umbral` menor que el de `mover-a-cola` termina con código 1 y no escribe en el estado (SC-005)

### Implementation for User Story 4

- [ ] T047 [US4] Añadir la opción `--politica RUTA` a `route` en `src/jevlab/entrypoints/cli/main.py`, traducir `InvalidPolicy` a código 1 con el mensaje del contrato y comprobar que `RouteTicket` carga la política antes de cualquier efecto. T045 y T046 pasan (depende de T032)

**Checkpoint**: las cuatro historias funcionan y se demuestran por separado.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: cobertura de las grabaciones, documentación, humo en vivo y validación.

- [ ] T048 [P] Tests sobre las grabaciones reales en `tests/unit/recordings/test_route_recordings.py`: cada grabación de `recordings/soporte/enrutado/` tiene `model`, `recorded_on`, `synthetic`, ninguna cabecera y se reproduce con la definición actual; con la política inicial, los ejemplos cubren los cinco casos de SC-006; `instruccion-incrustada` no automatiza ninguna acción (plan, «Contenido adversarial»); la confianza recalculada de `solicitud` coincide con la del servicio con una diferencia máxima de 0,01 (como SC-003 de la 001)
- [ ] T049 [P] Humo en vivo en `tests/live/test_route_live.py` con `@pytest.mark.live(max_usd=0.01)`: `route --en-vivo "<texto propio>"` con `JEVLAB_STATE_DIR` temporal termina con código 0, `Origen: en vivo` y una entrada de auditoría
- [ ] T050 [P] Documentar en `docs/setup.md` dónde vive el estado local (`estado.sqlite3`), cómo cambiarlo con `JEVLAB_STATE_DIR` y cómo empezar de cero borrando el archivo; enlazar `contracts/cli-route.md` como referencia en `docs/standards/cli-ux.md` junto a la de `triage` si hace falta para el formato `≥`/`<`
- [ ] T051 Ejecutar `uv run poe live` con `.env` (humo de `triage` y de `route`; tope de la sesión)
- [ ] T052 Ejecutar `uv run poe check` y anotar aquí la cobertura, el número de tests y el tiempo de la suite; la cobertura sigue ≥ 80 %
- [ ] T053 Validar `quickstart.md` en Linux o Git Bash y en Windows (PowerShell), y anotar aquí lo que haya que corregir

---

## Fase final: cierre de la feature (jev-lab)

> Deriva de: Constitución §VII y *Governance* (revisión periódica)

- [ ] T054 Escribir la lección `docs/lessons/002-la-confianza-como-segundo-eje-y-umbrales-por-riesgo.md`: qué se aprende, cómo se ejecuta, qué puede fallar y su mitigación (spec, «Corte vertical y lección»), con las cifras de las grabaciones reales
- [ ] T055 Demostrar cada historia con el comando de la tabla «Corte vertical y lección» de la spec y anotar aquí la salida resumida de cada una
- [ ] T056 Retro: ¿algún principio estorbó?, ¿faltó alguno?, ¿alguno no se pudo verificar? Respuestas en el commit de cierre; cada «sí» abre su cambio o se anota en `docs/ideas.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de Setup y bloquea todas las historias. T023 (grabar)
  necesita `.env` con la clave de TypeSafe.
- **User Stories (Phase 3+)**: dependen de Foundational. Sus tests unitarios avanzan sin T023;
  los de integración (T028, T035, T041, T046) y T048 necesitan las grabaciones del enrutado.
- **Polish (Phase 7)**: después de las historias.
- **Cierre**: al final.

### User Story Dependencies

- **US1 (P1)**: tras Foundational; crea `decide_routing`, `RouteTicket`, el comando y la vista.
- **US2 (P2)**: tras US1, porque amplía `decide_routing` y la vista; se demuestra por separado
  con `--ejemplo`.
- **US3 (P3)**: tras US1; su ejemplo de reembolso pendiente (T041) necesita la US2.
- **US4 (P4)**: tras US1; independiente de US2 y US3.

### Within Each User Story

- Los tests se escriben y fallan antes de implementar.
- Dominio, después puertos, después aplicación, después adaptadores y, por último, entrypoints.

### Parallel Opportunities

- Setup: T001 y T002.
- Foundational: T003 a T011 (tests y fakes); T014, T015, T017 y T021.
- US1: T024 a T028. US2: T033 y T035 (T034 en serie con T026). US3: T038 a T041. US4: T045 y
  T046 (T045 toca archivos de la US1: en serie con T025 y T027).
- Polish: T048 a T050.

---

## Parallel Example: Foundational

```bash
# Tests de la base en paralelo:
Task: "Política y huella en tests/unit/domain/test_policy.py"
Task: "SqliteRoutingStore en tests/contract/test_sqlite_store.py"
Task: "YamlPolicyLoader y enrutado en tests/contract/test_yaml_files.py"
Task: "ResolvedRequest y RouteSpec en tests/unit/domain/test_decision_spec.py"

# Implementación independiente en paralelo:
Task: "Puertos nuevos en src/jevlab/ports/"
Task: "solicitud.yaml y enrutado.yaml en src/jevlab/specs/soporte/"
Task: "Política inicial en src/jevlab/policies/soporte/enrutado.yaml"
```

## Parallel Example: User Story 1

```bash
Task: "decide_routing para mover-a-cola en tests/unit/domain/test_routing_queue.py"
Task: "RouteTicket con fakes en tests/unit/application/test_routing.py"
Task: "Vista de route en tests/unit/entrypoints/test_route_view.py"
Task: "Comando route en tests/unit/entrypoints/test_cli_route.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 y Phase 2, con T023 en cuanto se revise la grabación.
2. Phase 3 (US1): mover a cola con umbral, motivo y auditoría.
3. Validar la US1 por separado con quickstart, «US1».

### Incremental Delivery

1. Setup y Foundational: petición genérica, política, almacén y grabaciones.
2. US1: confianza como segundo eje (MVP).
3. US2: umbral por riesgo con el reembolso.
4. US3: cola de revisión y `jevlab review`.
5. US4: política alternativa y errores de validación.
6. Polish, lección y cierre.

---

## Notes

- [P]: archivos distintos y sin dependencias pendientes.
- Commit después de cada tarea o grupo lógico, en Conventional Commits y sin atribuciones de
  agentes.
- T023, T049 y T051 necesitan claves reales; T053 incluye una comprobación manual en Windows.
