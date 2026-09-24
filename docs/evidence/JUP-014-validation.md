# Evidencia de validacion JUP-014

- Fecha: 2026-09-19.
- Repositorio: `EconomiconFinOps/tfm-economicon`.
- Rama: `feat/JUP-014-normalize-cost-hierarchy` hacia `develop`.
- Tarjeta: https://trello.com/c/xLIfC3am.
- Liderazgo: Lucia Mateo; pairing: Paris Arcos Martin; revision: Victor
  Mendez; validacion, pruebas y documentacion: Alejandro Aguado.

## Alcance implementado

- `ResourceId`, `ResourceName` y `BillingAccountId` expuestos como
  dimensiones consultables en la API Azure simulada
  (`docs/api/azure-cost-query-mapping.json`).
- `resource_id` y `resource_name` promovidos a campos tipados en
  `AzureCostNormalizer`, con el mismo patron de alias que JUP-013.
- Deteccion no bloqueante, dentro de una misma tanda de normalizacion, de
  un `resource_id` reportado bajo mas de un `resource_group`
  (case-insensitive, preservando el casing original por fila), persistida
  en la columna JSONB `resource_group_conflicts`.
- Migracion aditiva `004_resource_hierarchy.py`: nuevas columnas
  nullable, backfill desde `dimensions` para las dos primeras,
  `transactional = False` desde el inicio.
- Guardarraiz automatico (`app/db/migration_safety.py` +
  `tests/test_migration_safety.py`): detecta cualquier migracion que
  combine "anadir columna" + `UPDATE` en el mismo fichero sin
  `transactional = False`, cubriendo las migraciones reales (cero
  violaciones hoy) y casos reconstruidos pre/post-fix de JUP-013.
  Documentado en `docs/manuals/python-service-conventions.md`.
- `openspec/findings/backlog.md`: registrado `RF-014-001` (validacion de
  jerarquia entre ejecuciones historicas, fuera de alcance).

## Correccion durante la validacion: limite real de 2 dimensiones

El diseño original asumia que se podia anadir `ResourceId` como tercera
dimension de agrupacion junto a `ResourceGroup` + `ServiceName`. Un ensayo
real end-to-end (ver mas abajo) devolvio `400 BadRequest`: la API Azure
simulada limita `grouping` a 2 elementos
(`apps/azure-cost-api/app/models.py`, `Field(max_length=2)`), replicando
una limitacion real de Azure Cost Management.

Investigacion del historial: `ServiceName` se anadio exactamente en
JUP-013 (`bba770f`), llenando el hueco hasta el limite de 2 que ya existia
desde JUP-074 — no fue una decision deliberada de prioridad que esta
tarjeta deba respetar por encima de su propio objetivo.

Resuelto quitando `ServiceName` del `grouping` por defecto de
`run_azure_cost_ingestion.py`, quedando `ResourceId` + `ResourceGroup` — el
par que esta tarjeta necesita para la deteccion de jerarquia.
`service_name` deja de poblarse en la ingesta real por defecto, en la
misma situacion en la que ya estaban `subscription_name`/
`billing_account_id` antes de esta tarjeta (el normalizador los sabe
promover, pero la consulta por defecto no los pide). Nada en el codigo
consume `service_name` hoy (`GET /billing/summary` sigue devolviendo cifras
mock, `RF-091-004`).

## Validacion automatizada

| Comprobacion | Resultado |
| --- | --- |
| `azure-cost-api`: `pytest tests` | 59/59 |
| `processor`: `pytest tests` (sin la suite de CockroachDB real) | 273/273 |
| `processor`: `pytest tests/test_azure_cost_cockroach_integration.py` con CockroachDB 24.1.11 real desechable | 34/34 (17:25 min) |
| `pnpm openspec:validate` | 30/31 (el unico fallo, `containerized-runtime`, es preexistente en `develop`, no introducido aqui) |
| `pnpm jup:check:all` | Todos los cambios activos enlazados y completos |
| Governance/CI node tests (`jup-check`, `pr-policy`, `ci-workflow`, `delivery-roadmap`, `repository-governance`, `jup-cleanup-check`, `assistant-corpus`, `llm-gateway-config`) | 56/56 |
| Frontend: `lint` / `typecheck` / `build` | Correcto (sin tocar frontend) |
| `backend`: `pytest tests` | 115/115 (sin tocar backend) |

Ciclo RGR seguido en cada tarea de codigo de producto: test en rojo antes
de implementar, verde despues, suite completa sin regresiones, commit por
tarea.

## Validacion real de extremo a extremo

Se levanto un CockroachDB 24.1.11 desechable (sin volumen persistente,
puerto SQL solo en `127.0.0.1`, marcado con
`SET CLUSTER SETTING cluster.organization = 'processor-integration-tests'`)
y la API Azure simulada real (`uvicorn`) con el mapping actualizado de esta
tarjeta. Se ejecuto `app.run_azure_cost_ingestion` contra ambos, con
`RUNTIME_ENVIRONMENT=development` y `ALLOW_INSECURE_LOCAL_DATABASE=true`
para el opt-in local explicito.

- Resultado: `38` filas persistidas (antes `34`, con el grouping viejo
  `ResourceGroup` + `ServiceName`), cubriendo `31` recursos distintos en
  `9` resource groups distintos, para la suscripcion de muestra
  `64e355d7-997c-491d-b0c1-8414dccfcf42`.
- `38/38` filas con `resource_id` y `resource_group` poblados.
- `0` conflictos de jerarquia detectados — esperado: el dataset de muestra
  es un unico periodo estatico (menos de un mes), sin recursos que se
  muevan de resource group en la ventana consultada.
- Contenedor y base de datos manual (`jup014_manual`) desechables,
  verificados y retirados al finalizar. No se tocaron `develop` ni
  entornos compartidos.

## Bug real encontrado y corregido durante la validacion

`SqlAzureCostRepository.fetch_records` devolvia `resource_group_conflicts`
como lista de Python (JSON no distingue lista de tupla), rompiendo el
round-trip exacto con la tupla que produce `AzureCostNormalizer`. Detectado
por el test de integracion real contra CockroachDB (`test_fresh_migrations_and_repository_round_trip`),
no por los tests unitarios con conexion falsa — estos usan una conexion
simulada que nunca serializa a JSON de verdad. Corregido convirtiendo a
tupla en la lectura; 34/34 tests de integracion en verde tras el fix.

## Limitaciones y residuales

- `resource_group_conflicts` no se puede rellenar retroactivamente para
  filas ya ingeridas antes de esta tarjeta: es una senal calculada por
  lote de normalizacion, no un dato bruto disponible en `dimensions`.
  Queda `NULL` para datos historicos, documentado en `tasks.md`.
- `service_name` deja de poblarse en la ingesta real por defecto (ver
  seccion de correccion arriba). No es una regresion nueva: es la misma
  situacion en la que ya estaban `subscription_name`/`billing_account_id`.
- La validacion de jerarquia entre ejecuciones historicas de ingesta queda
  fuera de alcance, registrada como `RF-014-001`.
