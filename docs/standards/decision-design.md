# Estándar: diseño de decisiones Jev

> Concreta: Constitución §I, §II, §III y §IV · Exigido por: preset jevlab-decision · ADRs:
> *(ninguno)*

Cómo se redacta, se define y se presenta cada decisión que se pide a Jev. Fuentes:
[*How to build*](https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md),
[*Confidence*](https://docs.typesafe.ai/confidence.md) y
[*Jaggedness*](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md).

## 1. Una pregunta, una idea

**Regla.** Cada pregunta evalúa una sola idea, de forma literal, afirmativa y directa. Si hacen
falta dos ideas, son dos preguntas y el código compone sus respuestas.

**Motivo.** La lectura literal y las instrucciones contradictorias son limitaciones documentadas
del modelo (*Jaggedness*).

**Correcto:** «¿El ticket describe un fallo del producto?»

**Incorrecto:** «¿El ticket no es una consulta de facturación y además es urgente?» (negación y
dos ideas).

**Cómo se verifica:** pregunta de revisión del plan, «¿se pide al modelo una cifra, una fecha, un
permiso o más de una idea?».

## 2. El código decide cifras, fechas, conteos y permisos

**Regla.** Lo calculable no se pregunta. El modelo juzga contenido; el código calcula y compone.

**Correcto:** el código calcula la antigüedad del ticket y la usa en la política.

**Incorrecto:** «¿El ticket tiene más de tres días?»

**Cómo se verifica:** tests unitarios de política y composición, sin modelo.

## 3. Rutas e identificadores fuera del enunciado

**Regla.** Las rutas, nombres de archivo e identificadores técnicos se escriben entre backticks en
la documentación y nunca dentro del texto de la pregunta que recibe el modelo.

**Motivo.** El modelo lee el enunciado de forma literal; un identificador técnico es ruido que
puede cambiar la respuesta.

**Correcto:** pregunta «¿A qué cola pertenece este ticket?», definida en
`src/jevlab/specs/soporte/cola-destino.yaml`.

**Incorrecto:** «¿A qué cola de `queues.yaml` pertenece este ticket?»

**Cómo se verifica:** revisión de cada `DecisionSpec` nuevo.

## 4. Estado mínimo

**Regla.** Al modelo se le envían solo los campos necesarios para responder la pregunta. El plan
lista esos campos y explica por qué bastan.

**Motivo.** Menos estado es menos ruido, menos coste y menos superficie para contenido
adversarial (§V).

**Correcto:** para «¿A qué cola pertenece este ticket?», se envían asunto y cuerpo.

**Incorrecto:** se envía el ticket completo con el historial del cliente y sus datos de contacto.

**Cómo se verifica:** un test comprueba que el adaptador envía solo los campos declarados en el
`DecisionSpec`.

## 5. Escape y abstención

**Regla.** Toda Choice incluye `other` o `none`. Una respuesta de escape, o la falta de una
respuesta válida, va a revisión o termina en abstención explícita, según indique la spec. Nunca
se convierte en una de las opciones normales.

**Correcto:** `other` encola el ticket para revisión manual y lo registra con su motivo.

**Incorrecto:** `other` se asigna a la cola `técnico` por ser la más frecuente.

**Cómo se verifica:** una definición sin escape falla su validación (test); un test de propiedades
comprueba que el escape siempre termina en revisión o abstención.

## 6. Umbrales por riesgo

**Regla.** Los umbrales de confianza viven en un YAML versionado, fuera del código. Cuanto mayor es
el riesgo de la acción, más exigente es el umbral. Cada umbral indica la evaluación que lo justifica
o se marca como provisional.

**Correcto:**

```yaml
version: 0.1.0
acciones:
  mover-a-cola:
    riesgo: bajo
    umbral: 0.80
    justificacion: provisional  # se fija con la evaluación de la spec 004
```

**Incorrecto:** `if confidence > 0.8:` en el código del caso de uso, sin origen.

**Cómo se verifica:** test de propiedades (las bandas son monótonas; nada por debajo del umbral se
automatiza) y revisión de que cada umbral tiene `justificacion`.

## 7. Transparencia ante cada persona

**Regla.** Toda salida de una decisión muestra:
- el resultado;
- la confianza;
- el motivo del escalado, si lo hay;
- «no disponible» cuando falta un dato;
- si el resultado es grabado (cassette) o sintético.

**Correcto:** `técnico · confianza 0,62 · a revisión: umbral 0,80 · grabado`

**Incorrecto:** `técnico` (sin confianza ni motivo, y parece una decisión automática).

**Cómo se verifica:** tests de la salida de la CLI y de la API. El formato concreto de cada
interfaz está en `cli-ux.md` y `api-errors.md`, cuando existan.
