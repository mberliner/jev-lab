# Feature Specification: Enrutado con confianza según riesgo

**Feature Branch**: `002-enrutado-confianza`

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "Spec 002: Enrutado con confianza según riesgo (persona: Usuario
inicial de Jev -> Operador). Aprende: la confianza como segundo eje de decisión y umbrales por
riesgo. Parte del triaje de la spec 001. US1 un ticket con confianza alta se enruta solo y la CLI
explica el motivo (umbral y valor); US2 una acción destructiva (reembolso automático) exige un
umbral más alto y, si no se alcanza, se pide confirmación; US3 lo que tiene confianza baja o
`other` entra en una cola de revisión (SQLite), que el Operador lista y resuelve con
`jevlab review`; US4 el Operador cambia los umbrales en `policy.yaml` versionado, sin tocar
código, y la CLI muestra qué versión se aplicó. Producción: configuración validada con Pydantic,
auditoría de decisiones con `request_id` y tests de propiedades (hypothesis) que comprueban que
las bandas son monótonas. Fuente: sección «002» de `docs/roadmap.md`."

## Clarifications

### Session 2026-10-14

- Q: Si un reembolso no alcanza su umbral, ¿cómo se pide la confirmación? -> A: queda en la cola
  de revisión como «pendiente de confirmación» y el Operador lo confirma o lo rechaza con
  `jevlab review`.
- Q: ¿Qué umbrales iniciales lleva la política? -> A: «mover a cola» 0,90 y «reembolsar» 0,97,
  los dos provisionales hasta la evaluación de la spec 004.
- Q: ¿De qué decisión depende el reembolso? -> A: de una Choice nueva, `solicitud` («¿Qué pide el
  cliente en este ticket?»), con `reembolso`, `consulta`, `incidencia` y `other`, porque tiene
  confianza y un Noul no.
- Q: Si la solicitud es `reembolso` con confianza suficiente pero la cola no se mueve sola, ¿se
  reembolsa automáticamente? -> A: no; el reembolso solo se automatiza si además la cola se movió
  sola a `facturacion`; si no, queda pendiente de confirmación.
- Q: Si una petición no automatiza ninguna de sus dos acciones, ¿cuántos elementos crea en la cola
  de revisión? -> A: uno por petición, con sus acciones pendientes; el reembolso solo se confirma
  cuando la cola es `facturacion`, y asignar otra cola o descartar el elemento lo rechaza.
- Q: Si cambia un umbral de la política sin subir su versión, ¿qué pasa? -> A: la salida, la
  auditoría y la cola de revisión guardan la versión semver y una huella corta del contenido,
  calculada por el código, que distingue los dos contenidos; no se bloquea el cambio.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enrutar solo lo que tiene confianza suficiente, con el motivo (Priority: P1)

Como usuario inicial de Jev, quiero ejecutar `jevlab route "<texto>"` y ver si el ticket se mueve
solo a su cola o se queda sin mover, con la confianza, el umbral aplicado y el motivo, para
aprender que el valor de una respuesta no basta y que la confianza es el segundo eje de la
decisión.

**Why this priority**: Es el mínimo viable: la primera acción automatizada del proyecto, condicionada
a la confianza además de al valor (Constitución §II), y explicada.

**Independent Test**: Enrutar un ticket de ejemplo con confianza por encima del umbral y otro por
debajo, y comprobar que el primero se mueve a su cola y el segundo no, y que la salida muestra en
los dos casos la cola propuesta, la confianza, el umbral, el riesgo de la acción y el motivo.

**Acceptance Scenarios**:

1. **Given** un ticket cuya cola tiene una confianza mayor o igual que el umbral de «mover a
   cola», **When** la persona ejecuta `jevlab route "<texto>"`, **Then** la salida dice que el
   ticket se mueve automáticamente a esa cola e indica la confianza, el umbral y el riesgo.
