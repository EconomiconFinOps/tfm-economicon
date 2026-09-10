JUP: JUP-044

ADR no aplicable: extiende la convención de correlación ya establecida en JUP-042 (mismo patrón `structlog.contextvars`, sin dependencia nueva ni cambio de límites de servicio); no introduce una decisión de arquitectura duradera distinta a la ya registrada allí.

## Context

`POST /jobs/ingest` (`apps/backend/app/api/routes/jobs.py`) construye un `job` (vía `Database.create_job`) y lo publica en RabbitMQ con `queue.publish(job)` (`apps/backend/app/services/rabbitmq_queue.py`), como `json.dumps(payload)` sin ningún campo de correlación. El `ProcessorWorker` (`apps/processor/app/workers/runner.py`) consume ese mensaje en un bucle síncrono (`run_forever`, un mensaje a la vez, sin concurrencia) y lo pasa a `IngestTask.execute` → `PipelineRunner.run` (`apps/processor/app/graphs/pipeline.py`: chunking, embeddings, guardado en pgvector), sin enlazar ningún `request_id` a sus logs.

El patrón de correlación ya existe para peticiones HTTP síncronas desde JUP-042: `RequestIdMiddleware` genera un `request_id`, hace `structlog.contextvars.bind_contextvars(request_id=...)` al empezar la petición y `clear_contextvars()` antes de eso — todos los `structlog.get_logger(...)` de esa petición heredan el `request_id` automáticamente. Esta HU extiende el mismo patrón al límite asíncrono HTTP → cola → worker.

## Goals / Non-Goals

**Goals:**

- El `request_id` de la petición HTTP que crea un job de ingesta viaja dentro del mensaje publicado a RabbitMQ.
- El `ProcessorWorker`, al consumir un mensaje, enlaza ese `request_id` a `structlog.contextvars` antes de procesar el job, de forma que todos los logs de `IngestTask`, `PipelineRunner` y sus dependencias (chunker, embeddings, vector store) lo hereden sin cambios en cada función.
- Si un mensaje no trae `request_id` (publicado por una vía no HTTP, o ya en la cola antes de este cambio), el worker genera uno propio para no perder trazabilidad del resto del pipeline de ese job.
- El worker limpia el contexto entre mensajes, para que el `request_id` de un job no se filtre al siguiente.

**Non-Goals:**

- Tracing distribuido con spans (OpenTelemetry/Jaeger/Zipkin): no hay esa librería en el proyecto y el volumen actual no lo justifica: un identificador simple de correlación basta.
- Trazar el pipeline batch de ingesta de costes Azure (`apps/processor/app/clients/azure_cost.py`, `run_azure_cost_ingestion.py`): es un flujo CLI independiente, no forma parte de ingesta-de-documentos → respuesta del agente.
- Cambiar el contrato de `POST /jobs/ingest` ni el de `IngestJobResponse`: el `request_id` viaja dentro del mensaje interno de cola, no en la respuesta HTTP.
- Persistir el `request_id` en la tabla `jobs`: esta HU correlaciona logs, no añade una columna de auditoría (se puede proponer aparte si hace falta consultarlo después de que termine el job).

## Decisions

- **Reusar el nombre de campo `request_id` en el mensaje de cola y en los logs del worker**, en vez de introducir un `trace_id` distinto. Es el mismo concepto (un identificador que agrupa todo lo que pasó por una petición de ingesta) y reusar el nombre permite buscar por `request_id` en los logs agregados de ambos servicios sin traducir entre campos. Alternativa descartada: `trace_id` propio — añadiría un segundo vocabulario para la misma idea sin beneficio real a este tamaño de proyecto.

- **Leer el `request_id` de `structlog.contextvars` en el momento de publicar, no del objeto `Request`.** En `apps/backend/app/api/routes/jobs.py`, tras `queue.publish(job)` fallando o antes de publicar, se lee `structlog.contextvars.get_contextvars().get("request_id")` y se añade a `job["request_id"]`. Consistente con cómo `RequestIdMiddleware` ya expone el valor, sin pasar `Request` a capas que no lo necesitan.

- **Bind y clear en el worker, alrededor de cada mensaje, no dentro de `IngestTask`.** `ProcessorWorker._process_message` extrae `message.payload.get("request_id")` (con `uuid4()` de fallback si falta), hace `structlog.contextvars.clear_contextvars()` seguido de `bind_contextvars(request_id=...)` antes de `self.task.execute(job)`. Mismo patrón que `RequestIdMiddleware`, en el único punto de entrada real de cada job — evita tocar `IngestTask`, `PipelineRunner` ni sus dependencias.

- **Sin persistencia en base de datos.** El `request_id` vive en el mensaje de cola y en los logs; no se añade columna a `jobs`. Si el negocio necesita consultar el trace de un job ya terminado desde la API, es una HU distinta con su propio contrato.

## Risks / Trade-offs

- **Mensajes ya en la cola antes de este cambio no tienen `request_id`.** → El fallback (`uuid4()` generado por el worker) asegura que el pipeline de ese job siga teniendo un identificador único en sus logs, aunque no enlace con la petición HTTP original (que además, en la práctica, ya habrá devuelto su respuesta 202 hace tiempo).
- **El worker es de un solo hilo/mensaje a la vez** (`run_forever` procesa secuencialmente), así que `bind_contextvars`/`clear_contextvars` global por mensaje es seguro sin condiciones de carrera. Si en el futuro el worker se paraleliza (varios mensajes concurrentes en el mismo proceso), este mecanismo dejaría de ser seguro y habría que revisar el patrón — anotado como riesgo futuro, no aplicable hoy.
- **Reintentos (`nack` con `requeue=True`).** Si un job se reintenta tras un fallo, el mensaje reencolado conserva el mismo `request_id` (viaja en el payload), así que los logs del reintento siguen correlacionados con el intento original — comportamiento deseado, no un riesgo.

## Migration Plan

1. Backend: añadir `request_id` al `job` antes de `queue.publish(job)` en `apps/backend/app/api/routes/jobs.py`.
2. Processor: extraer `request_id` del mensaje (con fallback) y hacer bind/clear de contextvars en `ProcessorWorker._process_message` (`apps/processor/app/workers/runner.py`).
3. Documentar la convención en `docs/manuals/python-service-conventions.md`.
4. **Rollback:** revertir ambos cambios; no hay migración de datos ni cambio de contrato de API pública. Los mensajes en cola siguen siendo válidos con o sin el campo `request_id` (el worker ya lo trata como opcional).

## Open Questions

Ninguna abierta: el alcance quedó acotado explícitamente al pipeline de ingesta de documentos (excluyendo Azure cost) tras la investigación previa a esta propuesta.
