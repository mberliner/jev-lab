# jev-lab

Laboratorio progresivo para aprender y demostrar Jev, el modelo de decisión tipada de TypeSafe
(Choice, Score y Noul), desde lo básico hasta técnicas de producción.

## Qué es

jev-lab es un proyecto de aprendizaje con rigor. Cada entrega es un corte vertical que una persona
puede ejecutar (una CLI, una API, un informe) y trae su lección: qué se aprende, cómo se ejecuta y
qué puede fallar.

Tres ideas lo guían:

- **El modelo juzga, el código decide.** Jev responde preguntas atómicas; la aritmética, las
  fechas, los permisos y la política se calculan en código.
- **Escape y confianza.** Cada Choice tiene una opción de escape, y solo se automatiza lo que
  supera un umbral de confianza según el riesgo.
- **Evidencia antes que afirmación.** Tests sin red ni claves por defecto; las pruebas contra
  servicios reales están marcadas y tienen tope de coste.

Se construye con Spec-Driven Development ([Spec Kit](https://github.com/github/spec-kit)): cada
funcionalidad pasa por especificación, plan, tareas e implementación, con una constitución que fija
los principios. Funciona igual en Linux y en Windows, y con Claude Code o con Antigravity.

## Estado

Spec 000, «Cimientos»: entorno reproducible, esqueleto hexagonal, puertas de calidad en pre-commit
y CI, y la comprobación `jevlab doctor`. El plan completo y el punto de reanudación están en el
[roadmap](docs/roadmap.md).

## Inicio rápido

Requisitos: Git, [uv](https://docs.astral.sh/uv/) y un `python3` 3.8 o superior con PyYAML para
Spec Kit. Los pasos completos para Linux y Windows están en la
[guía de puesta en marcha](docs/setup.md).

```
git clone <url-del-repo> jev-lab && cd jev-lab
uv sync
uv run poe test
uv run jevlab doctor
```

## Mapa de documentos

| Documento | Para qué |
| --- | --- |
| [docs/setup.md](docs/setup.md) | Puesta en marcha en Linux y Windows, claves y agentes |
| [docs/lessons/](docs/lessons/000-metodo-sdd-y-entorno-reproducible.md) | Una lección por spec; la 000 explica el método y el entorno, y la 001, las tres primitivas y la confianza |
| [docs/roadmap.md](docs/roadmap.md) | Plan de specs y estado actual |
| [Constitución](.specify/memory/constitution.md) | Principios que cumple todo el proyecto |
| [docs/governance.md](docs/governance.md) | Dónde vive cada regla: constitución, presets y estándares |
| [docs/standards/](docs/standards/architecture.md) | Cómo se hace: arquitectura, testing, seguridad, redacción, commits |
| [docs/adr/](docs/adr/0001-arquitectura-hexagonal.md) | Decisiones de arquitectura con sus alternativas |
| [docs/personas.md](docs/personas.md) | Perfiles de usuario a los que sirve cada spec |
| [specs/](specs/000-cimientos/spec.md) | Especificación, plan y tareas de cada feature |
| [AGENTS.md](AGENTS.md) | Instrucciones para agentes de código (no para personas) |

## Licencia

[Apache-2.0](LICENSE), para el código y la documentación.