2. **Given** un ticket cuya cola tiene una confianza por debajo del umbral, **When** lo enruta,
   **Then** el ticket no se mueve y la salida explica el motivo con la confianza y el umbral,
   separando lo que propone el modelo de lo que aplica el código (por ejemplo,
   `IA propone la cola: cuenta · confianza 0,87` y `regla: 0,87 < 0,90 · motivo: confianza por
   debajo del umbral`).
3. **Given** un ticket cuyo resultado es `other` o no tiene una respuesta válida, **When** lo
   enruta, **Then** el ticket no se mueve, sea cual sea la confianza, y la salida lo explica.
4. **Given** cualquier ticket enrutado, **When** termina el comando, **Then** la decisión queda
   registrada en la auditoría con su identificador de petición, y la salida muestra ese
   identificador.

---

### User Story 2 - Exigir más confianza a una acción destructiva (Priority: P2)

Como usuario inicial de Jev, quiero que un reembolso automático (simulado) exija un umbral de
confianza más alto que mover un ticket de cola y que, si no se alcanza, se pida confirmación, para
aprender que el umbral depende del riesgo de la acción y no de la pregunta.

**Why this priority**: Enseña el umbral por riesgo (Constitución §II) con una acción cuyo error
cuesta dinero. Usa el mismo comando de la US1, pero se puede demostrar por separado.

**Independent Test**: Enrutar un ticket que pide claramente un reembolso y otro que lo pide de
forma ambigua, y comprobar que el primero se reembolsaría automáticamente y el segundo queda en
la cola de revisión como pendiente de confirmación.

**Acceptance Scenarios**:

1. **Given** un ticket cuya solicitud es `reembolso` con una confianza mayor o igual que el umbral
   de «reembolsar» y cuya cola se mueve sola a `facturacion`, **When** la persona lo enruta, **Then** la salida dice que el reembolso se
   ejecutaría automáticamente (simulado), con la confianza, el umbral y el riesgo `alto`.
2. **Given** un ticket cuya solicitud es `reembolso` con una confianza por debajo del umbral de
   «reembolsar», aunque supere el de «mover a cola», **When** lo enruta, **Then** el reembolso no
   se ejecuta, entra en la cola de revisión como «pendiente de confirmación» y la salida lo dice
   con la confianza y el umbral.
3. **Given** cualquier política válida, **When** se comparan los umbrales, **Then** el de
   «reembolsar» (riesgo alto) es mayor o igual que el de «mover a cola» (riesgo bajo).
4. **Given** un ticket cuya solicitud no es `reembolso` (otra opción, `other` o sin respuesta
   válida), **When** lo enruta, **Then** no se propone ningún reembolso, y la salida y la auditoría
   lo registran como abstención explícita, con el valor y la confianza de la solicitud.
5. **Given** un ticket cuya solicitud es `reembolso` con confianza suficiente pero cuya cola no se
   mueve sola a `facturacion`, **When** lo enruta, **Then** el reembolso queda pendiente de
   confirmación y la salida explica que la cola no se automatizó a `facturacion`.

---

### User Story 3 - Atender la cola de revisión (Priority: P3)

Como Operador, quiero listar con `jevlab review` lo que no se automatizó y resolver cada elemento
(asignar una cola o descartarlo, o confirmar o rechazar un reembolso), con el motivo por el que
llegó a la cola, para que nada se pierda cuando el modelo duda o se abstiene.

**Why this priority**: Cierra el ciclo de §II: lo que no se automatiza va a revisión y alguien lo
resuelve. Necesita las US1 y US2 para tener elementos que revisar.

**Independent Test**: Enrutar tickets de ejemplo que terminan en revisión (confianza baja, `other`
y reembolso sin confianza suficiente), listarlos con `jevlab review`, resolver uno y comprobar que
deja de estar pendiente y que la resolución queda en la auditoría.

**Acceptance Scenarios**:

