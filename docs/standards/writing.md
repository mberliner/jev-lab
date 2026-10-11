# Estándar: redacción de la documentación

> Concreta: Constitución §VI, §VII · Exigido por: *(sin preset)* · ADRs: *(ninguno)*

Convenciones para todo texto en Markdown del repositorio: documentos, lecciones y artefactos de
Spec Kit (`specs/`). Se aplican igual a lo que escribe una persona y a lo que genera un agente.

## 1. Sin emojis ni pictogramas

**Regla.** Los documentos MUST NOT contener emojis ni pictogramas: `✅ ⏳ ⚠️ 🚀 ★ ✔ ❌` y
similares. El estado y el énfasis se expresan con palabras: «hecho», «siguiente», «pendiente»,
**Atención:**.

**Motivo.** Su visualización depende de la fuente y del terminal. Su ancho varía entre 1 y 2
columnas y algunos llevan un selector de variante invisible (U+FE0F). Además, no se pueden buscar
por significado y no añaden información que no dé una palabra.

**Correcto:**

```markdown
- [hecho] Paso 2: revisión.
- **[siguiente] Paso 4:** segunda opinión.
```

**Incorrecto:**

```markdown
- ✅ Paso 2: revisión.
- ⏳ Paso 4: segunda opinión.
```

## 2. Caracteres de caja y flechas, solo en bloques de código

**Regla.** Los caracteres de dibujo de cajas (`─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼`, U+2500–257F), las flechas
(`→ ← ↑ ↓`) y los triángulos (`▲ ▼ ► ◄`) MAY usarse **solo dentro de bloques de código**, para
diagramas. En el texto corrido se escribe con palabras o con `->`.

**Motivo.** Estos caracteres están en todas las fuentes monoespaciadas habituales y se ven bien en
editores, GitHub y terminales con UTF-8. Dentro de un bloque de código conservan la alineación.
Sin embargo, una consola con una página de códigos distinta de UTF-8 (conhost de Windows con
850/1252) los muestra corruptos. Limitarlos a diagramas reduce ese riesgo al mínimo.

**Fuera de alcance.** La salida de la CLI por terminal se rige por el estándar `cli-ux.md`.

## Excepciones

Los archivos generados por Spec Kit y no editados por el proyecto (`.specify/templates/`,
`.claude/skills/`, `.agents/skills/`) se excluyen de la comprobación. También se excluye este
estándar, porque muestra los símbolos que prohíbe. Su salida se ajusta mediante
los presets propios, no editando esos archivos a mano.

## Verificación

- **Automática:** un script del repo, ejecutado en pre-commit y en CI, rechaza los emojis y
  pictogramas en `*.md` fuera de las excepciones, y los caracteres de caja y flechas fuera de los
  bloques de código. Se implementa en la spec 000.
- **Revisión:** «¿hay algún símbolo que debería ser una palabra?».
