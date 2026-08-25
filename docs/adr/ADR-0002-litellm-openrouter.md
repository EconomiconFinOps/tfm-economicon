# ADR-0002: LiteLLM como gateway y OpenRouter como upstream

- Estado: Proposed
- Fecha: 2026-08-25
- Tarjeta: [JUP-078](https://trello.com/c/M4zqDGlW)
- Decision requerida antes de: octubre de 2026

## Contexto

Economicon necesita chat y embeddings reales para evaluar su RAG, pero el codigo actual solo implementa mocks. El equipo no dispone de un tenant de Azure AI y quiere evitar que backend y processor queden acoplados a credenciales, catalogos y politicas de un proveedor externo.

Trello recoge LiteLLM + OpenRouter y la seleccion de GLM-5.2 y DeepSeek. El
benchmark autenticado ya esta disponible, pero muestra limites de latencia y
un timeout de DeepSeek, y todavia no existe una aprobacion verificable de los
cuatro miembros. Esta propuesta permanece `Proposed` hasta su revision conjunta.

Alejandro establecio GLM-5.2 y DeepSeek como modelos de chat. Para hacer la
configuracion reproducible se fija la variante vigente
`deepseek/deepseek-v4-pro`; si el equipo acuerda otra variante DeepSeek, debera
cambiarse explicitamente antes del benchmark. El 25 de agosto de 2026 se
verificaron los tres IDs contra la API oficial de modelos de OpenRouter.

## Decision propuesta

Usar LiteLLM como gateway interno OpenAI-compatible y OpenRouter como unico upstream inicial.

- Los servicios usan `LITELLM_BASE_URL`, `LITELLM_API_KEY` y alias logicos.
- `economicon-chat` se mapea a `z-ai/glm-5.2` como modelo principal.
- `economicon-chat-deepseek` se mapea a `deepseek/deepseek-v4-pro` como segundo modelo de chat bajo seleccion explicita.
- `economicon-embedding` se mapea a `openai/text-embedding-3-small` con 1536 dimensiones.
- Cada alias tiene un unico despliegue; un fallo se propaga y se observa.
- El routing upstream fija expresamente `allow_fallbacks: false`.
- Los alias de chat fijan `reasoning.enabled: false` para la linea base FinOps;
  el razonamiento de alto esfuerzo queda reservado a una evaluacion explicita.
- Los mocks solo son validos en `test` y `development`; `evaluation` los rechaza.

## Catalogo y precios verificados

Consulta publica realizada el 25 de agosto de 2026 al endpoint oficial
`GET /api/v1/model/{author}/{slug}`; los precios se indican en USD por millon
de tokens y deben volver a comprobarse antes de cualquier gasto real.

| Modelo | ID OpenRouter | Contexto | Entrada / 1M | Salida / 1M |
|---|---|---:|---:|---:|
| GLM-5.2 | `z-ai/glm-5.2` | 1.048.576 | 1,19 USD | 3,74 USD |
| DeepSeek V4 Pro | `deepseek/deepseek-v4-pro` | 1.048.576 | 0,572808 USD | 1,145616 USD |
| Embeddings | `openai/text-embedding-3-small` | 8.192 | 0,02 USD | No aplica |

## Criterios

| Criterio | Peso | Umbral de aceptacion |
|---|---:|---|
| Exactitud FinOps sobre casos de ejemplo | 35% | 90% de comprobaciones objetivas |
| Fidelidad al contexto y citas | 20% | Sin cifras inventadas en casos criticos |
| Salida estructurada y robustez | 15% | 95% de respuestas parseables |
| Latencia | 15% | p95 menor o igual a 10 s en desarrollo |
| Coste | 10% | Estimacion dentro del techo aprobado |
| Operabilidad | 5% | Errores y modelo resuelto trazables |

Un candidato que invente costes, falle privacidad o no cumpla salidas estructuradas queda descartado aunque obtenga mayor puntuacion total.

## Benchmark autenticado del 25 de agosto de 2026

Ejecucion real desde una instancia LiteLLM 1.82.6 aislada en `dockerserver`,
con imagen fijada por digest, cinco casos publicos por modelo, salida acotada
a 256 tokens, razonamiento opcional desactivado y timeout de 30 segundos.

| Alias | Casos completados | Puntuacion por terminos | p95 | Coste atribuido |
|---|---:|---:|---:|---:|
| GLM-5.2 | 5/5 | 90% | 11,73 s | 0,0005395524 USD |
| DeepSeek V4 Pro | 4/5 | 75% | 10,88 s | 0,0003567 USD |

DeepSeek agoto los 30 segundos en el caso de acciones FinOps; el runner
devuelve error deliberadamente cuando cualquier caso no se completa. Ninguno
de los modelos alcanza el objetivo provisional de p95 <= 10 s. La puntuacion
por palabras es orientativa y no sustituye la revision humana de respuestas.

El alias de embeddings completo una solicitud real con 1536 dimensiones,
6 tokens y 450,39 ms. El coste acumulado de las tres tandas de diagnostico y la
comprobacion de embeddings fue 0,011825531 USD segun la propia cuenta de
OpenRouter; incluye solicitudes previas o agotadas que no aparecen en el coste
atribuido a las respuestas exitosas del benchmark final.

Los resultados sin prompts, respuestas ni secretos se conservan en
`docs/evidence/JUP-078-benchmark-results.json`. GLM-5.2 queda como candidato
principal; DeepSeek requiere estudiar latencia, timeout y calidad antes de
aprobar su politica de uso.

## Limites provisionales pendientes de aprobacion

- Presupuesto de desarrollo: 10 USD/mes mediante clave virtual de LiteLLM.
- Salida maxima: 800 tokens por llamada de chat.
- Benchmark FinOps: respuestas acotadas a 256 tokens por caso, siempre dentro
  del limite operativo de 800 tokens.
- Razonamiento opcional desactivado en la linea base para evitar que consuma el
  presupuesto de salida o agote el timeout antes de entregar texto.
- Timeout: 30 segundos; reintentos: 2 solo para errores transitorios.
- Sin fallback automatico.
- Los limites definitivos se actualizaran con el benchmark y el volumen esperado.

Como referencia, ejecutar 100 casos por cada modelo con 2.000 tokens de entrada
y 500 de salida costaria aproximadamente 0,425 USD para GLM-5.2 y 0,1718424
USD para DeepSeek: 0,5968424 USD en total. Esta estimacion no incluye
variaciones de routing, reintentos, impuestos ni otros cargos y no autoriza
ningun consumo.

## Privacidad y secretos

- `OPENROUTER_API_KEY` solo existe en el entorno del gateway.
- `LITELLM_MASTER_KEY` se configura en `general_settings.master_key`, nunca en
  `litellm_settings`, y no se entrega a backend o processor.
- La clave que consume el producto es virtual, revocable y presupuestada.
- El routing fija ZDR, `data_collection: deny` y `allow_fallbacks: false`; si
  no existe un provider compatible, falla sin relajar la politica.
- El benchmark rechaza redirecciones HTTP y nunca reenvia la clave interna a
  otro origen.
- No se habilita logging de prompts o respuestas.
- Metricas admitidas: correlation ID, alias, modelo resuelto, estado, latencia, tokens y coste.

## Alternativas consideradas

### OpenRouter directo desde cada servicio

Reduce un componente, pero distribuye credenciales, limites, telemetria y logica de proveedor. Se rechaza para el MVP.

### LiteLLM con varios upstream y fallback

Mejora disponibilidad, pero puede cambiar calidad, coste y privacidad durante una evaluacion. Se aplaza hasta definir reglas y trazabilidad.

### Modelo local en dockerserver

Evita un upstream externo, pero no hay capacidad ni rendimiento medidos. Se mantiene como opcion futura.

## Consecuencias

LiteLLM se convierte en una dependencia operativa y necesitara healthcheck, version fijada, gestion de claves y monitorizacion. A cambio, los servicios conservan una interfaz estable y la politica de coste/privacidad se centraliza.

Cambiar el modelo de embeddings o su dimension requerira una coleccion nueva y reindexacion; nunca se realizara en caliente de forma silenciosa.

## Condiciones para aceptar este ADR

1. Benchmark real y resultados adjuntos: completado; persisten hallazgos de
   latencia y disponibilidad que requieren revision.
2. Instancia de benchmark aislada y fijada por digest en `dockerserver`:
   completado.
3. Aprobar presupuesto, privacidad, hallazgos y politica de seleccion por los
   cuatro miembros: pendiente.
4. Crear una clave virtual revocable con el techo que apruebe el equipo:
   pendiente; la API key upstream actual tiene un limite propio de 25 USD/mes.
5. Revisar el PR publicado contra `develop` en
   `EconomiconFinOps/tfm-economicon` y aceptar expresamente la decision.

## Referencias consultadas

- [LiteLLM: proveedor OpenRouter y prefijos de modelo](https://docs.litellm.ai/docs/providers/openrouter)
- [LiteLLM: configuracion del proxy y general_settings.master_key](https://docs.litellm.ai/docs/proxy/configs)
- [OpenRouter: catalogo de modelos](https://openrouter.ai/api/v1/models)
- [OpenRouter: GLM-5.2](https://openrouter.ai/z-ai/glm-5.2)
- [OpenRouter: DeepSeek V4 Pro](https://openrouter.ai/deepseek/deepseek-v4-pro)
- [OpenRouter: embeddings con text-embedding-3-small](https://openrouter.ai/docs/api/api-reference/embeddings/create-embeddings)
- [OpenRouter: Zero Data Retention](https://openrouter.ai/docs/guides/features/zdr)
- [OpenRouter: seleccion de providers](https://openrouter.ai/docs/guides/routing/provider-selection)
