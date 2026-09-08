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

- `React`
- `Vite`
- `TypeScript` (aplicacion y contratos de props/API con `strict: true`; `allowJs: true` hasta F5 —
  ver [ADR-0003](../../docs/adr/ADR-0003-frontend-typescript.md))
- `Vitest`, React Testing Library y jsdom para pruebas de los recorridos del frontend
- `TanStack Query`
- `react-router`, `recharts`, `lucide-react` — dependencias fusionadas para F3; ninguna se importa
  todavia en `src/`
- Tailwind CSS v4 + un subconjunto de shadcn/ui (6 primitivos Radix: label, select, slot, separator,
  dialog, tooltip) — instaladas para F3, sin cablear en el build todavia
  (ver [ADR-0004](../../docs/adr/ADR-0004-frontend-shadcn-ui.md))
- `ESLint`

## Estructura

```text
apps/frontend
|-- src/
|   |-- components/
|   |-- hooks/
|   |-- layouts/
|   |-- pages/
|   |-- services/
|   `-- styles/
|-- tests/
|-- Dockerfile
|-- index.html
|-- package.json
|-- tsconfig.json
|-- tsconfig.node.json
|-- tsconfig.test.json
`-- vite.config.ts
```

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

- `services/api.ts` centraliza el acceso HTTP con respuestas tipadas.
- `hooks/useDashboardData.ts` usa TanStack Query para el dashboard.
- `layouts/AppShell.tsx` define la estructura general de la aplicacion.

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
introducir globals de Node o del runner en el proyecto browser. La regla
`react/prop-types` permanece activa para cualquier componente `.jsx`; los `.tsx`
declaran contratos de props comprobados por TypeScript.
