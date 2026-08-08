# Flujo combinado Trello/JUP y OpenSpec

Trello controla prioridad, responsables, roles, fechas, bloqueos y estado. OpenSpec contiene requisitos, diseno y tareas tecnicas versionadas. GitHub conserva codigo, revision, CI y evidencias.

El identificador `JUP-XXX` se conserva en Trello, OpenSpec, rama, commits y pull request. No se crea una numeracion paralela.

OpenSpec es obligatorio para cambios que afecten arquitectura, seguridad, datos, IA/RAG, observabilidad, contratos externos o varios servicios. Cada tarjeta mantiene como maximo un change activo.

| Trello | Condicion tecnica |
|---|---|
| Backlog | El change puede no existir. |
| Preparado | Proposal, specs, diseno y tareas validados. |
| En curso | Implementacion iniciada en una rama JUP. |
| En revision | Pull request abierto y verificaciones registradas. |
| Validacion | Criterios funcionales comprobados. |
| Hecho | PR integrado, evidencias enlazadas y change archivado. |

Antes de implementar deben pasar `pnpm openspec:validate` y `pnpm jup:check --change <change>`. El change solo se archiva despues del merge y de la validacion registrada en Trello.
