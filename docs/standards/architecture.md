# Estándar: arquitectura

> Concreta: Constitución §III · Exigido por: preset jevlab-arch · ADRs: 0001

Monolito modular con arquitectura hexagonal (puertos y adaptadores) en un solo paquete Python,
`jevlab`, bajo `src/jevlab/`.

## 1. Capas y regla de dependencias

**Regla.** El código se reparte en cinco capas y las dependencias van solo en estas direcciones:

```
entrypoints -> application -> domain
adapters    -> ports
application -> ports
```

| Capa | Contiene |
| --- | --- |
| `domain/` | `DecisionSpec`, política, confianza y composición |
| `application/` | Casos de uso (`TriageTicket`, `GuardInput`…) |
| `ports/` | Interfaces de los efectos externos |
| `adapters/` | Implementaciones de los puertos: TypeSafe, cassettes, Azure, almacenamiento, YAML |
| `entrypoints/` | CLI (`cli/`) y API (`api/`) |

**Motivo.** Si el dominio no conoce los adaptadores, se puede cambiar de proveedor, probar sin red
y comparar con un baseline sin tocar la lógica.

**Correcto:** `application/triage.py` importa `ports.judge.JudgePort`.

**Incorrecto:** `domain/policy.py` importa `adapters.typesafe`.

**Cómo se verifica:** contratos de `import-linter` (`.importlinter`) en pre-commit y CI.

## 2. Dominio puro

**Regla.** `domain/` no hace entrada/salida ni importa SDKs de proveedores: solo funciones y
modelos Pydantic.

**Motivo.** Un dominio puro se prueba con tests unitarios y de propiedades, rápidos y sin
dependencias.

**Correcto:** `apply_policy(answer, thresholds) -> Outcome`, que recibe los datos ya cargados.

**Incorrecto:** `apply_policy()` lee el YAML de umbrales del disco.

**Cómo se verifica:** contrato de `import-linter` que prohíbe a `domain` importar `adapters`,
`typesafe` y `openai`.

## 3. Puertos como `typing.Protocol`

**Regla.** Cada puerto es un `typing.Protocol`. Cada adaptador real tiene un fake en memoria que
cumple el mismo protocolo.

**Motivo.** Los fakes sustituyen al proveedor en los tests, y `mypy --strict` comprueba que real y
fake tienen la misma forma.

**Correcto:**

```python
class JudgePort(Protocol):
    def choose(self, spec: DecisionSpec, state: State) -> ChoiceAnswer: ...
```

**Incorrecto:** una clase base abstracta con lógica compartida entre adaptadores.

**Cómo se verifica:** `mypy --strict` en pre-commit y CI.

## 4. Inyección por constructor

**Regla.** Los casos de uso reciben sus puertos por constructor. No hay singletons ni llamadas
globales al SDK. El cableado se hace solo en `entrypoints/`.

**Correcto:** `TriageTicket(judge=judge, queue=queue, clock=clock)`.

**Incorrecto:** `TriageTicket` crea un `TypeSafeClient()` dentro de su método.

**Cómo se verifica:** tests de aplicación con fakes inyectados; revisión del plan (columna «Cómo se
prueba aislada»).

## 5. Tiempo, azar e IDs por puertos

**Regla.** La hora, los números aleatorios y los identificadores se obtienen de puertos (`Clock`,
`IdGenerator`), nunca de `datetime.now()`, `random` o `uuid4()` directos fuera de `adapters/`.

**Motivo.** Tests deterministas y reproducibles (§IV).

**Correcto:** `clock.now()` con `FrozenClock` en los tests.

**Incorrecto:** `datetime.now()` en un caso de uso.

**Cómo se verifica:** revisión de código. La comprobación automática se decide al configurar el
lint en la spec de cimientos.

## 6. Una sola definición de decisión

**Regla.** Cada `DecisionSpec` vive en `src/jevlab/specs/<dominio>/<decision>.yaml` y todos sus
consumidores (CLI, API, evaluación, laboratorio de fallos) lo cargan con el mismo cargador.

**Motivo.** Lo que se evalúa es exactamente lo que se despliega.

**Correcto:** `jevlab triage` y `jevlab eval` llaman a `load_spec("soporte/cola-destino")`.

**Incorrecto:** la evaluación copia las preguntas en su propio archivo.

**Cómo se verifica:** un test comprueba que servicio, evaluación y laboratorio cargan la misma
definición.
