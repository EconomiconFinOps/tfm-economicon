# Evidencia de validacion JUP-095

- Fecha: 2026-09-12.
- Tarjeta: https://trello.com/c/G4FPtBdE/87-jup-095-portar-el-c%C3%B3digo-fuente-del-frontend-de-economicon.
- Rama: `feat/JUP-095-portar-codigo-fuente`.
- Base: `origin/develop` en `278769c` (JUP-094, PR #28).
- Pull request: pendiente de abrir (se completa este enlace y el de CI tras el paso 7 del flujo).

## Alcance validado

- Los 8 `.tsx` vivos del origen portados (5 dashboards de coste, `Layout`, `ExportButton`,
  `routes.tsx`), con sus constantes extraídas a `src/data/demo/` (origen de datos señalizado como
  sustituible).
- Enrutado real montado: `SessionGate` (nuevo) como ruta padre de `Layout`, pasando sesión/tenant a
  las rutas hijas vía `Outlet context` de react-router (Addendum del grupo 6 de `design.md`).
  `LoginPage`/`IngestPage`/`ConversationsPage`/`DashboardPage` reconstruidas sobre Tailwind
  conservando su lógica verbatim (mismas llamadas a `services/api.js`, mismas queries/mutaciones).
- Sistema de estilos del origen adoptado (`@tailwindcss/vite`, `tailwind.css`, `theme.css`), ámbito
  oscuro declarado explícitamente (`class="dark"` en `<html>`), alias `@/` en `tsconfig.json` y
  `vite.config.ts`.
- 5 primitivos de shadcn/ui copiados a `src/components/ui/` (`label`, `separator`, `select`,
  `dialog`, `tooltip`) más la utilidad `cn()` — subconjunto autorizado por
  [ADR-0004](../adr/ADR-0004-frontend-shadcn-ui.md), sin consumidor real fuera de sus propios tests
  al cierre de la tarjeta (peso muerto aceptado por escrito en el ADR).
- Runner de pruebas (Vitest + Testing Library) adoptado, con job `Frontend tests` promovido a
  comprobación obligatoria de CI (`.github/workflows/ci.yml` y ambos rulesets).
- Entrypoint reconciliado: `main.jsx` → `main.tsx` (ambos proveedores, `QueryClientProvider` +
  `App`/`RouterProvider`), `index.html` apunta a `/src/main.tsx`, título y `div#root` del destino
  intactos. `App.jsx` → `App.tsx`, `src/styles/main.css` y `src/pages/PlaceholderPage.jsx`
  retirados.
- `src/services/api.js` y `src/hooks/useDashboardData.js` **sin tocar** (frontera con la lógica del
  destino, decisión 1 de `design.md`), verificado con `git diff` vacío contra `278769c`.
- `RF-082-002` cerrado `Fixed` (línea base de lint: 49 violaciones en 9 `.jsx` → 0 violaciones, 0
  `.jsx` en `src/**`). Finding nuevo `RF-095-002` (datos de demostración en 5 pantallas de coste) y
  `RF-095-001` (backend sin `CORSMiddleware`, descubierto en la verificación E2E de la tarea 6.6),
  ambos registrados en `openspec/findings/backlog.md`, fuera de alcance de esta tarjeta.

## Ciclo TDD

Primera tarjeta de la épica con superficie unit-testeable real en el frontend (el runner se instala
en el grupo 2 de esta misma tarjeta). Resumen por grupo — detalle completo, hashes de commit y
justificación de cada excepción en `review.md` (sección "Cierre de la tarjeta — resumen").

| Grupo | Red/Green | Mutación | Veredicto QA |
| --- | --- | --- | --- |
| 2 (runner) | `HarnessSmoke` (canario), CI | 100% (`HarnessSmoke`) | `accept` |
| 3 (estilos) | ámbito oscuro (único con comportamiento nuevo) | N/A (config/CSS/atributo estático) | `accept` |
| 4 (primitivos shadcn) | 6 primitivos + `cn()` | 25.81% (4/7 supervivientes remediados) | `accept` |
| 5 (pantallas portadas) | 7 pantallas | 12.11% (aceptada, bajo retorno documentado) | `accept` |
| 6 (enrutado y armazón) | 4 sub-rondas, cada una Red/Green propio | 51.15% / 43.48%→82.61% / 18.66% / 35.48% según sub-ronda | `accept` en las 4 |
| 7 (entrypoint) | `index.html` → `main.tsx` (único comportamiento nuevo real) | N/A (Stryker sin tests que importen `main.tsx` en runtime) | `accept` |
| 8 (`.tsx` restante y limpieza) | sin ciclo (rename mecánico + borrado de código muerto, sin comportamiento nuevo) | N/A (mismo motivo que grupo 7) | `accept` |

**Sin ningún `changes-requested` en toda la tarjeta.**

## Resultados (batería completa, tarea 9.1)

| Comprobación | Resultado |
| --- | --- |
| `pnpm --filter @finops/frontend typecheck` | Superado (2 proyectos: `src` y `tsconfig.node.json`) |
| `pnpm --filter @finops/frontend lint` | **0 problemas** (línea base original: 49 `react/prop-types` en 9 `.jsx`) |
| `pnpm --filter @finops/frontend test` | **39/39 tests, 27 archivos** |
| `pnpm --filter @finops/frontend build` | Superado — JS `762.55 kB` / gzip `215.75 kB`, CSS `39.63 kB` / gzip `7.86 kB` (bundle crece por Tailwind + recharts + react-router real, esperado) |
| `pnpm install --frozen-lockfile` | Lockfile sin cambios |
| `pnpm openspec:validate` | 23/23 elementos válidos, 0 fallos |
| `pnpm jup:check -- --change jup-095-portar-codigo-fuente` | Enlazada con Trello y completa |
| `pnpm jup:cleanup:check` | 448 archivos aceptados |

**Sustitución documentada:** `pnpm lint`/`pnpm build`/`pnpm typecheck`/`pnpm test` en la raíz (vía
turbo) sustituidos por sus equivalentes `--filter @finops/frontend`, por la misma limitación de
entorno preexistente que documenta `RF-093-001` (un `pnpm` global instalado vía `npm` en la máquina
de desarrollo pisa al gestionado por `corepack` cuando `turbo` invoca los scripts por paquete;
confirmado que afecta a los 4 paquetes del monorepo por igual, no específico de esta tarjeta). El
mismo motivo bloqueó `.claude/harness/check-dod.mjs` en las tareas 7.1/7.2 y 8.1/8.2; verificado
manualmente con los comandos `--filter` equivalentes en ambos casos (detalle en `review.md`).

## Verificación manual E2E

- **Tarea 6.6** (paridad de JUP-090): backend real (`docker compose`), frontend con `pnpm dev`,
  recorrido con Playwright + Chromium real. Los 6 pasos del guion (acceso → login con el seed
  `operator@example.com`/`secret` → dashboard índice → selector de tenant con auto-selección →
  `/overview-legacy` con datos reales → cambio de tenant sobrevive a la navegación → logout)
  completados con éxito, cero errores de consola. Hallazgo: `RF-095-001` (CORS del backend).
- **Tarea 7.3** (arranque tras reconciliar el entrypoint): mismo patrón, smoke check más ligero (no
  repite el guion completo) sobre las 8 rutas del mapa abiertas directamente, login/logout reales.
  Cero errores de consola, cero excepciones de página.

## Limitaciones y deuda declaradas

1. **`/overview-legacy`** es una ruta puente temporal (decisión 6 de `design.md`): único dashboard
   con datos reales hoy. Dueño: la siguiente tarjeta de F3 que reconcilie la capa de datos, que la
   retira al conectar el nuevo Overview.
2. **Datos de demostración en la ruta de producto** (`RF-095-002`): las 5 pantallas de coste
   portadas muestran datos estáticos de `src/data/demo/`, no datos reales — relacionado con
   `RF-091-003`/`RF-091-004`, decisión de épica pendiente sobre qué capacidades de backend se
   construyen primero.
3. **6 primitivos de shadcn/ui sin consumidor real** (`label`, `separator`, `select`, `dialog`,
   `tooltip`, `cn()`): peso muerto aceptado por escrito en ADR-0004, disponibles para consumo futuro
   sin trabajo adicional de instalación.
4. **`RF-095-001`** (backend sin `CORSMiddleware`): bloquea cualquier navegador real contra el
   backend local; fuera de alcance de esta tarjeta (responsabilidad exclusiva del backend).
5. La séptima comprobación obligatoria (`Frontend tests`) queda versionada en ambos rulesets pero no
   activa en GitHub todavía: requiere que un administrador reaplique el ruleset, mismo paso
   pendiente que dejaron JUP-079/JUP-093 para `Frontend type check`.

## Pendiente

- Abrir el pull request hacia `develop` y completar este enlace y el de la ejecución de CI.
- Gate post-review (aprobación humana) y archivado del change OpenSpec.
- Activación en vivo de la nueva check context (`Frontend tests`) por un administrador del
  repositorio.
- Siguientes tarjetas de F3 (`reconciliar-capa-api`, `reconciliar-auth-tenant`,
  `unificar-estilos-assets`), citando ADR-0003/ADR-0004 en su `design.md` y resolviendo `RF-095-002`.
