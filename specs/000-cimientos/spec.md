# Feature Specification: Cimientos de jev-lab

**Feature Branch**: `000-cimientos`

**Created**: 2026-10-12

**Status**: Draft

**Input**: User description: "000 Cimientos de jev-lab: entorno reproducible en Linux y Windows,
esqueleto hexagonal vacío, puertas de calidad en pre-commit y CI, documentación de puesta en
marcha, lección y comprobación de humo `jevlab doctor`. Fuente: sección «000: Cimientos» de
`docs/roadmap.md`."

Esta spec es la de cimientos: no entrega un corte vertical (Constitución §VII), pero sí historias
demostrables y una lección. Las herramientas que nombra (uv, Python 3.13, pre-commit, Spec Kit) no
son elecciones de esta spec: vienen decididas por la constitución, los estándares y los ADRs, y
aquí son requisitos de entrada.

## Clarifications

### Session 2026-10-12

- Q: ¿Con qué licencia se publica el repositorio público? -> A: Apache-2.0 para todo el
  repositorio (código y documentación).
- Q: ¿Qué comprobaciones se ejecutan al hacer commit y cuáles solo en CI? -> A: todas en los dos
  sitios; pre-commit ejecuta también la suite completa con cobertura.
- Q: Si se piden las comprobaciones remotas de `jevlab doctor` y no hay red, ¿termina con error?
  -> A: sí; con la opción remota, «no disponible» cuenta como fallo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Poner en marcha el proyecto desde un clon limpio (Priority: P1)

Como usuario inicial de Jev, quiero instalar jev-lab desde un clon limpio, en Linux o en Windows,
siguiendo solo `docs/setup.md`, para empezar a probar Jev sin configurar nada a mano ni gastar
dinero ni claves.

**Why this priority**: Sin un entorno reproducible no se puede construir ni verificar nada más;
es la base de todas las specs siguientes (Constitución §VI).

**Independent Test**: En un clon nuevo, en cada sistema operativo, seguir solo `docs/setup.md` y
ejecutar la suite por defecto con la red desactivada; debe pasar.

**Acceptance Scenarios**:

1. **Given** un clon limpio en Linux con los requisitos de `docs/setup.md`, **When** la persona
   ejecuta los comandos de instalación y la suite por defecto, **Then** la suite pasa sin red ni
   claves.
2. **Given** un clon limpio en Windows, **When** sigue los mismos pasos de `docs/setup.md`,
   **Then** obtiene el mismo resultado, y los scripts de Spec Kit funcionan con el `python3` que
   la guía indica.
3. **Given** el entorno instalado, **When** la persona ejecuta un test que intenta abrir una
   conexión de red, **Then** ese test falla.

---

### User Story 2 - Comprobar el entorno con `jevlab doctor` (Priority: P2)

Como usuario inicial de Jev, quiero ejecutar `jevlab doctor` y ver, requisito a requisito, si mi
entorno está listo (el `python3` de Spec Kit, el intérprete del proyecto, las claves y, si lo
pido, el acceso a TypeSafe y a Azure OpenAI), para saber qué arreglar y cómo antes de hacer mi
primera llamada a Jev.

**Why this priority**: Convierte los fallos típicos de puesta en marcha en mensajes accionables y
deja comprobado el acceso a los dos proveedores antes de la spec 001.

**Independent Test**: Simular cada requisito ausente (sin `python3`, versión antigua, sin `.env`,
clave vacía) y comprobar que `jevlab doctor` lo detecta y da su instrucción; con claves reales,
comprobar las verificaciones remotas.

**Acceptance Scenarios**:

1. **Given** un entorno completo, **When** la persona ejecuta `jevlab doctor`, **Then** cada
   comprobación local aparece como correcta y el comando termina con éxito.
2. **Given** un entorno sin `.env` o con una clave vacía, **When** ejecuta `jevlab doctor`,
   **Then** el comando señala la clave que falta, remite a `.env.example` y termina con error,
   sin mostrar nunca el valor de ninguna clave.
3. **Given** claves válidas, **When** pide las comprobaciones remotas con la opción explícita,
   **Then** el comando lista los modelos de Jev disponibles y confirma que el deployment de Azure
   responde.
4. **Given** una máquina sin red, **When** ejecuta `jevlab doctor` sin esa opción, **Then** se
   hacen todas las comprobaciones locales y el comando no intenta conectarse.

