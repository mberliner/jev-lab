# Contrato: `jevlab route`

## Uso

```
jevlab route [TEXTO] [--ejemplo NOMBRE] [--en-vivo] [--politica RUTA]
```

Los modos y la selección del ejemplo son los de `jevlab triage`
(`specs/001-triaje-ticket/contracts/cli-triage.md`), sobre las grabaciones de
`src/jevlab/recordings/soporte/enrutado/`. `--politica` carga otra política en lugar de
`src/jevlab/policies/soporte/enrutado.yaml`.

Cada ejecución, grabada o en vivo, escribe en el archivo de estado local (research R5): la
auditoría siempre y, si alguna acción no se automatiza, un elemento en la cola de revisión.

## Salida (éxito)

Texto plano en UTF-8, con coma decimal y dos decimales, y cada dato con la etiqueta de su origen
(`docs/standards/cli-ux.md` §6). Forma, con cifras ilustrativas:

```
Origen: grabado · ejemplo cobro-duplicado (ticket sintético) · jev-1.13.0 · 2026-10-15
Política: 0.1.0 · huella 3fa9c2d1
Petición: 7c1e0f4a-…

Acción: mover a cola · estado: automatizada
  IA propone la cola: facturacion · confianza 1,00
  política: umbral 0,90 (riesgo bajo, provisional)
  regla: 1,00 ≥ 0,90

Acción: reembolsar · estado: automatizada (simulado)
  IA clasifica la solicitud: reembolso · confianza 0,98
  política: umbral 0,97 (riesgo alto, provisional)
  regla: 0,98 ≥ 0,97 · cola facturacion automatizada
```

Con acciones sin automatizar:

```
Origen: grabado · ejemplo reembolso-ambiguo (ticket sintético) · jev-1.13.0 · 2026-10-15
Política: 0.1.0 · huella 3fa9c2d1
Petición: 2b90d6e3-…

Acción: mover a cola · estado: automatizada
  IA propone la cola: facturacion · confianza 0,95
  política: umbral 0,90 (riesgo bajo, provisional)
  regla: 0,95 ≥ 0,90

Acción: reembolsar · estado: pendiente de confirmación
  IA clasifica la solicitud: reembolso · confianza 0,81
  política: umbral 0,97 (riesgo alto, provisional)
  regla: 0,81 < 0,97 · motivo: confianza por debajo del umbral

En la cola de revisión: elemento 4
qué hacer: jevlab review
```

Reglas:
- La línea `Origen:` va primero (`cli-ux.md` §5); después, la versión y la huella de la política
  y el identificador de petición.
- Cada acción empieza por `Acción: <acción> · estado: <estado>`; debajo, con sangría:
  - `IA propone la cola:` o `IA clasifica la solicitud:`, con el valor que da el modelo y su
    confianza. Sin valor válido, `ninguna`; sin confianza, `confianza no disponible`.
  - `política:`, con el umbral, el riesgo y `provisional` si la justificación lo es.
  - `regla:`, con la comparación del código (`0,87 < 0,90`, o `sin valor válido` si no hay valor o
    confianza que comparar) y, si no se automatiza, `motivo:` (`confianza por debajo del umbral`,
    `la cola no se automatizó a facturacion`, o los textos de la 001: `el ticket no encaja en
    ninguna cola`, `respuesta fuera de la definición`, `sin respuesta válida`).
- `mover a cola` siempre aparece.
- `reembolsar` siempre aparece. Si la solicitud no es `reembolso`, la abstención es explícita:
  estado `sin reembolso`, la línea `IA clasifica la solicitud:` con su valor (`other (escape)`
  con el escape; `ninguna` sin respuesta válida) y `regla: sin umbral · motivo: …` (`la solicitud
  no es reembolso`, `la solicitud no encaja en ninguna opción` o `sin respuesta válida`). No lleva
  línea de política ni va a revisión.
- Si algo va a revisión, las dos últimas líneas dan el número del elemento y `qué hacer: jevlab
  review`.
- Las acciones son simuladas: `automatizada` no tiene efectos fuera de jev-lab. El reembolso lo
  dice con `(simulado)`.

## Códigos de salida y errores

Los de `jevlab triage` y, además:

| Código | Caso | Mensaje (forma) |
| --- | --- | --- |
| 0 | Enrutado hecho, aunque algo vaya a revisión | (salida anterior) |
| 1 | Política no válida | `error: política no válida (enrutado.yaml): acciones.reembolsar.umbral 0,85 es menor que el de mover-a-cola 0,90 con más riesgo` |
| 1 | Política inexistente o ilegible | `error: no se puede leer la política <ruta>` |
| 1 | Archivo de estado ilegible o de otra versión | `error: el archivo de estado <ruta> no es de esta versión de jevlab` |

Con un error de política no se pregunta al modelo ni se escribe en el estado.

## Logs

En nivel `info`, una línea por ejecución en el logger `jevlab`, solo con metadatos:

```
route peticion=7c1e0f4a-… modo=grabado ejemplo=cobro-duplicado modelo=jev-1.13.0 politica=0.1.0/3fa9c2d1 mover-a-cola=automatizada reembolsar=automatizada
```

`reembolsar` toma los valores `automatizada`, `pendiente-de-confirmacion` o `sin-reembolso`.
