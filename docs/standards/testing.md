# Estándar: testing

> Concreta: Constitución §IV · Exigido por: preset jevlab-testing · ADRs: *(ninguno)*

## 0. Definición: *cassette*

Una *cassette* (en el proyecto, «grabación») es un archivo que guarda una petición HTTP real a un
servicio externo y la respuesta que devolvió, sin cabeceras. Se graba una vez, con red y clave;
después, el test o la CLI la reproduce sin conectarse. El formato es propio y se graba en el
transporte de `httpx2` (`RecordingTransport` y `ReplayTransport` en `adapters/`), de modo que la
respuesta reproducida pasa por el mismo cliente y el mismo decodificador del SDK que en vivo
(`specs/001-triaje-ticket/contracts/recording.md`).

```
Grabación:     test -> adaptador -> red -> servicio -> respuesta real ─┐
                                                                      ▼
                                                               cassette (YAML)
                                                                      │
Reproducción:  test -> adaptador -> cassette ─────────────────────────┘  (sin red)
```

| Doble de prueba | Qué devuelve | Para qué capa |
| --- | --- | --- |
| Fake (`FakeJudge`) | Lo que el test programa | `application/` |
| *Cassette* | Lo que el servicio respondió de verdad | `adapters/` |

## 1. Un tipo de test por capa

**Regla.** Cada capa de `docs/standards/architecture.md` §1 se prueba aislada, con el tipo de test
de esta tabla. La gran mayoría de los tests son unitarios, sin red ni claves, y el conjunto de cada
módulo tarda menos de 1 s.

| Capa | Tipo de test | Cómo se aísla | Ejemplos |
| --- | --- | --- | --- |
| `domain/` | Unitario y de propiedades (`hypothesis`) | Sin dependencias: funciones y modelos Pydantic | La fórmula de confianza coincide con la oficial; las bandas de política son monótonas; `other` siempre va a revisión; una `DecisionSpec` sin escape falla su validación |
| `application/` | Unitario | Puertos inyectados con fakes en memoria (`FakeJudge` con respuestas programables, `InMemoryReviewQueue`, `FrozenClock`) | `TriageTicket` con confianza 0,4 encola revisión y audita; modo degradado si `JudgePort` lanza un error |
| `adapters/` | Contrato | *Cassettes*; SQLite en memoria; `httpx2.MockTransport` con respuestas sintéticas para HTTP | `TypeSafeJudge` traduce la respuesta del SDK a tipos de dominio; un 429 simulado provoca reintentos |
| `entrypoints/` | Unitario | `typer.testing.CliRunner`; `TestClient` de FastAPI con dependencias sustituidas | Códigos HTTP, validación de entrada, salida de la CLI |

**Motivo.** Si cada capa se prueba sola, un fallo señala su causa y la suite es rápida y gratuita.

**Correcto:** el test de `TriageTicket` usa `FakeJudge` y comprueba que el ticket va a revisión.

**Incorrecto:** el test de `TriageTicket` llama a TypeSafe para obtener una respuesta.

**Cómo se verifica:** revisión del plan (columna «Cómo se prueba aislada» del preset jevlab-arch)
y de las tareas.

## 2. Pirámide: tres niveles y cuántos de cada uno

**Regla.** Los tests se reparten en tres niveles. Los dos superiores tienen un número fijo; el
inferior crece hasta cubrir el código.

| Nivel | Qué cruza | Red | Marca | Cuántos |
| --- | --- | --- | --- | --- |
| Unitario y contrato | Una capa, con fakes o *cassettes* (§1) | No | *(ninguna)* | Los necesarios para alcanzar la cobertura de §4 por sí solos |
| Integración | Entrypoint -> aplicación -> adaptadores reales locales (SQLite temporal, YAML real, juez con *cassette*) | No | `integration` | 1 por historia: su escenario de aceptación principal |
| Extremo a extremo | La aplicación desplegada contra servicios reales | Sí | `live` | 1 humo por aplicación desplegable (CLI, API, stack operativo) |

Los tests de integración forman parte de la suite por defecto; los `live`, no (§6).

**Motivo.** Cuanto más alto el nivel, más lento y frágil es el test y peor señala la causa de un
fallo. La cobertura se mide sin los niveles superiores (§4), así que estos no pueden sustituir a
los unitarios: la proporción queda acotada por abajo con la cobertura y por arriba con su número
fijo.