---

### User Story 3 - Puertas de calidad automáticas en cada commit y en CI (Priority: P3)

Como mantenedor de jev-lab, quiero que cada cambio, mío o de un agente, pase automáticamente las
reglas del proyecto al hacer commit y en CI, en Linux y en Windows, y trabajar con Claude Code o
con Antigravity sobre los mismos artefactos, para no romper la constitución ni los estándares sin
darme cuenta, use el agente que use.

**Why this priority**: Las reglas solo valen si se aplican igual con cualquier agente o sin
ninguno (Constitución §VI, ADR-0002); sin estas puertas, los estándares escritos en la fase HITL
se erosionan desde la spec 001.

**Independent Test**: Introducir, una a una, una violación de cada regla de la lista de FR-007 y
comprobar que la puerta correspondiente la rechaza en local y en CI; ejecutar `/speckit-specify`
de prueba en cada agente.

**Acceptance Scenarios**:

1. **Given** un cambio en que `domain/` importa un adaptador, **When** se intenta hacer commit,
   **Then** la comprobación de dependencias lo rechaza.
2. **Given** un mensaje de commit con una línea `Co-Authored-By`, **When** se intenta hacer commit,
   **Then** el hook de mensaje lo rechaza.
3. **Given** la copia instalada de un preset distinta de su fuente, o «Tests are OPTIONAL» en la
   skill de un agente, **When** se ejecutan las puertas, **Then** fallan e indican qué preset o
   agente se ha desincronizado.
4. **Given** un cambio que cumple todas las reglas, **When** se ejecuta la CI, **Then** pasa en
   Linux y en Windows.
5. **Given** cada uno de los dos agentes, **When** se ejecuta `/speckit-specify` de prueba,
   **Then** los dos generan la spec desde la misma plantilla resuelta.

---

### User Story 4 - Entender el método con el README y la lección (Priority: P4)

Como usuario inicial de Jev, quiero leer `README.md` y la lección 000 para entender qué es
jev-lab y cómo se construye: el flujo de Spec Kit, dónde vive cada regla y cómo se aplica un
preset.

**Why this priority**: Es el valor de aprendizaje de la spec (Constitución §VII).

**Independent Test**: Una persona sin contexto previo, solo con `README.md`, `docs/setup.md` y la
lección, explica el flujo SDD y aplica el procedimiento de un preset.

**Acceptance Scenarios**:

1. **Given** el repositorio, **When** una persona abre `README.md`, **Then** encuentra qué es
   jev-lab, el estado con enlace al roadmap, un inicio rápido de 3 o 4 comandos enlazado a
   `docs/setup.md`, un mapa de documentos y la licencia.
2. **Given** la lección 000, **When** la persona la sigue, **Then** aprende el flujo SDD, las capas
   de reglas, el entorno de dos intérpretes y los fallos típicos con su mitigación.

---

### Edge Cases

- `python3` no existe o es anterior a 3.8 (habitual en Windows): `docs/setup.md` y `jevlab doctor`
  indican el enlace `python3.exe`.
- El `python3` de Spec Kit no tiene PyYAML: la composición de plantillas falla; la guía indica
  cómo resolverlo (`docs/governance.md` §5, nota técnica).
- Un clon en Windows convierte finales de línea: las reglas de `.gitattributes` mantienen LF salvo
  en los archivos de Windows.
- `specify integration use` copia los scripts de shell del sistema junto a los de Python: no se
  versionan y la puerta de presets lo detecta.
- `specify integration upgrade --force` devuelve a la base las skills del agente no activo: la
  puerta de paridad lo detecta.
- Sin red durante `jevlab doctor` con comprobaciones remotas: el comando informa «no disponible»
  para esas comprobaciones, distingue error de red de clave inválida, no se cuelga y termina con
  error.
- El paquete casi no tiene código: los umbrales de cobertura se aplican igual desde el principio.
- Un test intenta usar la red sin la marca `live`: falla.

## Requirements *(mandatory)*

### Functional Requirements

**Entorno**
- **FR-001**: El proyecto MUST instalarse desde un clon limpio en Linux y en Windows siguiendo solo
  `docs/setup.md`, con Python 3.13 gestionado por uv para el código del proyecto y un `python3`
  ≥ 3.8 con PyYAML para Spec Kit.
