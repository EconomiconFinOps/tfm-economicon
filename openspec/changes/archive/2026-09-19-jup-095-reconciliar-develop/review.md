JUP: JUP-095
Trello: https://trello.com/c/G4FPtBdE/87-jup-095-portar-el-c%C3%B3digo-fuente-del-frontend-de-economicon
Rama: `feat/JUP-095-portar-codigo-fuente`

## Nota sobre el proceso seguido

A diferencia del ciclo Red/Green/mutación por tarea de `jup-095-portar-codigo-fuente` (archivada),
esta tarjeta se ejecutó de forma interactiva junto con Víctor: resolución de conflictos de merge
fichero a fichero con su confirmación explícita en cada bloque, seguida de tres arreglos de
comportamiento implementados y verificados con `typecheck`/`lint`/`test`/`build` en cada punto de
control, no con mutación por tarea. No hay evidencia Red/Green por commit porque no se siguió ese
patrón; la evidencia real es el resultado de la suite completa en cada commit, citado abajo.

## Grupo 1-2 — Fusión de `develop` y conflictos silenciosos

17 conflictos de Git resueltos por bloques (borrados, armazón, tarjetas, páginas, config, docs), más
dos conflictos "silenciosos" que el auto-merge dejaba rotos sin marcador: la migración de 4 páginas de
`api.js` sin tipar a `api.ts`/`contracts.ts`, y un job de CI duplicado (`frontend-tests`) que ejecutaba
la suite del frontend dos veces tras fusionar `ci.yml`.

- Commits: `03325b9` (merge), `0c32ea2` (SessionGate/DashboardPage sin volver a añadir al índice tras
  un fix ya verificado — detectado y corregido en el mismo turno).
- Decisión explícita de Víctor: consolidar a los 7 checks de CI ya activos en vez de conservar el
  octavo sin activar (design.md, Decisión 4).
- Verificado: `typecheck` (3 tsconfig) y `lint` limpios. `pnpm install` regenera `pnpm-lock.yaml` sin
  fricciones (1 paquete nuevo, resto reutilizado).

## Grupo 3 — Adaptar la suite heredada de `develop` a `createMemoryRouter`

- Commit: `74e46a8`.
- `test-support.tsx` pasa de renderizar `<App/>` directo (arquitectura antigua) a
  `createMemoryRouter(routeConfig, { initialEntries })`, mismo patrón que `routes.integration.test.tsx`
  ya commiteado.
- 4 de las 5 suites de `develop` (`ingestion`, `conversations`, `session-and-dashboard`,
  `LoginPage.mutation`) adaptadas: navegación por ruta inicial en vez de clic en botones inexistentes,
  etiquetas ajustadas al `Layout` real (español donde `SessionGate`/`Layout` lo son, inglés donde las
  páginas conectadas al backend ya lo eran).
- `tenant-switching.test.tsx` (5ª suite) se deja sin tocar: prueba el aislamiento de tenant, que
  todavía no existía — decisión explícita de Víctor de implementar la funcionalidad antes de adaptar
  esa suite, no al revés.
- Verificado: 57 passed, 7 failed (`tenant-switching`, esperado), 3 skipped (2 casos que dependen de
  enlaces de menú aún no implementados + su `it.each`), de 67.

## Grupo 4 — Aislamiento de estado entre tenants (Punto 1)

- Commit: `ec1bfa9`.
- Primera versión (`key` en el `Outlet` de `Layout`, afectando a las 8 pantallas) rompió 3 pruebas de
  login en vivo por una carrera en el arranque de sesión (`activeTenant` resuelve en dos renders:
  `null` mientras `activeTenantId` local vale `""`, luego el tenant auto-seleccionado). Corregido con
  `TenantScopedOutlet`, acotado a `/ingest`/`/assistant` — ver design.md, Decisión 2.
- `tenant-switching.test.tsx` adaptado a `createMemoryRouter` una vez la funcionalidad existe.
- Verificado: 64 passed, 0 failed, 3 skipped (Punto 5, sin implementar todavía), de 67.

## Grupo 5 — Enlaces de menú (Punto 5)