**Correcto:** los umbrales de política se prueban con tests unitarios de dominio, y la historia
tiene un test de integración: `jevlab triage` con un ticket grabado termina en revisión y queda
auditado.

**Incorrecto:** un test de integración por cada umbral de la política.

**Cómo se verifica:** revisión de tareas; la CI informa del número de tests de cada marca
(`pytest -m integration --collect-only -q`).

## 3. Suite por defecto sin red

**Regla.** La suite por defecto se ejecuta con la red bloqueada: un test que intenta abrir una
conexión falla. Solo los tests `live` (§6) la habilitan.

**Motivo.** Sin red no hay claves, coste ni resultados que cambian de un día para otro.

**Correcto:** `pytest` con `--disable-socket` de `pytest-socket` en la configuración por defecto.

**Incorrecto:** un test unitario que pasa solo si hay conexión a internet.

**Cómo se verifica:** la CI ejecuta la suite sin credenciales y con la red bloqueada.

## 4. Cobertura mínima

**Regla.** La cobertura de líneas es de al menos el 80 % en todo el paquete y del 95 % en
`domain/`. Se mide solo con los tests unitarios y de contrato
(`pytest -m "not integration and not live"`).

**Motivo.** El dominio contiene las reglas que deciden; es puro y barato de probar, así que se le
exige más.

**Cómo se verifica:** la CI falla por debajo de cualquiera de los dos umbrales (`pytest-cov` para
el global y `coverage report --include` para `domain/`).

## 5. Tests antes que la implementación

**Regla.** En cada historia, las tareas de test van antes que las de implementación y fallan antes
de implementar (rojo -> verde -> refactor). Si el plan justifica otro orden, se respeta.

**Motivo.** Un test que nunca ha fallado no demuestra que comprueba algo.

**Cómo se verifica:** la plantilla de tareas del preset jevlab-testing; la CI falla si «Tests are
OPTIONAL» reaparece en la plantilla resuelta (`docs/governance.md` §5).

## 6. Pruebas contra servicios reales: marcadas y con tope

**Regla.** Un test que usa un servicio real lleva la marca `live`, queda fuera de la suite por
defecto y declara su tope de coste. Se ejecuta con `pytest -m live`. Cuántos hay: §2.

**Motivo.** Gastar dinero o claves es una decisión explícita, nunca un efecto de ejecutar los
tests.

**Correcto:** el humo diario de CI ejecuta `-m live` con un tope declarado.

**Incorrecto:** un test sin marca que llama a TypeSafe si encuentra la clave en el entorno.

**Cómo se verifica:** revisión de tareas. Cada test declara `@pytest.mark.live(max_usd=...)` y
`tests/live/conftest.py` aborta la sesión antes de empezar si la suma de los topes seleccionados
supera `JEVLAB_LIVE_BUDGET_USD` (0,10 USD por defecto) o si algún test no declara su tope.

## 7. Procedencia de los datos de prueba

**Regla.** Cada *cassette* registra el modelo y la fecha de la grabación. Los datos sintéticos se
etiquetan como tales. Cada respuesta grabada vive en un sitio según su uso:

| Uso | Dónde | Etiqueta |
| --- | --- | --- |
| Ejemplos reales que reproduce la CLI | `src/jevlab/recordings/<dominio>/<petición>/<nombre>.yaml`, dentro del paquete | `origen: sintetico` (el ticket es propio; la respuesta, real) |
| Respuestas inventadas solo para tests (errores, respuestas mal formadas) | `tests/contract/fixtures/` | `origen: sintetico` |
| Datasets de evaluación | `data/<dominio>/` | Según su procedencia y licencia |

**Motivo.** Una cifra sacada de una grabación vale para ese modelo y esa fecha; un dato inventado
no puede pasar por real.

**Correcto:** una *cassette* con `model: jev-1.13.0` y `recorded_on: 2026-10-20`; un conjunto de
tickets con `origen: sintetico`. El modelo es el identificador fijado (`jev-1.13.0`), nunca un
alias móvil.

**Incorrecto:** una *cassette* sin modelo ni fecha que alimenta un informe de precisión.

**Cómo se verifica:** un test recorre las *cassettes* y falla si falta el modelo o la fecha.
