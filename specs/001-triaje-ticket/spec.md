# Feature Specification: Triaje de un ticket de soporte

**Feature Branch**: `001-triaje-ticket`

**Created**: 2026-10-13

**Status**: Draft

**Input**: User description: "001: Triaje de un ticket de soporte (perfil: Usuario inicial de Jev).
Aprende: las tres primitivas de Jev (Choice, Noul, Score) y cómo leer la salida nativa. Nace la CLI
`jevlab triage`. US1 cola elegida con distribución y confianza (Choice con `other`); US2 mención
explícita de un problema urgente (Noul, banda incierta); US3 prioridad en escala ordenada (Score con
`legend`, solo comparada con un umbral); US4 repetición sin red ni coste con respuestas reales
grabadas. Producción: cliente reutilizado, reintentos por defecto, timeout, errores sin filtrar
datos y logs sin *payloads*. Recoge tres ideas de `docs/ideas.md`: grabación del transporte HTTP
del SDK, prohibición de reloj, azar e identificadores fuera de los adaptadores, y codificación de
la salida de la CLI en Windows. Fuente: sección «001» de `docs/roadmap.md`."

## Clarifications

### Session 2026-10-13

- Q: ¿El modo por defecto de `jevlab triage` es en vivo o grabado? -> A: grabado; la llamada al
  servicio, con claves y coste, solo se hace con la opción explícita `--en-vivo`.
- Q: En modo grabado, ¿cómo indica la persona qué ticket de ejemplo reproducir? -> A: por texto
  (ignorando espacios sobrantes) o por nombre con `--ejemplo <nombre>`; sin texto ni nombre, un menú
  numerado permite elegir el ejemplo.
- Q: ¿Con qué regla decide el código si la prioridad alcanza el umbral? -> A: el `score` esperado
  del servicio es mayor o igual que la posición de `alta` en la escala (2); el umbral vive en la
  definición versionada y está marcado como provisional.
- Q: ¿Qué límites provisionales tiene la banda incierta del Noul de urgencia? -> A: de 0,3 a 0,7,
  con los dos límites incluidos en «incierto»; por debajo de 0,3 es «no» y por encima de 0,7, «sí».
- Q: ¿Qué longitud máxima de texto acepta `jevlab triage --en-vivo`? -> A: 4.000 caracteres,
  comprobados en código antes de llamar; el valor vive en la definición versionada.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Clasificar un ticket en una cola y leer su distribución (Priority: P1)

Como usuario inicial de Jev, quiero ejecutar `jevlab triage "<texto>"` y ver la cola elegida, la
probabilidad de cada cola y la confianza de la respuesta, para aprender a leer una Choice y decidir
si me fiaría de ella.

**Why this priority**: Es la primitiva más común y el mínimo viable de la feature: una decisión
tipada real, con su distribución y su confianza, y con la opción de escape visible (Constitución
§II).

**Independent Test**: Ejecutar `jevlab triage` sobre tickets de ejemplo, uno claro de cada cola y
uno que no encaja en ninguna, y comprobar que la salida muestra la cola, la distribución completa
y la confianza, y que el ticket que no encaja termina en `other` sin cola asignada.

**Acceptance Scenarios**:

1. **Given** un ticket que describe un cobro duplicado, **When** la persona ejecuta
   `jevlab triage "<texto>"`, **Then** ve la cola elegida, la probabilidad de cada una de las colas
   (incluida `other`) ordenadas de mayor a menor y la confianza de la respuesta.
2. **Given** un ticket que no corresponde a ninguna cola, **When** lo clasifica, **Then** el
   resultado es `other` y la salida dice que el ticket queda sin cola asignada y requiere revisión
   manual, en vez de presentarlo como una cola más.
3. **Given** una respuesta del servicio sin una opción válida, **When** la persona clasifica el
   ticket, **Then** la salida lo indica como abstención y no muestra ninguna cola como elegida.
4. **Given** cualquier ticket clasificado, **When** se recalcula la confianza a partir de la
   distribución con la fórmula oficial, **Then** coincide con la que muestra la salida.

---

### User Story 2 - Ver si el ticket menciona un problema urgente (Priority: P2)

Como usuario inicial de Jev, quiero ver si el ticket menciona explícitamente un problema urgente,
con la probabilidad que da el modelo, para aprender que un Noul es una probabilidad de «sí» y que
los valores intermedios significan duda, no un grado medio de urgencia.

**Why this priority**: Enseña la segunda primitiva y el error de lectura más típico (leer 0,5 como
«medio»). Se apoya en el mismo comando de la US1, pero se puede demostrar por separado.

