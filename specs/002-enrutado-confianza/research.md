# Investigación: Enrutado con confianza según riesgo

Fase 0 de `/speckit-plan`. Cada apartado resuelve una incógnita del contexto técnico con la forma
decisión, motivo y alternativas. Parte del código de la 001 en `main` (`10109a6`) y del SDK
instalado (`typesafe-sdk` 0.7.4).

## R1. Una petición genérica en lugar de una atada al triaje

- **Decisión:** el dominio gana una petición resuelta genérica, `ResolvedRequest`: la
  `RequestSpec` y sus decisiones validadas por nombre de pregunta, con un único modelo. Las
  respuestas pasan a `Answers`: el modelo y, por pregunta, `ChoiceAnswer`, `NoulAnswer`,
  `ScoreAnswer` o `None`.
  - `JudgePort.ask(request: ResolvedRequest, ticket) -> Answers`.
  - `SpecLoader.load_request(name) -> ResolvedRequest`.
  - `TriageSpec` y la nueva `RouteSpec` se construyen a partir de una `ResolvedRequest`; cada
    una comprueba sus preguntas y primitivas, igual que hoy `TriageSpec.resolve`.
  - `TypeSafeJudge` traduce cada respuesta del SDK según su tipo, sin conocer los nombres de las
    preguntas.
- **Motivo:** el enrutado necesita otra petición con dos preguntas (`cola` y `solicitud`). Hoy el
  puerto, el adaptador y el cargador solo admiten la de triaje, con sus tres nombres fijos
  (`typesafe_judge.py`, `decision_spec.py`). Generalizar el transporte de la petición y dejar la
  forma concreta en `TriageSpec` y `RouteSpec` mantiene una sola definición por decisión
  (Constitución §III).
- **Alternativas:**
  - Añadir `solicitud` a la petición de triaje y compartir las grabaciones. Se descarta: cambia
    la petición de `jevlab triage`, obliga a regrabar sus ejemplos y contradice FR-001 («sigue
    igual que en la 001»).
  - Un segundo método `ask_route` en el puerto. Se descarta: duplica el adaptador y el fake.

## R2. Decisión nueva `solicitud` y petición `enrutado`

- **Decisión:**
  - `src/jevlab/specs/soporte/solicitud.yaml`, `0.1.0`: Choice «¿Qué pide el cliente en este
    ticket?», con `reembolso`, `consulta`, `incidencia` y `other` (escape).
  - `src/jevlab/specs/soporte/enrutado.yaml`, `0.1.0`: petición con `cola: cola-destino` y
    `solicitud: solicitud`, `max_chars: 4000`.
  - Las dos con `jev-1.13.0`, el modelo de la 001 (research R4 de la 001).
- **Motivo:** el reembolso necesita una confianza, y Noul no la tiene (research R3 de la 001;
  aclaración de la spec). `cola-destino` se reutiliza sin cambios: la misma definición sirve al
  triaje y al enrutado (§III).
- **Alternativas:** Noul «¿pide un reembolso?» con un umbral sobre la probabilidad. Lo descartó la
  persona en la aclaración.

## R3. Política: archivo, forma y huella

- **Decisión:**
  - Archivo `src/jevlab/policies/soporte/enrutado.yaml`, dentro del paquete para que la CLI
    funcione desde cualquier directorio (mismo motivo que research R10 de la 001). En la spec y
    la lección se le llama `policy.yaml`.
  - Forma, según `docs/standards/decision-design.md` §6: `version` semver y `acciones`, con
    `mover-a-cola` y `reembolsar`; cada una con `riesgo` (`bajo`, `medio` o `alto`), `umbral`
    (0 a 1) y `justificacion`.
  - Valores iniciales: `mover-a-cola` riesgo bajo, umbral 0,90; `reembolsar` riesgo alto, umbral
    0,97; los dos `provisional`.
  - Validación con Pydantic en el dominio (`Policy`), con `extra="forbid"`. Es no válida si:
    falta una de las dos acciones o sobra una desconocida, el umbral está fuera de 0 a 1, el
    riesgo es desconocido, la justificación está vacía o, ordenadas por riesgo, una acción de más
    riesgo tiene un umbral menor que una de menos riesgo.
  - Qué decisión usa cada acción y cómo se componen no está en la política: es código (§I).
  - `--politica <ruta>` carga otro archivo para experimentar.
  - Huella: los 8 primeros caracteres hexadecimales del SHA-256 del JSON canónico de la política
    validada (claves ordenadas, sin espacios). La calcula el dominio, que no hace entrada/salida:
    `hashlib` es puro.
