# Evidencia de validación JUP-077

- Fecha: 2026-08-25.
- Repositorio oficial: `EconomiconFinOps/tfm-economicon`.
- Rama: `test/JUP-077-azure-cost-e2e`, con destino `develop`.
- Tarjeta: https://trello.com/c/2ZCQUbhr.
- Liderazgo: Alejandro Aguado; pairing: Lucia Mateo; revisión: Paris Arcos
  Martin; validación, pruebas y documentación: Victor Mendez.

## Alcance validado

- Dataset público Microsoft → API simulada Azure Cost → cliente HTTP resiliente.
- Tres páginas contractuales y normalización de 30 filas públicas.
- Preservación de costes positivos, cero y negativos sin anonimización.
- Validación de decimales finitos, divisas, fechas, dimensiones y scopes.
- Migraciones, clave foránea, estados válidos y persistencia CockroachDB.
- Identidades reproducibles, repetición idempotente y aislamiento por tenant.
- Fallo `401` controlado, cero filas residuales y logs sin token Bearer.
- Base de datos persistente con SQL y consola publicados solo en loopback.
- Compatibilidad con las tareas JUP-072 a JUP-076 ya integradas en `develop`.

## Reproducción local

```powershell
corepack pnpm install --frozen-lockfile
corepack pnpm build
corepack pnpm test
corepack pnpm openspec:validate
corepack pnpm jup:check -- --change jup-077-azure-cost-e2e
corepack pnpm jup:cleanup:check
python -m unittest discover -s scripts/tests -v
```

Las suites específicas comprueban cliente y API Azure, parser contractual,
normalización, scopes, estados, frontend, backend y pipeline preexistente.

```text
apps/processor:      94 passed
apps/azure-cost-api: 58 passed
apps/backend:        10 passed
scripts/tests:       21 passed
jup:check:test:       6 passed
jup:cleanup:test:     6 passed
OpenSpec:            12 passed, 0 failed
pnpm build/test:      4 servicios verificados correctamente
```

La advertencia de `TestClient` y las dos advertencias de longitud de clave del
fixture JWT ya existían en las suites de desarrollo y no afectan al resultado.

## Recorrido Docker reproducible

Con API simulada y CockroachDB disponibles en la red de Docker:

```powershell
docker compose run --rm --no-deps processor python -m app.run_azure_cost_ingestion `
  --tenant-id tenant-e2e `
  --subscription-id 64e355d7-997c-491d-b0c1-8414dccfcf42
```

La primera ejecución crea las migraciones formales, consulta las tres páginas y
persiste exactamente 30 registros. La segunda conserva el mismo identificador
de ejecución y reemplaza sus 30 filas sin duplicarlas. Otro tenant produce una
ejecución independiente con sus propios 30 registros.

```json
{
  "page_count": 3,
  "persisted_row_count": 30,
  "retry_count": 0,
  "row_count": 30,
  "run_id": "cdbc4aad-c920-5918-9ffb-1fefecb2ff25",
  "status": "completed",
  "tenant_id": "tenant-e2e"
}
```

Si se repite la misma ejecución con un bearer incorrecto, el comando finaliza
con código `1`, marca el estado `failed` y elimina en la misma transacción los
registros anteriores para evitar residuos o métricas inconsistentes:

```json
{"error_code": "AzureCostHttpError", "status": "failed"}
```

Consulta final directa en CockroachDB tras repetir el `401` sobre una ejecución
que antes había completado correctamente:

```text
tenant-e2e        failed     pages=0  rows=0   persisted=0  AzureCostHttpError
tenant-e2e-other  completed  pages=3  rows=30  persisted=30 NULL
migrations: 001, 002
```

Esto demuestra simultáneamente limpieza de datos obsoletos, ausencia de filas
parciales e independencia de la ejecución del otro tenant.

La salida y los eventos estructurados contienen únicamente scopes, IDs,
contadores y clases de error; nunca credenciales Bearer. El adaptador SQL
utiliza `cockroachdb+psycopg` y `sqlalchemy-cockroachdb` tanto en processor como
en backend, conservando el resto del comportamiento previo del equipo.

## Referencias de trazabilidad

- Diseño: `docs/architecture/azure-cost-e2e.md`.
- Decisión: `docs/adr/ADR-0001-azure-cost-api-simulation.md`.
- OpenSpec archivado: `openspec/changes/archive/2026-08-28-jup-077-azure-cost-e2e/`.
- Secuencia integrada: `docs/integration/JUP-072-077-stacked-integration.md`.
