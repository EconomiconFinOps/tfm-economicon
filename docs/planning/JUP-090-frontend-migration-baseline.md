# Línea base de migración del frontend (JUP-090)

JUP: JUP-090
Trello: https://trello.com/c/DtlNd0u0/82-jup-090-inventariar-frontend-actual
OpenSpec change: `openspec/changes/jup-090-inventory-current-frontend/`
Rama: `docs/JUP-090-inventory-current-frontend`
Commit base del inventario: `0967692`

## Alcance

Este documento es la línea base de la épica *Migrar frontend del repositorio Economicon* para el
**destino** (`apps/frontend` en este repo). Clasifica cada archivo y punto de integración como:

- **PRESERVAR** — se mantiene sin cambios funcionales al reemplazar el frontend.
- **REEMPLAZAR** — se sustituye por completo por el código/config de Economicon.
- **RECONCILIAR** — requiere fusión dirigida: parte del origen, parte del destino.

Fuera de este inventario quedan los artefactos generados y no versionados:
`apps/frontend/node_modules/**` y cualquier caché de build (`node_modules/.vite`).

El inventario del **origen** (Economicon) no es objeto de este documento: ya está cubierto por
JUP-083 ([docs/spikes/frontend-migration.md](../spikes/frontend-migration.md)) y por la tarjeta
`jup-0xx-inventariar-frontend-economicon` de F1.

## Qué se preserva del destino

<!-- Se completa en la tarea 2.2/2.3 -->

## Clasificación archivo a archivo

Leyenda: **PRESERVAR** (sin cambio funcional, aunque cambie de extensión a `.ts`/`.tsx`) ·
**REEMPLAZAR** (sustituido por completo por el origen) · **RECONCILIAR** (fusión dirigida: chrome o
estructura del origen + lógica del destino, que el origen no tiene).

### `apps/frontend/src/**`

| Archivo | Clasificación | Justificación |
| --- | --- | --- |
| `src/App.jsx` | RECONCILIAR | Concentra sesión (`localStorage.finops.session`), tenant activo (`finops.activeTenant`), login/logout y el fetch de tenants vía TanStack Query (líneas 35-94). Esa lógica no existe en el origen (T4/T3 de JUP-083) y debe sobrevivir; solo el enrutado manual por `activeView` (líneas 127-150) se descarta a favor de `react-router` 7. |
| `src/main.jsx` | RECONCILIAR | Hoy solo monta `QueryClientProvider` (líneas 7-14). El origen monta `createBrowserRouter`/`RouterProvider` en su `main.tsx` (T2). El entrypoint final necesita ambos providers, portado a `.tsx`. |
| `src/layouts/AppShell.jsx` | RECONCILIAR | El chrome visual (sidebar, nav) se reemplaza por el `Layout` del origen (Tailwind v4 + shadcn/ui, T5), pero el selector de tenant (líneas 36-50) y el panel de sesión/logout (líneas 52-61) son capacidades del destino sin equivalente en el origen y deben injertarse en el nuevo `Layout`. |
| `src/pages/LoginPage.jsx` | RECONCILIAR | El origen no tiene pantalla de login (T4). Se preserva la lógica (formulario controlado + `useMutation(login)`, líneas 5-19) reconstruida sobre el sistema de diseño del origen. |
| `src/pages/DashboardPage.jsx` | RECONCILIAR | El origen no tiene capa de datos (T3): esta página aporta el único fetch real de billing/health (`useDashboardData`, línea 7) y el estado tenant-vacío/cargando/error (líneas 12-41) que debe preservarse sobre la presentación del origen. |
| `src/pages/IngestPage.jsx` | RECONCILIAR | Formulario + `useMutation(createIngestJob)` (líneas 13-26) sin equivalente en el origen (dashboards estáticos, T3). Pendiente confirmar en F3 si el origen trae una pantalla de ingesta que reciba esta lógica o si se compone de cero sobre el `Layout`. |
| `src/pages/ConversationsPage.jsx` | RECONCILIAR | Lógica de listado/creación/envío de conversaciones vía TanStack Query (líneas 17-65) sin equivalente en el origen. Misma nota que IngestPage: confirmar en F3 la pantalla destino del origen. |
| `src/pages/PlaceholderPage.jsx` | REEMPLAZAR | Sin lógica de negocio ni llamadas a backend; placeholder puro (12 líneas). Lo que el origen aporte para "Settings" lo sustituye directamente. |
| `src/components/MetricCard.jsx` | REEMPLAZAR | Puramente presentacional, sin estado ni llamadas a API; candidato a sustituirse por primitivas shadcn/ui del origen (T5). |
| `src/components/SectionCard.jsx` | REEMPLAZAR | Igual que `MetricCard.jsx`: wrapper presentacional sin lógica propia. |
| `src/components/StatusPill.jsx` | REEMPLAZAR | Igual que `MetricCard.jsx`: normaliza un string y pinta una clase CSS; sin lógica de negocio. |
| `src/hooks/useDashboardData.js` | PRESERVAR | Combina `fetchBillingSummary` + `fetchHealth` con `useQueries` (líneas 5-17); el origen no tiene librería de datos (T3). Se porta a `.ts` sin cambiar su contrato ni su forma de consumo. |
| `src/services/api.js` | PRESERVAR | Es la única capa HTTP del monorepo (decisión #4 del `proposal.md` de la épica); el origen no tiene ninguna (T3). Se porta a TS manteniendo `VITE_API_BASE_URL` (línea 1) y los headers `Authorization`/`X-Tenant-Id` (líneas 3-10). |
| `src/styles/main.css` | REEMPLAZAR | Regla explícita de la tabla de conflictos del spike: "Unificar en el sistema del origen; eliminar `main.css` antiguo al validar". 443 líneas de tema oscuro plano, incompatible con Tailwind v4 + shadcn/ui + MUI (T5). |

## Contratos del backend consumidos por el frontend

<!-- Se completa en la tarea 2.4 -->

## Criterios de paridad funcional (login → tenant → dashboard)

<!-- Se completa en la tarea 3.1 -->

## Rollback

<!-- Se completa en la tarea 3.2 -->
