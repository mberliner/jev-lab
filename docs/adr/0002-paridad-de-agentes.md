---
status: aceptada
date: 2026-10-12
---

# ADR-0002: paridad entre Claude Code y Antigravity

## Contexto y problema

jev-lab se desarrolla con Spec-Driven Development y agentes de código. La constitución (§VI) exige
que todo flujo funcione igual con cualquier agente soportado, con una única fuente de
instrucciones y con hooks, comandos y puertas de calidad independientes del agente. Se usan dos
agentes: Claude Code y Antigravity (`agy`).

¿Cómo se configura el repositorio para que los dos trabajen sobre los mismos artefactos y con las
mismas reglas, sin que diverjan?

## Factores de decisión

- Mismos artefactos SDD (constitución, plantillas, specs) para los dos agentes (§VI).
- Una sola fuente de instrucciones, sin copias que se desincronicen (§VI).
- Un clon nuevo funciona sin configuración externa (§VI).
- Las reglas se cumplen igual con cualquier agente, o sin ninguno.
- Mantenimiento bajo al actualizar Spec Kit y los presets.

## Opciones consideradas

1. Las dos integraciones de Spec Kit en el repo, con `AGENTS.md` como fuente única y la lógica en
   tareas del repo.
2. Un solo agente (Claude Code).
3. Instrucciones separadas por agente (`CLAUDE.md` y `AGENTS.md` con contenido propio).
4. Ninguna integración versionada: cada persona instala la de su agente.

## Decisión

Opción 1:
- Las integraciones `claude` (`.claude/skills/`) y `agy` (`.agents/skills/`) se instalan en el
  mismo repo y comparten `.specify/` y `specs/`. La integración por defecto es `claude`.
- `AGENTS.md` es la única fuente de instrucciones; `CLAUDE.md` solo contiene `@AGENTS.md`.
- Un hook o comando de agente solo se admite si su lógica vive en una tarea del repo y existe de
  forma equivalente en los dos agentes. Las puertas de calidad son pre-commit y CI.

Es la única opción que cumple los cuatro primeros factores.

### Consecuencias

- Buena: cualquiera de los dos agentes retoma el trabajo del otro con los mismos artefactos.
- Buena: las reglas no dependen del agente: pre-commit y CI las aplican a todo commit.
- Mala: `agy` no está declarada como segura para convivir con otras integraciones; se instala con
  `--force`.
- Mala: Spec Kit registra los comandos de un preset solo en el agente activo. Instalar un preset
  con comandos exige pasar por cada agente (`docs/governance.md` §5, «Instalar o cambiar un
  preset»).
- Mala: las skills de Spec Kit están duplicadas en `.claude/skills/` y `.agents/skills/`, y se
  renuncia a las funciones propias de un solo agente.

### Confirmación

- `specify integration status` muestra las dos integraciones.
- `.specify/presets/.registry` lista cada comando de preset para los dos agentes.
- Un test comprueba que `CLAUDE.md` solo importa `AGENTS.md`.
- La spec de cimientos ejecuta `/speckit-specify` de prueba en cada agente.

## Ventajas e inconvenientes de las opciones

### 1. Dos integraciones y fuente única

- Buena: artefactos e instrucciones compartidos.
- Mala: instalación con `--force` y un paso extra por agente en los presets con comandos.

### 2. Un solo agente

- Buena: lo más sencillo; sin duplicados ni pasos extra.
- Mala: ata el proyecto a una herramienta, en contra de §VI.

### 3. Instrucciones separadas por agente

- Buena: cada agente recibe instrucciones a su medida.
- Mala: dos fuentes que acaban divergiendo; un agente sigue reglas que el otro no conoce.

### 4. Integraciones sin versionar

- Buena: el repo no lleva archivos de agente.
- Mala: un clon nuevo no funciona sin pasos externos y cada persona puede tener una versión
  distinta de las skills.

## Más información

- Constitución §VI (`.specify/memory/constitution.md`).
- Referencia de integraciones de Spec Kit:
  <https://github.github.io/spec-kit/reference/integrations.html>.
- Procedimientos de presets y actualización: `docs/governance.md` §5.
