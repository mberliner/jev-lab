# Constitución de jev-lab

> Las palabras clave MUST, MUST NOT, SHOULD, SHOULD NOT y MAY se interpretan según
> [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

## Core Principles

### I. El modelo juzga, el código decide

**Enunciado.**
- Jev MUST usarse solo para juicios sobre contenido: clasificar, puntuar o verificar.
- La aritmética, las fechas, los conteos, los permisos, la composición de resultados y cualquier
  invariante de seguridad MUST resolverse en código determinista.
- Cada pregunta al modelo MUST evaluar una sola idea, formulada de forma literal,
  afirmativa y directa.
- El estado enviado al modelo SHOULD ser el mínimo necesario para responder.

**Justificación.** Entre las limitaciones documentadas de jev-1.13
([*Jaggedness*](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md)) están el conteo,
las representaciones numéricas, las matemáticas sobre Score, la lectura literal y las
instrucciones contradictorias. La guía oficial
[*How to build*](https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md) deja el control y la composición en
el código, y recomienda preguntas atómicas con estado mínimo.

**Verificación.**
- Tests unitarios de política y composición, sin modelo.
- Pregunta de revisión para cada plan y cada pregunta nueva: «¿se pide al modelo una cifra, una
  fecha, un permiso o más de una idea?».
- Los fallos de redacción conocidos se reproducen y se miden en el laboratorio de modos de fallo.

### II. Automatizar solo con escape y confianza

**Enunciado.**
- Toda Choice MUST incluir una opción de escape (`other` o `none`).
- Una respuesta de escape, o la falta de una respuesta válida, MUST enviarse a revisión
  o resolverse como abstención explícita.
- Toda acción automatizable MUST condicionarse a la confianza de la respuesta, además de a su
  valor.
- Los umbrales de confianza MUST ser más exigentes cuanto mayor sea el riesgo de la acción y MUST
  estar versionados fuera del código.
- Los umbrales SHOULD justificarse con datos propios, comparando confianza frente a acierto.

**Justificación.** Sin escape, el modelo se ve obligado a elegir una opción incorrecta cuando
ninguna aplica, y esa elección parece legítima. La documentación oficial define la
[confianza](https://docs.typesafe.ai/confidence.md) de Choice y Score, y [recomienda](https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md) elegir los umbrales trazando confianza frente a acierto con datos
propios.

**Verificación.**
- Una definición de decisión sin escape MUST fallar su validación (test).
- Tests de propiedades:
  - el escape siempre termina en revisión o abstención;
  - las bandas de confianza son monótonas;
  - nada por debajo del umbral se automatiza.
- Cada umbral referencia la evaluación que lo justifica o se marca como provisional.

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
- Los tests SHOULD escribirse antes de la implementación (rojo -> verde -> refactor).
- La suite por defecto MUST ejecutarse sin red, sin claves y sin coste.
- Las pruebas contra servicios reales MUST ser opcionales, estar marcadas y tener un tope de
  coste.
- Toda afirmación sobre calidad, coste o rendimiento MUST apoyarse en una ejecución reproducible e
  indicar los datos y la versión de modelo usados.
- Los datos sintéticos MUST etiquetarse como tales.
- Lo desconocido MUST mostrarse como «no disponible».
- Las conclusiones de una comparación MUST limitarse a las condiciones medidas.

**Justificación.** Las conclusiones de un laboratorio son su producto: solo valen si cualquiera
puede reproducirlas de forma rápida y gratuita, y si ninguna cifra está inventada ni sacada de
contexto.

**Verificación.**
- La CI ejecuta la suite por defecto sin credenciales y aplica los umbrales del estándar de
  testing.
- En el orden de tareas, los tests van antes que la implementación salvo que el plan justifique
  lo contrario.
- Los informes se generan a partir de los datos e incluyen su procedencia.
- Las pruebas contra servicios reales declaran su marca y su tope de coste (revisión de tareas).
- Pregunta de revisión: «¿cada cifra tiene una ejecución o una fuente que la produzca?».

### V. Seguridad y privacidad por defecto

**Enunciado.**
- Los secretos MUST NOT entrar en el repositorio ni en los logs.
- Los logs MUST NOT contener *payloads* (los datos que viajan en una petición o una respuesta,
  sin los metadatos) ni datos personales.
- Todo contenido externo (estado, documentos, entradas de usuario) MUST tratarse como dato no
  confiable y nunca como instrucción.

**Justificación.** El SDK registra los *payloads*, sin redactar, en su nivel de log más
detallado ([*Usage*](https://docs.typesafe.ai/sdk/python/usage.md)), y el contenido
adversarial es un modo de fallo conocido.

**Verificación.**
- Escáner de secretos en pre-commit y en CI.
- Un test comprueba que la configuración de logs por defecto no emite *payloads*.
- La evaluación incluye casos adversariales.

### VI. Proyecto autocontenido, neutral y original

**Enunciado.**
- El repositorio MUST arrancar y funcionar solo con su propio contenido.
- Todo flujo de trabajo MUST funcionar igual en Linux y en Windows y con cualquier agente de
  código soportado, con una única fuente de instrucciones para agentes.
- Las puertas de calidad MUST ser independientes del agente.
- Los hooks, comandos y herramientas MUST implementarse de forma neutral: su lógica vive en
  tareas del repositorio, y la configuración propia de cada agente solo invoca esas tareas y
  MUST existir de forma equivalente para todos los agentes soportados. Un mecanismo se usa solo si
  todos los agentes soportados lo admiten.
- El código y los textos MUST ser originales.
- Los escenarios y los datos SHOULD ser propios. MAY incorporarse datos externos si su licencia lo
  permite, se citan como corresponde y aportan claridad, velocidad o simplicidad.
- Las únicas referencias externas MUST ser la documentación oficial de TypeSafe y otras fuentes
  primarias, citadas donde se usan.

**Justificación.** El proyecto debe poder retomarse en otra máquina, con otro agente o por otra
persona sin conocimiento tácito. También debe poder publicarse sin conflictos de autoría, con
afirmaciones contrastables en su fuente.

**Verificación.**
- CI en Linux y en Windows.
- Una comprobación en CI rechaza rutas absolutas de máquina.
- Un test comprueba que las instrucciones de agente tienen una sola fuente.
- Pregunta de revisión: «¿este hook o comando existe con el mismo efecto para todos los agentes
  y llama solo a tareas del repositorio?».
- Prueba de clon limpio en la spec de cimientos.
- Pregunta de revisión: «¿hay material sin cita, derivado de una fuente no primaria o con una
  licencia que no permite incorporarlo?».

### VII. Cortes verticales que enseñan

**Enunciado.**
- Cada feature, salvo la de cimientos, MUST entregar a uno de los perfiles de usuario del
  proyecto una capacidad ejecutable de extremo a extremo.
- Cada historia MUST poder probarse y demostrarse por separado.
- El diseño SHOULD limitarse a lo que las historias necesitan (YAGNI).
- Cada feature, incluida la de cimientos, MUST incluir una lección que explique qué se aprende,
  cómo se ejecuta y qué puede fallar, con su mitigación.

**Justificación.** Las capas sin un usuario que las use no demuestran nada y tienden a diseñarse
de más. El propósito del proyecto es aprender y demostrar Jev: una feature sin lección cumple solo
la mitad de su objetivo.

**Verificación.**
- El preset de spec exige el perfil de usuario y escenarios independientes por historia.
- `/speckit-analyze` termina sin historias huérfanas.
- La spec se cierra solo con su lección (checklist de cierre).

## Flujo de desarrollo y puertas de calidad

- Toda feature sigue el flujo de Spec Kit: especificar -> clarificar -> planificar -> tareas ->
  analizar -> implementar.
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
- **Precedencia:** constitución > preset > estándar > `plan.md` de la feature. Una capa inferior
  MUST NOT contradecir a una superior. El reparto entre capas está en `docs/governance.md`.
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

**Version**: 0.3.1 | **Ratified**: 2026-10-11 | **Last Amended**: 2026-10-12
