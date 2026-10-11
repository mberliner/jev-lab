<!--
Sync Impact Report (borrador HITL, paso 2 en curso; se elimina antes del commit de ratificación)
- Versión: plantilla sin rellenar → 0.3.0 (propuesta, NO ratificada; regla de versión inicial
  en docs/governance.md, «Versionado de documentos»)
- Principios: 12 del borrador → 7 consolidados (decisión humana, 2026-10-10)
  · I   El modelo juzga, el código decide         ← juzga/decide + preguntas atómicas
  · II  Automatizar solo con escape y confianza   ← opción de escape + confianza por riesgo
  · III Una definición de decisión, aislada del proveedor
  · IV  Evidencia antes que afirmación            ← verificación aislada + honestidad
  · V   Seguridad y privacidad por defecto
  · VI  Proyecto autocontenido, neutral y original ← entorno reproducible + contenido original
  · VII Cortes verticales que enseñan             ← cortes verticales + lección
- Secciones añadidas: Alcance y relación con otras capas; Flujo de desarrollo y puertas de calidad
- Secciones eliminadas: ninguna
- Detalle movido fuera de la constitución (destino propuesto):
  · rutas entre backticks, estado mínimo → estándar decision-design
  · umbrales de cobertura, bloqueo de red en tests → estándar testing
  · .env, escáner de secretos concreto → estándar security
  · fuente única de instrucciones, tareas, pre-commit, matriz Linux/Windows → estándar/AGENTS.md
  · «unas 4 historias» → preset de spec
- Paso 2 HITL (revisión principio a principio) completado:
  · I, II, III, V, VI, VII: se mantienen
  · IV: escribir el test antes pasa de MUST a SHOULD
  · Rutas y herramientas SDD permitidas solo fuera de los enunciados (docs/governance.md §8)
