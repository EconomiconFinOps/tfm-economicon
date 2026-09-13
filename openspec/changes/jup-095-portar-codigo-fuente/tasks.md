## 1. Gate pre-código y línea base

- [x] 1.1 Llevar al **gate pre-código** las decisiones del `design.md` y registrar la resolución en el
  bloque `## Human Approval` del `proposal.md`. Requieren aprobación explícita: la decisión 6
  (`/overview-legacy` como ruta puente hasta JUP-096) y la decisión 7 (promover *Frontend tests* a
  comprobación obligatoria, tocando `.github/rulesets/` y la guía de gobernanza). Hecho: aprobado por
  Victor el 2026-09-07 (commit `eaafc90`), con ambas decisiones aprobadas explícitamente.
- [x] 1.2 Registrar la línea base **antes** de tocar nada: recuento de `corepack pnpm --filter
  @finops/frontend lint` (esperado: 49 violaciones de `react/prop-types` en 9 archivos), salida de
  `build` con el tamaño del bundle, inventario de `src/**` (14 archivos) y comprobaciones obligatorias
  de CI vigentes (esperado: 7, sin ninguna de pruebas de frontend). **Confirmado**: 49 problems (49
  errors) en 9 archivos `.jsx`; bundle `203.37 kB` JS / gzip `63.38 kB`, CSS `5.60 kB`; 14 archivos en
  `src/**`; 7 checks obligatorios en `.github/rulesets/develop.json` (`JUP policy`, `OpenSpec`, 3×
  `Python tests`, `Frontend build`, `Frontend type check`), ninguno de pruebas de frontend.

## 2. Runner de pruebas

- [x] 2.1 Instalar el runner con `corepack pnpm --filter @finops/frontend add -D vitest
  @testing-library/react @testing-library/jest-dom jsdom` (pnpm-only; **nunca** `npm i`) y verificar
  que las versiones resueltas no traen un mayor incompatible con React 18 ni con Vite 5 — precedente
  de JUP-093 y JUP-094, donde el resolutor trajo `typescript@7` y `react-router@8`. **Ocurrió de
  nuevo**: el resolutor trajo `vitest@5.0.0`, que exige `vite ^6/^7/^8` (incompatible con el `^5.3.3`
  fijado en JUP-094). Reinstalado fijando `vitest@3.2.7` explícito, cuya dependencia regular declara
  `vite: "^5.0.0 || ^6.0.0 || ^7.0.0-0"` — compatible sin forzar el salto. `@testing-library/react`,
  `@testing-library/jest-dom` y `jsdom` resolvieron sin aviso de peer dependency nuevo.
- [x] 2.2 Configurar Vitest sobre el `vite.config.ts` existente (entorno DOM y fichero de setup) y
  sustituir el script `test` (`echo`) por la invocación real, conservando los otros 6 scripts y el
  puerto 5173 del script `dev`. Hecho: `defineConfig` importado de `vitest/config` (tipa `test` sin
  pragma triple-slash), `test.environment: "jsdom"`, `test.setupFiles: ["./src/test/setup.ts"]`
  (carga los matchers de `@testing-library/jest-dom/vitest`), script `test` → `vitest run`.
  `typecheck` y `build` verificados en verde tras el cambio; bundle idéntico (203.37 kB).
- [x] 2.3 **Red/Green**: primera prueba real que renderice un componente y falle antes de existir el
  código que la satisface, para dejar evidencia del ciclo del harness. Verificar que `test` termina
  con estado de error cuando una prueba falla. Hecho: componente canario `HarnessSmoke` (Red
  `1070a3e`, Green `a03aa76`). Mutación 100%, 0 supervivientes. QA detectó que `.stryker-tmp/` sin
  limpiar contaminaba el conteo de tests de Vitest; corregido con `test.exclude` en `vite.config.ts`
  y verificado por QA de forma independiente. Veredicto QA: `accept`. Evidencia completa en
  `review.md`.
- [x] 2.4 Añadir el job *Frontend tests* a `.github/workflows/ci.yml`, con el mismo patrón de los jobs
  *Frontend build* y *Frontend type check* (`corepack pnpm --filter @finops/frontend test`). Hecho:
  job `frontend-tests`, copiado literal del patrón de `frontend-typecheck` (Red `f07367d` sobre
  `tools/ci-workflow.test.mjs`, Green pendiente de commit). Requirió desactivar y reactivar el hook
  `lock-committed-tests.mjs` con autorización de Victor — ver `review.md`.
