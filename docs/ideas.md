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