1. **Given** tickets enrutados con alguna acción no automatizada, **When** el Operador ejecuta
   `jevlab review`, **Then** ve qué contiene la cola y quién la resuelve, y un elemento pendiente
   por petición, con su identificador, el inicio del texto del ticket, la versión de la política,
   por cada acción pendiente el motivo, el valor propuesto por el modelo (o «ninguna»), la
   confianza y el umbral, y los comandos exactos que la resuelven.
2. **Given** un elemento pendiente, **When** el Operador lo resuelve asignando una cola válida,
   **Then** el elemento deja de estar pendiente y la resolución queda en la auditoría con el
   identificador de la petición original.
3. **Given** un elemento pendiente, **When** el Operador lo descarta, **Then** deja de estar
   pendiente y la auditoría registra que se descartó.
4. **Given** un elemento con un reembolso pendiente de confirmación y la cola ya en
   `facturacion` (automática o asignada por el Operador), **When** el Operador confirma o rechaza
   el reembolso, **Then** la auditoría registra la resolución; si lo confirma, la salida dice que
   el reembolso se ejecutaría (simulado).
5. **Given** un elemento con la cola y el reembolso pendientes, **When** el Operador intenta
   confirmar el reembolso antes de asignar la cola, **Then** el comando lo rechaza y explica que
   primero hay que asignar `facturacion`; **When** asigna otra cola o descarta el elemento,
   **Then** el reembolso queda rechazado y así consta en la auditoría.
6. **Given** un elemento, **When** el Operador resuelve todas sus acciones pendientes, **Then**
   el elemento deja de estar pendiente.
7. **Given** la cola sin elementos pendientes, **When** el Operador ejecuta `jevlab review`,
   **Then** la salida dice que no hay pendientes.
8. **Given** la cola de revisión con elementos, **When** se cierra la terminal y se vuelve a
   ejecutar `jevlab review`, **Then** los elementos siguen ahí (persistencia local).
9. **Given** un Operador que nunca ha usado la cola, **When** ejecuta `jevlab review guia`,
   **Then** ve qué es la cola, qué significa cada cola (de la definición `cola-destino`), el riesgo
   y el umbral de cada acción (de la política vigente), cómo la cola decide el reembolso y qué
   hace cada comando de resolución, sin que haga falta el archivo de estado.

---

### User Story 4 - Cambiar los umbrales en una política versionada (Priority: P4)

Como Operador, quiero cambiar los umbrales en la política de enrutado
(`src/jevlab/policies/soporte/enrutado.yaml`, el `policy.yaml` de la descripción), un archivo
versionado fuera del código, y ver en cada salida qué versión de la política se aplicó, para ajustar el
comportamiento sin tocar código y saber siempre con qué reglas se decidió.

**Why this priority**: Los umbrales versionados fuera del código son un requisito de §II, pero la
feature puede demostrarse antes con la política inicial. Prepara la spec 004, que propondrá
umbrales con datos.

**Independent Test**: Enrutar el mismo ticket grabado con la política inicial y con una política
de umbral distinto, y comprobar que el resultado cambia, que la salida y la auditoría muestran la
versión de cada política y que una política no válida se rechaza sin automatizar nada.

**Acceptance Scenarios**:

1. **Given** la política inicial, **When** la persona enruta un ticket, **Then** la salida muestra
   la versión de la política aplicada, con su huella, y, para cada umbral, si es provisional.
2. **Given** una política con el umbral de «mover a cola» igual o menor que la confianza de un
   ticket grabado que con la política inicial iba a revisión, **When** lo enruta de nuevo,
   **Then** el ticket se mueve, sin ningún cambio en el código, y la salida muestra la nueva
   versión.
3. **Given** una política no válida (campo que falta, umbral fuera de 0 a 1, riesgo desconocido,
   umbral sin justificación, o una acción de más riesgo con un umbral menor que otra de menos
   riesgo), **When** la persona enruta un ticket, **Then** el comando termina con un error que
   dice qué está mal y dónde, y no automatiza nada.