- [x] 2.5 Registrar *Frontend tests* como comprobación obligatoria en `.github/rulesets/develop.json`
  y `.github/rulesets/main.json`, y documentarlo en `docs/governance/github-branch-protection.md`,
  anotando que la activación remota es acción de administrador (mismo patrón que JUP-093). Hecho:
  `{ "context": "Frontend tests" }` añadido a ambos rulesets; guía de gobernanza actualizada. Test
  estático (`node --test tools/ci-workflow.test.mjs`) en 7/7. Veredicto QA: `accept`.

## 3. Estilos, Tailwind y alias

- [x] 3.1 Cablear `@tailwindcss/vite` en `apps/frontend/vite.config.ts` sin alterar el plugin de React
  ni introducir `server.port`/`server.host` que choquen con los flags del script `dev`. Hecho: plugin
  `tailwindcss()` junto a `react()`, mismo orden que el origen. `resolve.alias`/`server` sin tocar
  aparte del alias de 3.4. Commit `10e63b3`.
- [x] 3.2 Incorporar del origen `src/styles/tailwind.css` y `src/styles/theme.css`, más un
  `index.css` que los importe. **No** se copia `fonts.css` (vacío) ni `postcss.config.mjs` (stub).
  Hecho: copia verificada byte a byte contra el origen por QA. Commit `10e63b3`.
- [x] 3.3 Declarar explícitamente el ámbito oscuro para que los tokens de `theme.css` no rendericen en
  claro bajo pantallas oscuras (decisión 4 del `design.md`). Hecho: `class="dark"` en `<html>` de
  `index.html`, con test real que lee el archivo del disco (Red `10e63b3`, Green pendiente de commit).
  Veredicto QA: `accept`.
- [x] 3.4 Añadir el alias `@/` en **los dos** sitios: `paths` en `tsconfig.json` y `resolve.alias` en
  `vite.config.ts` (decisión 5). Verificar que `typecheck` y `build` lo resuelven ambos. Hecho:
  declarado en ambos; sin consumidor todavía, verificado que no rompe `typecheck`/`build`. Prueba de
  resolución de extremo a extremo diferida al grupo 4 (primer `@/lib/utils` real) — QA de acuerdo con
  el criterio. Commit `10e63b3`.
- [x] 3.5 Verificar que `main.css` **sigue en su sitio** y que la aplicación arranca: hasta el grupo 8
  no se retira nada. Confirmado: `main.jsx` sigue importando `./styles/main.css`; bundle sin cambio de
  tamaño (nada consume aún las hojas nuevas); `dev`/`build`/`typecheck` en verde.

## 4. Primitivos de shadcn/ui

- [x] 4.1 Copiar a `src/components/ui/` únicamente los primitivos que las pantallas reconstruidas
  vayan a usar, uno a uno, del subconjunto de 6 autorizado por
  [ADR-0004](../../../docs/adr/ADR-0004-frontend-shadcn-ui.md). Ningún otro de los 48 archivos de
  `ui/` del origen entra. Hecho: `label.tsx`, `separator.tsx`, `select.tsx`, `dialog.tsx`,
  `tooltip.tsx`, copias literales del origen verificadas por `diff` (por mí y por QA). Sin archivo
  para `@radix-ui/react-slot`: ninguno de los 5 lo importa, no hay bloque que portar.
- [x] 4.2 Añadir la utilidad de composición de clases que esos componentes importan (`@/lib/utils`),
  apoyada en `clsx` y `tailwind-merge`, ya instaladas por JUP-094. Hecho: `src/lib/utils.ts`, primer
  consumidor real del alias `@/` del grupo 3.
- [x] 4.3 **Red/Green** por primitivo copiado: prueba de render antes del componente. Hecho en un solo
  lote (Red `5d27677`, Green pendiente de commit): 6 tests reales (uno por primitivo + `cn()`), 15/15
  en verde con la suite completa. Mutación: 25.81% tras remediar 4 de 7 supervivientes en tests
  nuevos; 3 no remediados con motivo técnico verificado (uno equivalente, dos solo observables
  abriendo el tooltip). Veredicto QA: `accept`. Efecto colateral encontrado y corregido: `setup.ts`
  no registraba `afterEach(cleanup)` (requirió desactivar/reactivar el hook, autorizado por Victor,
  mismo patrón que en el grupo 2).
