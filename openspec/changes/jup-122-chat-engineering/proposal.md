# Entrega A de la interfaz conversacional

JUP: JUP-122
Trello: https://trello.com/c/gFYKmcLT

## Why

JUP-035 mezclaba infraestructura de chat con una aceptación semántica todavía
pendiente. El liderazgo confirma la división aprobada por el equipo en A/B.
La base de Paris de PR120 no está en develop: A debe incluirla para que los
arreglos de ingeniería sean aplicables. No es una PR pequeña de cinco parches.

## What Changes

- Incorporar la base f63c150 sobre develop c30a7d0, preservando JUP-119.
- Extraer carreras del stream, recuperación del planificador, UTF-8, HMAC,
  reconciliación de migraciones y cancelación de resúmenes.
- Clasificar la truncación de la búsqueda nativa conservada como transitoria.
- Desactivar por defecto el chat en Compose; impedir iniciar trabajo cuando
  el runtime esté desactivado. La activación requiere aceptación de B.
- Conservar PR120/121 como antecedentes cerrados sin merge tras publicar A.

## Capabilities

### New Capabilities
- `chat-engineering-delivery`: garantías de ingeniería y activación controlada.

## Impact

Backend, processor, frontend, migraciones y CD. JUP-123/B conserva el rediseño
semántico de PR121, scorer y campañas. No se cambia el banco JUP-069, no se
declara aceptación semántica, no se despliega ni se levanta ninguna review.
