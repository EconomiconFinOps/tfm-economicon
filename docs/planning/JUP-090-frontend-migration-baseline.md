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

Resumen ejecutivo; el detalle con evidencia de línea está en "Clasificación archivo a archivo".

- **Identidad del paquete:** nombre `@finops/frontend`, `type: module`
  ([package.json](../../apps/frontend/package.json)).
- **Scripts del monorepo:** `dev` (`vite --host 0.0.0.0 --port 5173`), `build`, `preview`,
  `docker:build`; `lint` y `test` se sustituyen por sus equivalentes TS.
- **Puerto/host:** `5173`, fijado en el script `dev` de `package.json` y replicado en
  `docker-compose.yml` (`${FRONTEND_PORT:-5173}:5173`).
- **Integración Docker:** `apps/frontend/Dockerfile` (`EXPOSE 5173`, `CMD ["pnpm", "dev"]`) y el
  servicio `frontend` de `docker-compose.yml` (contexto `./apps/frontend`, `VITE_API_BASE_URL`,
  dependencia de `backend` healthy).
- **Variable de entorno:** `VITE_API_BASE_URL` (por defecto `http://localhost:8000`), leída en
  `src/services/api.js:1`.
- **Capa API única:** `src/services/api.js`, con headers `Authorization: Bearer` y `X-Tenant-Id`
  (líneas 3-10) — el origen no aporta ninguna (T3 de JUP-083).
- **Flujo de sesión/tenant:** `localStorage` (`finops.session`, `finops.activeTenant`), lógica en
  `src/App.jsx` — el origen no tiene auth/sesión/tenant (T4 de JUP-083).
- **Pipeline turbo y workspace pnpm:** `turbo.json` y `pnpm-workspace.yaml` no requieren cambios.

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

### Configuración del paquete

| Archivo | Clasificación | Justificación |
| --- | --- | --- |
| `package.json` | RECONCILIAR | Regla explícita del spike: "Fusionar: deps del origen + conservar `@finops/frontend`, scripts y puerto 5173". Preservar literalmente: `name: @finops/frontend` (línea 2), `type: module` (línea 5), `dev`/`build`/`preview`/`docker:build` (líneas 7-11) y el puerto `5173` embebido en el script `dev` (`--host 0.0.0.0 --port 5173`, línea 7). Fusionar: dependencias del origen (react-router 7, Tailwind v4, shadcn/ui, MUI 7, lucide-react — T2/T5/T6) más `typescript`/`@types/*` (F2). Sustituir: `lint` (línea 8) para incluir `.ts`/`.tsx` y `test` (línea 9, hoy un placeholder sin tooling real). |
| `vite.config.js` | RECONCILIAR | El plugin `react()` (línea 5) se mantiene o se sustituye por el equivalente del origen en Vite 6 (salto de major, T1); el host/puerto **no vive aquí** sino en los scripts de `package.json`, así que al adoptar el `vite.config` del origen hay que confirmar que no define un `server.port`/`server.host` propio que choque con el flag `--port 5173` del script `dev`. |
| `eslint.config.js` | RECONCILIAR | Ya es flat config (línea 6), buena base. Regla del spike: "Migrar a flat config con parser/plugin TS; mantener reglas react/react-hooks". Preservar: `eslint-plugin-react` + `eslint-plugin-react-hooks` (líneas 22-25) y `"react/react-in-jsx-scope": "off"` (línea 34, necesaria con el nuevo JSX transform). Añadir: parser y plugin de `@typescript-eslint` y extender `files` (línea 9) a `.ts`/`.tsx`. |
| `index.html` | RECONCILIAR | Regla del spike: "Usar el del origen; conservar `<div id="root">` y título del producto". Preservar: `<div id="root">` (línea 9) y `<title>FinOps Control Tower</title>` (línea 6). Sustituir: `<script src="/src/main.jsx">` (línea 10) por el entrypoint `.tsx` una vez migrado. |
| `README.md` | RECONCILIAR | Preservar: sección "Como correrlo" (líneas 43-82, comandos Docker/turbo/individual), "Acceso Local Seed" (líneas 88-91) y "Contratos Esperados Del Backend" (líneas 99-110, ajustada si se retira `GET /me` por el hallazgo `RF-090-003`). Sustituir: sección "Stack" (líneas 18-24, pasa a incluir TypeScript, react-router, Tailwind/shadcn/MUI) y "Estructura" (líneas 26-41, refleja el árbol del origen). |