- **Motivo:** FR-009, FR-009a y FR-010. Una huella del contenido validado, y no de los bytes del
  archivo, no cambia por los comentarios ni por los finales de línea de Windows, y sí por
  cualquier umbral, riesgo o justificación.
- **Alternativas:**
  - Archivo en la raíz del repositorio (`policy.yaml`). Se descarta: la CLI instalada no lo
    encontraría desde otro directorio.
  - Huella de los bytes del archivo. Se descarta: un CRLF o un comentario cambiarían la huella sin
    cambiar las reglas.

## R4. Regla de decisión y composición

- **Decisión:** una función pura del dominio, `decide_routing(policy, queue, request_kind)`, a
  partir de los resultados ya interpretados de las dos Choice:
  - `mover-a-cola` se automatiza si la cola tiene una opción válida distinta del escape y su
    confianza es mayor o igual que el umbral. Si no, queda pendiente de revisión con su motivo:
    escape, respuesta fuera de la definición, sin respuesta o confianza por debajo del umbral.
  - `reembolsar` solo se considera si la solicitud es `reembolso`. Se automatiza si su confianza
    es mayor o igual que el umbral y `mover-a-cola` se automatizó a `facturacion`. Si no, queda
    pendiente de confirmación con su motivo. Si la solicitud no es `reembolso` (otra opción,
    escape o sin respuesta), no se propone reembolso.
  - Se compara la confianza que devuelve el servicio, la misma que muestra la salida. La
    recalculada solo comprueba la fórmula (FR-006 de la 001).
- **Motivo:** FR-003, FR-006 y las aclaraciones 4 y 5. Con una función pura, los tests de
  propiedades de FR-013 (hypothesis) recorren cualquier política válida y cualquier confianza sin
  modelo.
- **Alternativas:** comparar la confianza recalculada. Se descarta: la salida mostraría un número
  y decidiría con otro.

## R5. Almacenamiento local: SQLite de la biblioteca estándar

- **Decisión:**
  - `sqlite3` de la biblioteca estándar; sin dependencias nuevas.
  - Un archivo, `estado.sqlite3`, con la auditoría y la cola de revisión. Una ejecución de
    `jevlab route` escribe sus registros de auditoría y, si lo hay, su elemento de revisión en una
    sola transacción.
  - Ubicación: la variable `JEVLAB_STATE_DIR` si existe; si no, el directorio de estado del
    usuario (`%LOCALAPPDATA%\jevlab` en Windows, `$XDG_STATE_HOME/jevlab` o
    `~/.local/state/jevlab` en Linux). Queda fuera del repositorio (FR-016) y es el mismo
    desde cualquier directorio. Los tests usan `JEVLAB_STATE_DIR` con una carpeta temporal.
  - Esquema creado al abrir si no existe, con `PRAGMA user_version = 1` para detectar un archivo
    de otra versión.
  - Los modos grabado y en vivo escriben en el mismo archivo; cada registro guarda su origen.
- **Motivo:** la descripción de la feature fija SQLite; la biblioteca estándar basta para un
  único Operador local. Un único archivo y una transacción evitan peticiones auditadas sin su
  elemento de revisión, o al revés.
- **Alternativas:**
  - `.jevlab/` en el directorio actual. Se descarta: cada directorio tendría su propia cola.
  - `platformdirs`. Se descarta: una dependencia para tres líneas de código.
  - SQLAlchemy. Se descarta por YAGNI.

## R6. Identificadores y hora

- **Decisión:**
  - Puerto nuevo `IdGenerator.new_request_id() -> str`; adaptador `UuidIdGenerator` (`uuid4`) y
    fake `SequentialIds` en los tests.
  - El puerto `Clock` gana `now() -> datetime` (UTC, con zona); `SystemClock` lo implementa y
    `FrozenClock` lo fija.
  - Los elementos de revisión se identifican con un entero corto, que asigna SQLite, para que el
    Operador lo escriba con comodidad; cada elemento guarda también el identificador de la
    petición.
