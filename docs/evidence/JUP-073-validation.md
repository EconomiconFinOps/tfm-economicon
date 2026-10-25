# Evidencia de validación de JUP-073

- Fecha: 2026-08-25
- Rama: `docs/JUP-073-azure-cost-query-contract`
- Base integrada: `develop`, commit `c674ab504bb2c4439c941f9bb53894a27a16069a`
- Dependencia integrada: JUP-072, pull request #4
- Tarjeta: https://trello.com/c/ll3GzmuN
- OpenSpec archivado: `openspec/changes/archive/2026-08-28-jup-073-azure-cost-query-contract/`
- ADR: `docs/adr/ADR-0001-azure-cost-api-simulation.md`

## Controles ejecutados

```powershell
python -m unittest discover -s scripts/tests -v
npx --yes @redocly/cli@2.46.0 lint docs/api/azure-cost-query.openapi.json
python -m json.tool docs/api/azure-cost-query.openapi.json
python -m json.tool docs/api/azure-cost-query-mapping.json
python -m json.tool docs/api/azure-cost-query-contract-cases.json
corepack pnpm openspec:validate
corepack pnpm jup:check -- --change jup-073-azure-cost-query-contract
corepack pnpm jup:cleanup:check
corepack pnpm assistant-corpus:validate
corepack pnpm build
corepack pnpm test
git diff --check origin/develop...HEAD
```

Resultado:

- 21 pruebas documentales superadas: 13 del contrato y 8 del dataset público.
- OpenAPI 3.1 válido, sin errores ni avisos de lint.
- Los tres documentos JSON son sintácticamente válidos.
- Todas las columnas de origen del mapeo existen en
  `EA-Cost-Actual.sample.csv`.
- La suscripción de referencia existe en el fixture público integrado.
- OpenAPI exige `timePeriod` cuando el `timeframe` es `Custom`.
- Los ejemplos mantienen correspondencia posicional entre `columns` y `rows`.
- Los casos cubren agrupación, filtros de dimensión y tag, página intermedia,
  última página, ausencia de datos, versión, autenticación, scope y skip token.
- Las especificaciones OpenSpec, la trazabilidad JUP y la higiene del
  repositorio son válidas.
- `git diff --check` no detecta errores de whitespace.

## Participación prevista en Trello

- Lucía: pairing/coautoría del contrato y mapeo.
- Paris: revisión técnica del contrato y ADR-0001.
- Víctor: validación de casos y adecuación al análisis FinOps.
- Alejandro: incorporar las observaciones y coordinar la trazabilidad.

La incidencia `RF-082-002` permanece fuera del alcance de esta tarea: el lint
del frontend mantiene los mismos 49 errores `react/prop-types` ya existentes
en `develop`. JUP-073 no modifica código de `apps/`.
