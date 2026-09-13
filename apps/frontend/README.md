# Frontend

## Descripcion

`apps/frontend` es la interfaz web del proyecto.

Su funcion es mostrar el dashboard del asistente FinOps y consumir la API del `backend` por HTTP.

Aqui vive la parte visual del sistema:

- login del operador
- seleccion de tenant activo
- overview operativo
- ingesta de documentos
- chat con el asistente
- resumen de billing y salud del sistema

## Stack

- `React` 18
- `Vite` 5 + `@vitejs/plugin-react`
- `TypeScript` (`strict: true`, `allowJs: true` mientras `src/services/api.js` y
  `src/hooks/useDashboardData.js` sigan sin migrar — ver
  [ADR-0003](../../docs/adr/ADR-0003-frontend-typescript.md)). Alias `@/` → `src/` en
  `tsconfig.json` y `vite.config.ts`.
- `JavaScript` — solo `src/services/api.js` y `src/hooks/useDashboardData.js` (fuera de alcance de
  JUP-095, frontera con la lógica del destino; migración pendiente de la siguiente tarjeta de F3 que
  reconcilie la capa de datos). El resto de `src/**` es `.tsx`/`.ts`.
- `react-router` (enrutado real vía `createBrowserRouter`, `SessionGate` como ruta padre pasando
  sesión/tenant a las rutas hijas por `Outlet context`), `TanStack Query`, `recharts`,
  `lucide-react`.
- Tailwind CSS v4 (`@tailwindcss/vite`) + un subconjunto de shadcn/ui (5 primitivos Radix copiados a
  `src/components/ui/`: label, select, separator, dialog, tooltip — ver
  [ADR-0004](../../docs/adr/ADR-0004-frontend-shadcn-ui.md); sin consumidor real todavía fuera de
  sus propios tests, peso muerto aceptado por el ADR).
- `Vitest` + `@testing-library/react` (runner de pruebas, comprobación obligatoria de CI).
- `ESLint`

## Estructura

```text
apps/frontend
|-- src/
|   |-- components/
|   |   `-- ui/          # primitivos shadcn/ui copiados (label, select, separator, dialog, tooltip)
|   |-- data/
|   |   `-- demo/        # datos de demostracion de las 5 pantallas de coste (sustituibles, RF-095-002)
|   |-- hooks/
|   |   `-- useDashboardData.js   # sin tipar, fuera de alcance de JUP-095
|   |-- layouts/
|   |   |-- SessionGate.tsx       # sesion/tenant, padre de Layout en el arbol de rutas
|   |   `-- Layout.tsx            # nav + selector de ambito + panel de sesion
|   |-- lib/
|   |   `-- utils.ts     # cn(), utilidad de composicion de clases
|   |-- pages/           # LoginPage, IngestPage, ConversationsPage, DashboardPage, 5 dashboards de coste
|   |-- services/
|   |   `-- api.js       # sin tipar, unica capa HTTP, fuera de alcance de JUP-095
|   |-- styles/          # tailwind.css, theme.css, index.css
|   |-- test/            # setup.ts (jsdom, mocks) y pruebas del harness
|   |-- App.tsx           # monta <RouterProvider>
|   |-- main.tsx          # entrypoint: QueryClientProvider + App
|   `-- routes.tsx        # mapa de rutas (routeConfig + router)
|-- Dockerfile
|-- index.html
|-- package.json
|-- tsconfig.json
|-- tsconfig.node.json
`-- vite.config.ts
```

## Rutas

Mapa montado en `src/routes.tsx` (JUP-095). `/login` vive fuera del `Layout`; el resto cuelga de
`SessionGate` (redirige a `/login` sin sesión) y `Layout` (navegación, selector de tenant, sesión):

| Ruta | Pantalla | Notas |
| --- | --- | --- |
| `/login` | `LoginPage` | Fuera de `SessionGate`; crea la sesión |
| `/` | `ExecutiveCostDashboard` | Datos de demostración (`RF-095-002`) |
| `/operational` | `OperationalCostDashboard` | Datos de demostración |
| `/cuts` | `ExecutiveCutDashboard` | Datos de demostración |
| `/anomalies` | `AnomaliesPanel` | Datos de demostración |
| `/recommendations` | `RecommendationsPanel` | Datos de demostración |
| `/ingest` | `IngestPage` | Datos reales vía `services/api.js` |
| `/assistant` | `ConversationsPage` | Datos reales vía `services/api.js` |
| `/overview-legacy` | `DashboardPage` | Ruta puente temporal — **único dashboard con datos reales** (`GET /billing/summary`, `GET /health`); la retira la siguiente tarjeta de F3 que reconcilie la capa de datos |

## Como correrlo

### Con Docker Compose

Desde la raiz del repo:

```powershell
docker compose up --build frontend
```

Puerto visible:

- `http://localhost:5173`

### Con Turborepo

Desde la raiz del repo:

```powershell
pnpm dev
```

Esto levanta `frontend`, `backend` y `processor` a la vez.

Puerto visible del frontend:

- `http://localhost:5173`

### Individualmente

Desde `apps/frontend`:

```powershell
pnpm install
pnpm dev
```

Puerto visible:

- `http://localhost:5173`

## Variables De Entorno

- `VITE_API_BASE_URL`: URL base del backend. En local suele ser `http://localhost:8000`

## Acceso Local Seed

- email: `operator@example.com`
- password: `secret`

## Build

```powershell
pnpm build
```

## Contratos Esperados Del Backend

- `GET /health`
- `POST /auth/login`
- `GET /me`
- `GET /tenants`
- `GET /billing/summary`
- `POST /jobs/ingest`
- `GET /assistant/conversations`
- `POST /assistant/conversations`
- `GET /assistant/conversations/{conversation_id}`
- `POST /assistant/conversations/{conversation_id}/messages`

## Notas

- `services/api.js` centraliza el acceso HTTP (única capa HTTP del monorepo).
- `hooks/useDashboardData.js` usa TanStack Query para `/overview-legacy` (`DashboardPage`).
- `layouts/SessionGate.tsx` + `layouts/Layout.tsx` definen la estructura general de la aplicación
  (sesión, tenant activo, navegación); `AppShell.jsx` fue retirado en JUP-095, su contenido se
  repartió entre ambos.
- Las 5 pantallas de coste (`/`, `/operational`, `/cuts`, `/anomalies`, `/recommendations`) muestran
  datos de demostración estáticos (`src/data/demo/`), no datos reales — ver `RF-095-002` en
  `openspec/findings/backlog.md`.
