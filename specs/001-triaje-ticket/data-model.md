# Modelo de datos: Triaje de un ticket de soporte

Modelos Pydantic inmutables en `src/jevlab/domain/`, salvo que se indique otra capa. Los nombres de
código van en inglés y los textos que ve la persona, en español, como en la spec 000.

## Definiciones: una por decisión y una por petición

Siguen `docs/standards/architecture.md` §6: cada decisión en su archivo, y una definición de
petición que agrupa las que viajan juntas (research R10). El dominio las valida; el adaptador
`YamlSpecLoader` solo lee los archivos.

### Decisión (`DecisionSpec`)

Un archivo por decisión en `src/jevlab/specs/soporte/<decision>.yaml`.

| Campo | Tipo | Regla |
| --- | --- | --- |
| `version` | texto semver | Obligatorio; viaja en cada grabación |
| `model` | texto | Identificador fijado (`jev-1.13.0`); un alias móvil (`jev-latest`, `jev-preview`) falla la validación (Constitución §III: la decisión incluye su modelo) |
| `primitive` | `choice`, `noul` o `score` | Selecciona el resto de campos |
| `instructions` | texto | La pregunta, una idea, literal y afirmativa |

Campos por primitiva:

- **`choice`**: `options` (mapa ordenado nombre -> descripción) y `escape` (nombre). Validación:
  `escape` es `other` o `none` y está en `options`; al menos dos opciones contando el escape
  (FR-003, research R3).
- **`noul`**: `criteria_true`, `criteria_false` y `uncertain_band` (`low`, `high`,
  `justification`). Validación: `0 <= low <= high <= 1`; `justification` es `provisional` o la
  referencia a una evaluación.
- **`score`**: `levels` (lista ordenada de `{name, description}`) y `threshold` (`level`,
  `justification`). Validación: al menos dos niveles; `threshold.level` es el nombre de un nivel.
  La posición del nivel (desde 0) es el valor con el que se compara el `score`.

### Petición (`RequestSpec`)

Agrupa las decisiones que se envían en una misma llamada, con el mismo estado. Archivo
`src/jevlab/specs/soporte/triaje.yaml`.

| Campo | Tipo | Regla |
| --- | --- | --- |
| `version` | texto semver | Obligatorio; viaja en cada grabación |
| `max_chars` | entero > 0 | 4.000 (aclaración de la spec) |
| `questions` | mapa nombre de pregunta -> nombre de decisión | Cada decisión existe; sin nombres repetidos; todas comparten `model`, que es el de la llamada |

Ejemplos:

```yaml
# src/jevlab/specs/soporte/cola-destino.yaml
version: 0.1.0
model: jev-1.13.0
primitive: choice
instructions: ¿A qué cola de soporte pertenece este ticket?
options:
  facturacion: Cobros, facturas, reembolsos o métodos de pago.
  tecnico: Fallos, errores o mal funcionamiento del producto.
  cuenta: Acceso, contraseña, datos del perfil o alta y baja de la cuenta.
  other: Ninguna de las anteriores.
escape: other
```

```yaml
# src/jevlab/specs/soporte/urgencia-explicita.yaml
version: 0.1.0
model: jev-1.13.0
primitive: noul
instructions: ¿El ticket menciona explícitamente un problema urgente?
criteria_true: El texto dice de forma explícita que el problema es urgente o bloqueante.
criteria_false: El texto no menciona urgencia de forma explícita.
uncertain_band: {low: 0.30, high: 0.70, justification: provisional}
```

```yaml
# src/jevlab/specs/soporte/prioridad.yaml
version: 0.1.0
model: jev-1.13.0
primitive: score
instructions: ¿Qué prioridad de atención necesita este ticket?
levels:
  - {name: baja, description: Puede esperar.}
  - {name: media, description: Atender esta semana.}
  - {name: alta, description: Atender hoy.}
  - {name: critica, description: Atender de inmediato.}
threshold: {level: alta, justification: provisional}
```

```yaml
# src/jevlab/specs/soporte/triaje.yaml
version: 0.1.0
max_chars: 4000
questions:
  cola: cola-destino
  urgencia: urgencia-explicita
  prioridad: prioridad
```

`TriageSpec` es la petición ya resuelta: `RequestSpec` más sus tres `DecisionSpec` validadas y el
modelo común. Es lo que reciben el caso de uso y el adaptador.

## Respuestas traducidas por el adaptador