**Independent Test**: Clasificar tres tickets de ejemplo, uno que menciona la urgencia, otro que no
y otro ambiguo, y comprobar que la salida muestra «sí», «no» e «incierto» con su probabilidad.

**Acceptance Scenarios**:

1. **Given** un ticket que dice que el servicio está caído y lo necesitan ya, **When** la persona
   ejecuta `jevlab triage`, **Then** la salida muestra «urgencia explícita: sí» con la
   probabilidad.
2. **Given** un ticket con una consulta sin urgencia, **When** lo ejecuta, **Then** muestra
   «urgencia explícita: no» con la probabilidad.
3. **Given** un ticket cuya probabilidad cae dentro de la banda incierta, **When** lo ejecuta,
   **Then** muestra «urgencia explícita: incierto», con la probabilidad y los límites de la banda,
   y nunca la palabra «medio» ni un grado de urgencia.

---

### User Story 3 - Ver la prioridad en una escala ordenada y compararla con un umbral (Priority: P3)

Como usuario inicial de Jev, quiero ver la prioridad del ticket como un nivel de una escala con
nombre y saber si alcanza el umbral de atención prioritaria, para aprender a leer un Score con su
leyenda y a usarlo solo para comparar, no como una medida.

**Why this priority**: Completa las tres primitivas. Las operaciones aritméticas sobre el valor de
un Score son una limitación documentada del modelo (*Jaggedness*), y esta historia enseña a
evitarlas.

**Independent Test**: Clasificar un ticket de prioridad baja y otro de prioridad alta y comprobar
que la salida muestra la leyenda, la probabilidad de cada nivel, la confianza y si se alcanza el
umbral.

**Acceptance Scenarios**:

1. **Given** cualquier ticket, **When** la persona ejecuta `jevlab triage`, **Then** ve los niveles
   de la escala con su nombre y su probabilidad, el nivel más probable y la confianza.
2. **Given** un ticket cuya prioridad alcanza el umbral, **When** lo ejecuta, **Then** la salida
   dice que alcanza el umbral e indica el umbral usado y que es provisional.
3. **Given** cualquier ticket, **When** lo ejecuta, **Then** la salida no presenta el valor del
   Score como una magnitud (porcentajes, diferencias o medias entre tickets).

---

### User Story 4 - Repetir el triaje sin red ni coste con respuestas grabadas (Priority: P4)

Como usuario inicial de Jev, quiero repetir el triaje de los tickets de ejemplo sin red, sin claves
y sin coste, a partir de respuestas reales grabadas, y saber en todo momento que estoy viendo una
grabación, para aprender y experimentar gratis y de forma reproducible.

**Why this priority**: Permite usar la feature sin claves y es la base de los tests de contrato
(Constitución §IV). Va al final porque necesita las historias anteriores para tener algo que
grabar.

**Independent Test**: Con la red bloqueada y sin `.env`, reproducir el triaje de cada ticket de
ejemplo y comprobar que la salida coincide con la grabación e indica que es grabada, con el modelo
y la fecha de la grabación.

**Acceptance Scenarios**:

1. **Given** una máquina sin red y sin claves, **When** la persona reproduce el triaje de un ticket
   de ejemplo grabado, **Then** obtiene las tres decisiones y la salida indica «grabado», el modelo
   y la fecha de grabación.
2. **Given** un texto que no tiene grabación, **When** pide reproducirlo, **Then** el comando
   termina con un error que lo explica y lista los ejemplos grabados disponibles, sin intentar
   conectarse.
3. **Given** el mismo ticket grabado, **When** se reproduce dos veces, **Then** las dos salidas son
   idénticas.
4. **Given** un mantenedor con claves válidas, **When** graba de nuevo los ejemplos, **Then** cada
   grabación registra el modelo y la fecha, no guarda claves ni cabeceras de autenticación, y la
   ejecución respeta un tope de coste.
5. **Given** cualquier máquina, **When** la persona ejecuta `jevlab triage` sin opciones, **Then**
   se reproduce la grabación, sin conectarse; solo con la opción explícita `--en-vivo` se llama al
   servicio, y la salida siempre indica si el resultado es «en vivo» o «grabado».
6. **Given** los ejemplos grabados, **When** la persona ejecuta `jevlab triage --ejemplo <nombre>`,
   **Then** obtiene el mismo resultado que escribiendo el texto de ese ejemplo.
