# Informe de metricas tecnicas del asistente

Catalogo 1.0.0 · generado 2026-10-08T23:30:00Z
Commit 8a116df28472a30b21b996ab6fa02377dde7b2c1 · fecha de la ejecucion 2026-10-08T21:01:44Z · proveedor litellm · alias economicon-embedding
Generacion: {"model_alias": "plantilla-sin-modelo", "temperature": null}
Huellas: corpus cf2633b96ca30a63f70952c6cb23ca8139dcb665e9a51a0d52dbcc144b00c8dc · bateria 1.0.0 e15349564edfa5ce6cef94ff90ee2bfd15ef17656a2c4b201ac37bcd6d44571c
Corpus: 4 documentos y 52 fragmentos · top_k 4 · distancia maxima 0.6 · fragmentos de 500 con solape 50

Casos: 28 · pass 0 · fail 28 · blocked 0 · not_run 0. Los casos blocked y not_run no entran en ningun denominador.

Las tasas se muestran como k de n con su intervalo de Wilson al 95 %. Los objetivos son provisionales y no son una puerta de aceptacion.

| Id | Metrica | Valor | Objetivo |
| --- | --- | --- | --- |
| ACC-1 | Casos con resultado pass | 0 de 20 (0.0 %; IC 95 % 0.0 a 16.1 %) | sin objetivo |
| ACC-2 | Comprobaciones objetivas cumplidas | 25 de 51 (49.0 %; IC 95 % 35.9 a 62.3 %) | objetivo provisional >= 0.9 (origen ADR-0002): no cumple |
| REL-1 | Acierto de documento | 20 de 20 (100.0 %; IC 95 % 83.9 a 100.0 %) | sin objetivo |
| REL-2 | Acierto de seccion | 16 de 20 (80.0 %; IC 95 % 58.4 a 91.9 %) | sin objetivo |
| GRD-1 | Citas validas | 60 de 60 (100.0 %; IC 95 % 94.0 a 100.0 %) | sin objetivo |
| GRD-3 | Integridad de referencias de evidencia | 60 de 60 (100.0 %; IC 95 % 94.0 a 100.0 %) | sin objetivo |
| STR-1 | Respuestas que cumplen el esquema | 28 de 28 (100.0 %; IC 95 % 87.9 a 100.0 %) | objetivo provisional >= 0.95 (origen ADR-0002): cumple |
| AVL-1 | Disponibilidad del chat | 56 de 56 (100.0 %; IC 95 % 93.6 a 100.0 %) | sin objetivo |
| ACC-2 | Comprobaciones juzgadas cumplidas | 0 de 30 (0.0 %; IC 95 % 0.0 a 11.4 %) | sin objetivo |
| ACC-3 | Casos clarify y abstain con resultado pass (clarify) | 0 de 6 (0.0 %; IC 95 % 0.0 a 39.0 %) | sin objetivo |
| ACC-3 | Casos clarify y abstain con resultado pass (abstain) | 0 de 2 (0.0 %; IC 95 % 0.0 a 65.8 %) | sin objetivo |
| REL-3 | Resultado vacio (answer) | 0 de 20 (0.0 %; IC 95 % 0.0 a 16.1 %) | sin objetivo |
| REL-3 | Resultado vacio (clarify) | 0 de 6 (0.0 %; IC 95 % 0.0 a 39.0 %) | sin objetivo |
| REL-3 | Resultado vacio (abstain) | 0 de 2 (0.0 %; IC 95 % 0.0 a 65.8 %) | sin objetivo |
| REL-4 | Confianza de la recuperacion | n 20; mediana 0.617; cuartiles 0.558 y 0.636 | sin objetivo |
| GRD-2 | Cifras sin rastro | 0 en total; casos criticos afectados: ninguno | objetivo provisional == 0 (origen ADR-0002, casos criticos): cumple |
| LAT-1 | Latencia mediana (embedding, n 28, solo llamadas correctas) | 0 ms | sin objetivo |
| LAT-1 | Latencia mediana (retrieval, n 28, solo llamadas correctas) | 0 ms | sin objetivo |
| LAT-1 | Latencia mediana (generation, n 28, solo llamadas correctas) | 3213.097 ms | sin objetivo |
| LAT-1 | Latencia mediana (total, n 28, solo llamadas correctas) | 3213.097 ms | sin objetivo |
| LAT-2 | Latencia percentil 95 (embedding, n 28, solo llamadas correctas) | 0 ms | sin objetivo |
| LAT-2 | Latencia percentil 95 (retrieval, n 28, solo llamadas correctas) | 0 ms | sin objetivo |
| LAT-2 | Latencia percentil 95 (generation, n 28, solo llamadas correctas) | 4561.659 ms | sin objetivo |
| LAT-2 | Latencia percentil 95 (total, n 28, solo llamadas correctas) | 4561.659 ms | objetivo provisional <= 10000 (origen ADR-0002, etapa total, en desarrollo): cumple |
| LAT-3 | Latencia maxima (embedding, n 28, solo llamadas correctas) | 0 ms | sin objetivo |
| LAT-3 | Latencia maxima (retrieval, n 28, solo llamadas correctas) | 0 ms | sin objetivo |
| LAT-3 | Latencia maxima (generation, n 28, solo llamadas correctas) | 5679.037 ms | sin objetivo |
| LAT-3 | Latencia maxima (total, n 28, solo llamadas correctas) | 5679.037 ms | sin objetivo |
| LAT-4 | Llamadas fallidas o agotadas (embedding) | 0 de 28 (0.0 %; IC 95 % 0.0 a 12.1 %) | sin objetivo |
| LAT-4 | Llamadas fallidas o agotadas (retrieval) | 0 de 28 (0.0 %; IC 95 % 0.0 a 12.1 %) | sin objetivo |
| LAT-4 | Llamadas fallidas o agotadas (generation) | 0 de 28 (0.0 %; IC 95 % 0.0 a 12.1 %) | sin objetivo |
| STR-2 | Fallos por categoria | sin fallos | sin objetivo |

