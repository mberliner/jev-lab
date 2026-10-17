# Estándar: salida de la CLI

> Concreta: Constitución §II, §IV, §V, §VI · Exigido por: preset jevlab-decision · ADRs:
> *(ninguno)*

Convenciones para todo lo que `jevlab` escribe en la terminal. Lo que muestra cada decisión está
en `decision-design.md` §7; aquí se fija cómo se escribe. El ejemplo de referencia es el contrato
de `jevlab triage` (`specs/001-triaje-ticket/contracts/cli-triage.md`); para acciones con umbral
(`≥` o `<`, riesgo y motivo), el de `jevlab route`
(`specs/002-enrutado-confianza/contracts/cli-route.md`).

## 1. Texto plano en UTF-8, en cualquier terminal

**Regla.** La CLI escribe texto plano, sin colores ni tablas de Rich, y reconfigura `stdout` y
`stderr` a UTF-8 al arrancar, en todos los comandos. Las tildes y el separador `·` se ven igual en
la consola de Windows, en PowerShell, por una tubería de Git Bash y en Linux.

**Motivo.** En Windows, `sys.stdout.encoding` es `cp1252` cuando la salida va a una tubería, y Git
Bash, que espera UTF-8, muestra mal las tildes. En la consola, Python escribe en Unicode con
independencia de esa codificación.

**Correcto:** `uv run jevlab triage --ejemplo cobro-duplicado | cat` muestra `Urgencia explícita`.

**Incorrecto:** pedir a cada persona que defina `PYTHONUTF8=1`, o escribir solo ASCII.

**Caso conocido:** en una PowerShell con `[Console]::OutputEncoding` distinto de UTF-8, la salida
capturada en una variable (`$salida = uv run jevlab ...`) se decodifica con esa página de códigos.
Se arregla en la sesión con `[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()`; en
PowerShell 7 con la configuración por defecto no hace falta.

**Cómo se verifica:** test unitario que sustituye `stdout` y `stderr` por flujos `cp1252` y
comprueba que quedan en UTF-8 (`tests/unit/entrypoints/test_cli_encoding.py`); prueba manual en
Windows al cerrar cada feature con CLI.

## 2. Números

**Regla.** Probabilidades, confianzas y umbrales se escriben con coma decimal y dos decimales
(`0,84`). Los enteros grandes llevan punto de miles (`4.000`). Las posiciones de una escala se
escriben como enteros (`2`).

**Motivo.** Es la convención del español, la misma de los documentos y las lecciones.

**Correcto:** `Cola: facturacion · confianza 0,84`

**Incorrecto:** `Cola: facturacion (84%)`: un porcentaje sugiere una magnitud que se puede operar.

**Cómo se verifica:** tests de la vista de cada comando.

## 3. Errores en `stderr`, en una línea y sin *payloads*

**Regla.** Un error se escribe en `stderr` en una sola línea que empieza por `error: `, sin traza.
El mensaje lleva el tipo del fallo y, si lo hay, el estado HTTP o el número de intentos; nunca el
texto de la entrada, la respuesta del servicio ni claves (`security.md` §2). Si el arreglo es
conocido, el mensaje lo nombra (`ver .env.example y jevlab doctor`).

**Motivo.** Un error se copia en un *issue* o en un chat; lo que lleva dentro sale del equipo.

**Correcto:** `error: TypeSafe no disponible (503) tras 3 intentos`

**Incorrecto:** `error: 503 {"detail": ...} para el ticket «Me habéis cobrado...»`

**Cómo se verifica:** tests de los comandos que fuerzan cada error y buscan el texto de entrada y
la clave en `stdout` y `stderr`.

## 4. Códigos de salida

| Código | Significado |
| --- | --- |
| 0 | El comando hizo su trabajo, aunque el resultado sea una abstención o «incierto» |
| 1 | Fallo del servicio, de la configuración o de una grabación; o la persona no eligió nada |
| 2 | Error de uso: argumentos incompatibles, entrada vacía o demasiado larga, ejemplo inexistente |

**Motivo.** Un script distingue así entre «repetir más tarde» (1) y «corregir la llamada» (2).
El 2 es también el código de uso de Typer.

**Cómo se verifica:** tests de los comandos con `CliRunner`.

## 5. Origen siempre visible

**Regla.** Toda salida con un resultado del modelo empieza por una línea `Origen:` que dice si es
`en vivo` o `grabado`, con el modelo y, si es grabado, el ejemplo, si el ticket es sintético y la
fecha de la grabación (`decision-design.md` §7).

**Correcto:** `Origen: grabado · ejemplo cobro-duplicado (ticket sintético) · jev-1.13.0 · 2026-10-20`

**Cómo se verifica:** tests de la vista y test de integración sin red.

## 6. Cada valor dice de dónde sale, y lo pendiente dice qué hacer

**Regla.** Cuando una salida presenta una acción que depende de una decisión del modelo, cada
dato lleva una etiqueta con su origen (`decision-design.md` §7):

| Etiqueta | Origen | Ejemplo |
| --- | --- | --- |
| `Acción:` y `estado:` | lo que se hizo o queda por hacer | `Acción: mover a cola · estado: a revisión` |
| `IA propone …:` o `IA clasifica …:` | el valor que da el modelo, con la pregunta y la confianza | `IA propone la cola: cuenta · confianza 0,88` |
| `política:` | el umbral, el riesgo y si es provisional | `política: umbral 0,90 (riesgo bajo, provisional)` |
| `regla:` | lo que comprueba el código y el motivo del estado | `regla: 0,88 < 0,90 · motivo: confianza por debajo del umbral` |

Un valor no se escribe solo detrás del nombre de la acción. Lo que queda pendiente de una persona
termina con una línea `qué hacer:` que da los comandos exactos que lo resuelven, con el número del
elemento y, si piden un valor, los valores válidos. Un listado de pendientes empieza diciendo qué
contiene y quién lo resuelve.

**Motivo.** En la prueba de SC-004 de la spec 002, una persona sin experiencia no supo si
`Mover a cola: cuenta` era una cola asignada o lo que proponía el modelo, ni por qué estaba en la
cola, ni con qué comando resolverlo, y no terminó en 10 minutos. El principio del proyecto, «el
modelo juzga, el código decide», solo se ve si la salida separa las dos cosas.

**Correcto:**

```text
Acción: reembolsar · estado: pendiente de confirmación
  IA clasifica la solicitud: reembolso · confianza 0,87
  política: umbral 0,97 (riesgo alto, provisional)
  regla: 0,87 < 0,97 · motivo: confianza por debajo del umbral
  qué hacer: jevlab review confirmar 2 | jevlab review rechazar 2
```

**Incorrecto:** `Reembolsar: reembolso · pendiente de confirmación` (no dice que `reembolso` lo
propone el modelo, ni qué regla lo dejó pendiente, ni cómo se resuelve), o `automatizada por IA`
(automatiza el código, al aplicar la política).

**Cómo se verifica:** tests de la vista de cada comando, que buscan las etiquetas y la línea
`qué hacer:`; y la prueba con una persona del criterio de éxito correspondiente, si la spec lo
tiene.