- **Motivo:** `docs/standards/architecture.md` §5: hora e identificadores solo por puertos. La
  regla `TID251` ya prohíbe `uuid4` y `datetime.now` fuera de `adapters/`.

## R7. Comandos `route` y `review`

- **Decisión:**
  - `jevlab route [TEXTO] [--ejemplo NOMBRE] [--en-vivo] [--politica RUTA]`: los mismos modos que
    `triage` (selección por texto, nombre o menú; sin terminal, lista y código 2), sobre las
    grabaciones de `src/jevlab/recordings/soporte/enrutado/`.
  - `jevlab review` lista los pendientes. Subcomandos: `asignar ID COLA`, `descartar ID`,
    `confirmar ID` y `rechazar ID`.
  - Códigos de salida de `docs/standards/cli-ux.md` §4: 0 aunque algo vaya a revisión; 2 para un
    elemento inexistente, una acción ya resuelta, una cola que no existe o una confirmación sin
    `facturacion`; 1 para una política no válida o un archivo de estado ilegible.
  - Contratos en `contracts/cli-route.md` y `contracts/cli-review.md`.
- **Motivo:** FR-001, FR-002 y FR-008. Reutilizar la selección de ejemplos y el menú de la 001
  mantiene una sola forma de elegir un ejemplo.
- **Alternativas:** añadir el enrutado a `triage` con `--enrutar`. Se descarta: `triage` debe
  seguir sin efectos (FR-001).

## R8. Grabaciones del enrutado

- **Decisión:**
  - Las grabaciones viven en `src/jevlab/recordings/soporte/enrutado/`, con el mismo formato que
    las de la 001 (`contracts/recording.md` de la 001) y la petición `enrutado`.
  - Ejemplos: los seis textos de la 001 y uno nuevo, `reembolso-ambiguo`, que insinúa una
    devolución sin pedirla claramente. `cobro-duplicado` ya pide la devolución de un cargo y sirve
    como reembolso claro.
  - El caso «reembolso con confianza suficiente y cola distinta de `facturacion`» no tiene
    ejemplo grabado: la descripción de `facturacion` incluye los reembolsos, así que un texto real
    difícilmente lo produce. Lo cubren los tests unitarios y de propiedades con respuestas
    construidas en el test.
  - `tests/live/test_record_route.py`, con `@pytest.mark.live(max_usd=0.01)`; `poe record`
    ejecuta los dos archivos de grabación.
  - Si la respuesta real de un ejemplo no cae en el lado que pretende cubrir, se reescribe el
    texto, como se hizo con `urgencia-ambigua` en la 001. Un test comprueba que, con la política
    inicial, los ejemplos cubren los cinco casos de SC-006.
- **Motivo:** FR-014 y SC-006, sin tocar las grabaciones de `jevlab triage`.
- **Alternativas:** grabaciones sintéticas para los casos que la respuesta real no cubra. Se
  descarta para la CLI: los ejemplos de la CLI son respuestas reales. Las sintéticas siguen
  limitadas a `tests/contract/fixtures/` (research R10 de la 001).

## R9. Auditoría sin *payloads*

- **Decisión:** cada registro de auditoría guarda solo metadatos: identificador de petición,
  fecha y hora UTC, tipo (`decision` o `resolucion`), acción, valor elegido, confianza, umbral,
  riesgo, versión y huella de la política, resultado, motivo, origen, modelo, versiones de las
  definiciones y, en las resoluciones, el elemento resuelto. Nunca el texto del ticket ni la
  respuesta del servicio. La cola de revisión sí guarda el texto (FR-012).
- **Motivo:** FR-011, SC-003 y `docs/standards/security.md`. El texto queda en el archivo de
  estado local, fuera del repositorio y de los logs, solo para que el Operador pueda resolver.
- **Alternativas:** guardar un resumen del texto en la auditoría. Se descarta: sigue siendo
  *payload*.

## R10. Dependencias

- **Decisión:** ninguna nueva. `sqlite3`, `hashlib` y `uuid` son de la biblioteca estándar;
  `pydantic`, `pyyaml`, `typer` y `hypothesis` ya están.