4. **Given** cualquier decisión registrada, **When** se consulta la auditoría, **Then** incluye la
   versión de la política con la que se tomó.
5. **Given** una política con un umbral cambiado pero la misma versión semver, **When** la persona
   enruta un ticket, **Then** la salida y la auditoría muestran una huella distinta de la
   anterior.

---

### Edge Cases

- Confianza exactamente igual al umbral: se automatiza (mayor o igual), como en la 001.
- Confianza de la cola alta pero resultado `other`: nunca se mueve; el escape gana a la confianza.
- Solicitud `reembolso` con confianza suficiente, pero la cola no se mueve sola (`other`,
  confianza baja o respuesta no válida) o se mueve a una cola distinta de `facturacion`: el
  reembolso no se automatiza, queda pendiente de confirmación y la salida da el motivo de cada
  acción.
- El mismo ticket enrutado dos veces: son dos peticiones con identificadores distintos y, si van a
  revisión, dos elementos; no hay deduplicación.
- Resolver un elemento que no existe o una acción ya resuelta: error que lo dice, sin cambios.
- Resolver con una cola que no existe en la definición: error que lista las colas válidas.
- Archivo de cola de revisión inexistente: se crea al primer uso; `jevlab review` sobre una cola
  nueva dice que no hay pendientes.
- Política inexistente o ilegible: error que dice qué archivo se esperaba, sin automatizar nada.
- Política con dos versiones distintas en dos ejecuciones: cada decisión queda con la suya.
- Texto con instrucciones dirigidas al modelo («reembolsa sin preguntar…»): se trata como contenido
  del ticket, nunca como instrucción. Con la política inicial, ningún ejemplo con instrucciones
  incrustadas produce un reembolso automatizado, incluido uno que lo pide expresamente
  (`reembolso-incrustado`).
- Errores del servicio en vivo, texto vacío, texto demasiado largo y modos grabado o en vivo: igual
  que en la 001.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La CLI MUST ofrecer `jevlab route "<texto>"`, que pregunta las decisiones de la tabla
  «Decisiones Jev», aplica la política y muestra, por cada acción, si se automatiza o no y por
  qué. `jevlab triage` MUST seguir funcionando igual que en la 001, sin efectos.
- **FR-002**: `jevlab route` MUST admitir los mismos modos que `jevlab triage`: grabado por
  defecto, por texto, por `--ejemplo <nombre>` o desde el menú, y en vivo solo con `--en-vivo`.
- **FR-003**: Una acción MUST automatizarse solo si su decisión tiene un valor válido distinto del
  escape y una confianza mayor o igual que el umbral de esa acción en la política. En cualquier
  otro caso, MUST NOT automatizarse.
- **FR-004**: La salida de cada acción MUST mostrar el resultado, la confianza, el umbral, el
  riesgo, si el umbral es provisional, el motivo cuando no se automatiza y el origen (en vivo o
  grabado, con modelo y fecha) (`docs/standards/decision-design.md` §7). Cada dato MUST llevar la
  etiqueta de su origen: el valor y la confianza, del modelo; el umbral y el riesgo, de la
  política; la comparación, el estado y el motivo, del código (`docs/standards/cli-ux.md` §6).
  Cuando el reembolso queda `sin reembolso` no se aplica ningún umbral: la salida muestra el
  valor y la confianza de la solicitud (o «no disponible») y el motivo, sin umbral. Si el modelo
  elige el escape de la cola, la salida muestra ese valor marcado como escape, con su confianza, y
  que no se compara con el umbral.
- **FR-005**: Las acciones automatizadas MUST ser simuladas: se registran y se muestran, sin
  efectos fuera de jev-lab.
