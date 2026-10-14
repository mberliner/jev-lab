# Investigación: Triaje de un ticket de soporte

Fase 0 de `/speckit-plan`. Cada apartado resuelve una incógnita del contexto técnico con la forma
decisión, motivo y alternativas. SDK consultado en el código instalado (`typesafe-sdk` 0.7.4) y
documentación oficial de TypeSafe consultada el 2026-10-13.

## R1. Llamada a Jev: una petición con tres preguntas

- **Decisión:** `TypeSafeClient.system_one(state=<texto>, questions={...}, model=...)` con tres
  preguntas con nombre: `cola` (`Choice`), `urgencia` (`Noul`) y `prioridad` (`Score`). La
  respuesta (`SystemOneResponse`) trae `model`, `usage` y `answers` por nombre.
- **Motivo:** es la forma documentada de preguntar varias cosas sobre el mismo estado (ejemplo del
  propio constructor del cliente y [*System One*](https://docs.typesafe.ai/concepts/system-one)).
  El estado es solo el texto del ticket (FR-016, estado mínimo). Comparar una llamada frente a N es
  la spec 003.
- **Alternativas:** tres llamadas, una por pregunta (triplica el coste de entrada y adelanta la 003).

## R2. Forma de las respuestas del SDK

- **Hallazgo:** en el SDK instalado (`_schemas/models.py` y `_core/response_types.py`):
  - `ChoiceAnswer`: `choice`, `confidence` y `probabilities` por opción. El SDK no comprueba que
    `choice` sea una de las opciones enviadas.
  - `NoulAnswer`: solo `noul`, la probabilidad de «sí». No hay `confidence`.
  - `ScoreAnswer`: `score` (valor esperado, puede caer entre niveles), `confidence`, `legend` y
    `probabilities`, con claves enteras (posición del nivel desde 0).
- **Decisión:** el adaptador traduce estas respuestas a tipos propios del dominio. El dominio
  comprueba que la opción elegida pertenece a la definición; si no, o si falta la respuesta de una
  pregunta, esa decisión termina en abstención (FR-005). Una respuesta que el SDK no puede
  decodificar es un error del servicio (código 1, sin *payload*).

## R3. Fórmula oficial de la confianza

- **Decisión:** `domain/confidence.py` implementa las fórmulas de
  [*Confidence*](https://docs.typesafe.ai/confidence.md):
  - Choice, con `n` opciones (escape incluido) y `p_max` la mayor probabilidad:
    `(p_max - 1/n) / (1 - 1/n)`, sin recortar.
  - Score, con `m` el nivel más probable y `MAD_unif = (1/n) · Σ |i - (n-1)/2|`:
    `max(0, 1 - Σ p_i · |i - m| / MAD_unif)`.
  - Noul: la documentación dice que no hay confianza; la salida muestra la probabilidad y la banda,
    sin inventar una confianza (Constitución §IV).
- **Motivo:** FR-006 y SC-003; la lección explica la fórmula con las mismas cifras de la salida.
- **Hallazgo al grabar (2026-10-13):** la API devuelve probabilidades y confianzas con 2 decimales.
  En `instruccion-incrustada`, `p_max = 0,93` da 0,9067 y el servicio devuelve 0,91, calculado con
  la probabilidad sin redondear. La tolerancia de SC-003 pasa de 0,001 a 0,01: un error de fórmula
  da diferencias de décimas, no de milésimas. La cota teórica del redondeo en una Choice de 4
  opciones es 0,005 / 0,75 + 0,005 ≈ 0,012; si algún día se supera, se revisa la tolerancia.
- **Riesgos:** con `n = 1` las dos fórmulas dividen por cero; la validación de la definición exige
  al menos dos opciones (Choice, contando el escape) y dos niveles (Score). Si las probabilidades
  no suman 1, se usan tal como llegan (spec, «Edge Cases»). Los empates en `p_max` o en `m` se
  resuelven con la primera opción o el primer nivel en el orden de la definición. Es una decisión
  propia, porque la documentación no trata los empates; no cambia la confianza, que solo usa el
  valor máximo y no cuál lo alcanza en Choice.

## R4. Modelo fijado

- **Decisión:** `jev-1.13.0` en la definición versionada.
- **Motivo:** según [*Models*](https://docs.typesafe.ai/models.md), `jev-1.13.0` es el identificador
  fijado; `jev-latest` y `jev-preview` son alias móviles. El roadmap y los estándares escriben
  `jev-1.13` (nombre comercial), que no es un identificador válido para la API.
- **Alternativas:** `jev-latest` (las respuestas pueden cambiar sin cambiar el repo; rompe la
  reproducibilidad de las grabaciones).

## R5. Grabaciones: formato propio sobre el transporte de `httpx2` (idea de la retro 000)

- **Hallazgo:** `vcrpy` 8.3.0 sí parchea `httpx2` (`vcr/patch.py` sustituye `handle_request` de
  `httpx2.HTTPTransport` y de `MockTransport`). Comprobado en local: una llamada
  `system_one` del SDK se graba y se reproduce sin red, y la cabecera de autorización no llega a
  la *cassette* con `filter_headers`.
- **Decisión:** aun así, grabaciones con un formato propio y dos transportes de `httpx2` en
  `adapters/`:
  - `RecordingTransport`: envuelve el transporte real, deja pasar la petición y guarda el cuerpo de
    la petición y el estado y cuerpo de la respuesta, sin cabeceras.
  - `ReplayTransport`: devuelve la respuesta guardada si el cuerpo de la petición coincide con el
    grabado; si no, lanza `RecordingOutdated` (la definición cambió y hay que regrabar).
  - Cada grabación es un YAML con el ejemplo (nombre, texto, `origen: sintetico`), el modelo, la
    fecha, la versión de la definición, la petición y la respuesta (`contracts/recording.md`).
- **Motivo:**
  - La reproducción es una función del producto (`jevlab triage` graba por defecto, aclaración de
    la spec), no solo de los tests: `vcrpy` pasaría a dependencia de ejecución y parchea el
    transporte de forma global.
  - El formato propio lleva el modelo, la fecha y la procedencia que exige
    `docs/standards/testing.md` §7, y permite elegir por nombre o por texto (FR-010a).
  - La comparación del cuerpo detecta que la definición cambió (Constitución §III): una grabación
    hecha con otras preguntas no se reproduce en silencio.
  - La respuesta reproducida pasa por el mismo cliente y el mismo decodificador del SDK que en
    vivo, así que el test de contrato prueba el adaptador real.
- **Alternativas:** `vcrpy` con `pytest-recording` (válido para los tests, pero no para la CLI y
  sin metadatos propios); guardar solo el resultado interpretado (no ejercita el SDK ni sirve de
  contrato).
- **Consecuencia:** `docs/standards/testing.md` §0 y §1 cambian para describir este formato y
  `httpx2.MockTransport` en lugar de `pytest-recording` y `respx`. `vcrpy` y `pytest-recording` no
  se añaden (actualiza la nota de la 000, R14).

## R6. Cliente, reintentos y tiempo de espera

- **Decisión:** un solo `TypeSafeClient` por ejecución, creado en el *entrypoint* con
  `RetryPolicy()` por defecto del SDK (2 reintentos, *backoff* exponencial, estados 408, 429 y
  5xx, presupuesto total de 30 s) y `timeout=10.0` (el valor por defecto del SDK, explícito). El
  adaptador recibe el cliente ya creado y se cierra al terminar (`with`).
- **En modo grabado:** el mismo cliente con `ReplayTransport` y `RetryPolicy(max_retries=0)`. El
  SDK exige una clave no vacía para construirse; se pasa un valor fijo que indica que es una
  reproducción y nunca sale de la máquina.
- **Errores:** `TypeSafeAPIConnectionError` y `TypeSafeAPITimeoutError` -> `ProviderUnavailable`;
  `TypeSafeAPIError` 5xx -> `ProviderUnavailable`, 4xx -> `ProviderRejected`; error de validación
  de la respuesta -> `InvalidProviderResponse`. Los mensajes llevan el tipo y el estado HTTP, nunca
  el cuerpo (FR-014). Se reutilizan las excepciones de `domain/diagnostics.py` de la 000.

## R7. Codificación de la salida en Windows (idea de la retro 000)

- **Hallazgo:** en Windows, `sys.stdout.encoding` es `cp1252` cuando la salida va a una tubería, y
  Git Bash, que espera UTF-8, muestra mal las tildes. Con `sys.stdout.reconfigure(encoding="utf-8")`
  la salida es correcta en Git Bash y en PowerShell 7 (`[Console]::OutputEncoding` UTF-8). En la
  consola, Python escribe en Unicode con independencia de esa codificación.
- **Decisión:** la CLI reconfigura `stdout` y `stderr` a UTF-8 al arrancar, en todos los
  comandos, incluido `doctor`. `docs/standards/cli-ux.md` lo fija y documenta el caso de una
  PowerShell con `[Console]::OutputEncoding` antiguo al capturar la salida en una variable.
- **Alternativas:** `PYTHONUTF8=1` en la documentación (depende de que cada persona lo configure);
  salida solo ASCII (contradice la regla de redacción con tildes).

## R8. Prohibición de reloj, azar e identificadores (idea de la retro 000)

- **Decisión:** regla `TID251` de ruff (`flake8-tidy-imports.banned-api`) con
  `datetime.datetime.now`, `datetime.datetime.today`, `datetime.date.today`, `time.time`,
  `random` y `uuid.uuid4`, ignorada por ruta (`per-file-ignores`) en `src/jevlab/adapters/` y
  `tests/`. Primer puerto: `Clock.today()` con `SystemClock` (adaptador) y `FrozenClock` (fake),
  usado al grabar.
- **Verificación:** un test unitario pasa a `ruff check --stdin-filename src/jevlab/domain/x.py`
  un fragmento con `datetime.now()` y espera `TID251`, y otro con la misma ruta en `adapters/` y
  espera que pase. `docs/standards/architecture.md` §5 sustituye «se decide al configurar el lint
  en la spec de cimientos» por la regla.
- **Alternativas:** script propio en `scripts/checks/` (duplica lo que ruff ya hace).

## R9. Selección del ejemplo y menú

- **Decisión:**
  - Por texto: se normaliza (Unicode NFC, espacios al principio y al final eliminados, espacios
    repetidos reducidos a uno) y se compara con el texto normalizado de cada ejemplo.
  - Por nombre: `--ejemplo <nombre>`.
  - Sin texto ni nombre: menú numerado con `typer.prompt` si `stdin` es una terminal; si no, lista
    y código 2. La comprobación de terminal es una función del *entrypoint* que los tests
    sustituyen.
- **Motivo:** aclaraciones de la spec; la normalización NFC evita que una tilde compuesta o
  descompuesta impida encontrar el ejemplo.

## R10. Dónde viven la definición y las grabaciones

- **Decisión:**
  - Definiciones: un archivo por decisión, como exige `docs/standards/architecture.md` §6
    (`soporte/cola-destino.yaml`, `soporte/urgencia-explicita.yaml`, `soporte/prioridad.yaml`),
    cada uno con su versión, su modelo y la justificación de su umbral. Un archivo de petición,
    `soporte/triaje.yaml`, agrupa las que viajan juntas y declara la longitud máxima; su validación
    exige que las decisiones existan, no se repitan y compartan modelo.
  - La 002 y la 004 trabajan con la cola sola, y la 003 y la 005 recombinan decisiones: con un
    archivo por decisión las reutilizan sin copiar preguntas, y cada umbral se versiona y se
    justifica por separado.
  - Respuestas grabadas, un sitio por uso (acordado con la persona el 2026-10-13):
    - Ejemplos reales que reproduce la CLI: `src/jevlab/recordings/soporte/triaje/<nombre>.yaml`,
      dentro del paquete, para que la CLI las encuentre desde cualquier directorio de trabajo
      (`importlib.resources`). Los tests los leen con el mismo adaptador y prueban lo que ve la
      persona.
    - Respuestas sintéticas solo para tests (503, respuesta mal formada, opción fuera de la
      definición): `tests/contract/fixtures/`, con `origen: sintetico`.
    - Datasets de evaluación (spec 004): `data/<dominio>/`, cuando lleguen.
    - La regla se fija en `docs/standards/testing.md` §7.
- **Alternativas:**
  - Un solo `triaje.yaml` con las tres decisiones: más simple, pero contradice §6 y ata la versión
    de las tres; descartado por la persona el 2026-10-13.
  - Agrupar en el código del caso de uso, sin archivo de petición: dejaría la longitud máxima fuera
    de la definición versionada (aclaración de la spec).
  - Ejemplos reales en `data/soporte/` o en `tests/`: la CLI tendría que localizar la raíz del
    repo y su modo por defecto dependería de archivos ajenos al paquete; en `tests/`, además, el
    código de producción leería archivos de los tests.
- **Consecuencia:** `pyyaml` pasa de dependencia de desarrollo a dependencia del proyecto.

## R11. Recogida de ejemplos y grabación

- **Decisión:** la grabación es un test `live` (`tests/live/test_record_triage.py`, `max_usd=0.01`)
  que solo escribe archivos con `JEVLAB_RECORD=1`; la tarea `uv run poe record` lo lanza con esa
  variable. El humo `live` de la CLI (`tests/live/test_triage_live.py`, `max_usd=0.01`) ejecuta
  `jevlab triage --en-vivo` sobre un ejemplo. Los dos usan el tope de `tests/live/conftest.py`.
- **Coste estimado:** 7 ejemplos de unos 300 tokens de entrada son unos 2.100 tokens; a 0,042 USD
  por millón (*Models*, 2026-10-13) son unos 0,0001 USD. El tope de 0,01 USD deja margen.
- **Riesgo:** el resultado real puede no cubrir algún caso de SC-006 (por ejemplo, ningún
  «incierto»). Un test unitario recorre las grabaciones y falla si falta un caso; el remedio es
  reescribir el texto del ejemplo y regrabar.
- **Dependencia:** grabar necesita la clave real (T037 de la spec 000). Hasta entonces, los tests
  unitarios y de contrato usan respuestas sintéticas etiquetadas; los de integración necesitan las
  grabaciones reales.

## R12. Dependencias

| Paquete | Versión | Cambio |
| --- | --- | --- |
| `pyyaml` | 6.0.3 | Pasa a dependencia del proyecto (R10) |
| `types-pyyaml` | 6.0.12.20260906 | Sigue en desarrollo |

No se añade ninguna otra dependencia: Typer ya trae Rich, pero la salida usa texto plano
(`docs/standards/cli-ux.md`).
