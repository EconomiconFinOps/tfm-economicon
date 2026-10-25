## Context

JUP-095 (archivada) portó pantallas, router y estilos a `apps/frontend` desde un punto de `develop`
anterior a JUP-087 (línea base de calidad) y JUP-020 (ingesta HTTP). Su PR #36 generaba 17 rutas en
conflicto contra el `develop` vigente. Ver proposal.md - Why para el origen completo y la propuesta
de reconciliación que motivó esta tarjeta.

## Goals / Non-Goals

**Goals:**
- Cerrar los 17 conflictos de merge conservando router/pantallas/estilos de JUP-095 y
  contratos/regresión/calidad de `develop`, sin degradar ningún contrato de API.
- Implementar los tres requisitos nuevos de `frontend-navigation-shell` (aislamiento de tenant,
  validación de sesión, alcanzabilidad por menú) y restaurar los dos comportamientos que ya exigían
  specs existentes (contraseña vacía, errores de conversación visibles).
- Dejar las dos suites de test (JUP-095 + JUP-087) descubiertas, tipadas y en verde bajo una sola
  arquitectura de render (`createMemoryRouter`).

**Non-Goals:**
- Conectar las 5 pantallas de coste a datos reales del backend (`RF-095-002`, fuera de alcance,
  dueño: la siguiente tarjeta de F3 que reconcilie la capa de datos).
- Corregir el CORS de JUP-085, el JSONB del historial de JUP-035 o la carrera de migraciones —
  hallazgos de backend/processor no tocados por esta tarjeta.
- Activar en vivo el octavo check de GitHub: se opta por consolidar a los 7 ya activos (ver Decisión
  4) en vez de pedir esa acción de administrador.

## Decisions

### 1. Fusionar `develop` en la rama de JUP-095 en vez de una rama de reconciliación aislada

La propuesta original sugería una rama nueva. Se optó por `git merge origin/develop` directamente
sobre `feat/JUP-095-portar-codigo-fuente`: un merge no es una reescritura de historial, la PR #36
existente se actualiza sola, y evita abrir una segunda PR para el mismo trabajo. Alternativa
descartada: rama de reconciliación aparte, con el coste de una PR nueva y de mantener dos ramas
vivas para el mismo cambio.

### 2. Frontera de remontaje por tenant acotada a `TenantScopedOutlet`, no al `Outlet` de `Layout`

Primera implementación: `key={activeTenant?.id}` directamente en el `<Outlet>` de `Layout`, afectando
a las 8 pantallas. Rompió 3 pruebas de login en vivo: `SessionGate` resuelve `activeTenant` en dos
renders durante el arranque (null mientras `activeTenantId` local vale `""`, luego el tenant
auto-seleccionado tras su efecto), y la key forzaba un remontaje espurio de la pantalla índice sin
que hubiera cambio real de tenant. Se corrigió introduciendo `TenantScopedOutlet` (`Layout.tsx`), un
segundo nivel de `Outlet` con la key, insertado en `routes.tsx` únicamente alrededor de `/ingest` y
`/assistant` — mismo alcance que `tenantPageKey` en el `App.jsx` original, que tampoco envolvía el
dashboard ni las pantallas de demostración. `DashboardPage` no necesita remontarse: no tiene estado
local editable, solo re-consulta con la `tenantId` nueva.

### 3. Validación de sesión (`isSession`) trasladada literal desde `develop`, no rediseñada

Se copia el validador de `develop/App.jsx` casi verbatim (comprobación de `accessToken` y de la forma
completa de `UserProfile` en `user`) en vez de diseñar una validación nueva, para no introducir un
criterio de aceptación distinto al ya probado en la rama de origen. Efecto colateral detectado: dos
fixtures de test ya commiteados (`SessionGate.test.tsx`, `routes.integration.test.tsx`) sembraban una
sesión con `user` incompleto (sin `id`/`role`) — dejaban de ser válidas bajo el nuevo criterio y se
completaron. La cobertura del caso nuevo (JSON válido, estructura inválida) se añadió en un fichero de
test nuevo (`SessionGate.validation.test.tsx`) en vez de ampliar los ya commiteados, por convención
del harness del proyecto (tests commiteados son inmutables salvo que su propio contenido se haya
vuelto incorrecto, como en el caso de los dos fixtures).

