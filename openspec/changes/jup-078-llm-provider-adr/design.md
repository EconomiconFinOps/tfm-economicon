JUP: JUP-078
ADR propuesto: `docs/adr/ADR-0002-litellm-openrouter.md`

## Context

El codigo actual usa mocks. No existe en Discord, Trello ni el repositorio una decision aprobada sobre LiteLLM, OpenRouter, modelos o presupuesto. Hay un contenedor llamado `litellm` en `dockerserver`, pero no forma parte de esta rama y no se asume que sea reutilizable.

## Proposed Boundary

```text
backend/processor -> LiteLLM (URL + clave interna + alias) -> OpenRouter (clave upstream + modelo)
```

Los servicios solo conocen `economicon-chat` y `economicon-embedding`. LiteLLM conserva el mapeo a modelos externos. Cada alias tiene un unico upstream: no se permite fallback silencioso.

## Candidate Baseline

- Chat recomendado: `openai/gpt-5-mini`, expuesto como `economicon-chat`.
- Chat comparativo: `google/gemini-2.5-flash-lite`, expuesto como `economicon-chat-candidate` solo durante el benchmark.
- Embeddings: `openai/text-embedding-3-small`, expuesto como `economicon-embedding`, con 1536 dimensiones.
- Limite provisional: 800 tokens de salida, timeout de 30 segundos y 2 reintentos.
- Techo provisional de desarrollo: 10 USD/mes mediante clave virtual de LiteLLM; requiere aprobacion.

## Security and Privacy

- La clave de OpenRouter vive solo en el entorno de LiteLLM.
- Los servicios reciben una clave virtual de LiteLLM, nunca la del upstream.
- Las peticiones a OpenRouter exigen routing ZDR y deniegan proveedores que recopilan datos.
- No se registran prompts, respuestas, cabeceras Authorization ni secretos.
- La telemetria permitida contiene correlation ID, alias, upstream resuelto, estado, latencia, tokens y coste.

## Evaluation

`tools/llm-benchmark.py` ejecuta el mismo JSONL contra ambos alias, conserva solo metricas y verifica terminos esperados. La decision requiere despues revision humana sobre exactitud FinOps, citas, formato, latencia y coste. Los resultados mock no son admisibles.

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