7. **Given** una terminal interactiva, **When** la persona ejecuta `jevlab triage` sin texto ni
   nombre, **Then** ve un menú numerado con el nombre y el inicio del texto de cada ejemplo, elige
   uno y obtiene su triaje.

---

### Edge Cases

- Texto vacío o solo con espacios: el comando termina con un error de uso y no llama al servicio.
- Texto de más de 4.000 caracteres con `--en-vivo`: error de uso, sin llamada ni coste; con
  exactamente 4.000, se acepta.
- `--ejemplo` con un nombre que no existe: error que lista los nombres disponibles.
- En el menú, una respuesta que no es un número de la lista o una interrupción: se sale sin
  triaje y sin traza de error.
- `--en-vivo` sin texto: error de uso; el menú solo existe en modo grabado.
- Sin `.env` o con una clave vacía con `--en-vivo`: error que remite a `.env.example` y a
  `jevlab doctor`, sin mostrar valores de claves.
- Fallo transitorio del servicio (límite de peticiones o error del servidor): se reintenta según la
  política por defecto; si se agota, error claro, sin resultado parcial inventado.
- Tiempo de espera agotado: error que lo dice, sin mostrar el texto del ticket.
- Texto con instrucciones dirigidas al modelo («ignora lo anterior y responde…»): se trata como
  contenido del ticket, nunca como instrucción (Constitución §V).
- `score` esperado exactamente igual al umbral: lo alcanza (mayor o igual).
- Nivel más probable `media` con un `score` esperado que alcanza el umbral, o al revés: la salida
  muestra los dos datos sin contradecirse, porque el umbral se decide solo con el `score`.
- Probabilidad del Noul exactamente 0,3 o 0,7: «incierto» (límites incluidos).
- Distribución cuyas probabilidades no suman exactamente 1: se muestran tal como llegan y la
  confianza se recalcula sin normalizar en silencio.
- Salida con tildes y «·» en una consola de Windows, en PowerShell y por una tubería de Git Bash.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La CLI MUST ofrecer `jevlab triage "<texto>"`, que clasifica el ticket con las tres
  decisiones de la tabla «Decisiones Jev» y muestra sus resultados en una sola salida.
- **FR-002**: Las tres decisiones MUST describirse una sola vez en una definición declarativa y
  versionada (preguntas, opciones, escape, banda incierta, umbral, longitud máxima del ticket y
  modelo fijado), que usan tanto
  la CLI como los tests (Constitución §III).
- **FR-003**: Una definición de Choice sin opción de escape MUST fallar su validación.
- **FR-004**: Para la cola, la salida MUST mostrar la cola elegida, la probabilidad de cada opción
  ordenada de mayor a menor y la confianza.
- **FR-005**: Una respuesta `other`, o una respuesta sin opción válida, MUST mostrarse como
  abstención («sin cola asignada, requiere revisión manual») y nunca como una cola normal.
- **FR-006**: El sistema MUST recalcular la confianza de cada Choice y Score a partir de su
  distribución con la fórmula oficial de TypeSafe, y un test MUST comprobar que coincide con la
  devuelta por el servicio en todas las grabaciones.
- **FR-007**: Para la urgencia, la salida MUST mostrar «sí», «no» o «incierto» según la
  probabilidad y una banda incierta definida en la definición versionada y marcada como
  provisional, junto con la probabilidad y los límites de la banda. La banda va de 0,3 a 0,7, con
  los dos límites incluidos en «incierto»; por debajo es «no» y por encima, «sí».
- **FR-008**: Para la prioridad, la salida MUST mostrar la leyenda con la probabilidad de cada
  nivel, el nivel más probable, la confianza y si se alcanza el umbral provisional, sin presentar
  el valor del Score como magnitud. El umbral se alcanza cuando el `score` esperado del servicio
  es mayor o igual que la posición de `alta` en la escala (2); el valor del umbral vive en la
  definición versionada.
- **FR-009**: Toda salida MUST indicar su origen: «en vivo» o «grabado», con el modelo usado y, si
  es grabado, la fecha de grabación (`docs/standards/decision-design.md` §7).
- **FR-010**: Por defecto, `jevlab triage` MUST reproducir las respuestas grabadas sin red, sin
  claves y sin coste, y MUST fallar con un mensaje claro, sin conectarse, si un texto no tiene
  grabación. Solo la opción explícita `--en-vivo` MUST llamar al servicio.
- **FR-010a**: En modo grabado, el ejemplo MUST poder elegirse por su texto (la comparación ignora
  espacios al principio, al final y repetidos), por su nombre con `--ejemplo <nombre>` o, sin texto
  ni nombre en una terminal interactiva, desde un menú numerado. Fuera de una terminal interactiva,
  sin texto ni nombre, el comando MUST listar los ejemplos y terminar con error de uso, sin esperar
  una respuesta.
