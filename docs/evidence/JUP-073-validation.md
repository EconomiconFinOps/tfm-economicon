# Evidencia de validación de JUP-073

- Fecha: 2026-08-08
- Rama: `docs/JUP-073-azure-cost-query-contract`
- Base apilada: JUP-072, commit `61262c9`
- Tarjeta: https://trello.com/c/ll3GzmuN

## Controles ejecutados

```powershell
python -m unittest discover -s scripts/tests -v
npx --yes @redocly/cli@2.46.0 lint docs/api/azure-cost-query.openapi.json
python -m json.tool docs/api/azure-cost-query.openapi.json
python -m json.tool docs/api/azure-cost-query-mapping.json
python -m json.tool docs/api/azure-cost-query-contract-cases.json
git diff --check
```

Resultado:

- 8 pruebas superadas.
- OpenAPI 3.1 válido, sin errores ni avisos de lint.
- Los tres documentos JSON son sintácticamente válidos.
- Todas las columnas de origen del mapeo existen en
  `EA-Cost-Actual.sample.csv`.
- Los ejemplos mantienen correspondencia posicional entre `columns` y `rows`.
- Los casos cubren agrupación, filtros de dimensión y tag, página intermedia,
  última página, ausencia de datos, versión, autenticación, scope y skip token.
- `git diff --check` no detecta errores de whitespace.

## Pendiente de validación humana

- Lucía: pairing/coautoría del contrato y mapeo.
- Paris: revisión técnica y aceptación de ADR-0001.
- Víctor: validación de casos y adecuación al análisis FinOps.
- Alejandro: incorporar las observaciones y coordinar la trazabilidad.

`openspec:validate` y `jup:check` se ejecutarán cuando JUP-048 se integre en la
rama compartida. La ausencia temporal de OpenSpec no invalida los artefactos
OpenAPI ni las pruebas autónomas de esta rama.