La latencia se mide sobre un corpus de 4 documentos y 52 fragmentos; no se compara con ejecuciones de otro tamano.

Huecos del corpus (cobertura none, fuera de REL-2): JUP-069-024, JUP-069-026.

Casos criticos con una sola persona decidiendo los puntos juzgados: JUP-069-001, JUP-069-002, JUP-069-005, JUP-069-006, JUP-069-007, JUP-069-011, JUP-069-013, JUP-069-014, JUP-069-016, JUP-069-017, JUP-069-018, JUP-069-019, JUP-069-021, JUP-069-027.

## Definiciones

| Id | Familia | Numerador | Denominador | Poblacion | Fuente | Unidad |
| --- | --- | --- | --- | --- | --- | --- |
| ACC-1 | accuracy | casos pass | casos pass mas fail | casos answer | campo outcome de cada caso | tasa |
| ACC-2 | accuracy | comprobaciones objetivas (numbers y forbidden) con resultado pass | comprobaciones objetivas evaluadas | casos answer pass o fail | checks de clase objective | tasa |
| ACC-3 | accuracy | casos pass | casos pass mas fail | casos clarify y casos abstain, cada grupo por separado | campo outcome de cada caso | tasa |
| REL-1 | relevance | casos con algun fragmento recuperado de un documento declarado por el caso | casos evaluados | casos answer pass o fail | retrieved y fuentes del caso en la bateria | tasa |
| REL-2 | relevance | casos con algun fragmento recuperado de una seccion etiquetada | casos evaluados con cobertura direct o partial | casos answer pass o fail | retrieved y etiquetas de JUP-022 | tasa |
| REL-3 | relevance | casos sin fragmento recuperado | casos evaluados | casos pass o fail, por grupo de comportamiento | retrieved | tasa |
| REL-4 | relevance | mediana y cuartiles (rango mas cercano) de 1 menos la distancia coseno del mejor fragmento | no aplica | casos answer pass o fail con al menos un fragmento recuperado | distancias de retrieved | similitud |
| GRD-1 | grounding | citas que apuntan a un fragmento recuperado para esa pregunta | citas emitidas | casos answer pass o fail con citas | citations y retrieved | tasa |
| GRD-2 | grounding | cifras de la respuesta que no se rastrean al contexto, a la evidencia ni a la pregunta | no aplica | recuento por caso y total; los casos criticos se listan aparte | figures | recuento |
| GRD-3 | grounding | referencias de evidencia que existen | referencias de evidencia emitidas | casos answer pass o fail con referencias de evidencia | evidence_refs | tasa |
| LAT-1 | latency | mediana de los milisegundos registrados | no aplica | llamadas correctas de cada etapa (embedding, retrieval, generation, total) | latency_ms | ms |
| LAT-2 | latency | percentil 95 por rango mas cercano de los milisegundos registrados | no aplica | llamadas correctas de cada etapa | latency_ms | ms |
| LAT-3 | latency | maximo de los milisegundos registrados | no aplica | llamadas correctas de cada etapa | latency_ms | ms |
| LAT-4 | latency | llamadas fallidas de la etapa | llamadas totales de la etapa | todas las llamadas de cada etapa | latency_ms y failure_stage | tasa |
| STR-1 | robustness | respuestas con structured_ok verdadero | respuestas estructuradas recibidas | casos con structured_ok informado | structured_ok | tasa |
| STR-2 | robustness | fallos de cada categoria | todos los fallos | las nueve categorias del proveedor mas schema_validation | failure_category | recuento |
| AVL-1 | availability | peticiones al chat sin error del servidor (estado 500 a 599) | peticiones al chat de la ejecucion | peticiones al chat de la ejecucion | availability de la cabecera de la ejecucion | tasa |

## Evaluación de las respuestas (JUP-070)

**Veredicto: No aceptado**

Medición **provisional**: los casos críticos con un solo revisor se listan abajo.

Etapas no medidas: la herramienta solo ve la petición completa, así que la latencia de `embedding` y `retrieval` vale 0 por construcción y no es una medición.

| Umbral | Estado | Detalle |
| --- | --- | --- |
| ACC-2 | unmet | >= 0.9 no se cumple |
| GRD-2 | met | == 0 |
| LAT-2 (total) | met | <= 10000 |
| STR-1 | not_applicable | >= 0.95; el chat no devuelve salida estructurada |
| ACC-1 | unmet | >= 0.8 (JUP-070 (propuesta, a validar por el equipo)): medido 0.0 |

- Casos no ejecutados (`not_run`): ninguno
- Casos bloqueados por infraestructura: ninguno
- Casos críticos con un solo decisor: JUP-069-001, JUP-069-002, JUP-069-005, JUP-069-006, JUP-069-007, JUP-069-011, JUP-069-013, JUP-069-014, JUP-069-016, JUP-069-017, JUP-069-018, JUP-069-019, JUP-069-021, JUP-069-027
- Discrepancias entre revisores: ninguna
