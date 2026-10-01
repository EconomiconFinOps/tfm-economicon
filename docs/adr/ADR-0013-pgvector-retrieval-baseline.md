# ADR-0013: pgvector y recuperación exacta por tenant

- Status: Proposed
- Date: 2026-10-01
- Related JUP/OpenSpec: JUP-061, [registro de decisiones](../../openspec/changes/jup-061-architecture-decision-register/design.md)
- Trello: https://trello.com/c/qXoHFxyy
- Responsable de consolidación: Alejandro Aguado; revisión: Paris Arcos Martin; validación: Victor Mendez; pairing previsto: Lucia Mateo.
- Supersedes: none
- Superseded by: none

## Contexto

La arquitectura ya separa el estado operativo en CockroachDB y los documentos,
chunks y embeddings en PostgreSQL/pgvector. JUP-021 mantiene esa elección y
comprueba persistencia, dimensiones y recuperación; no selecciona un motor nuevo.

## Decisión documentada para ratificación

Conservar pgvector y el ranking coseno exacto con filtro de tenant. El motivo
reconstruido a partir del diseño existente es reutilizar el almacenamiento y las
transacciones del writer/reader actuales, manteniendo un resultado comprobable
sin introducir otro servicio vectorial. No se afirma que una comparativa haya
probado que pgvector es superior a otros motores.

## Alternativas y consecuencias

- Motor vectorial externo: posible, pero requeriría otro adapter, operación y
  pruebas de aislamiento/recuperación. No hay benchmark comparativo localizado.
- ANN global: el diseño JUP-021 conserva ranking exacto porque filtrar tenant
  después de una selección aproximada puede reducir resultados. Adoptarlo exige
  medir recall y latencia con el filtro real; no se acredita escalabilidad actual.
- Unificar el índice con la base operativa: cambiaría migraciones y contratos de
  ambos servicios; mantener dos almacenes preserva sus responsabilidades, a costa
  de más operación y de no tener una transacción distribuida.

La coincidencia de dimensión no acredita compatibilidad semántica entre modelos.
El baseline usa embeddings mock; 1536 dimensiones en ADR-0002 pertenece a la
propuesta externa, no demuestra que el volumen actual use ese modelo. Cambio de
modelo requiere nueva base/reingesta según JUP-021; no conversión silenciosa.

## Evidencias y aceptación pendiente

- [Arquitectura existente](../architecture.md#4-que-papel-tienen-rabbitmq-cockroachdb-y-pgvector).
- [Diseño JUP-021 en el commit revisado](https://github.com/EconomiconFinOps/tfm-economicon/blob/db2a0475214a031834fb6153de22317b20709347/openspec/changes/jup-021-vector-database-runtime/design.md).
- [Evidencia de persistencia y restauración](https://github.com/EconomiconFinOps/tfm-economicon/blob/db2a0475214a031834fb6153de22317b20709347/docs/evidence/JUP-021-validation.md).
- [PR #53](https://github.com/EconomiconFinOps/tfm-economicon/pull/53): abierta al corte;
  revisión de Paris y validación APPROVED de Victor el 01/10. No está integrada.

La evidencia de JUP-021 valida ese incremento; no es aceptación de este registro
retrospectivo ni evaluación de calidad semántica con proveedor externo.