El adaptador `TypeSafeJudge` convierte la respuesta del SDK en estos tipos (research R2). Una
pregunta sin respuesta llega como `None`.

| Tipo | Campos |
| --- | --- |
| `ChoiceAnswer` | `choice`, `confidence`, `probabilities` (opción -> probabilidad) |
| `NoulAnswer` | `probability` |
| `ScoreAnswer` | `score`, `confidence`, `probabilities` (posición -> probabilidad) |
| `TriageAnswers` | `model` (el que respondió), `queue`, `urgency`, `priority` (cada uno o `None`) |

## Interpretación (lo que decide el código)

Funciones puras en `domain/triage.py` y `domain/confidence.py`.

| Resultado | Campos | Regla |
| --- | --- | --- |
| `QueueOutcome` | `assigned` (opción o `None`), `abstention_reason`, `distribution` ordenada de mayor a menor, `confidence`, `recomputed_confidence` | `assigned` es `None` si la respuesta falta, si `choice` no está en `options` o si es el escape |
| `UrgencyOutcome` | `verdict` (`SI`, `NO`, `INCIERTO`, `ABSTENCION`), `probability`, `band` | `INCIERTO` si `low <= p <= high`; `SI` si `p > high`; `NO` si `p < low`; `ABSTENCION` si falta la respuesta |
| `PriorityOutcome` | `most_likely` (nivel), `distribution` por nivel, `confidence`, `recomputed_confidence`, `expected_score`, `threshold_level`, `reaches_threshold` | `reaches_threshold` si `score >= posición(threshold.level)`; abstención si falta la respuesta |
| `Origin` | `mode` (`GRABADO`, `EN_VIVO`), `model`, `recorded_on` (fecha o `None`), `example` (nombre o `None`), `synthetic` | Grabado: modelo y fecha de la grabación; en vivo: modelo de la respuesta |
| `TriageResult` | `queue`, `urgency`, `priority`, `origin` | Lo que muestra la CLI |

## Ticket y validación de entrada

`TicketText`: texto normalizado (NFC, sin espacios al principio ni al final, espacios repetidos
reducidos a uno). Errores de uso, sin incluir el texto:

| Caso | Error |
| --- | --- |
| Vacío tras normalizar | `EmptyTicket` |
| Más de `max_chars` (solo con `--en-vivo`) | `TicketTooLong(length, max_chars)` |

## Ejemplos grabados (`Recording`)

Formato del archivo en [contracts/recording.md](contracts/recording.md). En el dominio:

| Campo | Regla |
| --- | --- |
| `name` | Único; `[a-z0-9-]+`; coincide con el nombre del archivo |
| `text` | Texto del ticket de ejemplo |
| `synthetic` | Siempre `true` en esta feature (tickets propios, `docs/standards/testing.md` §7) |
| `model`, `recorded_on` | Obligatorios; un test falla si faltan |
| `spec_versions` | Versión de la petición y de cada decisión con las que se grabó |
| `request`, `response` | Cuerpo de la petición y estado y cuerpo de la respuesta; sin cabeceras |

Selección (`domain/examples.py`): por nombre exacto o por texto normalizado. Sin coincidencia:
`ExampleNotFound` con la lista de nombres disponibles.

## Errores del proveedor

Se reutilizan `ProviderUnavailable` y `ProviderRejected` de `domain/diagnostics.py` y se añaden:

| Error | Cuándo | Código de salida |
| --- | --- | --- |
| `InvalidProviderResponse` | El SDK no puede decodificar la respuesta | 1 |
| `RecordingOutdated` | La petición no coincide con la grabada (la definición cambió) | 1 |
| `MissingApiKey` | `--en-vivo` sin `TYPESAFE_API_KEY` | 1 |

## Puertos

| Puerto | Métodos | Adaptador real | Fake |
| --- | --- | --- | --- |
| `JudgePort` | `ask(spec, ticket) -> TriageAnswers` | `TypeSafeJudge` (cliente del SDK; en vivo o con `ReplayTransport`) | `FakeJudge` |
| `RecordingLibrary` | `all() -> list[Recording]`, `save(recording)` | `YamlRecordingLibrary` | `InMemoryRecordingLibrary` |
| `SpecLoader` | `load_request(name) -> TriageSpec` (carga y valida la petición y sus decisiones) | `YamlSpecLoader` | Definición construida en el test |
| `Clock` | `today() -> date` | `SystemClock` | `FrozenClock` |
