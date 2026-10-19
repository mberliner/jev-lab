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

## 3. Redacción en positivo

**Regla.** Las reglas y las instrucciones SHOULD redactarse en positivo: qué hay que hacer, no
qué hay que evitar. La forma negativa (MUST NOT, «nunca») se reserva para prohibiciones claras.

**Motivo.** Una frase en positivo dice directamente qué hacer y se puede comprobar. Una negación
obliga a deducir la alternativa y deja huecos.

**Correcto:**

```text
El diseño SHOULD limitarse a lo que las historias necesitan.
Los secretos MUST NOT entrar en el repositorio.   (prohibición clara)
```

**Incorrecto:**

```text
El diseño SHOULD NOT incluir nada que las historias no necesiten.
```

## Excepciones

Los archivos generados por Spec Kit y no editados por el proyecto (`.specify/templates/`,
`.claude/skills/`, `.agents/skills/` y los comandos compuestos en `.specify/presets/*/.composed/`)
se excluyen de la comprobación. También se excluye este
estándar, porque muestra los símbolos que prohíbe. Su salida se ajusta mediante
los presets propios, no editando esos archivos a mano.

Las copias de los presets (`presets/` y `.specify/presets/`) sí se comprueban, aunque partan de
texto de Spec Kit: son del proyecto y su texto llega a los artefactos. Las skills y las plantillas
base conservan sus símbolos, porque limpiarlas exigiría sustituir cada comando con `replace`
(`docs/governance.md` §5, regla 1); si un agente los copia a un artefacto, la puerta lo rechaza en
el commit.

## Verificación

- **Automática:** un script del repo, ejecutado en pre-commit y en CI, rechaza los emojis y
  pictogramas en `*.md` fuera de las excepciones, y los caracteres de caja y flechas fuera de los
  bloques de código. Lo implementa `scripts/checks/writing.py` (`uv run poe check-writing`).
- **Revisión:** «¿hay algún símbolo que debería ser una palabra?» y «¿hay alguna regla en
  negativo que no sea una prohibición clara?». La redacción en positivo no se comprueba de forma
  automática.