- [x] 4.4 Dejar anotado en `review.md` qué primitivos de los 6 instalados quedan **sin consumidor** al
  terminar la tarjeta: es el peso muerto que ADR-0004 aceptó por escrito como riesgo. Hecho: **los 6**
  quedan sin consumidor real fuera de sus propios tests (verificado por `grep`) — ver `review.md`.

## 5. Componentes del origen y datos de demostración

- [x] 5.1 Portar los **8 `.tsx` vivos** del origen (`ExecutiveCostDashboard`,
  `OperationalCostDashboard`, `ExecutiveCutDashboard`, `AnomaliesPanel`, `RecommendationsPanel`,
  `Layout`, `ExportButton`, `routes.tsx`) a la estructura del destino. **No entran**
  `figma/ImageWithFallback.tsx` (sin consumidor), el plugin `figmaAssetResolver` ni el `assetsInclude`
  del `vite.config.ts` del origen. Hecho: `Layout.tsx` copia byte a byte; los 5 dashboards idénticos
  salvo el bloque de imports; `routes.tsx` con imports reajustados, **sin montar** en
  `App.jsx`/`main.jsx` (verificado por grep, por mí y por QA). Prerrequisito resuelto antes del Red:
  mock de `ResizeObserver` en `setup.ts` (commit `f646ef0`), sin el cual `recharts` revienta en jsdom.
- [x] 5.2 Extraer las constantes estáticas de cada dashboard a `src/data/demo/`, señalizado como
  origen sustituible, sin cambiar los datos que muestran (decisión de aislamiento; escenarios de
  `frontend-navigation-shell`). Hecho: 5 módulos, cada uno con el comentario grep-able "DATOS DE
  DEMOSTRACION (sustituibles)", valores idénticos al origen (verificado por QA).
- [x] 5.3 Resolver los errores de `strict: true` **tipando**: prohibido `any` nuevo y `@ts-ignore`. Si
  el volumen desborda la tarjeta, aplicar el criterio de escape de ADR-0003 (documentar y superseder),
  nunca relajar `tsconfig.json` en silencio. Hecho: único `any` real del lote era en `ExportButton`
  (heredado del origen), sustituido por `Record<string, string | number>`. `typecheck` limpio, sin
  desbordamiento sobre esta tarjeta.
- [x] 5.4 **Red/Green** por pantalla portada: prueba de render que verifique que presenta sus datos de
  demostración. Hecho en un lote (Red `e128fcd`, Green pendiente de commit): 7 tests (5 dashboards +
  `Layout` + `ExportButton`), 23/23 en verde. Mutación: 12.11% global (198 supervivientes, 56 sin
  cobertura) — decisión explícita de Victor de aceptar tal cual dado el bajo retorno de una cobertura
  exhaustiva sobre pantallas que el grupo 6 puede reescribir y que dependen de `RF-091-003`. Veredicto
  QA: `accept`.
- [x] 5.5 Verificar `typecheck`, `test` y `build` en verde con las pantallas ya en el árbol, aún sin
  enrutar. Confirmado: `typecheck` limpio, `test` 23/23, `build` con bundle idéntico (203.37 kB /
  5.60 kB) porque nada importa aún los archivos portados.

## 6. Enrutado y armazón

**Arquitectura acordada con Victor antes de implementar** (ver "Addendum: arquitectura del grupo 6" en
`design.md`): `SessionGate` (nuevo) como ruta padre de `Layout`, pasando sesión/tenant a las rutas
hijas vía `Outlet context` de react-router (no Context API propio). Implementado en 4 sub-rondas, cada
una con su propio Red/Green.

**Sub-ronda (a) — `SessionGate` + `Layout` extendido + `routes.tsx` (parcial de 6.1/6.3): hecha.**
`SessionGate.tsx` (nuevo, lógica de `App.jsx` verbatim), `Layout.tsx` (selector de tenant + panel de
sesión vía `useOutletContext` defensivo), `routes.tsx` con `SessionGate` como padre de `Layout`.
Prerrequisito resuelto: parche de `Request` en `setup.ts` para navegación real de react-router en
jsdom (commits `d040272` + fix de lint). Mutación: 51.15% sobre `SessionGate`+`Layout`, aceptada y
documentada (decisión de Victor). Veredicto QA: `accept`. Detalle completo en `review.md`.
Faltan de 6.1: `/login`, `/ingest`, `/assistant`, `/overview-legacy` (sub-rondas b-d). Falta de 6.3:
retirar `AppShell` (sub-ronda d).

