JUP: JUP-095
Trello: https://trello.com/c/G4FPtBdE/87-jup-095-portar-el-c%C3%B3digo-fuente-del-frontend-de-economicon

## Why

F2 quedó cerrada con [JUP-093](../archive/2026-09-06-jup-093-configure-typescript/) (TypeScript
`strict`, type-check obligatorio en CI) y [JUP-094](../archive/2026-09-07-jup-094-reconcile-package-json/)
(`react-router`, `recharts`, `lucide-react`, Tailwind v4 y los 6 primitivos Radix de
[ADR-0004](../../../docs/adr/ADR-0004-frontend-shadcn-ui.md)). **Nada de eso se usa todavía**:
`apps/frontend/src/**` sigue siendo el scaffold del destino —14 archivos, 11 de ellos `.jsx`, cero
líneas del origen— y la aplicación navega con un `switch` manual sobre estado local
(`App.jsx:127-150`), sin rutas reales ni URL compartible.

Esta es la primera tarjeta de la épica que toca producto visible, y es la que desbloquea al resto de
F3: `reconciliar-capa-api` (JUP-096) y `reconciliar-auth-tenant` (JUP-097) reconcilian **sobre**
pantallas que hoy no existen aquí. Mientras el código del origen no entre, cada una de esas tarjetas
tendría que portarlo por su cuenta a mitad de su propio alcance — justo el "big bang" que el spike
prohíbe.

## What Changes

- **Entra la capa de presentación del origen**: los 5 dashboards (`ExecutiveCostDashboard`,
  `OperationalCostDashboard`, `ExecutiveCutDashboard`, `AnomaliesPanel`, `RecommendationsPanel`), el
  `Layout` y `ExportButton`. Son **8 archivos `.tsx` reales** contando `routes.tsx`; el resto del
  árbol del origen (los 48 de `ui/` y `figma/ImageWithFallback.tsx`) es código muerto sin un solo
  consumidor y **no entra**.
- **Entra el sistema de estilos del origen** (Tailwind v4 más sus hojas de tokens) y se cablea en el
  build por primera vez. `src/styles/main.css` (443 líneas de tema oscuro plano) se retira al final,
  con la aplicación ya renderizando sobre el sistema nuevo.
- **BREAKING (navegación)**: la aplicación pasa a enrutado real con URL por pantalla. El estado
  `activeView` desaparece; las vistas actuales dejan de alcanzarse por clic sobre estado local y
  pasan a tener ruta propia. Ninguna capacidad se pierde: las pantallas del destino con datos reales
  (login, ingesta, asistente y el resumen de facturación) conservan ruta propia.
- **Entra el primer runner de pruebas del frontend**. Su script `test` es hoy un `echo`: JUP-093 y
  JUP-094 documentaron por eso la excepción al ciclo Red/Green del harness. Esta tarjeta la cierra,
  porque es la primera del frontend con código de producto propio que verificar.
- **Los datos estáticos del origen quedan aislados** en un módulo propio, señalizado como sustituible,
  en vez de vivir como constantes dentro de cada dashboard. Las 5 pantallas del origen se alimentan de
  datos fijos: solo 2 de 14 tienen contrato en el backend, y ambos parcialmente
  ([JUP-091](../../../docs/planning/JUP-091-economicon-source-inventory.md), `RF-091-003`).
- **Se migran a `.tsx` los archivos del destino que el enrutado obliga a tocar**, preservando su
  lógica sin cambio de comportamiento. La sesión, el tenant activo, TanStack Query y
  `src/services/api.js` **no se tocan**: reconciliarlos es JUP-096 y JUP-097.

## Capabilities

### New Capabilities

- `frontend-navigation-shell`: el frontend navega entre sus pantallas mediante rutas direccionables y
  las presenta bajo un armazón único que conserva la identidad de la sesión y el ámbito de cliente
  activo, sin que la navegación pierda ese contexto ni obligue a recargar la aplicación. Incluye la
  separación entre los datos de demostración que acompañan a las pantallas migradas y los datos
  servidos por el backend, para que la sustitución posterior sea localizable y no quede escondida
  dentro de los componentes.

### Modified Capabilities

- `frontend-typescript-tooling`: hoy la cadena de verificación del frontend cubre tipos y lint. Se
  añade el requisito de que **ejecute pruebas automáticas reales**, con un runner ejecutable en local
  y en integración continua, en lugar del marcador vacío actual. No se altera ninguno de sus
  requisitos vigentes.

## Impact

- **Reemplazado:** `apps/frontend/src/**` en su capa de presentación y enrutado (componentes, páginas,
  layouts, estilos, entrypoint). `src/styles/main.css` y `src/pages/PlaceholderPage.jsx` se eliminan.
- **Preservado sin tocar:** `src/services/api.js`, `src/hooks/useDashboardData.js` y la lógica de
  sesión/tenant, que se migran de extensión solo si el enrutado lo obliga y siempre sin cambio de
  comportamiento.
- **Modificado:** `index.html` (entrypoint `.tsx`, conservando `<div id="root">` y el título del
  producto), `vite.config.ts` (plugin de Tailwind y alias de rutas), `tsconfig.json` (alias de rutas),
  `package.json` (runner de pruebas y script `test` real) y `pnpm-lock.yaml`.
- **Dependencias nuevas:** solo las del runner de pruebas y su entorno DOM, en desarrollo. Ninguna
  dependencia de ejecución nueva: todo lo que las pantallas importan lo instaló JUP-094.
- **Findings.** `RF-082-002` sigue `Open` y esta tarjeta registra su **nueva línea base de lint** (hoy
  49 violaciones exactas de `react/prop-types` en 9 archivos `.jsx`): baja al migrar archivos a
  `.tsx`, pero no se cierra mientras quede JavaScript sin tipar, empezando por `services/api.js`, que
  es de JUP-096. `RF-090-001`, `RF-090-003`, `RF-091-003`, `RF-091-004` y `RF-093-001` quedan fuera de
  alcance sin cambio de estado. Se espera **un finding nuevo** por los datos de demostración que
  entran en la ruta de producto.
- **Riesgo declarado:** el código del origen nunca ha pasado verificación de tipos —llega sin
  `tsconfig`, transpilado por esbuild— y aquí entra bajo `strict: true` (ADR-0003). El volumen de
  errores a resolver no es conocido hasta intentarlo; ADR-0003 ya fija que, si desborda, se documenta
  y se supersede el ADR, no se relaja la configuración en silencio.
- **Desbloquea:** JUP-096 (`reconciliar-capa-api`), JUP-097 (`reconciliar-auth-tenant`) y JUP-098
  (`unificar-estilos-assets`).
- **Aún no:** conectar las pantallas migradas a datos reales, el flujo de auth contra el backend, la
  reconciliación de Docker/turbo (F4), la validación E2E (F5) ni endurecer `allowJs` a `false`
  (cierre de F5).
