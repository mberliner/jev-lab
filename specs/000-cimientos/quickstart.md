# Guía de validación: Cimientos de jev-lab

Escenarios para demostrar cada historia una vez implementada. Los pasos de instalación son los de
`docs/setup.md`; aquí solo se enumeran.

## Requisitos

- Git, uv y Python 3.13 (uv lo instala si falta).
- `python3` ≥ 3.8 con PyYAML para Spec Kit (en Windows, el enlace `python3.exe` de `docs/setup.md`).
- Para la US2 remota: `.env` con claves reales de TypeSafe y Azure OpenAI.

## US1: clon limpio, suite sin red

```
git clone <url-del-repo> jev-lab && cd jev-lab
uv sync
uv run poe test
```

Resultado esperado, en Linux y en Windows: la suite pasa sin `.env` y sin red. Para comprobar el
bloqueo de red, `tests/unit/test_network_blocked.py` intenta abrir una conexión y espera el error de
`pytest-socket`.

## US2: `jevlab doctor`

| Paso | Resultado esperado |
| --- | --- |
| `uv run jevlab doctor` con todo instalado y `.env` completo | Tres `[ok]` locales; código de salida 0 |
| Igual, sin `.env` | `[fail] env-keys` con las variables que faltan, sin valores; código 1 |
| `uv run jevlab doctor --remote` con claves válidas | Además, `[ok] typesafe` (con los modelos) y `[ok] azure`; código 0 |
| `uv run jevlab doctor --remote` sin red | `[n/d]` en los remotos; código 1 |
| `uv run jevlab doctor` sin red | Solo comprobaciones locales; no intenta conectarse |

Contrato completo: `contracts/cli-doctor.md`.

## US3: puertas de calidad y paridad

```
uv run pre-commit install
uv run pre-commit run --all-files     # todo en verde
```

Comprobar que cada puerta rechaza su violación (después, deshacer el cambio):

| Violación | Puerta que la rechaza |
| --- | --- |
| `src/jevlab/domain/x.py` importa `jevlab.adapters` | `poe lint-imports` |
| Mensaje de commit con `Co-Authored-By:` | gancho `commit-msg` |
| Un emoji en un `.md` | `poe check-writing` |
| Un archivo de `.specify/presets/jevlab-testing/` distinto de `presets/jevlab-testing/` | `poe check-presets` |
| `.agents/skills/speckit-tasks/SKILL.md` vuelto a la base (con «Tests are OPTIONAL») | `poe check-presets` |
| Una ruta `/home/usuario/...` en un archivo versionado | `poe check-paths` |
| Una clave con forma de API key en un archivo | gitleaks |

En CI: el workflow pasa en `ubuntu-latest` y `windows-latest` tras `git push`.

Paridad: ejecutar `/speckit-specify` de prueba en Claude Code y en Antigravity sobre una rama
desechable y comprobar que los dos generan la spec con las secciones de los presets.

## US4: README y lección

- `README.md` muestra qué es jev-lab, el estado con enlace al roadmap, el inicio rápido, el mapa de
  documentos y la licencia.
- `docs/lessons/000-metodo-sdd-y-entorno-reproducible.md` cubre el flujo SDD, las capas de reglas,
  la aplicación de un preset y los fallos típicos, enlazando `docs/setup.md`.
