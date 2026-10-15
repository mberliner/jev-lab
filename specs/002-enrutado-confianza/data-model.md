# Modelo de datos: Enrutado con confianza según riesgo

Entidades del dominio (Pydantic, inmutables) y su persistencia. Las de la 001 que no cambian
(`ChoiceSpec`, `QueueOutcome`, `Origin`, `Recording`…) están en
`specs/001-triaje-ticket/data-model.md`.

## Definiciones

### `ResolvedRequest` (nueva, sustituye el núcleo de `TriageSpec.resolve`)

| Campo | Tipo | Regla |
| --- | --- | --- |
| `request` | `RequestSpec` | La de la 001, sin cambios |
| `decisions` | `dict[str, DecisionSpec]` | Pregunta -> decisión, en el orden de la petición; todas existen |

- Todas las decisiones comparten modelo; `model`, `max_chars`, `questions()` y `spec_versions()`
  se mueven aquí desde `TriageSpec`.
- `TriageSpec.from_request(r)` y `RouteSpec.from_request(r)` comprueban sus preguntas y
  primitivas.

### `RouteSpec` (nueva)

| Campo | Tipo | Regla |
| --- | --- | --- |
| `request` | `ResolvedRequest` | Preguntas exactamente `cola` y `solicitud` |
| `queue` | `ChoiceSpec` | `cola-destino` |
| `request_kind` | `ChoiceSpec` | `solicitud`; debe tener la opción `reembolso` |

Además, `queue` debe tener la opción `facturacion`: la regla del reembolso la nombra.

### Definiciones YAML nuevas

```yaml
# src/jevlab/specs/soporte/solicitud.yaml
version: 0.1.0
model: jev-1.13.0
primitive: choice
instructions: ¿Qué pide el cliente en este ticket?
options:
  reembolso: Que le devuelvan dinero cobrado.
  consulta: Información o ayuda para hacer algo.
  incidencia: Que se arregle un fallo o un problema.
  other: Ninguna de las anteriores.
escape: other

# src/jevlab/specs/soporte/enrutado.yaml
version: 0.1.0
max_chars: 4000
questions:
  cola: cola-destino
  solicitud: solicitud
```

## Respuestas

### `Answers` (nueva; `TriageAnswers` se deriva de ella)

| Campo | Tipo |
| --- | --- |
| `model` | `str` |
| `by_question` | `dict[str, ChoiceAnswer \| NoulAnswer \| ScoreAnswer \| None]` |

Una pregunta sin respuesta, o con una respuesta de otra primitiva, llega como `None`.

## Política

### `Risk` (enum ordenado)

`bajo` < `medio` < `alto`.

### `ActionPolicy`

| Campo | Tipo | Regla |
| --- | --- | --- |
| `riesgo` | `Risk` | Valor conocido |
| `umbral` | `float` | 0 <= umbral <= 1 |
| `justificacion` | `str` | No vacía: `provisional` o la referencia a una evaluación |

### `Policy`

| Campo | Tipo | Regla |
| --- | --- | --- |
| `version` | `str` | Semver |
| `acciones` | `dict[ActionName, ActionPolicy]` | Exactamente `mover-a-cola` y `reembolsar` |

- **Monotonía:** para dos acciones cualesquiera, si `a.riesgo > b.riesgo` entonces
  `a.umbral >= b.umbral`. Si no, la política es no válida y el error nombra las dos acciones.
- **`fingerprint`** (propiedad): 8 caracteres hexadecimales del SHA-256 del JSON canónico
  (research R3).
- **`PolicyRef`**: `version` y `fingerprint`; es lo que se muestra y se guarda.

```yaml
# src/jevlab/policies/soporte/enrutado.yaml
version: 0.1.0
acciones:
  mover-a-cola:
    riesgo: bajo
    umbral: 0.90
    justificacion: provisional  # se fija con la evaluación de la spec 004
  reembolsar:
    riesgo: alto
    umbral: 0.97
    justificacion: provisional  # se fija con la evaluación de la spec 004
```

## Resultado del enrutado

### `ActionName` (enum)

`mover-a-cola`, `reembolsar`.

### `ActionStatus` (enum)

| Valor | Cuándo |
| --- | --- |
| `automatizada` | Cumple la regla de research R4 |
| `a revisión` | `mover-a-cola` sin automatizar |
| `pendiente de confirmación` | `reembolsar` con solicitud `reembolso` sin automatizar |
| `sin reembolso` | `reembolsar` con solicitud distinta de `reembolso`, escape o sin respuesta: abstención explícita (Constitución §II); no va a revisión |

### `PendingReason` (enum, texto de la salida)

| Valor | Acción |
| --- | --- |
| `escape` («el ticket no encaja en ninguna cola») | `mover-a-cola` |
| `fuera de la definición` | `mover-a-cola` |
| `sin respuesta válida` | `mover-a-cola` |
| `confianza por debajo del umbral` | Las dos |
| `la cola no se automatizó a facturacion` | `reembolsar` |
| `la solicitud no es reembolso` | `reembolsar` (`sin reembolso`) |

Si hay varios motivos, se guardan todos, en este orden.

### `ActionOutcome`

