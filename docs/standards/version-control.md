# Estándar: control de versiones

> Concreta: Constitución §VI · Exigido por: *(sin preset)* · ADRs: *(ninguno)*

Convenciones para los mensajes de commit y las descripciones de PR. Se aplican igual a lo que
escribe una persona y a lo que genera un agente.

## 1. Formato del mensaje: Conventional Commits

**Regla.** Cada mensaje de commit MUST seguir [Conventional Commits 1.0.0](https://www.conventionalcommits.org/es/v1.0.0/):

```text
tipo(ámbito): resumen

cuerpo opcional

pies opcionales
```

- **Resumen:** en español, en imperativo o nominal y sin punto final. Su longitud SHOULD no pasar
  de unos 72 caracteres; es una recomendación, no se rechaza un commit por superarla.
- **Tipos:** `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`, `chore`.
- **Ámbito** (opcional): la zona afectada, por ejemplo `constitution`, `standards`, `spec-001`,
  `domain`, `cli` o `api`.
- **Cuerpo** (opcional): viñetas que explican qué cambia y por qué.
- **Cambios incompatibles:** `!` tras el tipo o el ámbito, y un pie `BREAKING CHANGE: …`.

**Motivo.** El historial queda legible y filtrable por tipo y ámbito, y permite generar un
changelog sin trabajo manual.

**Correcto:**

```text
docs(constitution): HITL paso 3 y estándar de redacción

- VI: hooks y comandos solo con implementación neutral
- VII: la spec 000 también lleva lección
```

**Incorrecto:**

```text
Actualizo varias cosas de la constitución.
```

## 2. Sin atribución de agentes

**Regla.** Los mensajes de commit y las descripciones de PR MUST NOT incluir firmas ni
atribuciones de agentes o herramientas, como `Co-Authored-By: <agente>` o `Generated with <herramienta>`.

**Motivo.** El proyecto es neutral respecto del agente (§VI). La autoría la asume la persona que
integra el cambio, que es quien lo aprueba. Una firma de herramienta no aporta información útil
al historial y lo hace depender del agente que se usó.

## Verificación

- **Automática:** un hook `commit-msg` en pre-commit valida las dos reglas: el formato de
  Conventional Commits y la ausencia de pies de atribución. La longitud del resumen como mucho
  genera un aviso, nunca un rechazo. Se implementa en la spec 000.
- **Revisión:** «¿el mensaje dice qué cambia y por qué, sin firmas?».