- Commit: `4908c4a`.
- `backendNavItems` en `Layout.tsx`: Ingestions/Assistant/Overview, separados visualmente de las 5
  pantallas de demostración con un divisor.
- Reactivados los 2 casos aparcados en el grupo 3, ajustando rol `link` (no `button`) y las etiquetas
  reales.
- Verificado: 67 passed, 0 failed, 0 skipped.

## Grupo 6 — Validación de sesión (Punto 2)

- Commit: `674f1d7`.
- `isSession`/`loadStoredSession` trasladados de `develop` (`App.jsx`) a `SessionGate.tsx`, usando
  `UserProfile` del contrato en vez de una forma local laxa.
- Efecto colateral detectado antes de romper CI: dos fixtures de test ya commiteados
  (`SessionGate.test.tsx`, `routes.integration.test.tsx`) sembraban una sesión con `user` incompleto
  (sin `id`/`role`) — completados para seguir siendo válidos bajo `isSession`.
- Cobertura nueva en fichero nuevo (`SessionGate.validation.test.tsx`, no se amplían los ya
  commiteados): JSON válido con estructura inválida (`{}` y `user` parcial con `accessToken`
  presente).
- Verificado: 69 passed, 0 failed, 0 skipped — la suite completa, sin ningún caso pendiente.

## Grupo 7 — Verificación final

- `corepack pnpm build` (frontend): 2477 módulos, sin errores. Aviso de Vite (no error): el bundle
  JS final pesa 765 kB minificado, por encima del umbral de 500 kB — preexistente a esta tarjeta
  (Radix, recharts ya presentes en ambas ramas), no introducido ni corregido aquí.
- `openspec:validate --all --strict`: 32/32 (incluye este change).
- `jup:check --change jup-095-reconciliar-develop`: enlazado con Trello y completo.

## Hallazgos fuera de alcance (sin tocar)

- `RF-095-001` (CORS ausente en backend), `RF-087-001`/`RF-087-002` (preflight/JSONB de historial) y
  la carrera de migraciones backend/processor (antes referenciada como "JUP-096", hoy sin número
  confirmado en `backlog.md`) siguen abiertos, tal como estaban.
- `RF-095-002` (5 pantallas de coste con datos de demostración) sigue abierto: fuera de alcance de
  esta reconciliación, dueño la siguiente tarjeta de F3 que reconcilie la capa de datos.
- `allowJs: true` en `tsconfig.json` sin ningún `.js`/`.jsx` restante en el árbol: deuda menor
  detectada, no introducida ni corregida por esta tarjeta.
- Dos changes de OpenSpec bajo el mismo identificador JUP-095 (esta tarjeta y la archivada): sin
  precedente en el repo, decisión explícita de Víctor para no reabrir el change ya aprobado ni
  inventar un número nuevo (ver proposal.md - Why).

## Human Approval

- Change: jup-095-reconciliar-develop
- Approval type: post-review
- Decision: approved
- Approver: Victor
- Date: 2026-09-19
- Review accepted: yes
- Checks accepted: yes
- Documentation synchronized: yes
- Archive decision: archive
- Notes: Reconciliación de la rama `feat/JUP-095-portar-codigo-fuente` con `develop` (JUP-087/JUP-020)
  aprobada tras resolución interactiva de los 17 conflictos de merge y de los 5 puntos de la propuesta
  de revisión (contraseña vacía, aislamiento de tenant, errores de conversación visibles, enlaces de
  menú, validación de sesión), más dos conflictos silenciosos detectados durante el proceso (páginas
  sin migrar a los contratos tipados, job de CI duplicado). Suite completa en verde (69/69, 0
  skipped), typecheck/lint/build limpios. Sin ADR nuevo: decisiones de alcance técnico dentro de
  patrones ya aprobados (ADR-0003 TypeScript, ADR-0004 shadcn/ui), documentadas en design.md. Pendiente
  fuera de esta tarjeta: conectar las 5 pantallas de demostración a datos reales (RF-095-002, dueño la
  siguiente tarjeta de F3), CORS de JUP-085, JSONB de JUP-035, carrera de migraciones sin número de
  tarjeta confirmado.
