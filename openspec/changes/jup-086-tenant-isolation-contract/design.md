JUP: JUP-086
ADR: pendiente solo si la implementacion cambia el modelo de identidad o la frontera de confianza actual.

## Context

El usuario autenticado se relaciona con tenants mediante `user_tenants`.
FastAPI valida la cabecera `X-Tenant-Id`, pero algunos payloads tambien contienen
`tenant_id`; los jobs atraviesan RabbitMQ y el retrieval consulta pgvector. Cada
salto debe conservar el tenant ya autorizado sin permitir su sustitucion.

## Goals / Non-Goals

**Goals:**

- Definir una fuente autorizada de tenant por request y por job.
- Inventariar todas las entidades tenant-aware y sus filtros obligatorios.
- Evitar enumeracion y acceso cruzado en API, SQL, cola, vector store y agente.
- Hacer reproducibles las pruebas negativas.

**Non-Goals:**

- Crear tenants de Azure reales o un panel de administracion de organizaciones.
- Diseñar RBAC detallado mas alla de pertenencia y rol ya persistidos.
- Permitir que el LLM elija o cambie el tenant.

## Decisions

### La sesion autoriza y la cabecera selecciona

El bearer identifica al usuario. `X-Tenant-Id` selecciona uno de sus tenants,
pero solo se acepta tras consultar `user_tenants`. Un `tenant_id` repetido en el
payload debe coincidir exactamente; no se convierte en una segunda autoridad.

### El contexto autorizado se propaga de forma inmutable

El backend publica en cada job el tenant autorizado y la identidad creadora. El
processor usa ese contexto para escrituras operativas y vectoriales. Parametros
de usuario, contenido documental y argumentos producidos por el LLM no pueden
sobrescribirlo.

### Las consultas incluyen tenant en el predicado de pertenencia

Buscar por ID y comprobar despues no es suficiente cuando revela existencia.
Conversaciones, mensajes, jobs, costes, documentos, chunks y embeddings se
resuelven dentro del mismo predicado tenant; un recurso ajeno se comporta como
no encontrado cuando el endpoint opera sobre un ID opaco.

### Matriz de errores

- `401`: identidad ausente o invalida.
- `400`: una operacion tenant-aware no incluye selector o payload y cabecera discrepan.
- `403`: el tenant seleccionado no pertenece al usuario, sin datos adicionales.
- `404`: un recurso opaco no existe dentro del tenant autorizado.

## Risks / Trade-offs

- [Filtros olvidados en un repositorio nuevo] -> matriz versionada y pruebas de
  contrato por tipo de recurso.
- [Job manipulado] -> tenant inmutable, validacion de esquema y correlacion con
  el creador antes de persistir.
- [LLM intenta cambiar contexto] -> herramientas reciben tenant del runtime,
  nunca de argumentos libres del modelo.
- [Errores permiten enumeracion] -> mensajes genericos y busqueda tenant-scoped.
