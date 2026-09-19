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
- `TypeScript` (`strict: true`) en todo `src/**`: `services/api.ts` y `services/contracts.ts`
  tipan la unica capa HTTP del frontend contra los contratos reales del backend — ver
  [ADR-0003](../../docs/adr/ADR-0003-frontend-typescript.md).
- `react-router` (enrutado real vía `createBrowserRouter`, `SessionGate` como ruta padre pasando
  sesión/tenant a las rutas hijas por `Outlet context`), `TanStack Query`, `recharts`,
  `lucide-react`.
- Tailwind CSS v4 (`@tailwindcss/vite`) + un subconjunto de shadcn/ui (primitivos Radix copiados a
  `src/components/ui/`: label, select, separator, dialog, tooltip — ver
  [ADR-0004](../../docs/adr/ADR-0004-frontend-shadcn-ui.md)).
- `Vitest` + `@testing-library/react` (runner de pruebas, comprobación obligatoria de CI). Dos
  ubicaciones de test conviven y se descubren juntas: `src/**/*.test.tsx` (junto al código que
  prueban) y `tests/**/*.test.tsx` (regresión end-to-end de sesión, tenant, ingesta y
  conversaciones).
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
|   |   `-- useDashboardData.ts
|   |-- layouts/
|   |   |-- SessionGate.tsx       # sesion/tenant, padre de Layout en el arbol de rutas
|   |   `-- Layout.tsx            # nav + selector de ambito + panel de sesion
|   |-- lib/
|   |   `-- utils.ts     # cn(), utilidad de composicion de clases
|   |-- pages/           # LoginPage, IngestPage, ConversationsPage, DashboardPage, 5 dashboards de coste
|   |-- services/
|   |   |-- api.ts       # unica capa HTTP, tipada contra services/contracts.ts
|   |   `-- contracts.ts # tipos de request/response compartidos con el backend
|   |-- styles/          # tailwind.css, theme.css, index.css
|   |-- test/            # setup.ts (jsdom, limpieza de storage/mocks, mocks de ResizeObserver/Request)
|   |-- App.tsx           # monta <RouterProvider>
|   |-- main.tsx          # entrypoint: QueryClientProvider + App
|   `-- routes.tsx        # mapa de rutas (routeConfig + router)
|-- tests/                # regresion end-to-end (sesion, tenant, ingesta, conversaciones)
|-- Dockerfile
|-- index.html
|-- package.json
|-- tsconfig.json
|-- tsconfig.node.json
|-- tsconfig.test.json
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
| `/ingest` | `IngestPage` | Datos reales vía `services/api.ts` |
| `/assistant` | `ConversationsPage` | Datos reales vía `services/api.ts` |
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
- password: campo vacio; introducir manualmente la password de la cuenta.

El backend solo crea la cuenta ausente con `DEMO_SEED_ENABLED=true` y
`DEMO_PASSWORD` externa no heredada. Si la cuenta ya existe, cambiar esa
variable no rota su hash; seguir la [rotacion manual](../../docs/manuals/python-service-conventions.md#rotacion-de-la-cuenta-demo).
Nunca pasar passwords, JWT, claves de gateway o DSN mediante `VITE_*` o
argumentos de build. `VITE_API_BASE_URL` es configuracion publica del navegador.

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

- `services/api.ts` centraliza el acceso HTTP con respuestas tipadas contra `services/contracts.ts`.
- `hooks/useDashboardData.ts` usa TanStack Query para `/overview-legacy` (`DashboardPage`).
- `layouts/SessionGate.tsx` + `layouts/Layout.tsx` definen la estructura general de la aplicación
  (sesión, tenant activo, navegación); `AppShell.jsx` fue retirado en JUP-095, su contenido se
  repartió entre ambos.
- Las 5 pantallas de coste (`/`, `/operational`, `/cuts`, `/anomalies`, `/recommendations`) muestran
  datos de demostración estáticos (`src/data/demo/`), no datos reales — ver `RF-095-002` en
  `openspec/findings/backlog.md`.

## Calidad y pruebas

Desde la raiz del monorepo:

```powershell
corepack pnpm install --frozen-lockfile
corepack pnpm lint --filter=@finops/frontend
corepack pnpm test --filter=@finops/frontend
corepack pnpm --filter @finops/frontend typecheck
corepack pnpm --filter @finops/frontend build
```

`test` ejecuta Vitest una vez; `test:watch` permite desarrollo interactivo. La
suite verifica login/logout, persistencia de sesion, bootstrap y seleccion de
tenant, dashboard, ingesta y conversaciones con respuestas HTTP controladas.
Cada caso usa almacenamiento y cache aislados y falla ante peticiones sin mock;
no necesita backend, Docker ni credenciales reales. Las fixtures siguen los
schemas versionados en `apps/backend/app/schemas/`.

CI ejecuta lint y pruebas antes del build en el check obligatorio `Frontend
build`. El typecheck tambien verifica los tests en `tsconfig.test.json`, sin
introducir globals de Node o del runner en el proyecto browser. Todos los
componentes son `.tsx` con contratos de props comprobados por TypeScript.
