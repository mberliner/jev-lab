# Modelo de datos: Cimientos de jev-lab

Solo hay datos en memoria; nada se persiste. Las entidades de dominio son modelos Pydantic
inmutables en `src/jevlab/domain/diagnostics.py`.

## `CheckStatus` (enumeración)

| Valor | Significado |
| --- | --- |
| `ok` | La comprobación pasa |
| `fail` | La comprobación falla y tiene instrucción de arreglo |
| `unavailable` | No se pudo comprobar (red caída, *timeout*); se muestra como «no disponible» |

## `Scope` (enumeración)

`local` o `remote`.

## `CheckResult`

| Campo | Tipo | Regla |
| --- | --- | --- |
| `name` | str | Identificador estable, p. ej. `speckit-python`, `project-python`, `env-keys`, `typesafe`, `azure` |
| `scope` | `Scope` | |
| `status` | `CheckStatus` | Una comprobación `local` nunca es `unavailable` |
| `detail` | str | Lo comprobado, sin valores de claves ni *payloads* (FR-013) |
| `fix` | str \| None | Obligatorio si `status` no es `ok` (FR-012) |

## `DoctorReport`

| Campo | Tipo | Regla |
| --- | --- | --- |
| `results` | tuple[`CheckResult`, ...] | Locales primero, en orden fijo; remotos solo si se pidieron |
| `remote_requested` | bool | |

Regla del código de salida (pura, `DoctorReport.exit_code()`):
- `1` si algún resultado es `fail`;
- `1` si `remote_requested` y algún resultado remoto es `unavailable` (aclaración de la spec);
- `0` en otro caso.

## Errores de dominio de los proveedores

Los adaptadores traducen las excepciones del SDK a estos dos tipos, para que la aplicación
distinga los casos sin conocer el SDK:

| Error | Cuándo | Resultado |
| --- | --- | --- |
| `ProviderUnavailable` | Red, DNS, *timeout*, 5xx tras reintentos | `unavailable` |
| `ProviderRejected` | 401, 403, 404 (deployment o modelo inexistente) | `fail`, con `fix` según el código |

## Entidades de soporte (fuera del paquete)

- **Puerta de calidad** (spec, *Key Entities*): no es un modelo en código. Cada puerta es una tarea
  `poe` que nombra la regla y el estándar del que deriva; la tabla está en `plan.md`, «Puertas de
  calidad».
