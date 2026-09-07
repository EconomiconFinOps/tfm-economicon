# Evidencia de validacion JUP-094

- Fecha: 2026-09-07.
- Tarjeta: https://trello.com/c/Yqg2iZsj/86-jup-094-reconciliar-packagejson-del-frontend.
- Rama: `chore/JUP-094-reconcile-package-json`.
- Base: `origin/develop` en `283a1d8` (JUP-093, PR #27).
- Pull request: pendiente de abrir (se completa este enlace y el de CI tras el paso 7 del flujo).

## Alcance validado

- Fusionadas las 11 dependencias `MANTENER` del inventario de JUP-091 en
  `apps/frontend/package.json`: `react-router`, `recharts`, `lucide-react`, `tailwindcss` +
  `@tailwindcss/vite`, `tw-animate-css`, `clsx`, `tailwind-merge`, `class-variance-authority`.
- Adoptado un subconjunto de 6 paquetes Radix (`@radix-ui/react-label`, `-select`, `-slot`,
  `-separator`, `-dialog`, `-tooltip`), decisión revisada durante el `apply` y registrada en
  [ADR-0004](../adr/ADR-0004-frontend-shadcn-ui.md) (`Accepted`).
- Vite se mantiene en la serie 5 (`^5.3.3`): verificado que ninguna dependencia entrante fuerza el
  salto a 6.
- Cerrado `RF-091-002` en `openspec/findings/backlog.md`.
- Cero archivos de `apps/frontend/src/**` modificados o renombrados.

## Ciclo TDD

No aplica. El frontend no tiene test runner (`test` es un `echo`) y esta tarjeta no toca `tools/`,
así que no hay superficie unit-testeable — a diferencia de JUP-093, que sí la tenía en
`tools/ci-workflow.test.mjs`. Sin tester/coder/QA por tarea; verificación vía los comandos reales.
Mutación: N/A por el mismo motivo.

## Revisión de la decisión de shadcn/ui durante el `apply`

La decisión aprobada en el gate pre-código (descartar shadcn/ui) se revirtió el mismo día, antes de
instalar cualquier paquete Radix. Motivo final: facilidad de desarrollo para las pantallas que F3 va
a construir (login, tenant, ingesta, chat), no paridad con el origen — el inventario de JUP-091
confirma que el origen tampoco renderiza esos componentes. Detalle completo en `review.md`.

## Resultados

| Comprobación | Resultado |
| --- | --- |
| `pnpm install --frozen-lockfile` | Lockfile sin cambios |
| `pnpm --filter @finops/frontend lint` | 49 problemas `react/prop-types`, idéntico a la línea base (`RF-082-002`) |
| `pnpm --filter @finops/frontend build` | Superado, bundle idéntico (JS 203.37 kB / gzip 63.38 kB) |
| `pnpm --filter @finops/frontend typecheck` | Superado (2 proyectos) |
| `pnpm openspec:validate` | 22 elementos válidos (4 specs, 18 changes), 0 fallos |
| `pnpm jup:check -- --change jup-094-reconcile-package-json` | Enlazada con Trello y completa |
| `pnpm jup:cleanup:check` | 389 archivos aceptados |

**Sustitución documentada:** `pnpm lint`/`pnpm build` en la raíz (vía turbo) sustituidos por sus
equivalentes `--filter @finops/frontend`, por la misma limitación de entorno preexistente que
documenta `RF-093-001` (confirmada anterior a JUP-093, ajena a esta tarjeta).

**Incidencias con el resolutor de dependencias** (segunda vez, mismo patrón que JUP-093):
`react-router` resolvió a `8.3.1` (exige `react >=19.2.7`, incompatible con el runtime `^18.3.1`).
Corregido fijando `react-router@7.13.0`, `recharts@2.15.2` y `lucide-react@0.487.0` — versiones
exactas del origen. `tailwindcss` resolvió `^4.3.3` (minor sin incompatibilidad): se dejó tal cual.

## Pendiente

- Abrir el pull request hacia `develop` y completar este enlace y el de la ejecución de CI.
- Gate post-review (aprobación humana) y archivado del change OpenSpec.
- Tarjetas de F3 (`portar-codigo-fuente`, `reconciliar-capa-api`, `reconciliar-auth-tenant`,
  `unificar-estilos-assets`), citando ADR-0003 y ADR-0004 en su `design.md`.
- Copiar el código fuente de cada componente shadcn a `src/components/ui/`, componente por
  componente, cuando F3 lo necesite.
