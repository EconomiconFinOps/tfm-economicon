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

## Human Approval

- Change: jup-095-portar-codigo-fuente
- Approval type: pre-code
- Decision: approved
- Approver: Victor
- Date: 2026-09-07
- Carril: standard
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Decisions approved: se aprueban las nueve decisiones del `design.md`. (1) **La frontera de la
  tarjeta es presentación y enrutado**: `services/api.js`, `useDashboardData` y la lógica de
  sesión/tenant se preservan verbatim, cambiando de extensión solo si el enrutado obliga y nunca de
  comportamiento; abrirlas aquí dejaría a JUP-096 y JUP-097 sin alcance propio y devolvería la
  migración al "big bang" que el spike prohíbe. (2) **Del origen entra solo lo que tiene consumidor
  verificado**: los 8 `.tsx` vivos, y quedan fuera `figma/ImageWithFallback.tsx` (sin un solo import,
  ni siquiera desde `ui/`), el plugin `figmaAssetResolver` —que resuelve contra una carpeta
  `src/assets` inexistente y solo puede fallar en silencio—, el `assetsInclude` sin consumidor,
  `postcss.config.mjs` (stub que su propio comentario declara innecesario) y `fonts.css` (vacío). Es
  el mismo criterio con el que JUP-091 clasificó dependencias y JUP-094 rechazó las 48 `DESCARTAR`.
  (3) **El acceso queda fuera del armazón**: el `Layout` muestra navegación, identidad de sesión y
  selector de ámbito, los tres sin sentido sin sesión; mezclarlo con el control de acceso invadiría
  JUP-097. (4) **El ámbito oscuro se declara explícitamente**, porque `theme.css` define `:root` en
  claro y `.dark` como variante, y el origen nunca aplica esa clase —sus pantallas fijan el color a
  mano y no consumen los tokens—, mientras que los componentes de shadcn copiados sí los consumen:
  sin declararlo renderizarían en claro sobre pantallas oscuras. Reescribir los 181 tokens es trabajo
  de JUP-098. (5) **El alias `@/` se declara en los dos sitios**, `paths` de `tsconfig.json` y
  `resolve.alias` de `vite.config.ts`: declararlo en uno solo produce el fallo de "compila pero no
  arranca", o el inverso. Entra por los componentes de shadcn copiados, no por el código portado, que
  no lo usa. (6) **`/overview-legacy` se conserva como ruta puente** hasta que JUP-096 conecte los
  datos reales al nuevo Overview: cuesta una entrada de ruta y evita que `develop` quede con su único
  dashboard con datos reales degradado durante dos tarjetas, lo que contradiría la regla de rollback
  del spike. Se declara como deuda con dueño explícito, no como ruta permanente. (7) **Vitest +
  Testing Library, con job propio en CI y promovido a comprobación obligatoria** en ambos rulesets y
  en la guía de gobernanza: es el precedente literal de JUP-093, que añadió así *Frontend type check*
  aplicando la decisión 3 de ADR-0003 ("de lo contrario `strict` es solo una anotación decorativa");
  el mismo razonamiento vale para unas pruebas que nadie ejecuta, y la alternativa —job sin
  promoverlo— reproduce la situación del lint, fuera de los checks obligatorios desde JUP-082 por una
  deuda que nadie ha cerrado. El runner **no requiere ADR**: no ata el diseño del código de producto
  ni cambia el modelo de build, y sustituirlo sería reescribir invocaciones, no arquitectura — la
  diferencia con ADR-0003 (cambió el lenguaje del frontend entero) y ADR-0004 (ata el vocabulario de
  componentes de F3 y F5). (8) **El orden de slices** pone estilos antes que componentes, para que un
  fallo de porte no se confunda con la ausencia de estilos, y deja la limpieza la última por ser el
  único punto sin retorno. (9) **`strict` no se silencia**: prohibido `any` nuevo y `@ts-ignore`; si
  el volumen desborda, se aplica el criterio de escape que ADR-0003 ya fijó —documentar y superseder
  el ADR—, nunca relajar la configuración en silencio.
- Main risks: el principal es **de ejecución y de volumen desconocido**: el código del origen entra
  bajo `strict: true` sin haber pasado nunca un type-check —llega sin `tsconfig`, transpilado por
  esbuild—, y ADR-0003 ya declaró este como el riesgo que más puede obligar a revisar su decisión.
  Mitigación: el orden de slices lo expone pronto (grupo 5, antes del enrutado) y la superficie es
  pequeña —unas 950 líneas entre los 8 archivos, con un grafo de imports de solo cuatro librerías—.
  Riesgo secundario: **injertar el selector de ámbito y el panel de sesión en un `Layout` ajeno**
  puede degradar el flujo actual; mitigación: los escenarios de `frontend-navigation-shell` fijan
  como criterio que el ámbito sobreviva a la navegación y que el cierre de sesión devuelva al acceso,
  y el recorrido de paridad de JUP-090 se repasa a mano antes de cerrar. Riesgo terciario, aceptado
  al aprobar la decisión 7: **promover *Frontend tests* a obligatorio puede bloquear PRs del equipo**
  si la suite es inestable; mitigación: nace pequeña y determinista (render y enrutado, sin red), y
  como la activación remota es acción de administrador hay una ventana natural para revisarla antes
  de que empiece a bloquear. Riesgo cuarto: **`/overview-legacy` puede quedarse para siempre** si
  JUP-096 no la retira; mitigación: se declara en `review.md` con dueño y se enuncia en el alcance de
  JUP-096.
- Required changes before execution: none
- Notes: primera tarjeta de F3 y **primera del frontend con superficie real para el ciclo Red/Green**
  del harness: a diferencia de JUP-093 y JUP-094, que documentaron la excepción por falta de test
  runner, aquí el runner entra en el grupo 2 y las tareas de los grupos 2, 4, 5 y 6 llevan Red/Green
  y mutación. Lleva `docs/evidence/JUP-095-validation.md`: no es doc-only. La verificación local usa
  los sustitutos `--filter @finops/frontend` por la limitación de entorno preexistente `RF-093-001`.
  Quedan explícitamente fuera: la capa API y `RF-090-003` (JUP-096); auth/sesión/tenant contra el
  backend y el guard de rutas (JUP-097); la unificación fina de estilos, fuentes, iconos y licencias
  (JUP-098); Docker y turbo con `RF-090-001` (F4); la validación E2E (F5); endurecer `allowJs` a
  `false` (cierre de F5); y conectar los 12 datos sin contrato de `RF-091-003`, que es decisión de
  épica. **`RF-082-002` permanece `Open`** y esta tarjeta solo registra su nueva línea base de lint:
  no se cierra mientras quede JavaScript sin tipar, empezando por `services/api.js`, que es de
  JUP-096.