### 4. Consolidar a los 7 checks de CI ya activos, retirando el job duplicado de JUP-095

El auto-merge de `ci.yml` combinó sin conflicto textual el job `frontend-build` de `develop` (que ya
ejecuta lint+test) con el job `frontend-tests` de JUP-095 (que ejecuta test otra vez): la suite se
ejecutaría dos veces en cada CI run. Se eligió retirar el job duplicado y mantener los 7 checks que
`docs/governance/github-branch-protection.md` confirma activos en GitHub desde el 08/09/2026, en vez
de conservar el octavo y pedir su activación en vivo a un administrador — decisión de menor alcance,
ya contemplada como opción en la propuesta de reconciliación. Se actualizan ambos `.github/rulesets/
*.json` y `tools/ci-workflow.test.mjs` (test commiteado, editado tras confirmar que sus 8 aserciones
pasan a 7 y los 8 tests del archivo siguen en verde).

### 5. Arnés de test unificado sobre `createMemoryRouter`, navegación por ruta inicial en vez de clic

`develop` montaba `<App/>` (con `onLogin` por props) directamente; JUP-095 sustituyó `App` por
`<RouterProvider router={router}/>` sobre `createBrowserRouter`. Se adapta `test-support.tsx` para
montar la misma `routeConfig` sobre `createMemoryRouter` con `initialEntries` configurable — mismo
patrón que `routes.integration.test.tsx`, ya commiteado. Las suites heredadas que navegaban clicando
botones en inglés ("Ingestions", "Assistant") pasan a indicar la ruta inicial directamente, porque
esos enlaces no existían todavía en el `Layout` real (Punto 5, resuelto más tarde en la misma
tarjeta); una vez añadidos, las dos pruebas que ejercitan navegación real tras un fallo se reactivan
usando rol `link` (no `button`, los ítems de menú son `<NavLink>`) y las etiquetas reales.

### 6. Etiquetas de navegación en inglés para las tres pantallas nuevas del menú

Las 5 pantallas de demostración están en español (traducidas del origen Figma); `LoginPage`,
`IngestPage`, `ConversationsPage` y `DashboardPage` están en inglés (heredadas de `App.jsx`). Los tres
enlaces nuevos del menú ("Ingestions", "Assistant", "Overview") se etiquetan en inglés para ser
coherentes con el idioma de las pantallas a las que apuntan, no con el resto del menú — y se separan
visualmente con un divisor para distinguir pantallas con datos reales de las de demostración.

## Risks / Trade-offs

- [El bundle JS de producción pesa 765 KB minificado, por encima del umbral de 500 KB de Vite] →
  Preexistente a esta tarjeta (dependencias ya presentes: Radix, recharts). No se introduce
  code-splitting aquí; queda como mejora de rendimiento fuera de alcance.
- [Dos changes de OpenSpec bajo el mismo identificador JUP-095, sin precedente en el repo] → Se
  documenta explícitamente en proposal.md y en este archivo; el change original archivado no se
  reabre ni se modifica su registro de aprobación.
- [`allowJs: true` sigue en `tsconfig.json` sin ningún `.js`/`.jsx` restante en el árbol] →
  Deuda menor detectada durante la reconciliación, no introducida por ella; no se toca en esta
  tarjeta.

## ADR

ADR not applicable: las seis decisiones de este change son de alcance técnico dentro de patrones de
arquitectura ya aprobados (ADR-0003 TypeScript strict, ADR-0004 shadcn/ui). Ninguna introduce una
decisión de arquitectura duradera o transversal nueva que justifique un ADR propio.

## Open Questions

- ¿Quién asume RF-044-002 (carrera de migraciones backend/processor) ahora que Trello asigna JUP-096
  a una épica distinta? Anotado en `backlog.md` como pendiente de una tarjeta de migraciones, sin
  asignar número.
