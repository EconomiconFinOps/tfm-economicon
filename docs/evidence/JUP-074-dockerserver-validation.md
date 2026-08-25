# JUP-074 — Histórico de validación inicial en dockerserver

Fecha: 2026-08-08

## Despliegue aislado

- Host: `dockerserver`.
- Commit desplegado: `9dae75c`.
- Directorio: `/home/danteadmin/economicon-deployments/jup-074-9dae75c`.
- Proyecto Compose: `economicon-jup074`.
- Servicio: `economicon-jup074-azure-cost-api-1`.
- Puerto de pruebas: `18002` del host hacia `8002` del contenedor.

El despliegue se realizó con:

```bash
AZURE_COST_API_PORT=18002 docker compose -p economicon-jup074 up -d --build azure-cost-api
```

## Evidencia

`docker compose ps` informó `Up (healthy)`. El healthcheck consultado desde el
host y desde la estación de desarrollo devolvió:

```json
{"status":"ok","dataset":"EA-Cost-Actual.sample.csv","rows":50,"subscriptions":4}
```

Una consulta contractual realizada desde la estación de desarrollo contra
`http://dockerserver:18002` devolvió:

- HTTP `200`;
- 30 filas;
- columnas `PreTaxCost`, `ResourceGroup`, `UsageDate`, `Currency`;
- `nextLink: null`.

Esto prueba construcción y arranque mediante Docker Compose, healthcheck dentro
del servidor y acceso HTTP desde fuera del contenedor y del propio host.

Este resultado corresponde al despliegue histórico del 2026-08-08; no implica
que ese contenedor o puerto sigan activos. La evidencia vigente de la entrega
integrada está en `docs/evidence/JUP-074-validation.md`; JUP-075 mantiene su
propia validación actualizada en `docs/evidence/JUP-075-validation.md`.
