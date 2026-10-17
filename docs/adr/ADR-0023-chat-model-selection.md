# ADR-0023: Selección de modelo para el candidato local del chat B

- Estado: Proposed
- Fecha: 2026-10-16
- Tarea documental: [JUP-063](https://trello.com/c/sRKGpYEy)
- Evaluación: [JUP-109](https://trello.com/c/orFyeUW2)
- Producto: [JUP-123](https://trello.com/c/TqtcumIN)
- OpenSpec: [jup-123-chat-semantic](../../openspec/changes/jup-123-chat-semantic/design.md)
- Antecedente aceptado: [ADR-0002](ADR-0002-litellm-openrouter.md), que no se sustituye.

## Contexto

Actualización 17/10/2026: la N5 final de B (`f3ec760d`,140 respuestas conformes,
825 comprobaciones PASS) usa DeepSeek V4.1 Flash/**DeepInfra FP8**, temperatura0,
razonamiento desactivado, ZDR sin fallback y banco1.0.1/corpus54. Esta es la
configuración medida del candidato entregado; no acredita disponibilidad futura
ni cambia el gateway compartido. Las referencias a CoreWeave de los apartados
siguientes describen la selección y campañas anteriores, no la ruta de la N5 final.
Se conserva Proposed hasta la revisión del equipo. El registro se renumera de
ADR-0022 a ADR-0023 al integrar, porque develop ya utiliza ADR-0022 para Grafana.
Evidencia actual: [resultado y límites](../validation/JUP-123-local-review.md).

### Contexto y propuesta anteriores — 16/10/2026

La comparación común de 84 pares favoreció GLM 5.2/DeepInfra FP4 en conformidad local
(82 frente 77 de DeepSeek, con 6 fallos y 1 duda), aunque GLM tuvo una regresión obligatoria.
DeepSeek V4.1 Flash/CoreWeave FP8 registró menor coste y latencia de generación.
Posteriormente, la validación API del candidato a7f9502d con GLM quedó parcial 4,
con 2 completed y 2fallos429. No es una estimación de disponibilidad general.

El candidato corregido, con corpus de 54/banco 1.0.1 y DeepSeek/CoreWeave, completó una
N3 nueva: 84 operaciones, 84 respuestas conformes en revisión local, 327 comprobaciones
del banco y 168 adicionales. Código, corpus y recorrido cambiaron respecto del
replay común: no se atribuye la diferencia al modelo de forma causal.

## Decisión documentada y propuesta

Conservar **DeepSeek V4.1 Flash/CoreWeave FP8** como selección operativa del
candidato local B: identificador `deepseek/deepseek-v4.1-flash`,
`coreweave/fp8`, temperatura 0, razonamiento desactivado, ZDR, recopilación
denegada y sin fallback. Se priorizan compatibilidad, requisitos obligatorios
y finalización de la validación; coste y tiempo son criterios secundarios.

La propuesta para el equipo es revisar esta configuración antes de activarla
como principal de B. **No cambia el gateway compartido, no supersede ADR-0002
y no afirma aprobación humana.** DeepSeek V4 Pro del ADR aceptado es otra variante.
Sonnet/Sol no se descartan por capacidad: sus parciales detectaron restricciones
del contrato, y no hay N3 semántica completa de ambos.

## Consecuencias y revisión

Se mantiene un servidor que recupera evidencia y calcula, con generación
estructurada y controles de contenido. La calidad se mide por versión completa
del sistema; un porcentaje medio no compensa un fallo obligatorio.
La elección queda condicionada al banco conocido, sin conjunto ciego,
adjudicación independiente o juez calibrado. N5 del candidato actual no ejecutada.

Cambios en modelo/proveedor/esquema/prompt/corpus/servidor requieren nueva
evaluación identificada. Los costes observados y máximos desconocidos se
conservan separados. No hay fallback automático, campañas nuevas, modificación
de claves ni cambio de despliegue por aprobar esta documentación.

## Evidencia

[Análisis y preparación para la memoria](../evidence/JUP-063-model-selection.md)
enlaza comparación, auditoría actual, propuesta fuera de Git y manifiesto de SHA-256.
La aceptación de B, las revisiones del equipo y la incorporación a la memoria
continúan pendientes; no se simulan en este ADR.
