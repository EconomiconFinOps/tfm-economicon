# ADR-0002: LiteLLM como gateway y OpenRouter como upstream

- Estado: Proposed
- Fecha: 2026-08-08
- Tarjeta: [JUP-078](https://trello.com/c/M4zqDGlW)
- Decision requerida antes de: octubre de 2026

## Contexto

Economicon necesita chat y embeddings reales para evaluar su RAG, pero el codigo actual solo implementa mocks. El equipo no dispone de un tenant de Azure AI y quiere evitar que backend y processor queden acoplados a credenciales, catalogos y politicas de un proveedor externo.

No se encontro una decision aprobada en el repositorio ni en la exportacion de Discord. Esta propuesta debe ser revisada por Lucia, Paris, Victor y Alejandro y validada con un benchmark real.

## Decision propuesta

Usar LiteLLM como gateway interno OpenAI-compatible y OpenRouter como unico upstream inicial.

- Los servicios usan `LITELLM_BASE_URL`, `LITELLM_API_KEY` y alias logicos.
- `economicon-chat` se mapea inicialmente a `openai/gpt-5-mini`.
- `economicon-embedding` se mapea a `openai/text-embedding-3-small` con 1536 dimensiones.
- `google/gemini-2.5-flash-lite` se mantiene como candidato comparativo por coste, no como fallback.
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

Como referencia de orden de magnitud, 100 casos con 2.000 tokens de entrada y 500 de salida costarian aproximadamente 0,15 USD con los precios publicados para GPT-5 mini el 8 de agosto de 2026. Esta cifra no incluye variaciones de routing, reintentos ni otros cargos.

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
2. Adjuntar resultados de calidad, p95, tokens y coste.
3. Aprobar modelo, presupuesto y privacidad por los cuatro miembros.
4. Auditar o aislar la instancia que vaya a desplegarse en `dockerserver`.
5. Integrar la decision mediante PR en el repositorio confirmado.

## Referencias consultadas

- [LiteLLM: gateway, claves virtuales, presupuestos y endpoints compatibles](https://docs.litellm.ai/)
- [OpenRouter: catalogo de modelos](https://openrouter.ai/api/v1/models)
- [OpenRouter: embeddings](https://openrouter.ai/docs/api/reference/embeddings)
- [OpenRouter: Zero Data Retention](https://openrouter.ai/docs/guides/features/zdr)
- [OpenRouter: seleccion de providers](https://openrouter.ai/docs/guides/routing/provider-selection)