### Integración de plataforma (monorepo/runtime)

| Elemento | Clasificación | Justificación |
| --- | --- | --- |
| `apps/frontend/Dockerfile` | RECONCILIAR | Preservar `EXPOSE 5173` (línea 12) y `CMD ["pnpm", "dev"]` (línea 14). Necesita un paso de build TS (`tsc`/type-check) antes de `vite build` para producción. **Hallazgo `RF-090-001`** (ver sección "Hallazgos"): construye fuera del lockfile del workspace. |
| Servicio `frontend` en `docker-compose.yml` (líneas 156-165) | PRESERVAR | `build.context: ./apps/frontend` (línea 158), `VITE_API_BASE_URL` (línea 160), `depends_on backend: condition: service_healthy` (líneas 161-163) y el mapeo `${FRONTEND_PORT:-5173}:5173` (línea 165) ya están correctos y no cambian con la migración. **Hallazgo `RF-090-002`** (ver sección "Hallazgos", ya corregido): el spike afirmaba `env_file: .env`, que no existe en el servicio real. |
| `turbo.json` | PRESERVAR | Pipeline `dev`/`build`/`lint`/`test`/`docker:build` (líneas 3-28) es genérico para todo el workspace; Vite ya compila TS de forma nativa, así que `build.outputs: ["dist/**", "build/**"]` (líneas 12-15) sigue siendo válido sin cambios. |
| `pnpm-workspace.yaml` | PRESERVAR | El glob `apps/*` (línea 2) ya cubre `apps/frontend`; nada que cambiar aquí. |

## Contratos del backend consumidos por el frontend

Contraste entre lo documentado en [apps/frontend/README.md](../../apps/frontend/README.md) (sección
"Contratos Esperados Del Backend") y las llamadas reales en `src/services/api.js`.

| Endpoint | Función en `api.js` | Consumido desde | Estado |
| --- | --- | --- | --- |
| `GET /health` | `fetchHealth()` (línea 27) | `useDashboardData.js:14` | Coincide |
| `POST /auth/login` | `login()` (línea 43) | `LoginPage.jsx:12` | Coincide |
| `GET /me` | `fetchProfile(token)` (línea 31) | — | **Divergencia**: definida pero nunca invocada. `App.jsx` toma `user` directamente del payload de `POST /auth/login` (`payload.user`, línea 77), no de `GET /me`. |
| `GET /tenants` | `fetchTenants(token)` (línea 35) | `App.jsx:45` | Coincide |
| `GET /billing/summary` | `fetchBillingSummary(token, tenantId)` (línea 39) | `useDashboardData.js:9` | Coincide |
| `POST /jobs/ingest` | `createIngestJob(token, tenantId, payload)` (línea 50) | `IngestPage.jsx:14` | Coincide |
| `GET /assistant/conversations` | `listConversations(token, tenantId)` (línea 59) | `ConversationsPage.jsx:19` | Coincide |
| `POST /assistant/conversations` | `createConversation(token, tenantId, payload)` (línea 63) | `ConversationsPage.jsx:43` | Coincide |
| `GET /assistant/conversations/{id}` | `getConversation(token, tenantId, conversationId)` (línea 72) | `ConversationsPage.jsx:25` | Coincide |
| `POST /assistant/conversations/{id}/messages` | `sendConversationMessage(...)` (línea 79) | `ConversationsPage.jsx:52` | Coincide |

Hallazgo `RF-090-003` — ver sección "Hallazgos".

## Criterios de paridad funcional (login → tenant → dashboard)

Guion ejecutable para la validación E2E de F5 (`jup-0xx-validacion-e2e`). Cada paso nombra la acción,
el endpoint implicado (con headers relevantes) y el resultado observable. Precondición: backend local
levantado (`docker compose up` o `pnpm dev` vía turbo) y seed `operator@example.com` / `secret`
disponible.

