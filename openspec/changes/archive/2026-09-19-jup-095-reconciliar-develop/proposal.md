JUP: JUP-095
Trello: https://trello.com/c/G4FPtBdE/87-jup-095-portar-el-c%C3%B3digo-fuente-del-frontend-de-economicon

## Why

[JUP-095](../archive/2026-09-12-jup-095-portar-codigo-fuente/) cerró archivada (40/40 tareas) desde
un punto de `develop` anterior a [PR #29](https://github.com/EconomiconFinOps/tfm-economicon/pull/29)
(JUP-087, línea base de calidad del frontend) y a [PR #34](https://github.com/EconomiconFinOps/tfm-economicon/pull/34)
(JUP-020). Su propia rama, al abrir [PR #36](https://github.com/EconomiconFinOps/tfm-economicon/pull/36),
generaba 17 rutas en conflicto con `develop`, y una revisión de compatibilidad detectó cinco
comportamientos que la rama de JUP-095 no incorporaba: contraseña de demostración precargada, sesión
sin validar su forma, errores de listado/detalle de conversaciones ocultos, capacidades del backend
sin enlace de menú y ausencia de aislamiento de estado entre tenants. Esta tarjeta reconcilia ambas
ramas y corrige esos cinco puntos, sin abrir un número JUP nuevo: es continuación del mismo trabajo,
ya en la rama `feat/JUP-095-portar-codigo-fuente`.

## What Changes

- Se fusiona `develop` (con JUP-087 y JUP-020 ya integradas) en la rama de JUP-095, resolviendo 17
  conflictos: se conservan el router, las pantallas y los estilos de JUP-095, y los contratos tipados
  (`api.ts`/`contracts.ts`), la regresión y la configuración de calidad de `develop`.
- Se corrigen dos "conflictos silenciosos" que el merge automático dejaba rotos sin marcador: las
  páginas que importaban el antiguo `services/api.js` sin tipar quedan adaptadas a `api.ts`/
  `contracts.ts`, y se retira el job `frontend-tests` duplicado que la fusión de `ci.yml` introducía
  (ejecutaba la suite dos veces), manteniendo los siete checks ya activos en GitHub.
- **BREAKING (comportamiento restaurado, no nuevo)**: el campo de contraseña del login vuelve a
  arrancar vacío (ya no precarga `"secret"`), y los errores de listado/detalle de conversaciones
  vuelven a mostrarse (`role="alert"`) en vez de presentarse como una lista vacía. Ambos ya estaban
  exigidos por specs existentes (`demo-auth-credentials`, `frontend-quality-baseline`); esta tarjeta
  hace que el código fusionado vuelva a cumplirlos.
- Se adaptan las cinco suites de test heredadas de `develop` (JUP-087) a la arquitectura de router de
  JUP-095 (`createMemoryRouter`), incluida la suite de aislamiento de tenant, antes bloqueada por
  falta de la funcionalidad que ahora se implementa.
- **Nuevo**: una frontera de remontaje por tenant (`TenantScopedOutlet`) alrededor de `/ingest` y
  `/assistant` reinicia formularios, selección y resultados de mutaciones pendientes al cambiar de
  tenant, y evita que una respuesta tardía de una mutación del tenant anterior altere el estado del
  nuevo tenant.
- **Nuevo**: `SessionGate` valida la forma de la sesión persistida (`isSession`, trasladado de
  `develop`) antes de confiar en ella; un JSON válido con estructura inválida (p.ej. `{}`) ya no se
  acepta como sesión.
- **Nuevo**: el menú de navegación enlaza `/ingest`, `/assistant` y `/overview-legacy` (antes solo
  alcanzables escribiendo la URL), separados visualmente de las cinco pantallas de demostración.

## Capabilities

### New Capabilities

(ninguna: todo lo nuevo encaja en la capacidad existente `frontend-navigation-shell`)

### Modified Capabilities

- `frontend-navigation-shell`: nuevos requisitos de aislamiento de estado entre tenants, validación
  de la sesión persistida, y alcanzabilidad de las pantallas conectadas al backend desde el menú (no
  solo por URL directa).

## Impact

- Código: `apps/frontend/src/App.tsx`, `main.tsx`, `layouts/SessionGate.tsx`, `layouts/Layout.tsx`,
  `routes.tsx`, `components/{MetricCard,SectionCard,StatusPill}.tsx`, `pages/{Login,Ingest,
  Conversations,Dashboard}Page.tsx`, `vite.config.ts`, `package.json`, `pnpm-lock.yaml`.
- Tests: `apps/frontend/tests/*.test.tsx` (adaptadas a `createMemoryRouter`),
  `src/layouts/SessionGate*.test.tsx` (fixture corregido + cobertura nueva),
  `src/pages/LoginPage.mutation.test.tsx` (valor por defecto corregido).
- CI/gobernanza: `.github/workflows/ci.yml`, `.github/rulesets/{develop,main}.json`,
  `tools/ci-workflow.test.mjs`, `docs/governance/github-branch-protection.md`.
- Documentación: `apps/frontend/README.md`, `openspec/findings/backlog.md` (RF-082-002 fusionado sin
  perder evidencia histórica de ninguna de las dos ramas).
- No afecta a backend ni processor: los hallazgos abiertos que los tocan (CORS de JUP-085, JSONB del
  historial de JUP-035, migraciones concurrentes) quedan fuera de esta tarjeta.
