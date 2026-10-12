# Preset `jevlab-decision`

> Deriva de: Constitución §I, §II, §III y §IV · Estándar: `docs/standards/decision-design.md` ·
> Gobernanza: `docs/governance.md` §4 y §5

Hace que cada decisión que se pide a Jev quede definida en la spec y diseñada en el plan antes de
escribir código.

| Plantilla | Estrategia | Qué añade |
| --- | --- | --- |
| `spec-template` | `append` | Sección «Decisiones Jev»: tabla de decisiones (pregunta, primitiva, opciones con escape, acción y riesgo, destino del escape), lo que decide el código y qué ve cada persona |
| `plan-template` | `append` | Sección «Diseño de decisiones»: `DecisionSpec`, modelo fijado, estado mínimo, umbrales y su justificación, revisión de I |

Decisiones de diseño:
- La spec dice **qué** se decide y qué pasa con el escape, porque es comportamiento visible; el
  plan dice **cómo** se implementa.
- La sección es obligatoria solo si la feature pregunta al modelo; si no, se marca «no aplica».
- La transparencia ante cada persona vive aquí y no en un tema UX propio (`docs/governance.md` §4).

Instalación: `specify preset add --dev presets/jevlab-decision --priority 20`.