| # | Acción | Endpoint | Resultado observable |
| --- | --- | --- | --- |
| 1 | Abrir la app sin sesión previa | — | Se renderiza `LoginPage` (`App.jsx:97`); no hay llamadas de red. |
| 2 | Enviar el formulario con el seed | `POST /auth/login` (sin headers de auth) | Respuesta 2xx con `access_token` + `user`; se persiste en `localStorage.finops.session` (`App.jsx:74-81`); `LoginPage` deja de mostrarse. |
| 3 | Bootstrap automático de tenants tras login | `GET /tenants` con `Authorization: Bearer <token>` (sin `X-Tenant-Id`: aún no hay tenant activo) | `tenantsQuery.data.items` no vacío; si no hay tenant activo válido se autoselecciona el primero (`App.jsx:61-66`) y se persiste en `localStorage.finops.activeTenant`. |
| 4 | Cambiar de tenant desde el selector del `AppShell` | — (cambio local; dispara refetch de queries dependientes) | `activeTenantId` cambia y se persiste (`App.jsx:91-94`); las siguientes llamadas usan el nuevo `X-Tenant-Id`. |
| 5 | Cargar el dashboard ("Overview") con un tenant activo | `GET /billing/summary` con `Authorization: Bearer <token>` + `X-Tenant-Id`; `GET /health` sin headers de auth | `MetricCard` "Monthly Spend" muestra `billing.monthly_spend`, "Savings Identified" muestra `billing.savings_identified` (`DashboardPage.jsx:65,71`); "Service Health" lista cada entrada de `health.services` con su `StatusPill` (`DashboardPage.jsx:104-111`). |
| 6 | Logout | — | `localStorage.finops.session` y `finops.activeTenant` se limpian, `queryClient.clear()` (`App.jsx:83-89`); vuelve a mostrarse `LoginPage`. |

**Fuera de este guion mínimo:** los pasos de ingesta y asistente (`POST /jobs/ingest`,
`/assistant/conversations…`) los añade la propia tarjeta `jup-0xx-validacion-e2e` de F5, que ya los
lista explícitamente en su alcance; aquí solo se fija el núcleo login → tenant → dashboard.

**Regla de headers a verificar:** `X-Tenant-Id` solo debe viajar en llamadas posteriores a tener un
tenant activo (`buildHeaders`, `api.js:3-10`, lo añade solo si `tenantId` es verdadero) — su ausencia
en el paso 3 y su presencia desde el paso 5 en adelante es parte de la paridad esperada, no un defecto.

## Rollback

- El scaffold actual de `apps/frontend` **no se elimina** hasta que la tarjeta `jup-0xx-validacion-e2e`
  de F5 valide E2E el guion de la sección anterior contra el backend local.
- Toda la migración avanza en la rama dedicada `docs/JUP-090-inventory-current-frontend` y las ramas
  posteriores de la épica (una por tarjeta JUP de F2-F5); `develop` conserva el scaffold intacto hasta
  el merge final aprobado.
- Revertir una tarjeta de la épica equivale a descartar su rama; no requiere acción sobre
  `apps/frontend` porque ninguna tarjeta anterior a la validación E2E borra el scaffold existente.
- Si la validación E2E de F5 falla, el rollback es no mergear esa tarjeta: el scaffold en `develop`
  sigue siendo el frontend actual, sin dejar un frontend a medio migrar en producción.

## Hallazgos

Detalle en `review.md` de esta HU y en `openspec/findings/backlog.md`.

| ID | Estado | Descripción | Acción |
| --- | --- | --- | --- |
| `RF-090-001` | Open | `apps/frontend/Dockerfile` copia solo `package.json` (línea 7) e instala con `pnpm install --no-frozen-lockfile` (línea 8): no copia `pnpm-lock.yaml` ni `pnpm-workspace.yaml` de la raíz, así que construye fuera del lockfile del workspace. Contradice la regla de instalación reproducible del propio spike. | Resolver en la tarjeta F4 `verificar-docker-compose`. |
| `RF-090-002` | Fixed (en esta HU) | El spike afirmaba que el servicio `frontend` de `docker-compose.yml` tenía `env_file: .env` (línea 55); esa clave no existe — `VITE_API_BASE_URL` viaja como `environment:` inline. | Corregido directamente en `docs/spikes/frontend-migration.md` como parte de esta HU. |
| `RF-090-003` | Open | `GET /me` (`fetchProfile`, `api.js:31`) está documentado en el README y contratado con el backend, pero el frontend no lo invoca: `App.jsx` toma `user` del payload de `POST /auth/login`. | Decidir en la tarjeta de reconciliación de la capa API de F3 (`jup-0xx-reconciliar-capa-api`) si se conecta o se retira. |