**Sub-ronda (b) — `LoginPage` reconstruida (parcial de 6.4): hecha.** `LoginPage.tsx` reemplaza al
`.jsx`: sin prop `onLogin`, persiste sesión y navega a `/` ella misma (`SESSION_KEY` ahora exportado
desde `SessionGate.tsx`, no duplicado). Mutación: 43.48% → reforzada a petición de Victor (archivo
pequeño, refuerzo barato) → **82.61%** tras `LoginPage.mutation.test.tsx` (verifica el `body` real
enviado a `fetch`, con y sin edición de campos). 3 supervivientes + 1 NoCoverage (`navigate`
options, `preventDefault`, texto `"Signing in..."`) no atacados deliberadamente, documentados en
`review.md`. Veredicto QA: `accept`. `lint` baja a 48 (desaparece la violación de `LoginPage.jsx`).
`App.jsx` sigue importando `./pages/LoginPage` (ahora inexistente): deuda esperada, resuelta en la
sub-ronda (d).

**Sub-ronda (c) — `IngestPage` + `ConversationsPage` + `SectionCard` (parcial de 6.4): hecha.**
Ambas páginas migran de props a `useOutletContext<SessionOutletContext>()`, lógica preservada
verbatim (verificado línea a línea por QA). `SectionCard.tsx` reconstruido sobre Tailwind (primer
consumidor compartido). `lint` baja de 48 a 28 (desaparecen `IngestPage.jsx`/`ConversationsPage.jsx`
por completo). Mutación: 18.66% global (`SectionCard` 100%, `IngestPage` 30%, `ConversationsPage`
14.56% — la más compleja, dos queries, dos mutaciones, un efecto de auto-selección) — aceptada y
documentada (decisión de Victor, mismo criterio que dashboards/SessionGate: flujo completo mejor
cubierto end-to-end en la tarea 6.6). Veredicto QA: `accept`. `App.jsx` sigue con imports rotos a
`./pages/IngestPage`/`./pages/ConversationsPage`: deuda esperada, resuelta en la sub-ronda (d).

**Sub-ronda (d) — `DashboardPage`/`MetricCard`/`StatusPill`, cableado final, cierre del grupo: hecha.**
Última sub-ronda: completa 6.1/6.2/6.3/6.4 a la vez. `DashboardPage.tsx` migra a `useOutletContext`
(lógica de `useDashboardData` y las tres ramas sin-tenant/loading/error verbatim, verificado por
QA). `MetricCard.tsx`/`StatusPill.tsx` reconstruidos sobre Tailwind. `routes.tsx` completado con las
9 rutas del mapa final (`/login`, `/ingest`, `/assistant`, `/overview-legacy`). `App.jsx` simplificado
a `<RouterProvider>`. `AppShell.jsx` retirado. Hallazgo del coder durante el Green, autocorregido:
Vite/Vitest resuelven `.jsx` antes que `.tsx` en la misma carpeta, así que dejar convivir ambos
producía un Red engañoso — se borra el `.jsx` en el mismo commit que introduce su `.tsx` (mismo
patrón ya aplicado en sub-rondas anteriores). `typecheck` **limpio por primera vez en todo el grupo
6** (ya no quedan imports rotos). `lint` baja a 1 solo problema (`PlaceholderPage.jsx`, sin
consumidor, deuda de la limpieza final de la tarjeta). Mutación: 35.48% (`DashboardPage` 55.56%,
`MetricCard`/`StatusPill` triviales, 14.29%/0%) — aceptada y documentada.

**Cambio adicional al cierre del grupo, decidido con Victor**: `main.jsx` seguía importando
`styles/main.css` (el sistema viejo), no `styles/index.css` (Tailwind, cableado desde el grupo 3) —
sin este cambio toda la reconstrucción visual de los grupos 3-6 quedaba inerte. Cambiado ahora (no
diferido al grupo 7): la tarea 6.4 pide explícitamente estilos nuevos, y la verificación manual de
6.6 tiene sentido real contra la app terminada. CSS del build: `5.60 kB` → `39.63 kB` (output real de
Tailwind). Veredicto QA: `accept` — **cierra el grupo 6 entero**.