- **FR-006**: La acción «reembolsar» MUST tener riesgo `alto` y la acción «mover a cola», riesgo
  `bajo`. El reembolso MUST automatizarse solo si la solicitud es `reembolso` con confianza
  mayor o igual que su umbral **y** la acción «mover a cola» se automatizó a `facturacion` en la
  misma petición; la composición la hace el código. Si la solicitud es `reembolso` y falta
  cualquiera de las dos condiciones, el reembolso MUST quedar en la cola de revisión como
  «pendiente de confirmación».
- **FR-007**: Toda petición con alguna acción no automatizada (cola con confianza baja, `other` o
  respuesta no válida, o reembolso pendiente de confirmación) MUST crear un único elemento en una
  cola de revisión persistente y local, con sus acciones pendientes y el motivo de cada una.
- **FR-008**: `jevlab review` MUST listar los elementos pendientes y permitir resolver sus
  acciones: asignar una cola válida o descartar el elemento, y confirmar o rechazar un reembolso
  pendiente. Un reembolso MUST poder confirmarse solo cuando la cola del elemento es
  `facturacion`; asignar otra cola o descartar el elemento MUST rechazarlo. Un elemento deja de
  estar pendiente cuando no le quedan acciones pendientes. Cada resolución MUST quedar en la
  auditoría. El listado MUST decir qué contiene la cola y quién la resuelve, y cada elemento, los
  comandos exactos que lo resuelven según lo que tenga pendiente, con las colas válidas.
  `jevlab review guia` MUST explicar qué es la cola, qué significa cada cola, el riesgo y el
  umbral de cada acción, cómo la cola decide el reembolso y qué hace cada comando, tomando las
  colas de la definición y los umbrales de la política, sin repetirlos a mano; la cabecera del
  listado MUST señalarla.
- **FR-009**: Los umbrales MUST vivir en un archivo de política versionado en el repositorio
  (`src/jevlab/policies/soporte/enrutado.yaml`; research R3), con una
  versión semver y, por acción, el riesgo, el umbral y su justificación (una evaluación o
  `provisional`) (`docs/standards/decision-design.md` §6).
- **FR-009a**: Al cargar la política, el código MUST calcular una huella corta de su contenido. En
  esta spec, «versión de la política» significa la versión semver más esa huella: la salida, la
  auditoría y la cola de revisión MUST mostrar o guardar las dos, de modo que dos contenidos con
  la misma versión semver se distingan.
- **FR-010**: La política MUST validarse al cargarla. Una política no válida MUST hacer terminar el
  comando con un error que indica el campo y el motivo, sin automatizar nada. Es no válida si una
  acción de más riesgo tiene un umbral menor que una de menos riesgo.
- **FR-011**: Cada ejecución de `jevlab route` MUST generar un identificador de petición único y
  registrar en la auditoría, por acción: identificador, fecha, decisión, valor, confianza, umbral,
  riesgo, versión de la política, resultado (automatizada, a revisión, pendiente de confirmación o
  sin reembolso), origen y modelo. La auditoría MUST NOT contener el texto del ticket ni las
  respuestas completas del servicio.
- **FR-012**: La cola de revisión MAY guardar el texto del ticket, porque el Operador lo necesita
  para resolver; MUST NOT guardar claves ni respuestas completas del servicio.
- **FR-013**: Tests de propiedades MUST comprobar, para cualquier política válida y cualquier
  confianza: que nada por debajo del umbral se automatiza; que el escape de la cola siempre
  termina en revisión y el de la solicitud en abstención explícita (`sin reembolso`); que ningún
  reembolso se automatiza sin que la cola se haya movido sola a
  `facturacion`; y que las bandas son monótonas (si una confianza se automatiza, cualquier confianza
  mayor también, y un umbral de más riesgo nunca es menor que uno de menos riesgo).