| Campo | Tipo | Regla |
| --- | --- | --- |
| `action` | `ActionName` | |
| `value` | `str \| None` | Cola propuesta o valor de la solicitud; `None` sin respuesta válida («sin cola» en `mover-a-cola`) |
| `confidence` | `float \| None` | La del servicio; `None` sin respuesta |
| `threshold` | `float` | De la política |
| `risk` | `Risk` | De la política |
| `justification` | `str` | De la política; la salida dice «provisional» si lo es |
| `status` | `ActionStatus` | |
| `reasons` | `tuple[PendingReason, ...]` | Vacía si `automatizada` |

### `RoutingResult`

| Campo | Tipo | Regla |
| --- | --- | --- |
| `request_id` | `str` | Del puerto `IdGenerator` |
| `decided_at` | `datetime` | UTC, del puerto `Clock` |
| `origin` | `Origin` | El de la 001 |
| `policy` | `PolicyRef` | |
| `spec_versions` | `dict[str, str]` | De `ResolvedRequest` |
| `actions` | `tuple[ActionOutcome, ...]` | Siempre `mover-a-cola` y `reembolsar`; si la solicitud no es `reembolso`, `reembolsar` queda `sin reembolso` |

- `needs_review`: alguna acción está `a revisión` o `pendiente de confirmación`; `sin reembolso`
  no cuenta.

## Cola de revisión

### `ReviewItem`

| Campo | Tipo | Regla |
| --- | --- | --- |
| `id` | `int` | Asignado por el almacén; corto para escribirlo |
| `request_id` | `str` | El de la petición |
| `created_at` | `datetime` | UTC |
| `ticket` | `str` | Texto normalizado (FR-012); nunca sale en logs ni errores |
| `origin` | `Origin` | |
| `policy` | `PolicyRef` | |
| `actions` | `tuple[ReviewAction, ...]` | Las que están `a revisión` o `pendiente de confirmación` |
| `queue` | `str \| None` | Cola actual: la automatizada o la asignada por el Operador |

- `pending`: le queda alguna `ReviewAction` sin resolución.

### `ReviewAction`

`ActionOutcome` más `resolution: Resolution | None`.

### `Resolution` (enum)

`asignada` (con la cola), `descartada`, `confirmada` y `rechazada`.

### Transiciones (dominio puro, `resolve`)

```text
mover-a-cola pendiente --asignar COLA--> asignada(COLA); queue = COLA
                                         si COLA != facturacion: reembolsar pendiente -> rechazada
cualquier acción pendiente --descartar--> mover-a-cola: descartada; reembolsar: rechazada
reembolsar pendiente --confirmar--> confirmada   solo si queue == facturacion
reembolsar pendiente --rechazar---> rechazada
```

- Confirmar sin `queue == facturacion` -> `RefundNeedsBillingQueue` (código 2).
- Una acción ya resuelta o un elemento sin pendientes -> `AlreadyResolved` (código 2).
- Una cola que no está en `cola-destino` o es el escape -> `UnknownQueue`, con las colas válidas
  (código 2).
- `resolve` devuelve el elemento actualizado y un `AuditEntry` de tipo `resolucion` por cada
  acción que resuelve: `asignar` a una cola distinta de `facturacion` con un reembolso pendiente
  produce dos (`asignada` y `rechazada`), y `descartar`, uno por acción pendiente. El almacén
  guarda el elemento y todas esas entradas en una sola transacción.

## Auditoría

### `AuditEntry`

| Campo | Tipo | Regla |
| --- | --- | --- |
| `request_id` | `str` | |
| `at` | `datetime` | UTC |
| `kind` | `decision` \| `resolucion` | |
| `action` | `ActionName` | |
| `value` | `str \| None` | |
| `confidence` | `float \| None` | Solo en `decision` |
| `threshold` | `float \| None` | Solo en `decision` |
| `risk` | `Risk` | |
| `outcome` | `str` | `ActionStatus` o `Resolution` |
| `reasons` | `tuple[PendingReason, ...]` | |
| `policy` | `PolicyRef` | |
| `origin_mode` | `OriginMode` | |
| `model` | `str` | |
| `spec_versions` | `dict[str, str]` | |
| `review_item` | `int \| None` | En las resoluciones y en las decisiones que crean elemento |

Nunca el texto del ticket ni la respuesta del servicio (FR-011, SC-003).

## Persistencia (`estado.sqlite3`, research R5)

```text
audit(id INTEGER PK, request_id TEXT, at TEXT, kind TEXT, action TEXT, value TEXT,
      confidence REAL, threshold REAL, risk TEXT, outcome TEXT, reasons TEXT,
      policy_version TEXT, policy_fingerprint TEXT, origin_mode TEXT, model TEXT,
      spec_versions TEXT, review_item INTEGER)
review_item(id INTEGER PK, request_id TEXT UNIQUE, created_at TEXT, ticket TEXT,
            origin TEXT, policy_version TEXT, policy_fingerprint TEXT, queue TEXT)
review_action(item_id INTEGER, action TEXT, value TEXT, confidence REAL, threshold REAL,
              risk TEXT, justification TEXT, status TEXT, reasons TEXT, resolution TEXT,
              PRIMARY KEY(item_id, action))
```

- `reasons`, `origin` y `spec_versions` se guardan como JSON.
- `PRAGMA user_version = 1`; un archivo con otra versión da un error que lo dice (código 1).
- El adaptador solo traduce filas a entidades; las reglas de transición son del dominio.
