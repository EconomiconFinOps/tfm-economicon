JUP: JUP-078
ADR: docs/adr/ADR-0002-litellm-openrouter.md

## Context

El codigo actual usa mocks. Trello recoge la propuesta LiteLLM/OpenRouter y la
seleccion GLM-5.2/DeepSeek, pero faltan benchmark real, presupuesto aprobado y
conformidad verificable de los cuatro miembros. Hay un contenedor llamado
`litellm` en `dockerserver`, pero no forma parte de esta rama y no se asume que
sea reutilizable.

## Proposed Boundary

```text
backend/processor -> LiteLLM (URL + clave interna + alias) -> OpenRouter (clave upstream + modelo)
```

Los servicios solo conocen alias de Economicon. LiteLLM conserva el mapeo a modelos externos. Cada alias tiene un unico upstream: no se permite fallback silencioso.

## Selected Model Baseline

- Chat principal: `z-ai/glm-5.2`, expuesto como `economicon-chat`.
- Segundo modelo de chat: `deepseek/deepseek-v4-pro`, expuesto como `economicon-chat-deepseek`.
- Embeddings: `openai/text-embedding-3-small`, expuesto como `economicon-embedding`, con 1536 dimensiones.
- Limite provisional: 800 tokens de salida, timeout de 30 segundos y 2 reintentos.
- Techo provisional de desarrollo: 10 USD/mes mediante clave virtual de LiteLLM; requiere aprobacion.

## Security and Privacy

- La clave de OpenRouter vive solo en el entorno de LiteLLM.
- La clave maestra se configura en `general_settings.master_key`; los servicios
  reciben una clave virtual de LiteLLM, nunca la del upstream.
- Las peticiones a OpenRouter exigen `zdr: true`, `data_collection: deny` y
  `allow_fallbacks: false`; el fallback del proveedor se habilita por defecto
  si no se desactiva expresamente.
- No se registran prompts, respuestas, cabeceras Authorization ni secretos.
- La telemetria permitida contiene correlation ID, alias, upstream resuelto, estado, latencia, tokens y coste.

## Evaluation

`tools/llm-benchmark.py` ejecuta el mismo JSONL contra GLM-5.2 y DeepSeek V4
Pro, conserva solo metricas, comprueba coste/tokens y verifica terminos
esperados. El transporte rechaza redirecciones HTTP para no reenviar la clave
interna del gateway. El benchmark no decide si DeepSeek debe usarse bajo
seleccion explicita para tareas concretas; esa politica requiere revision
humana sobre exactitud FinOps, citas, formato, latencia y coste. Los resultados
mock no son admisibles.

## Migration and Rollback

1. Validar OpenSpec y configuracion local.
2. Aprobar presupuesto y crear credenciales fuera de Git.
3. Levantar una instancia aislada de LiteLLM o auditar formalmente la existente.
4. Ejecutar benchmark y aceptar o modificar el ADR.
5. Implementar clientes en una tarjeta posterior.

El rollback mantiene `development` o `test` con mocks. `evaluation` falla de forma explicita si cualquiera de los proveedores sigue siendo mock.

## Risks

- Los catalogos y precios cambian: el ADR registra la fecha y el benchmark guarda el modelo resuelto.
- Cambiar la dimension de embeddings exige una nueva coleccion y reindexacion.
- El gateway agrega un punto de fallo: se requieren healthcheck, timeout y metricas antes de desplegar.
- ZDR puede reducir la disponibilidad de providers: se prefiere un error trazable a relajar privacidad silenciosamente.