- **FR-014**: Una nueva decisión, la solicitud del cliente, MUST describirse en la definición
  versionada con su escape, y el conjunto de ejemplos grabados MUST ampliarse con tickets que
  pidan un reembolso de forma clara y ambigua y con uno que lo pida mediante una instrucción
  incrustada, etiquetados como sintéticos. Los textos de los ejemplos de la 001 se reutilizan sin
  cambios.
- **FR-015**: Los mensajes de error y los logs `info` MUST NOT incluir el texto del ticket, las
  respuestas del servicio ni claves, igual que en la 001.
- **FR-016**: Los archivos de estado local (cola de revisión y auditoría) MUST quedar fuera del
  control de versiones y funcionar igual en Linux y Windows.

### Key Entities

- **Política**: archivo versionado con su versión semver y, por acción, riesgo, umbral y
  justificación; el código le calcula una huella de contenido al cargarla.
- **Acción**: algo que el sistema puede hacer solo (mover a cola, reembolsar), con su riesgo y la
  decisión de la que depende.
- **Petición de enrutado**: una ejecución de `jevlab route`, con su identificador único.
- **Registro de auditoría**: lo que se decidió para cada acción de una petición, o una resolución
  del Operador; solo metadatos, sin *payloads*.
- **Elemento de revisión**: una petición pendiente de una persona (uno por petición), con el
  texto del ticket, la versión de la política, el estado (pendiente o resuelto) y sus acciones
  pendientes; cada acción, con el motivo, el valor propuesto, la confianza, el umbral y su
  resolución.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En el 100 % de los casos de los tests de propiedades, ninguna acción con confianza
  por debajo de su umbral, con escape o sin respuesta válida se automatiza.
- **SC-002**: El 100 % de las salidas de `jevlab route` muestra, por acción, lo que exige FR-004
  (resultado, confianza, umbral, riesgo y motivo si no se automatiza; en `sin reembolso`, valor y
  confianza de la solicitud y motivo), además de la versión de la política y el origen.
- **SC-003**: El 100 % de las peticiones y resoluciones queda en la auditoría con su identificador
  y la versión de la política, y 0 registros de auditoría contienen el texto de un ticket.
- **SC-004**: Un Operador sin experiencia previa resuelve un elemento de la cola de revisión en
  menos de 1 minuto siguiendo solo la lección.
- **SC-005**: Cambiar un umbral en la política cambia el resultado de un ticket grabado sin
  modificar ningún archivo de código, y la salida muestra la nueva versión.
- **SC-006**: La suite por defecto reproduce todos los ejemplos de enrutado con 0 conexiones y 0
  coste; con la política inicial, los ejemplos cubren al menos: cola automatizada, cola a revisión
  por confianza baja, `other` a revisión, reembolso automático, reembolso que pide confirmación y
  solicitud sin reembolso; y ningún ejemplo con instrucciones incrustadas automatiza un reembolso.
  Cada ejemplo declara lo que cubre y un test lo comprueba sobre su grabación.

## Assumptions

- Acciones de la feature: «mover a cola» (riesgo bajo) y «reembolsar» (riesgo alto). Ambas son
  simuladas; no hay sistemas externos de colas ni de pagos.
- Umbrales iniciales: «mover a cola» 0,90 y «reembolsar» 0,97, provisionales hasta la evaluación
  de la spec 004. Las confianzas del enrutado solo se conocen al grabar: ningún test ni demo fija
  una cifra a mano, y los ejemplos de cada caso se eligen por lo que cubre su grabación.
- El reembolso depende de una decisión nueva, la solicitud del cliente (Choice con escape), y no de
  un Noul: el servicio no devuelve confianza para Noul (research R3 de la 001) y §II exige
  condicionar la acción a la confianza.
- Ni la urgencia ni la prioridad de la 001 intervienen en el enrutado; siguen visibles en
  `jevlab triage`.
- La cola de revisión y la auditoría se guardan en una base SQLite local, fuera del repositorio; la
  ruta se fija en el plan.
