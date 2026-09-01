JUP: JUP-091
Trello: https://trello.com/c/pVfcfvhu/83-jup-091-inventariar-dependencias-y-endpoints-del-frontend-economicon-origen

## Why

JUP-083 confirmó los 7 supuestos del origen (React 18.3.1, Vite 6, react-router 7, sin capa de datos
ni auth, Tailwind v4 + shadcn/ui + MUI 7, iconos lucide-react, sin variables `VITE_*`) y JUP-090
inventarió el destino con su
[línea base](../../../docs/planning/JUP-090-frontend-migration-baseline.md). Pero el spike deja dos
tareas abiertas sobre el **origen** que bloquean planificar F2 y F3 con datos reales:

- **F2 (tooling) no puede dimensionarse:** el origen declara **59 dependencias** (55 runtime +
  4 dev). Sin clasificarlas, la tarjeta de reconciliación de `package.json` trabajaría a ciegas y se
  arriesgaría a arrastrar al monorepo dependencias que aquí no aplican — justo el riesgo "arrastrar
  dependencias inútiles del origen" que el spike ya identifica.
- **F3 (porte de código) no sabe qué datos necesita:** el origen tiene 5 pantallas de analítica de
  costes (`ExecutiveCostDashboard`, `OperationalCostDashboard`, `ExecutiveCutDashboard`,
  `AnomaliesPanel`, `RecommendationsPanel`) alimentadas con datos estáticos. El backend de este repo
  solo expone `GET /billing/summary` para costes. Hasta no mapear pantalla por pantalla qué dato
  muestra cada una contra los contratos reales, no se sabe cuánto de la UI del origen es conectable
  ni cuánto backend faltaría.

## What Changes

- Crear `docs/planning/JUP-091-economicon-source-inventory.md` con dos inventarios:
  - **Dependencias:** las 59 de `../Economicon/frontend/package.json` clasificadas como
    `MANTENER` / `SUSTITUIR` / `DESCARTAR`, con justificación por dependencia o por grupo coherente
    (p. ej. los primitivos Radix de shadcn/ui).
  - **Pantallas → contratos:** las 5 rutas del origen con el dato que muestra cada una y el contrato
    del backend de este repo que debería suministrarlo, o `SIN EQUIVALENTE`.
- Registrar como finding cada pantalla o dato del origen sin contrato equivalente en el backend
  actual, sin resolverlo aquí.
- Marcar como completados los tres ítems de la tarjeta `inventariar-frontend-economicon` en
  `docs/spikes/frontend-migration.md` y enlazar el inventario.

Inspección **en solo lectura** de `../Economicon` (carpeta hermana fuera del repo), igual que
JUP-083: no se migra ni se copia código, no se instalan dependencias, no se toca `apps/frontend`.

## Capabilities

### New Capabilities

- `frontend-migration-source-inventory`: capability de **proceso** (no de producto) que exige que,
  antes de reconciliar dependencias o portar código, exista un inventario escrito del origen con
  cada dependencia clasificada y cada pantalla mapeada a un contrato del backend o marcada sin
  equivalente. Es el spec mínimo requerido por OpenSpec para un cambio doc-only; se archiva con
  `--skip-specs` y no se promociona a `openspec/specs/`.

### Modified Capabilities

<!-- Ninguna. No cambia ningún requisito de comportamiento del producto: esta HU solo produce
     documentación de planificación e inventario del repositorio origen. -->

## Impact

- **Nuevo:** `docs/planning/JUP-091-economicon-source-inventory.md`.
- **Modificado:** `docs/spikes/frontend-migration.md` (tarjeta F1 marcada + enlace al inventario) y
  `openspec/findings/backlog.md` (findings `RF-091-*`).
- **Solo lectura, fuera del repo:** `../Economicon/frontend/**`. Nada suyo se commitea aquí.
- **Solo lectura, dentro del repo:** `apps/frontend/src/services/api.js` y la línea base de JUP-090,
  como fuente de los contratos contra los que se mapea.
- **Sin código de producto, sin dependencias nuevas, sin `specs/` de producto.**
- Consumidores posteriores: F2 (`reconciliar-package-json`) usa la clasificación de dependencias;
  F3 (`portar-codigo-fuente` y `reconciliar-capa-api`) usa el mapeo pantalla → contrato.

## Human Approval

- Change: jup-091-inventory-economicon-frontend
- Approval type: pre-code
- Decision: approved
- Approver: Victor
- Date: 2026-08-31
- Carril: light
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Main risks: HU doc-only de solo lectura sobre `../Economicon`, sin código de producto. El riesgo real no es de ejecución sino de alcance: la hipótesis de trabajo es que la mayoría de las 5 pantallas del origen queden `SIN EQUIVALENTE` frente al único contrato de costes del backend (`GET /billing/summary`), lo que puede obligar a replanificar el alcance de F3 tal como está escrito hoy en el spike — se cuantificará y registrará como finding, sin resolverse aquí (tarea 4.3). Riesgo secundario: clasificar 59 dependencias puede desbordar un carril `light`, mitigado clasificando en bloque las familias coherentes (`@radix-ui/*`).
- Required changes before execution: none
- Notes: El inventario se publica en `docs/planning/JUP-091-economicon-source-inventory.md`, no dentro del change, porque lo consumen F2 y F3 y debe sobrevivir al archivado — mismo criterio que JUP-090. Los contratos se toman del código (`services/api.js` + línea base de JUP-090), no del README, aplicando lo aprendido en `RF-090-003`. Los findings se agrupan por capacidad de backend ausente, no por pantalla. Doc-only: se omiten tester/coder/mutación del harness TDD y se documenta la excepción en `review.md`; se archivará con `--skip-specs` y sin `docs/evidence/`, siguiendo el precedente de JUP-083 y JUP-090. ADR no aplicable en esta HU: documenta el estado de un repositorio externo, sin decisiones de arquitectura duraderas.
