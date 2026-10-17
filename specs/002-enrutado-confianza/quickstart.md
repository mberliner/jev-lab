# Quickstart: Enrutado con confianza según riesgo

Guía para validar la feature de extremo a extremo. Comandos iguales en Linux y Windows; los de
estado usan una carpeta temporal para no mezclar con el estado real.

## Requisitos

- `uv sync` hecho (`docs/setup.md`).
- Sin `.env` para todo salvo el último apartado.
- Estado aislado: `JEVLAB_STATE_DIR` apuntando a una carpeta vacía.

```bash
# Linux / Git Bash
export JEVLAB_STATE_DIR="$(mktemp -d)"
```

```powershell
# PowerShell
$env:JEVLAB_STATE_DIR = (New-Item -ItemType Directory -Path (Join-Path $env:TEMP "jevlab-qs")).FullName
```

Los ejemplos de cada apartado son los previstos en research R8. Si al grabar otro ejemplo cubre
el caso (tasks, T023), se actualizan aquí.

## US1: enrutar solo con confianza suficiente

```bash
uv run jevlab route --ejemplo cambio-de-correo
uv run jevlab route --ejemplo instruccion-incrustada
uv run jevlab route --ejemplo pregunta-fuera-de-ambito
```

Esperado: en `Acción: mover a cola`, el primero queda `estado: automatizada` (`IA propone la
cola: cuenta`); el segundo, `estado: a revisión` con `regla: 0,88 < 0,90`; el tercero, `estado: a
revisión` con `motivo: el ticket no encaja en ninguna cola` (escape). Cada salida muestra origen,
política, huella y petición, y las que van a revisión terminan con `qué hacer: jevlab review`
(`contracts/cli-route.md`).

## US2: reembolso con umbral alto

```bash
uv run jevlab route --ejemplo cobro-duplicado
uv run jevlab route --ejemplo reembolso-ambiguo
uv run jevlab route --ejemplo reembolso-incrustado
```

Esperado: el primero, reembolso `automatizada (simulado)`; el segundo, `pendiente de
confirmación` con su motivo y la cola `facturacion` automatizada; el tercero, adversarial, sin
reembolso automatizado.

## US3: atender la cola

```bash
uv run jevlab review guia
uv run jevlab review
uv run jevlab review asignar <ID de instruccion-incrustada> cuenta
uv run jevlab review confirmar <ID de reembolso-ambiguo>
uv run jevlab review
```

Esperado: la guía muestra las colas de `cola-destino`, el riesgo y el umbral de cada acción y los
comandos. La primera lista muestra un elemento por cada enrutado de arriba con algo pendiente
(al menos `instruccion-incrustada`, `pregunta-fuera-de-ambito` y `reembolso-ambiguo`), cada uno
con sus comandos en `qué hacer:`; tras resolver, esos dos dejan de estar pendientes
(`contracts/cli-review.md`).

## US4: cambiar la política sin tocar código

```bash
cp src/jevlab/policies/soporte/enrutado.yaml "$JEVLAB_STATE_DIR/politica.yaml"
# editar en la copia: mover-a-cola.umbral 0.90 -> la confianza que mostró la salida de
# instruccion-incrustada en US1 (con la grabación actual, 0.88), y version 0.1.0 -> 0.2.0
uv run jevlab route --ejemplo instruccion-incrustada --politica "$JEVLAB_STATE_DIR/politica.yaml"
```

Esperado: `instruccion-incrustada`, que con la política inicial iba a revisión, ahora se mueve
solo, y la salida muestra `Política: 0.2.0` con otra huella. Es también la lección de por qué un
umbral laxo es peligroso: el ticket adversarial se automatiza. Si en la copia se pone
`reembolsar.umbral` por debajo del de `mover-a-cola`, el comando termina con código 1 y el error
de monotonía.

## SC-004: prueba con una persona

Criterio en `spec.md`, SC-004. Lo que lee la persona es la lección
(`docs/lessons/002-la-confianza-como-segundo-eje-y-umbrales-por-riesgo.md`, §4); este apartado
solo fija cómo se mide, igual en cada repetición. Los resultados se anotan en T055 de `tasks.md`.

**Quién.** Alguien que no haya usado `jevlab review` ni leído la spec 002. Si no es así, se anota.

**Preparación**, antes de que llegue la persona, con el estado aislado de «Requisitos»:

```bash
uv run jevlab route --ejemplo instruccion-incrustada
uv run jevlab route --ejemplo reembolso-ambiguo
uv run jevlab route --ejemplo pregunta-fuera-de-ambito
uv run jevlab review    # comprobar: Pendientes: 3, los de la lección §4
```

Se deja esa terminal abierta y, al lado, la lección en «4. La cola de revisión». Sin spec, sin
contrato y sin `--help`.

**Consigna**, leída tal cual: «En esta terminal hay tickets que el sistema no se atrevió a resolver
solo. Usando solo esta lección, resuelve el primero que veas como te parezca correcto. Avísame
cuando termines.»

**Cronómetro.** Empieza al terminar de leer la consigna y para cuando la salida dice
`Elemento N resuelto: sin acciones pendientes`, o la lista ya no lo muestra. No se ayuda; a una
pregunta se responde «sigue con la lección» y se anota.

**Segunda ronda (opcional, el caso difícil):** «Ahora resuelve el del reembolso» (elemento 2).

**Respuesta esperada:** la que da la lección §4, en el paso 2 de «Cómo se resuelve un elemento».
Los elementos son los mismos que la lección usa de ejemplo.

**Qué se anota en T055:** el tiempo de cada ronda y si baja de 60 s; el comando usado y si coincide
con la respuesta esperada; si ejecutó `jevlab review guia` y cuánto tardó en leerla; los errores (código 2, o
«comando no encontrado» por escribir un comando sin `uv run`) y qué hizo después; dónde dudó o qué
preguntó; si ya conocía jevlab. Con varias personas, la mediana. Si alguien supera el minuto, el cambio es un ajuste de
nivel 2 (`docs/governance.md` §7).

Al terminar se borra la carpeta de `JEVLAB_STATE_DIR`.

## Suite y en vivo

```bash
uv run poe check                         # todas las puertas, sin red
uv run jevlab route --en-vivo "<texto>"  # con .env: llama a TypeSafe
```
