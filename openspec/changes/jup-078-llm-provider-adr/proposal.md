JUP: JUP-078
Trello: https://trello.com/c/M4zqDGlW

## Why

Economicon solo dispone de proveedores mock. El equipo necesita decidir y validar una frontera reproducible para chat y embeddings reales antes de evaluar el RAG del MVP.

## What Changes

- Proponer LiteLLM como gateway interno y OpenRouter como upstream.
- Fijar alias logicos, candidatos de modelos, dimensiones y limites provisionales.
- Impedir mocks en el modo de evaluacion y fallar ante configuraciones incompletas.
- Definir privacidad, secretos, telemetria, coste y un benchmark reproducible.
- Mantener la decision en estado propuesto hasta la aprobacion de los cuatro miembros y el benchmark real.

## Capabilities

### New Capabilities

- `llm-provider-routing`: acceso configurable y observable a chat y embeddings sin acoplar los servicios a identificadores de proveedor.

### Modified Capabilities

- Ninguna.

## Out of Scope

- Implementar clientes reales de chat o embeddings en los servicios.
- Desplegar o modificar el contenedor LiteLLM compartido de `dockerserver`.
- Activar fallback automatico, aportar credenciales o aprobar gasto real.

## Impact

Afecta a configuracion del processor, despliegue futuro, secretos, observabilidad, evaluacion RAG y coste. El ADR asociado permanece `Proposed` hasta contar con evidencia y aprobacion humana.
