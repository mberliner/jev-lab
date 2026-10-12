---
status: aceptada
date: 2026-10-12
---

# ADR-0001: monolito modular con arquitectura hexagonal

## Contexto y problema

jev-lab sirve decisiones Jev por CLI y API, las evalúa con datos propios, las compara con un
baseline de Azure OpenAI y estudia sus modos de fallo. La constitución (§III) exige que la lógica
de dominio no haga entrada/salida, que todo efecto externo pase por una interfaz sustituible y que
la misma definición de decisión se use para servir, evaluar y probar. La §IV exige que la suite
por defecto se ejecute sin red, sin claves y sin coste.

¿Qué estructura de código cumple esas exigencias sin complicar un laboratorio de un solo equipo?

## Factores de decisión

- Cambiar de juez (TypeSafe, *cassette*, Azure, fake) sin tocar la lógica (§III).
- Tests rápidos y sin red en todas las capas (§IV).
- Una sola definición de decisión para todos los consumidores (§III).
- Adaptadores que evolucionan: SQLite y memoria hasta la spec 006; Postgres y Redis en la 007.
- Sencillez: un equipo, un dominio, un paquete desplegable (§VII, YAGNI).
- Valor didáctico: que el código muestre dónde juzga el modelo y dónde decide el código (§I).

## Opciones consideradas

1. Monolito modular con arquitectura hexagonal (puertos y adaptadores).
2. Capas clásicas: presentación, servicios y acceso a datos.
3. Un script por caso de uso que llama directamente al SDK.
4. Microservicios, uno por decisión o por aplicación.

## Decisión

Opción 1: monolito modular hexagonal en un solo paquete, `jevlab`, con las capas `domain`,
`application`, `ports`, `adapters` y `entrypoints`. Es la única opción que cumple a la vez los
tres primeros factores sin añadir la operación de varios servicios.

Las reglas concretas están en `docs/standards/architecture.md`.

### Consecuencias

- Buena: el juez se elige al cablear en `entrypoints/`; los tests usan fakes o *cassettes* y la
  comparación con Azure usa el mismo caso de uso.
- Buena: el dominio es puro y se prueba con tests unitarios y de propiedades.
- Buena: pasar a Postgres y Redis en la spec 007 solo añade adaptadores.
- Mala: más archivos e indirección que un script: cada efecto externo necesita puerto, adaptador
  real y fake. Se limita creando puertos solo para efectos externos, no para lógica interna.
- Mala: la regla de dependencias hay que vigilarla; sin comprobación automática se erosiona.

### Confirmación

`import-linter` comprueba la regla de dependencias y `mypy --strict` que real y fake cumplen el
mismo protocolo, en pre-commit y CI (`docs/standards/architecture.md` §1 y §3).

## Ventajas e inconvenientes de las opciones

### 1. Monolito modular hexagonal

- Buena: proveedor sustituible y dominio sin entrada/salida por construcción.
- Buena: un solo despliegue y un solo repositorio.
- Mala: indirección y código de puertos y fakes.

### 2. Capas clásicas

- Buena: conocida y con menos piezas.
- Mala: la capa de servicios depende de la de datos y del SDK; sustituir el proveedor o probar sin
  red exige *mocks* por todas partes.

### 3. Un script por caso de uso

- Buena: lo más rápido para empezar.
- Mala: la definición de cada decisión y las llamadas al SDK se repiten en servir, evaluar y
  probar, que es justo lo que prohíbe §III.

### 4. Microservicios

- Buena: despliegue y escalado independientes.
- Mala: red, contratos y operación de varios servicios sin necesidad: un equipo y un dominio.

## Más información

- Constitución §I, §III, §IV y §VII (`.specify/memory/constitution.md`).
- Arquitectura hexagonal, de Alistair Cockburn: <https://alistair.cockburn.us/hexagonal-architecture/>.
