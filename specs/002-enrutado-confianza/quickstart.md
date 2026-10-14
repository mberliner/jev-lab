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

## US1: enrutar solo con confianza suficiente

```bash
uv run jevlab route --ejemplo cambio-de-correo
uv run jevlab route --ejemplo instruccion-incrustada
uv run jevlab route --ejemplo pregunta-fuera-de-ambito
```

Esperado: el primero se mueve a `cuenta` (`automatizada`); el segundo queda `a revisión` con
confianza por debajo de 0,90; el tercero, `sin cola · a revisión` por escape. Cada salida muestra
política, huella y petición (`contracts/cli-route.md`).

## US2: reembolso con umbral alto

```bash
uv run jevlab route --ejemplo cobro-duplicado
uv run jevlab route --ejemplo reembolso-ambiguo
```

Esperado: el primero, reembolso `automatizada (simulado)`; el segundo, `pendiente de
confirmación` con su motivo.

## US3: atender la cola

```bash
uv run jevlab review
uv run jevlab review asignar <ID de instruccion-incrustada> cuenta
uv run jevlab review confirmar <ID de reembolso-ambiguo>
uv run jevlab review
```

Esperado: la primera lista muestra los tres elementos de arriba; tras resolver, solo queda el de
`pregunta-fuera-de-ambito` (`contracts/cli-review.md`).

## US4: cambiar la política sin tocar código

```bash
cp src/jevlab/policies/soporte/enrutado.yaml "$JEVLAB_STATE_DIR/politica.yaml"
# editar en la copia: mover-a-cola.umbral 0.90 -> 0.80 y version 0.1.0 -> 0.2.0
uv run jevlab route --ejemplo instruccion-incrustada --politica "$JEVLAB_STATE_DIR/politica.yaml"
```

Esperado: `instruccion-incrustada`, que con la política inicial iba a revisión, ahora se mueve
solo, y la salida muestra `Política: 0.2.0` con otra huella. Es también la lección de por qué un
umbral laxo es peligroso: el ticket adversarial se automatiza. Si en la copia se pone `reembolsar.umbral` por
debajo del de `mover-a-cola`, el comando termina con código 1 y el error de monotonía.

## Suite y en vivo

```bash
uv run poe check                         # todas las puertas, sin red
uv run jevlab route --en-vivo "<texto>"  # con .env: llama a TypeSafe
```
