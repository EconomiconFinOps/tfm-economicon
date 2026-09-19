JUP: JUP-086
Trello: https://trello.com/c/bKxQK9HI

## Why

El baseline valida `X-Tenant-Id` en varias rutas y filtra conversaciones y
pgvector, pero el aislamiento completo no esta especificado extremo a extremo.
El tenant no puede depender de un identificador elegido por el cliente, el job
o el modelo sin comprobarlo contra la sesion autorizada.

## What Changes

- Definir el limite de confianza entre sesion, cabecera, payload, cola, worker,
  persistencia, retrieval y herramientas del agente.
- Exigir aislamiento para costes, jobs, conversaciones, mensajes, documentos,
  chunks y embeddings.
- Fijar respuestas `400`, `401`, `403` y `404` que no revelen recursos ajenos.
- Exigir pruebas negativas de lectura y escritura cruzadas.

## Capabilities

### New Capabilities

- `tenant-isolation`: autorizacion y propagacion de contexto tenant verificables
  en todos los limites de datos del MVP.

### Modified Capabilities

- None.

## Impact

- Afecta dependencias FastAPI, repositorios, payloads de jobs, RabbitMQ,
  processor, CockroachDB, pgvector y contexto seguro de herramientas JUP-084.
- No introduce administracion multi-organizacion ni aprovisionamiento de Azure.
