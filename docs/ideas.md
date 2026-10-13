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
| 000, 2026-10-12 (plan, research R3) | El SDK de TypeSafe y `openai` 3.x usan `httpx2`; `respx` y `vcrpy` interceptan `httpx`. Comprobar si `vcrpy` graba `httpx2`; si no, un grabador propio sobre el parámetro `transport` del cliente y ajustar `docs/standards/testing.md` §0 y §1 | IV, estándar de testing | 001 |
| 000, 2026-10-12 (implementación) | Comprobación automática de `docs/standards/architecture.md` §5: prohibir con ruff (TID251, `banned-api`) `datetime.now`, `time.time`, `random` y `uuid.uuid4` salvo en `src/jevlab/adapters/` y `tests/`, con un test que confirme que la puerta salta. Se añade con el primer puerto `Clock` o `IdGenerator`; después, quitar de §5 la frase «se decide al configurar el lint en la spec de cimientos» | IV, estándar de arquitectura | 001 |