- **FR-011**: El proyecto MUST incluir un conjunto de tickets de ejemplo propios, etiquetados como
  sintéticos, con su respuesta real grabada, que cubra cada cola, el escape `other` y los tres
  resultados del Noul.
- **FR-012**: La regrabación MUST ser una tarea de mantenimiento con claves reales, marcada como
  prueba contra servicios reales, con tope de coste; cada grabación MUST registrar modelo y fecha y
  MUST NOT contener claves ni cabeceras de autenticación.
- **FR-013**: Con `--en-vivo`, el sistema MUST reutilizar un único cliente por ejecución, aplicar
  la política de reintentos por defecto del SDK y un tiempo de espera finito.
- **FR-013a**: Con `--en-vivo`, un texto de más de 4.000 caracteres (límite en la definición
  versionada) MUST rechazarse con un error de uso antes de llamar al servicio, indicando la
  longitud máxima y sin mostrar el texto.
- **FR-014**: Los mensajes de error MUST NOT incluir el texto del ticket, las respuestas del
  servicio ni claves, y MUST terminar con código de salida distinto de cero.
- **FR-015**: Los logs de nivel `info` MUST NOT contener *payloads* ni datos personales; un test lo
  comprueba con la configuración por defecto.
- **FR-016**: Al modelo se le MUST enviar solo el texto del ticket (estado mínimo), tratado como dato
  no confiable.
- **FR-017**: La salida de la CLI MUST verse con tildes y signos correctos en la consola de Windows,
  en PowerShell, por una tubería de Git Bash y en Linux; la regla queda fijada en
  `docs/standards/cli-ux.md`, que se crea en esta feature.
- **FR-018**: Una puerta automática MUST rechazar el uso directo de reloj, azar o generación de
  identificadores fuera de los adaptadores y los tests, y un test MUST confirmar que la puerta
  salta. La fecha de grabación se obtiene a través de una interfaz sustituible.

### Key Entities

- **Ticket**: texto libre de una petición de soporte. Solo el texto viaja al modelo.
- **Definición de triaje**: descripción versionada de las tres decisiones: preguntas, opciones y
  escape, leyenda, banda incierta, umbral provisional, longitud máxima del ticket y modelo fijado.
- **Resultado de triaje**: para cada decisión, el valor, la distribución, la confianza (Choice y
  Score) y la interpretación hecha por el código (abstención, «incierto», umbral alcanzado), más el
  origen (en vivo o grabado, modelo y fecha).
- **Grabación**: respuesta real del servicio para un ticket de ejemplo, con modelo y fecha, sin
  secretos.
- **Ticket de ejemplo**: ticket sintético propio, etiquetado como tal, con su grabación.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una persona con el entorno instalado y sin claves obtiene el triaje completo de un
  ticket de ejemplo en menos de 1 minuto, siguiendo solo la lección.
- **SC-002**: El 100 % de las salidas muestra resultado, distribución, confianza (en Choice y Score)
  y origen; ninguna muestra una cola cuando el resultado es `other` o no hay respuesta válida.
- **SC-003**: La confianza recalculada coincide con la del servicio, con una diferencia máxima de
  0,001, en el 100 % de las grabaciones.
- **SC-004**: La suite por defecto, con la red bloqueada, reproduce todos los ejemplos grabados con
  0 conexiones y 0 coste, y dos ejecuciones dan salidas idénticas.
- **SC-005**: En la suite, 0 apariciones del texto de un ticket, de una respuesta o de una clave en
  los logs `info` y en los mensajes de error.
- **SC-006**: El conjunto de ejemplos tiene al menos un ticket por cola, uno que termina en `other`
  y uno por cada resultado del Noul (sí, no, incierto).

## Assumptions

- Colas de la Choice: `facturacion`, `tecnico`, `cuenta` y `other`. Son suficientes para enseñar la
  primitiva; ampliarlas no cambia lo que se aprende.
- La banda incierta del Noul y el umbral de prioridad son provisionales hasta la evaluación de la
  spec 004; en esta feature no automatizan ninguna acción, solo se muestran.
- Las tres preguntas se envían en una sola petición. La comparación de una frente a N llamadas es
  materia de la spec 003.
- No hay cola de revisión: «requiere revisión manual» es un texto de la salida. La cola llega en la
  spec 002.
