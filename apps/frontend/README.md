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
- `TypeScript` (tooling: `strict: true`, `allowJs: true` mientras dura la migracion de `src/` —
  ver [ADR-0003](../../docs/adr/ADR-0003-frontend-typescript.md))
- `JavaScript` (todo `src/` hoy; se migra a `.tsx` por slices en F3)
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
|-- Dockerfile
|-- index.html
|-- package.json
|-- tsconfig.json
|-- tsconfig.node.json
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

- `services/api.js` centraliza el acceso HTTP.
- `hooks/useDashboardData.js` usa TanStack Query para el dashboard.
- `layouts/AppShell.jsx` define la estructura general de la aplicacion.