- Un único Operador local, sin autenticación ni registro de quién resuelve: la autoría de la
  resolución queda fuera de alcance.
- La política inicial vive en el repositorio; una opción permite apuntar a otro archivo de
  política para experimentar, sin editar la del repositorio.
- Las nuevas grabaciones se hacen con `uv run poe record-route`, sin regrabar las del triaje y con
  el mismo tope de coste que en la 001.

## Decisiones Jev (jev-lab) *(mandatory si la feature pregunta al modelo)*

> Deriva de: Constitución §I, §II y §IV · Estándar: `docs/standards/decision-design.md`

| Decisión | Pregunta (una idea, literal) | Primitiva | Opciones + escape | Acción automatizable y riesgo | Destino del escape |
| --- | --- | --- | --- | --- | --- |
| cola-destino | «¿A qué cola de soporte pertenece este ticket?» (la de la 001) | Choice | `facturacion`, `tecnico`, `cuenta`, `other` | Mover a cola; riesgo bajo | Cola de revisión |
| solicitud | «¿Qué pide el cliente en este ticket?» | Choice | `reembolso`, `consulta`, `incidencia`, `other` | Reembolsar (solo si `reembolso` y la cola se movió sola a `facturacion`); riesgo alto | Sin reembolso, como abstención explícita en la salida y en la auditoría; la cola sigue su propia regla |

- **Lo que decide el código**: la comparación de la confianza con el umbral de cada acción, el
  escape y la respuesta no válida, el riesgo de cada acción, la validación de la política (incluida
  la monotonía por riesgo), el identificador de petición, la fecha y el estado de cada elemento de
  revisión.
- **Qué ve cada persona**: el usuario inicial de Jev ve, por acción, el resultado, la confianza, el
  umbral, el riesgo, «provisional» junto a cada umbral, el motivo de no automatizar, la versión de
  la política, el identificador de petición y el origen, con cada dato etiquetado según venga del
  modelo, de la política o del código. El Operador ve en `jevlab review` qué es la cola y los
  pendientes con su motivo, confianza, umbral, versión de la política, inicio del texto y los
  comandos que los resuelven; en `jevlab review guia`, qué significa cada cola, cada acción y cada
  comando.

## Corte vertical y lección (jev-lab) *(mandatory)*

> Deriva de: Constitución §VII · Perfiles de usuario: `docs/personas.md`

- **Persona principal**: Operador (US3 y US4); las US1 y US2 sirven al Usuario inicial de Jev.
- **Capacidad de extremo a extremo**: enrutar tickets desde la CLI automatizando solo lo que
  alcanza el umbral de su riesgo, atender el resto en una cola de revisión y ajustar los umbrales
  en una política versionada, con todo auditado.

| Historia | Persona | Cómo se demuestra (comando o petición) |
| --- | --- | --- |
| US1 | Usuario inicial de Jev | `uv run jevlab route --ejemplo cambio-de-correo` y `--ejemplo instruccion-incrustada` (cola a revisión) |
| US2 | Usuario inicial de Jev | `uv run jevlab route --ejemplo cobro-duplicado` (reembolso automático) y `--ejemplo reembolso-ambiguo` |
| US3 | Operador | `uv run jevlab review`, y resolver un pendiente |
| US4 | Operador | `uv run jevlab route --ejemplo instruccion-incrustada --politica <copia>`, con un umbral igual a su confianza grabada |

Ejemplos confirmados con las grabaciones de T023. Si una regrabación deja de cubrir un caso, el
test de las grabaciones lo detecta y la tabla se actualiza con el ejemplo que lo cubra.

- **Número de historias**: 4 (P1-P4).
- **Fuera de alcance (YAGNI)**: acciones reales sobre sistemas externos, importes de reembolso,
  varios operadores con autenticación, deduplicación de tickets, API (003), evaluación y umbrales
  con datos (004), modo *shadow* y métricas (007), y edición de la política desde la CLI.