- [x] 6.1 Montar el enrutado con el mapa de la decisión 3: bajo el `Layout`, `/`, `/operational`,
  `/cuts`, `/anomalies`, `/recommendations`, `/ingest` y `/assistant`; `/login` fuera del `Layout`;
  `/overview-legacy` como ruta puente del resumen de facturación actual.
- [x] 6.2 Retirar el enrutado manual por `activeView` de `App.jsx` (líneas 127-150) **preservando
  verbatim** la lógica de sesión, tenant activo, login/logout y la consulta de tenants.
- [x] 6.3 Injertar en el `Layout` del origen el selector de ámbito de cliente y el panel de
  sesión/logout que hoy viven en `AppShell.jsx:36-61`, y retirar el `AppShell`.
- [x] 6.4 Reconstruir sobre el sistema de estilos nuevo las pantallas del destino que conservan
  comportamiento (`LoginPage`, `IngestPage`, `ConversationsPage`, y el resumen de facturación en su
  ruta puente), sin tocar sus llamadas ni sus consultas.
- [x] 6.5 **Red/Green**: pruebas de enrutado que cubran los escenarios de la spec — abrir una
  dirección directamente presenta su pantalla, el ámbito activo sobrevive a la navegación, y sin
  sesión se presenta el acceso. Hecho: `routes.integration.test.tsx`, montado sobre el `routeConfig`
  real (no providers simulados). **Sin fase Green**: los 3 casos pasaron a la primera — el grupo 6 ya
  estaba implementado y verificado por piezas en las 4 sub-rondas anteriores; esta tarea añade
  cobertura de integración real, no comportamiento nuevo. Mutación N/A (ningún archivo de producto
  cambió). QA verificó el mecanismo rompiendo temporalmente `routes.tsx` y `SessionGate.tsx`
  (revertido): confirmó que los 3 tests fallan cuando el comportamiento real se rompe. Veredicto QA:
  `accept`.
- [x] 6.6 Verificar a mano el recorrido de paridad de JUP-090 (acceso → ámbito → resumen) contra el
  backend local con el seed `operator@example.com` / `secret`. Hecho: backend real levantado con
  `docker compose` (`cockroachdb`, `rabbitmq`, `postgres-pgvector`, `azure-cost-api`, `backend`),
  frontend con `pnpm dev`, recorrido conducido con Playwright + Chromium real (no jsdom) y capturado
  en pantalla en cada paso. Los 6 pasos del guion de JUP-090 completados con éxito: sin sesión →
  `/login`; login con el seed → dashboard índice; selector de tenant con auto-selección correcta
  (`Core Finance`); `/overview-legacy` con datos reales de `/billing/summary` y `/health`
  (`$184,250`/`$23,500`/2 tenants, 3 servicios `ok`); cambio de tenant (`Growth Ops`) sobrevive a la
  navegación real (clic en `NavLink`) a `/operational`; logout devuelve a `/login`. Cero errores de
  consola. **Hallazgo nuevo, no relacionado con esta tarjeta**: el backend no tiene `CORSMiddleware`
  configurado — bloquea `POST /auth/login` en cualquier navegador real (no en `curl`), verificado
  sorteándolo con `--disable-web-security` solo para esta verificación. Registrado como `RF-095-001`
  en `openspec/findings/backlog.md`, fuera de alcance de JUP-095 (responsabilidad del backend).
  Detalle completo, capturas y comandos en `review.md`.

## 7. Entrypoint e `index.html`

- [x] 7.1 Reconciliar `index.html`: entrypoint `.tsx`, conservando `<div id="root">` y el título
  `FinOps Control Tower` del destino (**no** el `Plataforma FinOps automatizada (copia)` del origen).
  Hecho: `main.jsx` → `main.tsx` (Red `1957e83`, Green `7e765db`), `index.html` apunta a
  `/src/main.tsx`; título y `div#root` sin tocar. Test real (`index-html-entrypoint.test.ts`) que lee
  el archivo del disco, mismo patrón que 3.3. Veredicto QA: `accept`.
- [x] 7.2 Reconciliar el entrypoint para que monte **ambos** proveedores: el de consultas de datos del
  destino y el de enrutado del origen. Hecho: ya estaba implementado en `main.jsx` desde el cierre del
  grupo 6 (`QueryClientProvider` envolviendo `App`/`RouterProvider`), sin cambio de comportamiento;
  esta tarea solo migró la extensión/tipado (mismo commit `7e765db`). Mutación N/A: Stryker no puede
  ejecutar sobre `main.tsx` porque ningún test lo importa en runtime (decisión de alcance, ver
  `review.md`). DoD verificado manualmente con `corepack pnpm --filter` por un problema de entorno de
  la máquina (pnpm global v11.9.0 pisando al de corepack), ajeno a este cambio. Veredicto QA: `accept`.
