# Puesta en marcha

Guía para dejar jev-lab listo en Linux o en Windows desde un clon limpio. Al terminar, la suite de
tests pasa sin red ni claves y `jevlab doctor` confirma el entorno.

## 1. Requisitos

| Herramienta | Para qué | Versión |
| --- | --- | --- |
| Git | Clonar y versionar (en Windows, Git for Windows con Git Bash) | Cualquiera reciente |
| [uv](https://docs.astral.sh/uv/) | Gestiona el Python del proyecto y sus dependencias | 0.9 o superior |
| Python del proyecto | Ejecuta el código de jev-lab; lo instala uv | 3.13 |
| `python3` del sistema | Ejecuta los scripts de Spec Kit; necesita PyYAML | 3.8 o superior |
| `specify` (Spec Kit) | Solo para cambiar presets o actualizar Spec Kit | 1.1.4.dev0 |

El proyecto usa **dos intérpretes con papeles separados**:

- El código del proyecto se ejecuta siempre con `uv run …`, que usa el Python 3.13 del entorno
  virtual (`.venv/`). Así nunca se cae en un Python de sistema antiguo.
- Los scripts de Spec Kit (`.specify/scripts/python/`) los lanza el agente con `python3`. Basta con
  un Python 3.8 o superior que tenga PyYAML, porque PyYAML hace falta para componer las plantillas
  de los presets (`docs/governance.md` §5, «Nota técnica»).

## 2. Linux

1. Instalar uv según su documentación y comprobar `uv --version`.
2. Comprobar el `python3` del sistema y PyYAML:
   ```
   python3 --version
   python3 -c "import yaml; print(yaml.__version__)"
   ```
   Si falta PyYAML, ver el apartado 4.
3. Clonar e instalar:
   ```
   git clone <url-del-repo> jev-lab
   cd jev-lab
   uv sync
   uv run poe test
   uv run pre-commit install
   ```
   `uv sync` descarga Python 3.13 si no está y crea `.venv/`. `uv run poe test` ejecuta la suite
   con la red bloqueada. `pre-commit install` activa las puertas de calidad en cada commit.

## 3. Windows

Los comandos se escriben en Git Bash, salvo los marcados como PowerShell.

1. Instalar Git for Windows (incluye Git Bash) y uv.
2. Instalar Python 3.13 desde python.org o reutilizar uno existente. uv lo reutiliza.
3. **Crear `python3.exe`.** En Windows suele haber solo `python.exe` y `py.exe`, y Spec Kit busca
   `python3`. Se crea un enlace duro junto a `python.exe` (PowerShell, en la carpeta del Python
   3.13):
   ```
   $dir = Split-Path (Get-Command python).Source
   New-Item -ItemType HardLink -Path "$dir\python3.exe" -Target "$dir\python.exe"
   ```
   Un enlace duro no es un enlace simbólico y no necesita permisos de administrador. Si
   `python3` abre la Microsoft Store, desactivar el alias de `python3.exe` en «Configuración >
   Aplicaciones > Alias de ejecución de aplicaciones».
4. Comprobar PyYAML con `python3 -c "import yaml"`. Si falta, ver el apartado 4.
5. Clonar e instalar, igual que en Linux:
   ```
   git clone <url-del-repo> jev-lab
   cd jev-lab
   uv sync
   uv run poe test
   uv run pre-commit install
   ```

Los finales de línea los fija `.gitattributes`: LF en todo el repositorio salvo los scripts de
Windows (`*.ps1`, `*.cmd`, `*.bat`), que usan CRLF. No hace falta configurar `core.autocrlf`.

## 4. PyYAML para Spec Kit

Hay dos formas; basta con una.

- **Instalarlo en `python3`:**
  ```
  python3 -m pip install --user pyyaml
  ```
- **Apuntar Spec Kit a un intérprete que ya lo tenga.** Si `python3` no tiene PyYAML, los scripts
  de Spec Kit delegan la lectura de los presets en el intérprete de `SPECKIT_PYTHON_EXECUTABLE`.
  El entorno de `specify-cli` instalado con `uv tool` ya trae PyYAML:
  ```
  uv tool dir     # muestra la carpeta de las herramientas de uv
  ```
  - Linux: añadir a `~/.bashrc` la línea
    `export SPECKIT_PYTHON_EXECUTABLE="<carpeta>/specify-cli/bin/python"`.
  - Windows (PowerShell):
    `setx SPECKIT_PYTHON_EXECUTABLE "<carpeta>\specify-cli\Scripts\python.exe"`, y abrir una
    terminal nueva.

`uv run jevlab doctor` comprueba las dos opciones (apartado 6).

## 5. Claves: `.env`

Las claves viven solo en `.env`, que no se versiona (`docs/standards/security.md` §1):

```
cp .env.example .env
```

Después se rellenan los valores de TypeSafe y de Azure OpenAI. La suite por defecto no las
necesita; solo las usan `jevlab doctor --remote` y los tests `live`.

## 6. Comprobar el entorno

```
uv run jevlab doctor            # comprobaciones locales, sin red
uv run jevlab doctor --remote   # además, acceso a TypeSafe y a Azure OpenAI
```

Cada comprobación muestra su estado y, si falla, cómo arreglarla. Contrato completo:
`specs/000-cimientos/contracts/cli-doctor.md`.

## 7. Tareas del proyecto

Todas se ejecutan igual en Linux y en Windows con `uv run poe <tarea>`:

| Tarea | Qué hace |
| --- | --- |
| `test` | Toda la suite salvo los tests `live`, con la red bloqueada |
| `check` | Todas las puertas de calidad (la ejecuta pre-commit en cada commit) |
| `live` | Tests contra servicios reales; necesitan `.env` y tienen tope de coste |
| `record` | Regraba los ejemplos de `jevlab triage` y `jevlab route` con la clave real; mismo tope que `live` |
| `record-triage`, `record-route` | Regraban solo los ejemplos de una de las dos peticiones |
| `lint`, `typecheck`, `lint-imports`, `cov` | Puertas sueltas, para depurar |

El tope de coste de los tests `live` se fija con `JEVLAB_LIVE_BUDGET_USD` (por defecto 0,10 USD).

## 8. Estado local: auditoría y cola de revisión

`jevlab route` y `jevlab review` guardan la auditoría y la cola de revisión en un archivo SQLite,
`estado.sqlite3`, fuera del repositorio y el mismo desde cualquier directorio:

| Sistema | Carpeta |
| --- | --- |
| Windows | `%LOCALAPPDATA%\jevlab` |
| Linux | `$XDG_STATE_HOME/jevlab` o, si no está definida, `~/.local/state/jevlab` |

- **Otra carpeta:** la variable `JEVLAB_STATE_DIR` la sustituye. Sirve para probar sin mezclar
  con el estado real, como hace `specs/002-enrutado-confianza/quickstart.md`.
- **Empezar de cero:** borrar `estado.sqlite3`; se crea vacío en el siguiente uso.
- **Qué contiene:** la auditoría guarda solo metadatos de cada decisión y resolución; la cola de
  revisión guarda además el texto de los tickets pendientes, para que el Operador pueda
  resolverlos. No contiene claves.
- **Otra versión:** si el archivo es de otra versión de jevlab, los comandos terminan con un error
  que dice la ruta; se puede mover o borrar.

## 9. Agentes: Claude Code y Antigravity

Los dos agentes trabajan sobre los mismos artefactos. La decisión está en
[ADR-0002](adr/0002-paridad-de-agentes.md).

- **Qué trae el clon.** Las dos integraciones de Spec Kit ya están instaladas y versionadas:
  `.claude/skills/` para Claude Code y `.agents/skills/` para Antigravity. Las dos comparten
  `.specify/` (constitución, plantillas, presets y scripts) y `specs/`. No hay que instalar nada
  más en el repositorio.
- **Instrucciones.** `AGENTS.md` es la única fuente; `CLAUDE.md` solo contiene `@AGENTS.md`.
- **Invocación.** En los dos agentes, las skills de Spec Kit se llaman `/speckit-*`
  (`/speckit-specify`, `/speckit-plan`…).
- **Skill de TypeSafe (opcional).** Se instala por usuario, no en el repositorio. En Claude Code:
  `claude plugin install typesafe@typesafe-ai`. En Antigravity, la misma skill en su directorio de
  usuario si la licencia lo permite; si no, la documentación oficial
  (`https://docs.typesafe.ai/llms.txt`).
- **Hooks y comandos de agente.** Solo con implementación neutral: la lógica vive en una tarea
  `poe` y las puertas de calidad son pre-commit y CI, que se aplican igual uses el agente que uses.

### Instalar Spec Kit (solo para mantener presets)

Para trabajar con los agentes no hace falta la CLI `specify`. Se necesita para instalar o cambiar
un preset y para actualizar Spec Kit:

```
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
specify integration status      # muestra claude y agy
```

Si se parte de un repositorio sin Spec Kit, la paridad se monta así:

```
specify init . --integration claude --script py
specify integration install agy --force
```

`agy` no está declarada como segura para convivir con otras integraciones, de ahí el `--force`.
Los procedimientos para cambiar un preset o actualizar Spec Kit, incluido el paso por cada agente,
están en `docs/governance.md` §5.

## 10. Repositorio público en GitHub

El mantenedor crea el repositorio una sola vez:

1. En github.com, «New repository»: nombre `jev-lab`, visibilidad pública, **sin** README,
   `.gitignore` ni licencia (ya están en el repositorio).
2. Añadir el remoto y subir las ramas:
   ```
   git remote add origin https://github.com/<usuario>/jev-lab.git
   git push -u origin main
   ```
3. Comprobar en la pestaña «Actions» que la CI pasa en Linux y en Windows.

La CI no usa *secrets*: las comprobaciones remotas y los tests `live` quedan fuera de ella
(`docs/standards/security.md` §5).

## 11. Problemas frecuentes

| Síntoma | Causa | Arreglo |
| --- | --- | --- |
| `python3: command not found` en Windows | Solo existe `python.exe` | Enlace `python3.exe` (apartado 3) |
| Spec Kit ignora los presets o falla al leer `preset.yml` | `python3` sin PyYAML | Apartado 4 |
| `uv run poe test` intenta usar Python 3.8 | Se ejecutó `python3 -m pytest` en vez de `uv run` | Usar siempre `uv run …` |
| Un test falla con `SocketBlockedError` | El test intenta usar la red | Usar un fake o marcar el test como `live` |
| `jevlab doctor` informa de claves que faltan | `.env` ausente o incompleto | Apartado 5 |
