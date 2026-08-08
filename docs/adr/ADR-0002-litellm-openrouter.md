# ADR-0002: LiteLLM como gateway y OpenRouter como upstream

- Estado: Proposed
- Fecha: 2026-08-08
- Tarjeta: [JUP-078](https://trello.com/c/M4zqDGlW)
- Decision requerida antes de: octubre de 2026

## Contexto

Economicon necesita chat y embeddings reales para evaluar su RAG, pero el codigo actual solo implementa mocks. El equipo no dispone de un tenant de Azure AI y quiere evitar que backend y processor queden acoplados a credenciales, catalogos y politicas de un proveedor externo.

No se encontro una decision aprobada en el repositorio ni en la exportacion de Discord. Esta propuesta debe ser revisada por Lucia, Paris, Victor y Alejandro y validada con un benchmark real.

El 8 de agosto de 2026, Alejandro corrigio la seleccion de chat a GLM-5.2 y DeepSeek. Para hacer la configuracion reproducible se fija la variante vigente `deepseek/deepseek-v4-pro`; si el equipo pretendia otra variante de la familia DeepSeek, debera cambiarse de forma explicita antes del benchmark.

## Decision propuesta

Usar LiteLLM como gateway interno OpenAI-compatible y OpenRouter como unico upstream inicial.

- Los servicios usan `LITELLM_BASE_URL`, `LITELLM_API_KEY` y alias logicos.
- `economicon-chat` se mapea a `z-ai/glm-5.2` como modelo principal.
- `economicon-chat-deepseek` se mapea a `deepseek/deepseek-v4-pro` como segundo modelo de chat bajo seleccion explicita.
- `economicon-embedding` se mapea a `openai/text-embedding-3-small` con 1536 dimensiones.
- Cada alias tiene un unico despliegue; un fallo se propaga y se observa.
- Los mocks solo son validos en `test` y `development`; `evaluation` los rechaza.

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

## Limites provisionales pendientes de aprobacion

- Presupuesto de desarrollo: 10 USD/mes mediante clave virtual de LiteLLM.
- Salida maxima: 800 tokens por llamada de chat.
- Timeout: 30 segundos; reintentos: 2 solo para errores transitorios.
- Sin fallback automatico.
- Los limites definitivos se actualizaran con el benchmark y el volumen esperado.

Como referencia de orden de magnitud, ejecutar 100 casos con 2.000 tokens de entrada y 500 de salida contra los dos modelos costaria aproximadamente 0,20 USD con los precios publicados por OpenRouter el 8 de agosto de 2026. Esta cifra no incluye variaciones de routing, reintentos ni otros cargos.

## Privacidad y secretos

- `OPENROUTER_API_KEY` solo existe en el entorno del gateway.
- La clave que consume el producto es virtual, revocable y presupuestada.
- El routing solicita ZDR y `data_collection: deny`; si no hay provider compatible, falla.
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

1. Ejecutar el benchmark de `tools/llm-benchmark.py` con credenciales temporales.
2. Adjuntar resultados de calidad, p95, tokens y coste para GLM-5.2 y DeepSeek V4 Pro.
3. Aprobar presupuesto, privacidad y politica de seleccion por los cuatro miembros.
4. Auditar o aislar la instancia que vaya a desplegarse en `dockerserver`.
5. Integrar la decision mediante PR en el repositorio confirmado.

## Referencias consultadas

- [LiteLLM: gateway, claves virtuales, presupuestos y endpoints compatibles](https://docs.litellm.ai/)
- [OpenRouter: catalogo de modelos](https://openrouter.ai/api/v1/models)
- [OpenRouter: GLM-5.2](https://openrouter.ai/z-ai/glm-5.2)
- [OpenRouter: DeepSeek V4 Pro](https://openrouter.ai/deepseek/deepseek-v4-pro)
- [OpenRouter: embeddings](https://openrouter.ai/docs/api/reference/embeddings)
- [OpenRouter: Zero Data Retention](https://openrouter.ai/docs/guides/features/zdr)
- [OpenRouter: seleccion de providers](https://openrouter.ai/docs/guides/routing/provider-selection)
