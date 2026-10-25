## 1. Fusión de `develop` y resolución de conflictos

- [x] 1.1 Simular la fusión sin tocar el checkout y clasificar los 17 archivos en conflicto por
  bloque (borrados, armazón, tarjetas, páginas, config, docs). Hecho: `git tag
  backup/JUP-095-pre-merge`, `git merge origin/develop`, inventario confirmado en 17 rutas.
- [x] 1.2 Resolver borrados (`AppShell.tsx`, `PlaceholderPage.tsx`), armazón (`App.tsx` reducido a
  `RouterProvider`, `main.tsx`) y tarjetas (`MetricCard`/`SectionCard`/`StatusPill` sobre Tailwind,
  `StatusPill` con `status` opcional/nulo).
- [x] 1.3 Resolver las cuatro páginas (`Login`/`Ingest`/`Conversations`/`Dashboard`): estructura por
  Outlet context de JUP-095 + tipos reales de `contracts.ts` en vez de duplicados locales. Punto 3
  (contraseña vacía) y Punto 4 (errores de conversación visibles) resueltos aquí, en la misma línea
  que ya distinguía ambas versiones.
- [x] 1.4 Resolver configuración (`vite.config.ts` con `include` de `src/**` y `tests/**` y setup
  unificado, `package.json` con `docker:build` de contexto de workspace y dependencias de test
  completas) y regenerar `pnpm-lock.yaml` con `pnpm install`.
- [x] 1.5 Resolver documentación (`README.md`, `github-branch-protection.md`, `backlog.md` con
  `RF-082-002` fusionado sin perder evidencia de ninguna rama) y retirar el job `frontend-tests`
  duplicado de `ci.yml` (Decisión 4 de design.md), actualizando ambos rulesets y
  `tools/ci-workflow.test.mjs`.
  Hecho: commit `03325b9`.

## 2. Conflictos silenciosos (sin marcador de Git)

- [x] 2.1 Adaptar `LoginPage`, `IngestPage`, `ConversationsPage` y `SessionGate` a los tipos reales
  de `api.ts`/`contracts.ts` (sustituyen a `api.js` sin tipar): tipos locales laxos reemplazados por
  los del contrato, guardas explícitas de tenant requerido donde el compilador lo exige.
  Hecho: incluido en commit `03325b9`.
- [x] 2.2 Completar el tipado de `SessionGate.tsx` (reemplazar `Tenant` local por `TenantRecord` del
  contrato) que quedó sin volver a añadir al índice tras el commit de merge. Hecho: commit `0c32ea2`.
- [x] 2.3 Verificar `typecheck` (3 tsconfig) y `lint` limpios tras el merge completo.

## 3. Adaptar la suite de test heredada a `createMemoryRouter`

- [x] 3.1 `test-support.tsx`: `renderApp()` monta `routeConfig` sobre `createMemoryRouter` con
  `initialEntries` configurable en vez de `<App/>` directo sobre `createBrowserRouter`.
- [x] 3.2 Adaptar `ingestion.test.tsx` y `conversations.test.tsx`: navegación por ruta inicial en vez
  de clic en un botón inexistente; etiquetas ajustadas al `Layout` real.
- [x] 3.3 Adaptar `session-and-dashboard.test.tsx`: rutas a `/overview-legacy` donde se necesita el
  dashboard real; textos de `SessionGate` en español; aparcar (`it.skip`, con comentario) los 2 casos
  que dependen de enlaces de menú aún no implementados.
- [x] 3.4 Corregir `LoginPage.mutation.test.tsx` (valor por defecto de password, Punto 3).
- [x] 3.5 Dejar `tenant-switching.test.tsx` sin tocar hasta implementar el aislamiento de tenant
  (grupo 4): prueba una funcionalidad que todavía no existe.
  Hecho: commit `74e46a8`. Verificado: 57 passed, 7 failed (tenant-switching, esperado), 3 skipped.

## 4. Aislamiento de estado entre tenants (Punto 1)

- [x] 4.1 Implementar `TenantScopedOutlet` en `Layout.tsx`: `Outlet` con
  `key={activeTenant?.id ?? "no-tenant"}`.
- [x] 4.2 Insertar `TenantScopedOutlet` en `routes.tsx` únicamente alrededor de `/ingest` y
  `/assistant` (Decisión 2 de design.md: la primera versión, a nivel del `Outlet` de `Layout`, rompía
  3 pruebas de login en vivo por una carrera en el arranque de sesión; corregido acotando el alcance).
- [x] 4.3 Adaptar `tenant-switching.test.tsx` a `createMemoryRouter` (mismo tratamiento que el grupo
  3) ahora que la funcionalidad existe.
  Hecho: commit `ec1bfa9`. Verificado: 64 passed, 0 failed, 3 skipped.

## 5. Enlaces de menú a pantallas conectadas al backend (Punto 5)

- [x] 5.1 Añadir `backendNavItems` a `Layout.tsx` (Ingestions, Assistant, Overview), separados
  visualmente de las 5 pantallas de demostración con un divisor.
- [x] 5.2 Reactivar y adaptar los 2 casos aparcados en el grupo 3 (`session-and-dashboard.test.tsx`):
  rol `link` en vez de `button`, etiquetas reales.
  Hecho: commit `4908c4a`. Verificado: 67 passed, 0 failed, 0 skipped.

## 6. Validación de la sesión persistida (Punto 2)

- [x] 6.1 Trasladar `isSession`/`loadStoredSession` desde `develop` a `SessionGate.tsx`, usando
  `UserProfile` del contrato en vez de una forma local laxa.
- [x] 6.2 Completar los fixtures de sesión en `SessionGate.test.tsx` y `routes.integration.test.tsx`
  (`user` sin `id`/`role`, ya no válidos bajo `isSession`).
- [x] 6.3 Añadir `SessionGate.validation.test.tsx` (fichero nuevo): JSON válido con estructura
  inválida (`{}` y `user` parcial con `accessToken` presente).
  Hecho: commit `674f1d7`. Verificado: 69 passed, 0 failed, 0 skipped.

## 7. Verificación final y cierre

- [x] 7.1 Ejecutar `build` de producción del frontend. Hecho: `vite build` sin errores (aviso
  preexistente de tamaño de chunk, no introducido por esta tarjeta).
- [x] 7.2 Escribir `review.md`: resumen de la reconciliación, decisiones, evidencia por grupo,
  hallazgos fuera de alcance.
- [x] 7.3 Registrar aprobación humana (`## Human Approval`, tipo post-review) y decisión de archivo.
- [x] 7.4 Archivar el change (`openspec:archive`) tras la aprobación.
- [x] 7.5 `openspec:validate` y `jup:check` en verde antes de archivar.