- **FR-002**: Todas las tareas del proyecto (tests, lint, comprobaciones) MUST ejecutarse con el
  mismo comando en los dos sistemas, sin depender de bash ni de cmd.
- **FR-003**: El repositorio MUST fijar finales de línea por tipo de archivo y no contener enlaces
  simbólicos.
- **FR-004**: El repositorio MUST incluir `.env.example` con las variables de TypeSafe y de Azure
  OpenAI sin valores; `.env` MUST quedar fuera del control de versiones.

**Estructura**
- **FR-005**: El paquete MUST tener las cinco capas de `docs/standards/architecture.md` §1, vacías
  salvo lo que necesite `jevlab doctor`, y la regla de dependencias entre capas MUST comprobarse
  automáticamente.
- **FR-006**: Los tests MUST organizarse por nivel según `docs/standards/testing.md` §2 (unitario,
  contrato, integración y `live`), con la red bloqueada en la suite por defecto y los umbrales de
  cobertura aplicados.

**Puertas de calidad**
- **FR-007**: Pre-commit y CI MUST ejecutar las mismas comprobaciones, incluida la suite completa
  con cobertura en cada commit, con el mismo resultado en Linux y Windows:
  1. estilo y tipos estrictos;
  2. dependencias entre capas;
  3. suite por defecto con la red bloqueada y cobertura (`docs/standards/testing.md` §3 y §4);
  4. ausencia de secretos;
  5. redacción de la documentación (`docs/standards/writing.md`);
  6. formato del mensaje de commit, sin atribuciones de agentes
     (`docs/standards/version-control.md`);
  7. presets: copia instalada igual a la fuente, sin «Tests are OPTIONAL» en la plantilla resuelta
     ni en las skills, skills de los comandos sustituidos iguales en los dos agentes y sin
     scripts de shell en `.specify/scripts/`;
  8. `CLAUDE.md` solo importa `AGENTS.md`;
  9. ausencia de rutas absolutas de máquina.
- **FR-018**: Los dos agentes MUST ejecutar el flujo de Spec Kit sobre los mismos artefactos y con
  la misma plantilla resuelta (ADR-0002).
- **FR-008**: Cada puerta que falla MUST indicar qué regla se incumple y dónde.
- **FR-009**: La lógica de cada puerta MUST vivir en una tarea del repositorio, invocable igual
  desde pre-commit, CI y cualquier agente (Constitución §VI).

**Comprobación de humo**
- **FR-010**: `jevlab doctor` MUST comprobar en local: `python3` ≥ 3.8 con PyYAML para Spec Kit,
  intérprete del proyecto 3.13 y presencia de las claves de `.env.example`.
- **FR-011**: `jevlab doctor` MUST comprobar en remoto solo con una opción explícita: modelos de
  Jev disponibles con la clave configurada (incluido el modelo por defecto) y respuesta del
  deployment de Azure OpenAI con una llamada mínima. Sin esa opción, el comando no usa la red.
- **FR-012**: Cada comprobación de `jevlab doctor` MUST mostrar su estado (correcto, falla, no
  disponible) y, si falla, cómo arreglarla; el comando MUST terminar con error si alguna falla.
  Con la opción remota, una comprobación remota «no disponible» cuenta como fallo.
- **FR-013**: `jevlab doctor` MUST NOT mostrar valores de claves ni *payloads*
  (`docs/standards/security.md` §2).

**Documentación**
- **FR-014**: `docs/setup.md` MUST cubrir la puesta en marcha en Linux y Windows: uv, Python 3.13,
  `python3` y PyYAML para Spec Kit, el enlace `python3.exe` en Windows, Git Bash, los dos agentes y
  los pasos de paridad que hoy están en el roadmap.
- **FR-015**: `README.md` MUST presentar el proyecto a personas (no a agentes): qué es, estado con
  enlace al roadmap, inicio rápido de 3 o 4 comandos, mapa de documentos y licencia.
- **FR-019**: El repositorio MUST incluir `LICENSE` con la licencia Apache-2.0, que cubre código y
  documentación.
- **FR-016**: La lección 000 MUST cubrir el flujo SDD, las capas de reglas, cómo se aplica un
  preset paso a paso (caso `jevlab-testing`), el entorno y los fallos típicos con su mitigación,
  reutilizando `docs/setup.md` en vez de repetirlo.

