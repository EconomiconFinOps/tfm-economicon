# Integración de JUP-072 a JUP-075

Repositorio oficial: `https://github.com/EconomiconFinOps/tfm-economicon`.
Rama compartida: `develop`. Ninguna tarea se integra directamente sobre `main`.

## Dependencias ya integradas

| Tarea | Entrega | Pull request hacia `develop` |
| --- | --- | --- |
| JUP-072 | Dataset público Microsoft, fixtures y auditoría | #4 |
| JUP-073 | Contrato OpenAPI, mapping, casos y ADR-0001 | #5 |
| JUP-074 | Servicio FastAPI, Docker endurecido y recorrido normal | #6 |
| JUP-075 | Bearer local, paginación firmada y fallos deterministas | PR propio |

Cada pull request se limita al alcance de su tarjeta Trello. La rama
`feat/JUP-075-azure-api-resilience` incorpora primero `origin/develop` para
conservar las entregas aprobadas, sus pruebas y las especificaciones OpenSpec;
su pull request también apunta exclusivamente a `develop`.

## Validaciones de JUP-075

- Instalar el workspace con `corepack pnpm install --frozen-lockfile`.
- Ejecutar `python -m pytest tests -v` en `apps/azure-cost-api`.
- Ejecutar `python -m unittest discover -s scripts/tests -v` desde la raíz.
- Validar el contrato OpenAPI y `corepack pnpm openspec:validate`.
- Comprobar trazabilidad con
  `corepack pnpm jup:check -- --change jup-075-azure-api-resilience`.
- Ejecutar build y tests completos del monorepo.
- Construir la imagen en `dockerserver` conservando usuario sin privilegios,
  filesystem de solo lectura y `no-new-privileges`.
- Ejecutar `scripts/smoke_azure_cost_api.py` contra el servicio y recorrer
  todas las páginas sin duplicados, incluyendo `401`, `403`, `429`, `500`,
  timeout, página vacía, datos inválidos y token manipulado.
- Publicar la rama, fusionar su PR hacia `develop` y enlazarlo en Trello.

La evidencia actualizada está en `docs/evidence/JUP-075-validation.md` y el
diseño archivado en `openspec/changes/archive/2026-08-28-jup-075-azure-api-resilience/`.
