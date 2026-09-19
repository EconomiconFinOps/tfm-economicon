# end-to-end-tracing Specification

## Purpose

El pipeline de ingesta (`POST /jobs/ingest` → RabbitMQ → `ProcessorWorker`) mantiene un único
`request_id` de principio a fin, extendiendo la correlación por request ya establecida para
peticiones HTTP síncronas (`structured-logging`) al límite asíncrono entre backend y processor.

## Requirements

### Requirement: El job de ingesta lleva el request_id de la petición HTTP que lo origina

Al publicar un job en RabbitMQ, `POST /jobs/ingest` SHALL incluir en el mensaje el `request_id` de la petición HTTP en curso.

#### Scenario: Ingesta creada desde una petición HTTP normal

- **WHEN** se completa con éxito una petición a `POST /jobs/ingest`
- **THEN** el mensaje publicado en RabbitMQ incluye un campo `request_id` con el mismo valor que el `request_id` de esa petición HTTP

### Requirement: El processor correlaciona los logs de un job con su request_id

Al consumir un mensaje de la cola de ingesta, el processor SHALL enlazar el `request_id` recibido a los logs estructurados de todo el procesamiento de ese job.

#### Scenario: Procesar un job con request_id

- **WHEN** el worker del processor consume un mensaje que incluye `request_id`
- **THEN** todos los logs emitidos durante el procesamiento de ese job (worker, tarea de ingesta, pipeline de chunking/embeddings) incluyen ese mismo `request_id`

#### Scenario: Procesar un job sin request_id

- **WHEN** el worker del processor consume un mensaje que no incluye `request_id` (publicado por una vía distinta a la HTTP, o encolado antes de esta capacidad)
- **THEN** el worker genera un identificador propio y lo enlaza a los logs de ese job, de forma que el pipeline sigue siendo trazable internamente

### Requirement: El contexto de correlación no se filtra entre jobs

El processor SHALL limpiar el contexto de correlación antes de procesar cada mensaje, de forma que el `request_id` de un job no aparezca en los logs de otro.

#### Scenario: Dos jobs consecutivos con request_id distintos

- **WHEN** el worker procesa un job y a continuación otro job con un `request_id` diferente
- **THEN** los logs del segundo job no contienen el `request_id` del primero
