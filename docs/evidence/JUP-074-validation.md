# JUP-074 — Evidencia de validación

Fecha: 2026-08-08

Rama: `feat/JUP-074-azure-cost-api`

## Alcance implementado

- Servicio FastAPI compatible con el contrato de JUP-073 para `POST /subscriptions/{subscriptionId}/providers/Microsoft.CostManagement/query`.
- Carga en memoria de las 50 filas del fixture público de Microsoft sin alterar sus valores, incluidos costes negativos y cero.
- Filtrado recursivo `and`/`or` por dimensiones y etiquetas, intervalos temporales, agrupación diaria y por hasta dos dimensiones, y suma de `PreTaxCost`.
- Respuesta determinista en formato `columns`/`rows`, errores con forma Azure y especificación OpenAPI contractual servida en `/openapi.json`.
- Imagen Docker, healthcheck y servicio `azure-cost-api` en `docker-compose.yml`.

## Validaciones automatizadas

| Comprobación | Resultado |
| --- | --- |
| `python -m pytest tests -v` en `apps/azure-cost-api` | 18 pruebas superadas |
| `python -m unittest discover -s scripts/tests -v` | 8 pruebas superadas |
| `python -m compileall -q apps/azure-cost-api/app apps/azure-cost-api/tests` | Correcto |
| Conversión de los tres artefactos JSON con `ConvertFrom-Json` | Correcto |
| `git diff --check` | Correcto; solo avisos locales de normalización LF/CRLF |
| `npx --yes @redocly/cli@2.46.0 lint docs/api/azure-cost-query.openapi.json` | Especificación válida |

Las advertencias de pytest proceden de FastAPI bajo el Python 3.14 local. La imagen de ejecución usa Python 3.12 y no presenta esas advertencias.

## Validación Docker

La imagen `economicon-azure-cost-api:jup-074` se construyó correctamente desde el `Dockerfile`. El smoke test ejecutado dentro del contenedor confirmó:

- `/health` disponible después del arranque;
- consulta contractual `daily-cost-by-resource-group` aceptada;
- 30 filas devueltas;
- columnas `PreTaxCost`, `ResourceGroup`, `UsageDate`, `Currency`;
- `nextLink` nulo.

El motor Docker de esta estación no expone el subcomando `docker compose`, por lo que la sintaxis Compose no pudo validarse con `docker compose config`. El contenedor y el mismo healthcheck definido en Compose sí se validaron directamente.

## Fuera de alcance de JUP-074

JUP-075 mantiene reservados autenticación, paginación mediante `$skiptoken` y modos de fallo configurables. Hasta implementarlos, el servicio rechaza `$skiptoken` explícitamente en lugar de simular una paginación incompleta.

La tarjeta permanece en curso hasta completar la revisión humana y la integración acordada por el equipo. Participación prevista: Lucia como lead, Paris en pair, Victor en revisión y Alejandro en validación, pruebas y documentación.
