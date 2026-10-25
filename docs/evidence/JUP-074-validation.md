# JUP-074 — Evidencia de validación

Fecha: 2026-08-25

Rama: `feat/JUP-074-azure-cost-api`

Base integrada: `develop`, commit `7c0d7a3a92bc733b91ef88aca7976499a7f4d70f`

Dependencias integradas: JUP-072 (PR #4) y JUP-073 (PR #5)

OpenSpec archivado: `openspec/changes/archive/2026-08-28-jup-074-implement-azure-cost-api/`

## Alcance implementado

- Servicio FastAPI compatible con el contrato de JUP-073 para `POST /subscriptions/{subscriptionId}/providers/Microsoft.CostManagement/query`.
- Carga en memoria de las 50 filas del fixture público de Microsoft sin alterar sus valores, incluidos costes negativos y cero.
- Filtrado recursivo `and`/`or` por dimensiones y etiquetas, intervalos temporales, agrupación diaria y por hasta dos dimensiones, y suma de `PreTaxCost`.
- Respuesta determinista en formato `columns`/`rows`, errores con forma Azure y especificación OpenAPI contractual servida en `/openapi.json`.
- Rechazo de campos no definidos por el contrato y arranque fallido si la versión del servicio difiere del OpenAPI versionado.
- Imagen Docker, healthcheck y servicio `azure-cost-api` en `docker-compose.yml`.
- Contenedor sin privilegios, filesystem de solo lectura y `no-new-privileges` en Compose.

## Validaciones automatizadas

| Comprobación | Resultado |
| --- | --- |
| `python -m pytest tests -v` en `apps/azure-cost-api` | 25 pruebas superadas |
| `python -m unittest discover -s scripts/tests -v` | 21 pruebas superadas |
| `python -m compileall -q apps/azure-cost-api/app apps/azure-cost-api/tests` | Correcto |
| Conversión de los tres artefactos JSON con `ConvertFrom-Json` | Correcto |
| `git diff --check` | Correcto; solo avisos locales de normalización LF/CRLF |
| `npx --yes @redocly/cli@2.46.0 lint docs/api/azure-cost-query.openapi.json` | Especificación válida |
| `corepack pnpm openspec:validate` | 9 especificaciones/cambios válidos |
| `corepack pnpm jup:check -- --change jup-074-implement-azure-cost-api` | Trazabilidad correcta |
| `corepack pnpm build` | Frontend, backend, processor y azure-cost-api correctos |
| `corepack pnpm test` | Backend 10/10, processor 3/3, azure-cost-api 25/25 |

Las advertencias de pytest proceden de FastAPI bajo el Python 3.14 local. La imagen de ejecución usa Python 3.12 y no presenta esas advertencias.

## Validación Docker

La imagen de Compose se construyó correctamente desde el `Dockerfile`. El smoke
test ejecutado contra el contenedor confirmó:

- `/health` disponible después del arranque;
- consulta contractual `daily-cost-by-resource-group` aceptada;
- 30 filas agrupadas devueltas;
- columnas `PreTaxCost`, `ResourceGroup`, `UsageDate`, `Currency`;
- `nextLink` nulo.

`docker compose config` validó además la configuración del servicio, el usuario
sin privilegios y el filesystem de solo lectura.

## Fuera de alcance de JUP-074

JUP-075 mantiene reservados autenticación, paginación mediante `$skiptoken` y modos de fallo configurables. Hasta implementarlos, el servicio rechaza `$skiptoken` explícitamente en lugar de simular una paginación incompleta.

La revisión, integración y evidencia final se conservan en el pull request y en
la tarjeta Trello de JUP-074. Los 49 errores `react/prop-types` ya presentes en
`develop` continúan registrados como RF-082-002 y quedan fuera de este cambio.