- **Lección**: `docs/lessons/002-la-confianza-como-segundo-eje-y-umbrales-por-riesgo.md`.
  - Qué se aprende: por qué el valor de una respuesta no basta para actuar, cómo se fija un umbral
    por riesgo, qué es una banda monótona, cómo el escape y la duda acaban en revisión, y cómo una
    política versionada y una auditoría permiten saber con qué reglas se decidió.
  - Qué puede fallar y su mitigación: automatizar con confianza baja (umbral obligatorio); un
    umbral de riesgo alto más laxo que uno bajo (validación de monotonía); umbrales escondidos en
    el código (política versionada); `other` con confianza alta tratado como una cola (el escape
    gana); instrucciones incrustadas que piden un reembolso (dato no confiable y umbral alto);
    filtrar el ticket en la auditoría (solo metadatos); decisiones sin trazabilidad
    (identificador y versión de política).

## Enmiendas

Ajustes de nivel 2 (`docs/governance.md` §7) hechos después del cierre. Los documentos de
comportamiento ya describen el vigente; aquí queda qué cambió y por qué.

| Fecha | Cambio | Motivo | Documentos actualizados | Commit |
| --- | --- | --- | --- | --- |
| 2026-10-17 | Salida de `route` y `review` con cada dato etiquetado según su origen (`Acción`/`estado`, `IA`, `política`, `regla`), `qué hacer:` con los comandos exactos y, en `review`, una explicación de qué es la cola | Prueba de SC-004: una persona sin experiencia no distinguió la propuesta del modelo de la decisión del código, no entendió la cola ni supo cómo resolver un elemento, y no terminó en más de 10 minutos | FR-004, FR-008, US1 escenario 2, US3 escenario 1, «Qué ve cada persona», `contracts/cli-route.md`, `contracts/cli-review.md`, lección §4 | `0e9eb05` |
| 2026-10-17 | Subcomando `jevlab review guia`: qué es la cola, qué significa cada cola (de `cola-destino`), riesgo y umbral de cada acción (de la política) y qué hace cada comando; la cabecera del listado la señala. Es nivel 2 y no 3: no añade historia de usuario, explica lo que el Operador ya hace en US3 sin permitirle nada nuevo | Tras la primera prueba de SC-004, entender la cola fue el primer bloqueo; el listado explica cada elemento, pero no el conjunto, y meterlo en el listado sería ruido para quien ya la conoce | FR-008, US3 escenario 9, «Qué ve cada persona», `contracts/cli-review.md`, lección §4 (paso 0) | `b140395` |
| 2026-10-17 | Con el escape de la cola, «mover a cola» guarda y muestra lo que respondió el modelo (`IA propone la cola: other (escape)`) en lugar de `ninguna`, y la regla dice `escape, no se compara con el umbral`. La auditoría guarda `other` como valor; el escape sigue sin asignarse nunca | Al repasar la lección, `ninguna · confianza 1,00` parecía contradictorio y no decía lo que respondió el modelo (`cli-ux.md` §6); la solicitud ya mostraba `other (escape)` | FR-004, `data-model.md` (`ActionOutcome.value`), `contracts/cli-route.md`, lección §3 y §4 | `e391381` |
| 2026-10-17 | La guía añade «La cola decide el reembolso»: con `facturacion` se puede confirmar o rechazar (en `route`, se automatiza desde el umbral de la política); con cualquier otra cola no se puede confirmar y asignarla lo rechaza; descartar lo rechaza; cuándo sale un elemento de la lista y que toda resolución se audita. La descripción de cada comando se acorta para no repetirlo | Lo menos evidente del sistema es que la cola condiciona el reembolso, y la guía solo lo decía en el comentario de `asignar`. Se generan con las colas válidas y el umbral de la política, sin una fila por cola | FR-008, US3 escenario 9, `contracts/cli-review.md`, lección §4 | `2e8ba83` |