- Siguiente: paso 3 HITL (escenarios de prueba de la constitución).
- Plantillas (.specify/templates/*): no modificadas; se alinearán mediante presets propios.
- TODO(RATIFICATION_DATE): se fija al ratificar (paso 5 HITL).
- TODO(FUENTES): confirmar enlaces exactos a la documentación oficial de TypeSafe citada.
-->

# Constitución de jev-lab

> **Estado: BORRADOR (proceso HITL, paso 3).** No es vinculante hasta su ratificación.
> Las palabras clave MUST, MUST NOT, SHOULD y SHOULD NOT se interpretan según RFC 2119.

## Core Principles

### I. El modelo juzga, el código decide

**Enunciado.**
- Jev MUST usarse solo para juicios sobre contenido: clasificar, puntuar o verificar.
- La aritmética, las fechas, los conteos, los permisos, la composición de resultados y cualquier
  invariante de seguridad MUST resolverse en código determinista.
- Cada pregunta al modelo MUST evaluar una sola idea, formulada de forma literal y sin negaciones
  ni indirección.
- El estado enviado al modelo SHOULD ser el mínimo necesario para responder.

**Justificación.** Entre las limitaciones documentadas de jev-1.13 (*Jaggedness*) están el conteo,
las representaciones numéricas, las matemáticas sobre Score, la lectura literal y las
instrucciones contradictorias. La guía oficial *How to build* deja el control y la composición en
el código, y recomienda preguntas atómicas con estado mínimo.

**Verificación.**
- Tests unitarios de política y composición, sin modelo.
- Pregunta de revisión para cada plan y cada pregunta nueva: «¿se pide al modelo una cifra, una
  fecha, un permiso o más de una idea?».
- Los fallos de redacción conocidos se reproducen y se miden en el laboratorio de modos de fallo.

### II. Automatizar solo con escape y confianza

**Enunciado.**
- Toda Choice MUST incluir una opción de escape (`other` o `none`).
- Una respuesta de escape MUST NOT ejecutarse automáticamente: se envía a revisión o se resuelve
  como abstención explícita.
- Toda acción automatizable MUST condicionarse a la confianza de la respuesta, además de a su
  valor.
- Los umbrales de confianza MUST ser más exigentes cuanto mayor sea el riesgo de la acción y MUST
  estar versionados fuera del código.
- Los umbrales SHOULD justificarse con datos propios, comparando confianza frente a acierto.

**Justificación.** Sin escape, el modelo se ve obligado a elegir una opción incorrecta cuando
ninguna aplica, y esa elección parece legítima. La documentación oficial define la confianza de
Choice y Score, y recomienda elegir los umbrales trazando confianza frente a acierto con datos
propios.

**Verificación.**
- Una definición de decisión sin escape MUST fallar su validación (test).
- Tests de propiedades:
  - el escape nunca produce una acción automática;
  - las bandas de confianza son monótonas;
  - nada por debajo del umbral se automatiza.
- Cada cambio de umbral referencia la evaluación que lo justifica.

### III. Una definición de decisión, aislada del proveedor

**Enunciado.**
- Cada decisión MUST describirse una sola vez, de forma declarativa y versionada: preguntas,
  escape, política y modelo fijado.
- Esa misma definición MUST usarse para servir, evaluar y probar.
- La lógica de dominio MUST NOT realizar entrada/salida ni depender de un proveedor concreto.
- Todo efecto externo MUST pasar por una interfaz sustituible.

**Justificación.** Si lo evaluado y lo desplegado son lo mismo, las métricas valen para
producción. Poder sustituir el proveedor permite tests sin red, comparaciones justas con un
baseline y modo sin conexión.

**Verificación.**
- La regla de dependencias entre capas se comprueba en CI.
- Un test comprueba que el servicio, la evaluación y el laboratorio cargan la misma definición.

### IV. Evidencia antes que afirmación

**Enunciado.**
- Todo comportamiento MUST tener tests automáticos.
- Los tests SHOULD escribirse antes de la implementación (rojo → verde → refactor).
- La suite por defecto MUST ejecutarse sin red, sin claves y sin coste.
- Las pruebas contra servicios reales MUST ser opcionales, estar marcadas y tener un tope de
  coste.
- Toda afirmación sobre calidad, coste o rendimiento MUST apoyarse en una ejecución reproducible e
  indicar los datos y la versión de modelo usados.
- Los datos sintéticos MUST etiquetarse como tales.
- Lo desconocido MUST mostrarse como «no disponible», no estimarse.
- Las comparaciones MUST NOT declarar un ganador fuera de las condiciones medidas.

**Justificación.** Las conclusiones de un laboratorio son su producto: solo valen si cualquiera
puede reproducirlas de forma rápida y gratuita, y si ninguna cifra está inventada ni sacada de
contexto.

**Verificación.**
- La CI ejecuta la suite por defecto sin credenciales y aplica los umbrales del estándar de
  testing.
- En el orden de tareas, los tests van antes que la implementación salvo que el plan justifique
  lo contrario.
- Los informes se generan a partir de los datos e incluyen su procedencia.
- Pregunta de revisión: «¿cada cifra tiene una ejecución o una fuente que la produzca?».

### V. Seguridad y privacidad por defecto

**Enunciado.**
- Los secretos MUST NOT entrar en el repositorio ni en los logs.
- Los logs MUST NOT contener cuerpos de petición o respuesta ni datos personales.
- Todo contenido externo (estado, documentos, entradas de usuario) MUST tratarse como dato no
  confiable y nunca como instrucción.

**Justificación.** El SDK registra los cuerpos en su nivel de log más detallado, y el contenido
adversarial es un modo de fallo conocido.

**Verificación.**
- Escáner de secretos en pre-commit y en CI.
- Un test comprueba que la configuración de logs por defecto no emite cuerpos.
- La evaluación incluye casos adversariales.

### VI. Proyecto autocontenido, neutral y original

**Enunciado.**
- El repositorio MUST arrancar y funcionar a partir de su propio contenido, sin depender de
  memorias, rutas ni configuración externas.
- Todo flujo de trabajo MUST funcionar igual en Linux y en Windows y con cualquier agente de
  código soportado, con una única fuente de instrucciones para agentes.
- Las puertas de calidad MUST ser independientes del agente.
- El código, los escenarios, los datos y los textos MUST ser originales.
- Las únicas referencias externas MUST ser la documentación oficial de TypeSafe y otras fuentes
  primarias, citadas donde se usan.

**Justificación.** El proyecto debe poder retomarse en otra máquina, con otro agente o por otra
persona sin conocimiento tácito. También debe poder publicarse sin conflictos de autoría, con
afirmaciones contrastables en su fuente.

**Verificación.**
- CI en Linux y en Windows.
- Una comprobación en CI rechaza rutas absolutas de máquina.
- Un test comprueba que las instrucciones de agente tienen una sola fuente.
- Prueba de clon limpio en la spec de cimientos.
- Pregunta de revisión: «¿hay material sin cita o derivado de una fuente no primaria?».

### VII. Cortes verticales que enseñan

**Enunciado.**
- Cada feature, salvo la de cimientos, MUST entregar a una persona concreta del proyecto una
  capacidad ejecutable de extremo a extremo.
- Cada historia MUST poder probarse y demostrarse por separado.
- Solo se construye lo que las historias necesitan (YAGNI).
- Cada feature MUST incluir una lección que explique qué se aprende, cómo se ejecuta y qué puede
  fallar, con su mitigación.

**Justificación.** Las capas sin un usuario que las use no demuestran nada y tienden a diseñarse
de más. El propósito del proyecto es aprender y demostrar Jev: una feature sin lección cumple solo
la mitad de su objetivo.

**Verificación.**
- El preset de spec exige la persona y escenarios independientes por historia.
- `/speckit-analyze` termina sin historias huérfanas.
- La spec no se cierra sin su lección (checklist de cierre).

## Alcance y relación con otras capas

Esta constitución recoge solo principios: qué debe cumplirse siempre y por qué. No nombra
tecnologías, versiones ni estructura de documentos. Cada principio se concreta en dos capas:

- **presets propios**, que obligan a cada spec, plan y lista de tareas a tratar el tema;
- **estándares**, que describen cómo se hace.

El reparto, la trazabilidad y las convenciones están en la guía de gobernanza del repositorio
(`docs/governance.md`).

**Precedencia:** constitución > preset > estándar > `plan.md` de la feature. Una capa inferior
MUST NOT contradecir a una superior.

## Flujo de desarrollo y puertas de calidad

- Toda feature sigue el flujo de Spec Kit: especificar → clarificar → planificar → tareas →
  analizar → implementar.
- Cada plan MUST superar la puerta *Constitution Check* antes y después del diseño. Un
  incumplimiento bloquea el plan salvo que haya una excepción registrada.
- Las excepciones MUST registrarse en *Complexity Tracking* del plan: principio afectado, motivo,
  alternativa más simple descartada y aprobación humana.
- `/speckit-analyze` MUST terminar sin conflictos con la constitución antes de implementar.
- Las puertas automáticas (lint, tipos, tests, regla de dependencias, secretos) MUST ejecutarse
  en pre-commit y en CI. Un fallo bloquea la integración.

## Governance

- **Autoridad:** esta constitución prevalece sobre cualquier otra práctica, guía o instrucción de
  agente del proyecto.
- **Enmiendas:** se proponen por PR con la justificación y el impacto en presets y estándares. La
  aprobación humana es obligatoria; ningún agente ratifica ni enmienda por sí mismo.
- **Versionado:** semver según la guía de gobernanza.
  - La versión inicial es `0.3.0` como máximo.
  - En `0.x`, un cambio incompatible (eliminar o redefinir un principio) sube MINOR y el resto
    sube PATCH.
  - `1.0.0` llega solo por decisión humana explícita, cuando la constitución ha superado al menos
    una spec completa sin cambios incompatibles. Desde entonces: MAJOR si se elimina o redefine,
    MINOR si se añade, PATCH si se aclara.
- **Numeración estable:** los principios conservan su número romano, y un número retirado no se
  reutiliza.
- **Revisión periódica:** al cerrar cada spec se hace una retro breve: ¿algún principio estorbó?,
  ¿faltó alguno?, ¿alguno no se pudo verificar? Cada «sí» abre una propuesta de enmienda o un
  cambio en la capa que corresponda.
- **Cumplimiento:** toda revisión de PR comprueba los principios que afecta.

**Version**: 0.3.0 (propuesta, borrador) | **Ratified**: TODO(RATIFICATION_DATE): se fija al ratificar (paso 5 HITL) | **Last Amended**: 2026-10-10