- [x] 7.3 Verificar arranque con `corepack pnpm --filter @finops/frontend dev` en el puerto 5173, sin
  errores de consola, navegando por todas las rutas del mapa. Hecho: verificación manual con
  Playwright + Chromium real contra el backend local (mismo patrón que 6.6), login/logout reales y
  las 8 rutas del mapa abiertas directamente. Cero errores de consola, cero excepciones de página.
  Único hallazgo, ya registrado y sorteado igual que en 6.6: `RF-095-001` (CORS del backend, fuera de
  alcance). Detalle completo en `review.md`. **Grupo 7 completo.**

## 8. Migración `.tsx` restante y limpieza

- [x] 8.1 Migrar a `.tsx`/`.ts` los archivos del destino que el enrutado ha obligado a tocar, sin
  cambio de comportamiento. `src/services/api.js` y `src/hooks/useDashboardData.js` **no se tocan**:
  son de JUP-096 (decisión 1 del `design.md`). Hecho: `App.jsx` → `App.tsx` (único `.jsx` que quedaba
  con ese perfil), verbatim (solo cambia el comentario de cabecera). `git diff` vacío confirmado sobre
  `api.js`/`useDashboardData.js`. Sin Red/Green: sin comportamiento nuevo (mismo criterio que 7.1/7.2
  para `main.tsx`). Veredicto QA: `accept`.
- [x] 8.2 Eliminar `src/styles/main.css` y `src/pages/PlaceholderPage.jsx`, y verificar que no queda
  ninguna referencia a ellos en el árbol. Hecho: verificado antes y después del borrado (grep + build
  real, QA confirmó que una referencia rota rompe `vite build`). Solo quedan menciones en comentarios
  explicativos de `MetricCard.tsx`/`SectionCard.tsx`/`StatusPill.tsx` (no son referencias activas).
  `find apps/frontend/src -name "*.jsx"` → sin resultados. Veredicto QA: `accept`.
- [ ] 8.3 Registrar la **nueva línea base de lint** y confirmar que `RF-082-002` sigue `Open`, con la
  lista de archivos `.jsx` que quedan y la tarjeta que los cerrará.
- [ ] 8.4 Confirmar que `git diff` sobre `src/services/api.js` y `src/hooks/useDashboardData.js` está
  vacío salvo el posible cambio de extensión sin cambio de lógica.

## 9. Cierre y verificación

- [ ] 9.1 Ejecutar la batería completa: `corepack pnpm --filter @finops/frontend typecheck`, `lint`,
  `test`, `build`; `corepack pnpm install --frozen-lockfile`; `corepack pnpm openspec:validate`;
  `corepack pnpm jup:check -- --change jup-095-portar-codigo-fuente`; `corepack pnpm jup:cleanup:check`
  (sustitutos con `--filter` por `RF-093-001`).
- [ ] 9.2 Añadir a `openspec/findings/backlog.md` el finding nuevo por los datos de demostración en la
  ruta de producto, con dueño (JUP-096) y su relación con `RF-091-003`. Confirmar sin cambio de estado
  `RF-090-001`, `RF-090-003`, `RF-091-003`, `RF-091-004` y `RF-093-001`.
- [ ] 9.3 Actualizar `docs/spikes/frontend-migration.md`: sustituir el placeholder
  `jup-0xx-portar-codigo-fuente` por `jup-095-portar-codigo-fuente`, marcar sus tres tareas y anotar en
  "Proximos pasos" qué queda de F3.
- [ ] 9.4 Escribir `review.md`: resultado, decisiones con su motivo, evidencia Red/Green y de mutación,
  veredicto QA, nueva línea base de lint, primitivos sin consumidor, y la deuda `/overview-legacy` con
  su dueño.
- [ ] 9.5 Crear `docs/evidence/JUP-095-validation.md` con comandos exactos, conteos de pruebas,
  resultado del DoD y enlaces de PR y CI.
- [ ] 9.6 Actualizar `apps/frontend/README.md` (stack, estructura y rutas) y la sección de seguimiento
  de [ADR-0003](../../../docs/adr/ADR-0003-frontend-typescript.md) con lo que esta tarjeta ejecutó.
