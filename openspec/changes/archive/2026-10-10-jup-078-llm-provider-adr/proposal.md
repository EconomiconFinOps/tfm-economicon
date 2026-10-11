JUP: JUP-078
Trello: https://trello.com/c/M4zqDGlW

## Why

Actualizacion 2026-10-10: ADR-0002 ya aceptado e integrado por PR #71. Este
cierre implementa el seguimiento operativo de claves en un gateway dedicado
de DockerServer. No modifica el gateway compartido ni repite el benchmark.
Las interacciones nuevas del equipo se sustituyen por subagentes por
autorizacion expresa del usuario, sin atribuir aprobaciones humanas nuevas.
Los apartados originales siguientes conservan su contexto historico.

Economicon solo dispone de proveedores mock. El equipo necesita decidir y validar una frontera reproducible para chat y embeddings reales antes de evaluar el RAG del MVP.

## What Changes

- Proponer LiteLLM como gateway interno y OpenRouter como upstream.
- Fijar alias logicos para GLM-5.2 y DeepSeek V4 Pro, dimensiones y limites provisionales.
- Impedir mocks en el modo de evaluacion y fallar ante configuraciones incompletas.
- Definir privacidad, secretos, telemetria, coste y un benchmark reproducible.
- Ejecutar un benchmark autenticado y mantener la decision en estado propuesto
  hasta que los cuatro miembros revisen sus hallazgos y aprueben el ADR.

## Capabilities

### New Capabilities

- `llm-provider-routing`: acceso configurable y observable a chat y embeddings sin acoplar los servicios a identificadores de proveedor.

### Modified Capabilities

- Ninguna.

## Out of Scope

- Implementar clientes reales de chat o embeddings en los servicios.
- Desplegar o modificar el contenedor LiteLLM compartido de `dockerserver`.
- Activar fallback automatico o guardar credenciales en Git.
- Aprobar unilateralmente el presupuesto o la decision definitiva del equipo.

## Impact

Afecta a configuracion del processor, despliegue futuro, secretos, observabilidad, evaluacion RAG y coste. El ADR asociado permanece `Proposed` hasta contar con evidencia y aprobacion humana.
