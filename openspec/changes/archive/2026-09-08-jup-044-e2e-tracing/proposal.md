JUP: JUP-044
Trello: https://trello.com/c/XxBbQEoy

## Why

JUP-042 correlaciona logs dentro de una misma petición HTTP (`request_id` vía `RequestIdMiddleware` + `structlog.contextvars`), pero la ingesta de documentos cruza un límite asíncrono real: `POST /jobs/ingest` publica el job en RabbitMQ y un `ProcessorWorker` en un proceso distinto lo consume más tarde, sin ningún identificador de correlación. Hoy no hay forma de relacionar los logs del backend que originó una ingesta con los logs del processor que la ejecutó, ni de seguir un job concreto de principio a fin. El flujo síncrono del asistente (consulta → recuperación → respuesta) no tiene este problema, porque ya ocurre dentro de una misma petición HTTP ya correlacionada.

## What Changes

- El backend incluye el `request_id` de la petición de ingesta (o un `trace_id` derivado de él) como campo del payload publicado a RabbitMQ en `POST /jobs/ingest`.
- El `ProcessorWorker`, al consumir un mensaje, extrae ese identificador y hace `structlog.contextvars.bind_contextvars` con él antes de procesar el job — todo el pipeline posterior (`IngestTask`, `PipelineRunner`, chunking, embeddings, guardado en pgvector) hereda la correlación automáticamente, sin tocar cada función.
- Si el mensaje no trae identificador (job publicado por una vía distinta a la HTTP, o mensaje antiguo en la cola), el worker genera uno propio para no perder trazabilidad del resto del pipeline.
- Documentar la convención de trazabilidad extremo a extremo en `docs/manuals/python-service-conventions.md`, junto a la de logging (JUP-042).

## Capabilities

### New Capabilities

- `end-to-end-tracing`: exige que todo job de ingesta lleve un identificador de traza desde la petición HTTP que lo origina hasta cada log emitido por el processor al procesarlo, de forma que ambos servicios puedan correlacionarse por ese identificador.

### Modified Capabilities

(ninguna — no cambia contratos de API existentes ni comportamiento de negocio, solo añade un campo interno de correlación)

## Impact

- **Backend:** `apps/backend/app/api/routes/jobs.py` (incluir el identificador al construir el payload del job), `apps/backend/app/services/rabbitmq_queue.py` si el campo se añade ahí en vez de en el payload del caller.
- **Processor:** `apps/processor/app/workers/runner.py` (`_process_message`, bind de contextvars antes de invocar `IngestTask.execute`).
- **Documentación:** `docs/manuals/python-service-conventions.md`.
- **Sin impacto en:** contratos de API públicos (el campo es interno del mensaje de cola, no de la respuesta HTTP), esquema de base de datos, frontend.
