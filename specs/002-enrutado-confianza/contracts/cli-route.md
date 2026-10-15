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

Texto plano en UTF-8, con coma decimal y dos decimales (`docs/standards/cli-ux.md`). Forma, con
cifras ilustrativas:

```
Origen: grabado · ejemplo cobro-duplicado (ticket sintético) · jev-1.13.0 · 2026-10-15
Política: 0.1.0 · huella 3fa9c2d1
Petición: 7c1e0f4a-…

Mover a cola: facturacion · automatizada
  confianza 1,00 ≥ umbral 0,90 (riesgo bajo, provisional)

Reembolsar: reembolso · automatizada (simulado)
  confianza 0,98 ≥ umbral 0,97 (riesgo alto, provisional) · cola facturacion automatizada
```

Con acciones sin automatizar:

```
Origen: grabado · ejemplo reembolso-ambiguo (ticket sintético) · jev-1.13.0 · 2026-10-15
Política: 0.1.0 · huella 3fa9c2d1
Petición: 2b90d6e3-…

Mover a cola: facturacion · automatizada
  confianza 0,95 ≥ umbral 0,90 (riesgo bajo, provisional)

Reembolsar: reembolso · pendiente de confirmación
  confianza 0,81 < umbral 0,97 (riesgo alto, provisional)
  motivo: confianza por debajo del umbral

En la cola de revisión: elemento 4 (jevlab review)
```

Reglas:
- La línea `Origen:` va primero (`cli-ux.md` §5); después, la versión y la huella de la política
  y el identificador de petición.
- `Mover a cola` siempre aparece. Sin cola válida: `Mover a cola: sin cola · a revisión`, con el
  motivo (`el ticket no encaja en ninguna cola`, `respuesta fuera de la definición` o `sin
  respuesta válida`, los textos de la 001).
- `Reembolsar` siempre aparece. Si la solicitud no es `reembolso`, la abstención es explícita:
  `Reembolsar: sin reembolso · solicitud consulta · confianza 0,92`. Con el escape,
  `solicitud other (escape)`; sin respuesta válida, `solicitud sin respuesta válida · confianza no
  disponible`. No lleva umbral ni va a revisión.
- Cada acción muestra la confianza, el signo `≥` o `<`, el umbral, el riesgo y `provisional` si la
  justificación lo es; si falta la confianza, `confianza no disponible`.
- Si algo va a revisión, la última línea da el número del elemento.
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