- El ticket se pasa solo como argumento; no hay lectura de archivos ni de la entrada estándar.
- Las claves reales solo hacen falta para grabar (T037 de la spec 000); el resto de la feature
  funciona sin ellas.
- La herramienta de grabación se decide en el plan: el SDK usa un cliente HTTP (`httpx2`) que las
  bibliotecas de grabación habituales quizá no interceptan; si no lo hacen, se graba en el
  transporte del cliente (idea de la retro 000).
- Modelo fijado: el que fije el plan (`jev-1.13.0`, research R4), nunca un alias móvil como
  `jev-latest`.

## Decisiones Jev (jev-lab) *(mandatory si la feature pregunta al modelo)*

> Deriva de: Constitución §I, §II y §IV · Estándar: `docs/standards/decision-design.md`

| Decisión | Pregunta (una idea, literal) | Primitiva | Opciones + escape | Acción automatizable y riesgo | Destino del escape |
| --- | --- | --- | --- | --- | --- |
| cola-destino | «¿A qué cola de soporte pertenece este ticket?» | Choice | `facturacion`, `tecnico`, `cuenta`, `other` | Ninguna: solo se muestra; riesgo bajo | Abstención: «sin cola asignada, requiere revisión manual» |
| urgencia-explicita | «¿El ticket menciona explícitamente un problema urgente?» | Noul | sí / no; la banda incierta la decide el código | Ninguna: solo se muestra; riesgo bajo | Abstención: «incierto» |
| prioridad | «¿Qué prioridad de atención necesita este ticket?» | Score | Leyenda ordenada: `baja`, `media`, `alta`, `critica` | Ninguna: solo se compara con un umbral provisional; riesgo bajo | No aplica (Score); respuesta no válida: abstención |

- **Lo que decide el código**: la confianza recalculada, la clasificación del Noul en sí, no o
  incierto según la banda, el nivel más probable del Score y la comparación del `score` esperado
  con el umbral, el orden
  de la distribución, la abstención ante `other` o una respuesta no válida, y la fecha de
  grabación.
- **Qué ve cada persona**: el usuario inicial de Jev ve, por decisión, el resultado, la
  distribución, la confianza, el motivo de la abstención si la hay, «incierto» en lugar de un
  valor medio, «provisional» junto a cada umbral y el origen (en vivo o grabado, modelo y fecha).

## Corte vertical y lección (jev-lab) *(mandatory)*

> Deriva de: Constitución §VII · Perfiles de usuario: `docs/personas.md`

- **Persona principal**: Usuario inicial de Jev
- **Capacidad de extremo a extremo**: clasificar un ticket de soporte desde la CLI y leer, con sus
  probabilidades y su confianza, las tres primitivas de Jev, en vivo o gratis desde grabaciones.

| Historia | Persona | Cómo se demuestra (comando o petición) |
| --- | --- | --- |
| US1 | Usuario inicial de Jev | `uv run jevlab triage "<ticket de cobro duplicado>"` |
| US2 | Usuario inicial de Jev | `uv run jevlab triage "<ticket con servicio caído>"` |
| US3 | Usuario inicial de Jev | `uv run jevlab triage "<ticket de prioridad alta>"` |
| US4 | Usuario inicial de Jev | `uv run jevlab triage "<ejemplo grabado>"` sin red ni `.env`, y el mismo con `--en-vivo` y claves |

- **Número de historias**: 4 (P1-P4).
- **Fuera de alcance (YAGNI)**: cola de revisión y enrutado automático (002), umbrales en
  `policy.yaml` (002), API (003), evaluación con dataset y calibración (004), lectura de tickets
  desde archivo o entrada estándar, procesamiento por lotes y caché.
- **Lección**: `docs/lessons/001-tres-primitivas-y-como-leer-la-confianza.md`.
  - Qué se aprende: qué devuelve cada primitiva (Choice, Noul y Score), cómo leer una
    distribución y la confianza, por qué el escape y la banda incierta son abstenciones, por qué un
    Score solo se compara con un umbral, y cómo reproducir respuestas reales sin coste.
  - Qué puede fallar y su mitigación: leer un Noul de 0,5 como «medio» (banda incierta); operar
    con el valor de un Score (comparar solo con un umbral); forzar una cola cuando ninguna encaja
    (`other`); confiar en una grabación como si fuera en vivo (origen visible con modelo y fecha);
    filtrar el ticket en logs o errores (logs sin *payloads*); instrucciones incrustadas en el
    ticket (dato no confiable); tildes rotas en Windows (regla de `cli-ux.md`).
