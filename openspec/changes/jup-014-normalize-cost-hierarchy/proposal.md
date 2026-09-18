JUP: JUP-014
Trello: https://trello.com/c/xLIfC3am

## Why

JUP-013 promueve `billing_account_id`, `subscription_name`, `resource_group`, `service_name` y `project` como campos tipados independientes, pero no valida que la jerarquía entre ellos sea coherente, y no llega al nivel de recurso individual. Hoy, además, ni la API Azure simulada expone `ResourceId`/`ResourceName` como dimensiones consultables ni la ingesta real los pide, así que ese nivel de la jerarquía es inalcanzable en la práctica aunque el dataset origen lo traiga.

## What Changes

- Añadir `ResourceId`, `ResourceName` y `BillingAccountId` como dimensiones consultables en el mapping de la API Azure simulada (`docs/api/azure-cost-query-mapping.json`); ya existen como columnas en el fixture.
- Ampliar el `grouping` por defecto de la ingesta real (`run_azure_cost_ingestion.py`) para pedir el nivel de recurso, asumiendo el aumento de volumen de filas que eso implica.
- Promover `resource_id` y `resource_name` a campos tipados explícitos en `AzureCostNormalizer`, siguiendo el mismo patrón de alias que los campos ya promovidos por JUP-013.
- Añadir detección, dentro de una misma tanda de normalización, de un `resource_id` que aparece bajo más de un `resource_group` (comparación case-insensitive). **No bloquea la ingesta ni la fila** — un resource group es mutable en Azure real y un recurso puede moverse legítimamente dentro de la ventana de tiempo consultada. La anomalía se persiste como señal visible, no como error.
- Registrar como finding nuevo, explícitamente fuera de alcance, la validación de jerarquía **entre** ejecuciones de ingesta históricas (ej. un `resource_group` que aparece bajo una subscription distinta en una ingesta anterior) — requeriría consultar CockroachDB vía el repositorio, no cabe en el normalizador stateless actual.
- La jerarquía tenant → subscription **no se toca**: ya está garantizada estructuralmente por el `subscription_id` de scope de la ingesta (`AzureCostIngestionService.ingest`), independiente de los datos de la fila.
- Añadir una comprobación automática (test) que detecte migraciones que añaden columnas y las rellenan (backfill) en el mismo fichero sin declarar `transactional = False`, para no depender de que cada persona recuerde el defecto de visibilidad de DDL que ya corrigió JUP-013 (ver `docs/manuals/python-service-conventions.md`, hueco detectado durante esta exploración: hoy no hay ninguna sección sobre convenciones de migraciones).

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `azure-cost-normalization`: se añaden los campos tipados `resource_id`/`resource_name` y el requisito de detección no bloqueante de inconsistencia `resource_id` → `resource_group` dentro de la tanda.

## Impact

- `docs/api/azure-cost-query-mapping.json` (API Azure simulada) — cambio de configuración, sin tocar código Python de `apps/azure-cost-api`.
- `apps/processor/app/run_azure_cost_ingestion.py` — `DEFAULT_DEFINITION.dataset.grouping`.
- `apps/processor/app/normalization/azure_cost.py` — nuevos campos promovidos y la detección de inconsistencia.
- `apps/processor/app/db/migrations/` — nueva migración aditiva para persistir `resource_id`, `resource_name` y la señal de inconsistencia.
- `openspec/findings/backlog.md` — nuevo finding para la validación histórica entre ejecuciones, fuera de alcance.
- Volumen de filas ingeridas: aumenta al pasar de agrupar por resource group a agrupar por recurso individual.
