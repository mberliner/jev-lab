# Ideas

Ideas abiertas para specs futuras. Al planificar una spec se revisa esta lista. Cuando una spec
recoge una idea, se borra de aquí en el mismo commit que la incorpora.

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
cambiada que obliga a adaptar algo ya hecho, o una mejora detectada al trabajar.

| Origen (spec, fecha) | Idea | Principio o capa | Spec que la recoge |
| --- | --- | --- | --- |
| 001, 2026-10-14 | Guardar el informe de `/speckit-analyze` en `specs/NNN-*/analysis.md`, con el estado de cada hallazgo. Se perdieron los LOW I2-I5 de la 001, que solo quedaron en la sesión | VII; preset `jevlab-spec` | |
