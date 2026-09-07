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

- [ ] 2.1 Instalar el runner con `corepack pnpm --filter @finops/frontend add -D vitest
  @testing-library/react @testing-library/jest-dom jsdom` (pnpm-only; **nunca** `npm i`) y verificar
  que las versiones resueltas no traen un mayor incompatible con React 18 ni con Vite 5 — precedente
  de JUP-093 y JUP-094, donde el resolutor trajo `typescript@7` y `react-router@8`.
- [ ] 2.2 Configurar Vitest sobre el `vite.config.ts` existente (entorno DOM y fichero de setup) y
  sustituir el script `test` (`echo`) por la invocación real, conservando los otros 6 scripts y el
  puerto 5173 del script `dev`.
- [ ] 2.3 **Red/Green**: primera prueba real que renderice un componente y falle antes de existir el
  código que la satisface, para dejar evidencia del ciclo del harness. Verificar que `test` termina
  con estado de error cuando una prueba falla.
- [ ] 2.4 Añadir el job *Frontend tests* a `.github/workflows/ci.yml`, con el mismo patrón de los jobs
  *Frontend build* y *Frontend type check* (`corepack pnpm --filter @finops/frontend test`).
- [ ] 2.5 Registrar *Frontend tests* como comprobación obligatoria en `.github/rulesets/develop.json`
  y `.github/rulesets/main.json`, y documentarlo en `docs/governance/github-branch-protection.md`,
  anotando que la activación remota es acción de administrador (mismo patrón que JUP-093).

## 3. Estilos, Tailwind y alias

- [ ] 3.1 Cablear `@tailwindcss/vite` en `apps/frontend/vite.config.ts` sin alterar el plugin de React
  ni introducir `server.port`/`server.host` que choquen con los flags del script `dev`.
- [ ] 3.2 Incorporar del origen `src/styles/tailwind.css` y `src/styles/theme.css`, más un
  `index.css` que los importe. **No** se copia `fonts.css` (vacío) ni `postcss.config.mjs` (stub).
- [ ] 3.3 Declarar explícitamente el ámbito oscuro para que los tokens de `theme.css` no rendericen en
  claro bajo pantallas oscuras (decisión 4 del `design.md`).
- [ ] 3.4 Añadir el alias `@/` en **los dos** sitios: `paths` en `tsconfig.json` y `resolve.alias` en
  `vite.config.ts` (decisión 5). Verificar que `typecheck` y `build` lo resuelven ambos.
- [ ] 3.5 Verificar que `main.css` **sigue en su sitio** y que la aplicación arranca: hasta el grupo 8
  no se retira nada.

## 4. Primitivos de shadcn/ui

- [ ] 4.1 Copiar a `src/components/ui/` únicamente los primitivos que las pantallas reconstruidas
  vayan a usar, uno a uno, del subconjunto de 6 autorizado por
  [ADR-0004](../../../docs/adr/ADR-0004-frontend-shadcn-ui.md). Ningún otro de los 48 archivos de
  `ui/` del origen entra.
- [ ] 4.2 Añadir la utilidad de composición de clases que esos componentes importan (`@/lib/utils`),
  apoyada en `clsx` y `tailwind-merge`, ya instaladas por JUP-094.
- [ ] 4.3 **Red/Green** por primitivo copiado: prueba de render antes del componente.
- [ ] 4.4 Dejar anotado en `review.md` qué primitivos de los 6 instalados quedan **sin consumidor** al
  terminar la tarjeta: es el peso muerto que ADR-0004 aceptó por escrito como riesgo.

## 5. Componentes del origen y datos de demostración

- [ ] 5.1 Portar los **8 `.tsx` vivos** del origen (`ExecutiveCostDashboard`,
  `OperationalCostDashboard`, `ExecutiveCutDashboard`, `AnomaliesPanel`, `RecommendationsPanel`,
  `Layout`, `ExportButton`, `routes.tsx`) a la estructura del destino. **No entran**
  `figma/ImageWithFallback.tsx` (sin consumidor), el plugin `figmaAssetResolver` ni el `assetsInclude`
  del `vite.config.ts` del origen.
- [ ] 5.2 Extraer las constantes estáticas de cada dashboard a `src/data/demo/`, señalizado como
  origen sustituible, sin cambiar los datos que muestran (decisión de aislamiento; escenarios de
  `frontend-navigation-shell`).
- [ ] 5.3 Resolver los errores de `strict: true` **tipando**: prohibido `any` nuevo y `@ts-ignore`. Si
  el volumen desborda la tarjeta, aplicar el criterio de escape de ADR-0003 (documentar y superseder),
  nunca relajar `tsconfig.json` en silencio.
- [ ] 5.4 **Red/Green** por pantalla portada: prueba de render que verifique que presenta sus datos de
  demostración.
- [ ] 5.5 Verificar `typecheck`, `test` y `build` en verde con las pantallas ya en el árbol, aún sin
  enrutar.

## 6. Enrutado y armazón

- [ ] 6.1 Montar el enrutado con el mapa de la decisión 3: bajo el `Layout`, `/`, `/operational`,
  `/cuts`, `/anomalies`, `/recommendations`, `/ingest` y `/assistant`; `/login` fuera del `Layout`;
  `/overview-legacy` como ruta puente del resumen de facturación actual.
- [ ] 6.2 Retirar el enrutado manual por `activeView` de `App.jsx` (líneas 127-150) **preservando
  verbatim** la lógica de sesión, tenant activo, login/logout y la consulta de tenants.
- [ ] 6.3 Injertar en el `Layout` del origen el selector de ámbito de cliente y el panel de
  sesión/logout que hoy viven en `AppShell.jsx:36-61`, y retirar el `AppShell`.
- [ ] 6.4 Reconstruir sobre el sistema de estilos nuevo las pantallas del destino que conservan
  comportamiento (`LoginPage`, `IngestPage`, `ConversationsPage`, y el resumen de facturación en su
  ruta puente), sin tocar sus llamadas ni sus consultas.
- [ ] 6.5 **Red/Green**: pruebas de enrutado que cubran los escenarios de la spec — abrir una
  dirección directamente presenta su pantalla, el ámbito activo sobrevive a la navegación, y sin
  sesión se presenta el acceso.
- [ ] 6.6 Verificar a mano el recorrido de paridad de JUP-090 (acceso → ámbito → resumen) contra el
  backend local con el seed `operator@example.com` / `secret`.

## 7. Entrypoint e `index.html`

- [ ] 7.1 Reconciliar `index.html`: entrypoint `.tsx`, conservando `<div id="root">` y el título
  `FinOps Control Tower` del destino (**no** el `Plataforma FinOps automatizada (copia)` del origen).
- [ ] 7.2 Reconciliar el entrypoint para que monte **ambos** proveedores: el de consultas de datos del
  destino y el de enrutado del origen.
- [ ] 7.3 Verificar arranque con `corepack pnpm --filter @finops/frontend dev` en el puerto 5173, sin
  errores de consola, navegando por todas las rutas del mapa.

## 8. Migración `.tsx` restante y limpieza

- [ ] 8.1 Migrar a `.tsx`/`.ts` los archivos del destino que el enrutado ha obligado a tocar, sin
  cambio de comportamiento. `src/services/api.js` y `src/hooks/useDashboardData.js` **no se tocan**:
  son de JUP-096 (decisión 1 del `design.md`).
- [ ] 8.2 Eliminar `src/styles/main.css` y `src/pages/PlaceholderPage.jsx`, y verificar que no queda
  ninguna referencia a ellos en el árbol.
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
