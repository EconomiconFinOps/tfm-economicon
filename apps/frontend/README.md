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
  [ADR-0004](../../docs/adr/ADR-0004-frontend-shadcn-ui.md)). Todos los colores salen de tokens del
  tema: ver [Estilos y colores](#estilos-y-colores) y
  [ADR-0012](../../docs/adr/ADR-0012-frontend-color-tokens.md).
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
|   |   |-- chartTheme.ts # estilo compartido del tooltip de Recharts (variables del tema)
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
|   |-- styles/          # tailwind.css, theme.css (tokens de color: unica paleta), index.css
|   |-- test/            # setup.ts (jsdom, limpieza de storage/mocks, mocks de ResizeObserver/Request)
|   |                    # color-tokens.guard.test.ts y theme-palette.test.ts (reglas de color)
|   |-- App.tsx           # monta <RouterProvider>
|   |-- main.tsx          # entrypoint: QueryClientProvider + App
|   `-- routes.tsx        # mapa de rutas (routeConfig + router)
|-- tests/                # regresion end-to-end (sesion, tenant, ingesta, conversaciones)
|-- ATTRIBUTIONS.md       # atribuciones de terceros (codigo copiado de shadcn/ui, MIT)
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

## Estilos y colores

La aplicacion tiene **una unica paleta**, definida una sola vez en `src/styles/theme.css` (bloque
`:root`, solo tema oscuro; no hay `.dark` ni `class="dark"` en `index.html`). Decision y motivos en
[ADR-0012](../../docs/adr/ADR-0012-frontend-color-tokens.md).

**Regla: ninguna pantalla, layout, componente ni dato demo escribe un color literal.** Ni
hexadecimales (`#1a1f2e`) ni utilidades de la paleta de Tailwind (`text-slate-400`, `bg-red-500/20`):
se usa la utilidad del token.

| Necesitas | Escribe |
| --- | --- |
| Fondo de pagina, tarjeta, degradado de tarjeta | `bg-background`, `bg-card`, `from-card to-accent` |
| Texto principal, secundario, intermedio, tenue | `text-foreground`, `text-muted-foreground`, `text-subtle-foreground`, `text-neutral` |
| Bordes y separadores | `border-border`, `divide-border` |
| Marca, foco, acento de navegacion | `bg-primary`, `border-primary`, `text-highlight` |
| Estados (exito, error, info, aviso, atencion) | `text-success`, `bg-danger-tint/20 text-danger-foreground`, `text-info`, `text-warning`, `bg-attention-tint/20` |
| Atributos de Recharts (`stroke`, `fill`) y estilos en linea | `var(--chart-axis)`, `var(--chart-2)`, `var(--primary)`, o `chartTooltipStyle` para el tooltip |

- **Cambiar un color** = editar su valor en `theme.css`; llega a todas las pantallas sin tocarlas.
- **Anadir un color** = crear un token con nombre de **funcion** (no de color), con consumidor real, en
  `:root` y en `@theme inline` (`--color-<nombre>`). Un token sin uso hace fallar los tests.
- **No construyas clases por interpolacion** (`` `text-${color}-400` ``): Tailwind no las detecta. Usa un
  mapa cerrado de cadenas completas (`Record<string, string>`), como `MetricCard`.
- **Excepciones**: solo si el tema no puede alcanzar el color (p. ej. el HTML autonomo que `ExportButton`
  abre para imprimir, que no carga `theme.css`). Se declaran una a una, con archivo, valor y motivo, en
  la lista de `src/test/color-tokens.guard.test.ts`.
- Los primitivos de `src/components/ui/` se conservan tal como los publica shadcn/ui; sus variantes
  `dark:` funcionan siempre porque `theme.css` declara `@custom-variant dark (&)`.

Dos tests estaticos lo hacen cumplir: `color-tokens.guard.test.ts` (ningun color literal fuera de las
excepciones) y `theme-palette.test.ts` (paleta unica, tokens sin duplicar ni huerfanos, `<html>` sin
clase de tema). Las atribuciones del codigo de terceros copiado estan en
[`ATTRIBUTIONS.md`](ATTRIBUTIONS.md).

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
- Un `401` en cualquier operación autenticada (o al revalidar `GET /me` al arrancar) cierra la sesión
  y devuelve a `LoginPage`, que muestra un aviso de sesión expirada; un cierre de sesión manual o un
  fallo que no sea `401` no lo muestran (JUP-098).
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

## Salud del sistema — JUP-047

La ruta `/system-health`, bajo sesión y ámbito del cliente, muestra disponibilidad y resúmenes de jobs e ingesta con componentes y tokens compartidos. OpenRouter recibe una intención de comprobación al abrir el panel y cada 10 minutos (600000 ms), únicamente con sesión autenticada y el panel abierto y visible. Actualizar comparte la exclusión de solicitudes y reinicia el plazo periódico. Ocultar el panel pausa los envíos; volver a mostrarlo no acumula comprobaciones atrasadas. El polling visible cada 30 segundos solo solicita diagnóstico GET, sin generar inferencias. Logout, cambio de ámbito y unmount cancelan solicitudes, limpian temporizadores y descartan resultados antiguos. Cada intención conserva los gates ordinarios de admisión, cooldown, presupuesto y reservas; el temporizador no autoriza gasto por sí mismo.

Se conserva la última observación real y su fecha hasta otro resultado real, sin caducidad automática por TTL. Un timeout nuevo produce `unknown` y conserva la fecha y el identificador del éxito anterior como historia; GET/polling no renueva fechas ni convierte esa historia en disponibilidad actual. OpenRouter muestra «Disponible» y «Respuesta válida a» para la última respuesta funcional válida que siga siendo el resultado actual. «Modelo informado»/«Identidad no confirmada» y coste del gateway no confirmado/no disponible/inválido aparecen aparte. Se usa el intento y tenant seleccionados. Azure mantiene la procedencia explícita «SIMULADO»; las fechas UTC válidas admiten hasta 1000 ms futuros inclusive respecto de la recepción para su presentación, conservando su valor original.

Véase el [runbook de salud](../../docs/runbooks/system-health.md) para contrato, configuración y gates reales. Las pruebas semánticas jsdom y la preview sintética no acreditan píxeles, overflow, recorrido completo de teclado ni OpenRouter real. La comprobación remota M5 corresponde a Alejandro y sigue pendiente.
