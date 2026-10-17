# Ideas

Ideas abiertas: de dominio, para specs futuras, y de las retros, para el nivel que les
corresponda. Al planificar una spec se revisa esta lista. Cuando una spec o un PR recoge una idea,
se borra de aquí en el mismo commit que la incorpora.

## Ideas de dominio

Dominios para specs posteriores a la 007, o como escenarios alternativos dentro de las existentes.
Se apoyan en los *cookbooks* y el *use-case map* oficiales de TypeSafe. Todo el contenido se
redacta de cero.

| Dominio | Decisiones candidatas | Primitiva / patrón |
| --- | --- | --- |
| Atención al cliente | Riesgo de baja, intención comercial, motivo de reembolso, sentimiento | Score, Choice + escape |
| Comercio | Atributos de producto, seguridad de marca, señales de demanda como *features* | Choice, Noul, composite |
| Confianza y seguridad | Spam, datos personales, cumplimiento de política propia | Noul con umbrales por riesgo |
| Agentes | Elección de herramienta o *skill*, escalado de modelo, juez con referencia explícita | Choice + `none`, confidence routing |
| Datos y extracción | Selección entre candidatos pre-extraídos, estructura de documento, taxonomía jerárquica (beam search) | Choice; cascada |
| Operaciones | Severidad de incidentes, deduplicación de alertas, triaje de cláusulas | Score, Noul |
| Simulación (didáctica) | Acción discreta con **interbloqueo de seguridad en código** que anula la propuesta | Choice + invariantes en código |

## Ideas de las retros

Lo que sale de la retro de cierre de cada spec (`docs/governance.md` §7): una regla nueva o
cambiada que obliga a adaptar algo ya hecho, o una mejora detectada al trabajar. Cada idea lleva
su nivel según §7, «Cambios en features ya entregadas»: 1 (PR de mantenimiento), 2 (ajuste con
«Enmiendas» en la spec afectada) o 3 (spec propia).

| Origen (spec, fecha) | Idea | Principio o capa | Nivel | Dónde se recoge |
| --- | --- | --- | --- | --- |
| 002, 2026-10-15 | Test que impida que cargar la CLI importe SDKs pesados (el de OpenAI costaba 1,4 s en cada comando desde la 000 y nadie lo vio hasta medir la meta de la 002) | §IV, `docs/standards/testing.md` | 1 | PR de mantenimiento |
| 002, 2026-10-15 | Medir cuánto varía la confianza al repetir la misma pregunta: entre dos grabaciones, `instruccion-incrustada` pasó de 0,85 a 0,88. Un umbral necesita ese margen | §II, §IV | 3 | Spec 004 (evaluación) |
| 002, 2026-10-15 | Protocolo para los criterios de éxito que miden a una persona (SC-004: resolver un elemento en menos de 1 minuto con la lección): un agente no puede verificarlos | §VII, preset `jevlab-spec` | No aplica (cambio de preset) | PR del preset, `docs/governance.md` §7 |
| 002, 2026-10-17 | Ampliar `qué hacer:` de `jevlab review`: sugerir el comando con la propuesta del modelo ya rellenada (`asignar 1 cuenta`) o resolver un elemento de forma interactiva, sin copiar comandos. Surge de la prueba de SC-004 | §II, `docs/standards/cli-ux.md` §6 | 2 si solo cambia la salida; 3 si añade un modo interactivo | Ajuste de la 002 o spec propia |
