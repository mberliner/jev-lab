# Contrato: `jevlab doctor`

## Invocación

```
uv run jevlab doctor            # solo comprobaciones locales; no usa la red
uv run jevlab doctor --remote   # añade TypeSafe y Azure OpenAI
```

## Comprobaciones

| Nombre | Ámbito | Correcto si | Arreglo si falla |
| --- | --- | --- | --- |
| `speckit-python` | local | `python3` (o `SPECKIT_PYTHON_EXECUTABLE`) existe, es ≥ 3.8 e importa `yaml` | Enlace `python3.exe` o instalar PyYAML, según `docs/setup.md` |
| `project-python` | local | El intérprete que ejecuta `jevlab` es 3.13 | `uv sync` en la raíz del repo |
| `env-keys` | local | Cada variable de `.env.example` tiene valor en `.env` o en el entorno | Copiar `.env.example` a `.env` y rellenar las que faltan (se nombran, sin valores) |
| `typesafe` | remote | `models.list()` devuelve modelos y el modelo por defecto figura o es un alias documentado | Según el error: clave inválida, modelo inexistente o red |
| `azure` | remote | El deployment responde a una llamada mínima | Según el error: clave, endpoint, deployment, versión de API o red |

## Salida

Una línea por comprobación, en el orden de la tabla, y una línea de resumen. Solo ASCII.

```
[ok]   speckit-python  python3 3.8.10 con PyYAML 5.3.1
[ok]   project-python  Python 3.13.11
[fail] env-keys        faltan: AZURE_OPENAI_API_KEY
       arreglo: copia .env.example a .env y rellena las variables que faltan
[n/d]  typesafe        no disponible: sin conexión con api.typesafe.ai
       arreglo: comprueba la red y vuelve a ejecutar con --remote
Resultado: 1 falla, 1 no disponible
```

- Nunca se muestran valores de claves, el endpoint completo de Azure ni el contenido de las
  respuestas (FR-013).
- Códigos de salida: `0` todo correcto; `1` alguna falla, o algún remoto no disponible con
  `--remote` (`data-model.md`, `DoctorReport.exit_code()`).
- Sin `--remote`, el comando no abre ninguna conexión de red (FR-011).