**Integración continua**
- **FR-017**: La CI MUST ejecutarse en Linux y en Windows en cada cambio, en GitHub Actions sobre
  un repositorio público de GitHub, que esta spec crea como remoto. Ningún token, clave o acceso
  MUST ser visible para el público (`docs/standards/security.md` §5).

### Key Entities

- **Puerta de calidad**: una regla automatizada; tiene el estándar o principio del que deriva, la
  tarea que la ejecuta y dónde se aplica (pre-commit, CI o ambos).
- **Comprobación de entorno**: un requisito que verifica `jevlab doctor`; tiene ámbito (local o
  remoto), estado e instrucción de arreglo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una persona sin contexto pone en marcha el proyecto desde un clon limpio en menos de
  15 minutos en Linux y en Windows, siguiendo solo `docs/setup.md`.
- **SC-002**: La suite por defecto pasa sin red ni claves y tarda menos de 1 minuto en el runner
  `ubuntu-latest` de la CI.
- **SC-003**: El 100 % de las violaciones de la lista de FR-007 se rechazan, en local y en CI, con
  un mensaje que nombra la regla.
- **SC-004**: `jevlab doctor` detecta el 100 % de los requisitos ausentes simulados y da su
  instrucción de arreglo.
- **SC-005**: Los dos agentes ejecutan el flujo de Spec Kit sobre los mismos artefactos, sin pasos
  propios de un solo agente.
- **SC-006**: Ningún archivo versionado contiene secretos, rutas absolutas de máquina ni enlaces
  simbólicos.

## Assumptions

- La persona tiene Git, uv y un Python 3.13 instalables sin privilegios de administrador; en
  Windows usa Git Bash para los comandos de Git.
- Spec Kit, sus dos integraciones, `AGENTS.md`, `CLAUDE.md`, la constitución v0.3.1, los presets,
  los estándares y los ADR-0001 y 0002 ya existen y quedan fuera de alcance.
- Las comprobaciones remotas de `jevlab doctor` tienen un coste despreciable: listar modelos
  (previsiblemente gratis, a confirmar en la documentación de TypeSafe) y una llamada mínima a
  Azure.
- El mantenedor crea el repositorio en GitHub; el plan indica cómo, porque `gh` no está instalado
  en la máquina Linux actual.
- La CI de esta spec no usa claves: las comprobaciones remotas y los tests `live` quedan fuera de
  ella. El primer job con *secrets* llega con la spec que añada un humo `live` a la CI.

## Decisiones Jev (jev-lab) *(mandatory si la feature pregunta al modelo)*

No aplica: esta spec no pregunta nada al modelo; `jevlab doctor` solo comprueba el acceso.

## Corte vertical y lección (jev-lab) *(mandatory)*

> Deriva de: Constitución §VII · Perfiles de usuario: `docs/personas.md`

- **Persona principal**: Usuario inicial de Jev
- **Capacidad de extremo a extremo**: no aplica corte vertical.

| Historia | Persona | Cómo se demuestra (comando o petición) |
| --- | --- | --- |
| US1 | Usuario inicial de Jev | Clon limpio + pasos de `docs/setup.md` + `uv run poe test` sin red |
| US2 | Usuario inicial de Jev | `uv run jevlab doctor` con el entorno completo y con una clave vacía |
| US3 | Mantenedor de jev-lab | Commit con una violación de cada regla; CI en Linux y Windows; `/speckit-specify` de prueba en cada agente |
| US4 | Usuario inicial de Jev | `README.md` y la lección |

- **Número de historias**: 4.
- **Fuera de alcance (YAGNI)**: código de dominio y de aplicación, `DecisionSpec`, adaptadores de
  juez, cassettes, API, Docker, evaluación e informes; cualquier pregunta al modelo. Llegan con la
  spec 001 y siguientes.
- **Lección**: `docs/lessons/000-metodo-sdd-y-entorno-reproducible.md`.
  - Qué se aprende: el flujo de Spec Kit; dónde vive cada regla (constitución, presets,
    estándares, ADRs) y cómo se rastrea hasta un principio; cómo se aplica un preset (`replace`,
    composición por prioridad, agente único activo); el entorno de dos intérpretes.
  - Qué puede fallar y su mitigación: `python3` antiguo o sin PyYAML; un preset con comandos
    registrado solo en el agente activo; `integration upgrade --force` que devuelve skills a la
    base; los scripts de shell que copia `integration use`; finales de línea en Windows.
