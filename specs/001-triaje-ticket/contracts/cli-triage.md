# Contrato: `jevlab triage`

## Uso

```
jevlab triage [TEXTO] [--ejemplo NOMBRE] [--en-vivo]
```

| Forma | Modo | Qué hace |
| --- | --- | --- |
| `jevlab triage "<texto>"` | Grabado | Busca el ejemplo cuyo texto normalizado coincide y lo reproduce |
| `jevlab triage --ejemplo <nombre>` | Grabado | Reproduce el ejemplo con ese nombre |
| `jevlab triage` (terminal interactiva) | Grabado | Menú numerado con nombre e inicio del texto de cada ejemplo |
| `jevlab triage` (sin terminal) | Grabado | Lista los ejemplos y termina con código 2 |
| `jevlab triage --en-vivo "<texto>"` | En vivo | Llama a TypeSafe con la clave de `.env` |

`TEXTO` y `--ejemplo` son excluyentes. `--en-vivo` exige `TEXTO` y no admite `--ejemplo`.

## Salida (éxito)

Texto plano en UTF-8, con coma decimal y dos decimales. Forma, con un ejemplo grabado:

```
Origen: grabado · ejemplo cobro-duplicado (ticket sintético) · jev-1.13.0 · 2026-10-20

Cola: facturacion · confianza 0,84
  facturacion  0,88
  tecnico      0,06
  cuenta       0,04
  other        0,02

Urgencia explícita: no · probabilidad 0,12
  incierto entre 0,30 y 0,70 (provisional)

Prioridad: más probable media · confianza 0,41
  0 baja      0,20
  1 media     0,55
  2 alta      0,20
  3 critica   0,05
  umbral alta (provisional): no alcanzado · valor esperado 1,10 < 2
```

Reglas:
- La primera línea siempre indica el origen: `grabado` con ejemplo, modelo y fecha, o `en vivo`
  con el modelo que respondió.
- `other`, una opción fuera de la definición o una respuesta que falta: `Cola: sin cola asignada,
  requiere revisión manual (motivo)`, y la distribución se muestra igualmente si existe.
- Urgencia: `sí`, `no` o `incierto`; nunca «medio». Si falta la respuesta: `Urgencia explícita:
  abstención (sin respuesta válida)`.
- Prioridad sin respuesta válida: `Prioridad: abstención (sin respuesta válida)`, sin niveles ni
  línea de umbral.
- En modo grabado, el texto que escribe la persona solo sirve para elegir el ejemplo; lo que se
  reproduce es la petición con el texto de la grabación, guardado ya normalizado.
- Prioridad: el valor esperado solo aparece en la línea del umbral, comparado con la posición del
  nivel; no hay porcentajes, diferencias ni medias.
- La confianza mostrada es la del servicio. La recalculada se comprueba en los tests (FR-006), no
  se muestra.

## Códigos de salida y errores

Los errores van a `stderr`, en una línea, y nunca incluyen el texto del ticket, la respuesta del
servicio ni claves.

| Código | Caso | Mensaje (forma) |
| --- | --- | --- |
| 0 | Triaje mostrado, aunque alguna decisión sea abstención o «incierto» | (salida anterior) |
| 1 | Servicio no disponible tras los reintentos, *timeout*, rechazo (4xx), respuesta no válida | `error: TypeSafe no disponible (503) tras 3 intentos` |
| 1 | Tiempo de espera agotado tras los reintentos | `error: TypeSafe no respondió a tiempo (10 s)` |
| 1 | `--en-vivo` sin clave | `error: falta TYPESAFE_API_KEY; ver .env.example y jevlab doctor` |
| 1 | Grabación desactualizada | `error: la grabación cobro-duplicado no corresponde a la definición actual; hay que regrabar` |
| 2 | Texto vacío | `error: el ticket está vacío` |
| 2 | Texto de más de 4.000 caracteres con `--en-vivo` | `error: el ticket tiene 5.230 caracteres; el máximo es 4.000` |
| 2 | Texto sin grabación o nombre inexistente | `error: no hay grabación para ese ticket; ejemplos: cobro-duplicado, servicio-caido, …` |
| 2 | Opciones incompatibles o sin terminal para el menú | Mensaje de uso y lista de ejemplos |
| 1 | En el menú, respuesta no válida o interrupción | `sin triaje: no se eligió ningún ejemplo`, sin traza |

## Logs

En nivel `info`, una línea por ejecución en el logger `jevlab`, solo con metadatos y resultados
interpretados (`docs/standards/security.md` §0):

```
triage modo=grabado ejemplo=cobro-duplicado modelo=jev-1.13.0 cola=facturacion urgencia=no prioridad=media umbral=no
```

El logger `typesafe_sdk` sigue en `WARNING` por defecto (spec 000, R12).
