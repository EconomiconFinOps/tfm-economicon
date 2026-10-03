# ADR-0013: pgvector y recuperación exacta por tenant

- Status: Proposed
- Date: 2026-10-01
- Related JUP/OpenSpec: JUP-061, [contrato de registro de decisiones](../../openspec/specs/architecture-decisions/spec.md)
- Trello: https://trello.com/c/qXoHFxyy
- Responsable de consolidación: Alejandro Aguado; revisión: Paris Arcos Martin; validación: Lucia Mateo; pairing previsto: Victor Mendez.
- Roles actualizados: 2026-10-03; intercambio Lucia/Victor documentado en [validación de Lucia](https://github.com/EconomiconFinOps/tfm-economicon/pull/60#pullrequestreview-5396865126). No acredita pairing realizado.
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
- [Diseño JUP-021 integrado](../../openspec/changes/archive/2026-10-02-jup-021-vector-database-runtime/design.md).
- [Evidencia de persistencia y restauración](../evidence/JUP-021-validation.md).
- [PR #53](https://github.com/EconomiconFinOps/tfm-economicon/pull/53): integrada el 02/10/2026 UTC;
  revisión de Paris y validación APPROVED vigente de Victor el 02/10 a las
+  19:56 UTC. La aprobación del 01/10 quedó descartada por un push posterior. El corte inicial
  del 01/10 la registraba abierta; la integración no ratifica este ADR.

La evidencia de JUP-021 valida ese incremento; no es aceptación de este registro
retrospectivo ni evaluación de calidad semántica con proveedor externo.
