# Evidencia de validacion JUP-093

- Fecha: 2026-09-06.
- Tarjeta: https://trello.com/c/MNgMl60p/85-jup-093-configurar-typescript-en-apps-frontend.
- Rama: `chore/JUP-093-configure-typescript`.
- Base: `origin/develop` en `b6eaa87`.
- Pull request: pendiente de abrir (se completa este enlace y el de CI tras el paso 7 del flujo).

## Alcance validado

- Dependencias de TypeScript instaladas en `@finops/frontend` con pnpm (`typescript@5.9.3`,
  `@types/react@18.3.31`, `@types/react-dom@18.3.7`, `@types/node`, `typescript-eslint@8.69.0`).
- `apps/frontend/tsconfig.json` (proyecto `src`) y `tsconfig.node.json` (proyecto Vite), conforme a
  ADR-0003: `strict: true`, `allowJs: true`, `checkJs: false`, ubicados en `apps/frontend`.
- `vite.config.js` migrado a `.ts`; host/puerto del monorepo (`0.0.0.0:5173`) sin cambios.
- `eslint.config.js` con soporte TypeScript en un bloque nuevo, sin tocar el bloque `.jsx` existente.
- Séptimo check obligatorio de CI (`Frontend type check`), versionado en `ci.yml` y ambos rulesets.
- Cero archivos de `apps/frontend/src/**` modificados o renombrados.

## Ciclo TDD (grupo 5, unico con comportamiento unit-testeable)

El frontend no tiene test runner (`test` es un `echo`); la unica superficie testeable de esta
tarjeta es `tools/ci-workflow.test.mjs`, que valida la estructura de `ci.yml` y de los rulesets.

| Fase | Comando | Resultado |
| --- | --- | --- |
| Red (tester) | `corepack pnpm ci:check:test` | 2 tests fallan (`TypeError` + `AssertionError`, motivos correctos) |
| Green (coder) | `corepack pnpm ci:check:test` | 7/7 pass |
| QA | checklist independiente | `accept`, sin escalados |

Incidencia de proceso durante Red: el hook `lock-committed-tests.mjs` bloqueo la edicion directa del
test ya commiteado (por diseno, no distingue rol). Resuelto con bypass puntual autorizado por
Victor, verificado funcionalmente que el candado volvia a bloquear antes de continuar. Detalle
completo en `review.md`.

Mutacion: sin runner aplicable en ambos casos (grupos 1-4/6 sin comportamiento testeable; grupo 5
con artefacto YAML/JSON, no JS/TS mutable por Stryker/mutmut). QA verifico a mano dos mutantes
hipoteticos y confirmo que los tests los detectan igual.

## Resultados

| Comprobacion | Resultado |
| --- | --- |
| `pnpm install --frozen-lockfile` | Lockfile sin cambios |
| `pnpm --filter @finops/frontend lint` | 49 problemas `react/prop-types`, identico a la linea base (`RF-082-002`) |
| `pnpm --filter @finops/frontend build` | Superado |
| `pnpm --filter @finops/frontend typecheck` | Superado (2 proyectos: `src` y `tsconfig.node.json`) |
| `pnpm --filter @finops/frontend dev` | `HTTP 200` en `0.0.0.0:5173`, sin errores de tipo |
| `pnpm ci:check:test` | 7/7 superados |
| `pnpm openspec:validate` | 21 elementos validos (3 specs, 19 changes), 0 fallos |
| `pnpm jup:check -- --change jup-093-configure-typescript` | Enlazada con Trello y completa |
| `pnpm jup:cleanup:check` | 380 archivos aceptados |

**Sustitucion documentada:** `pnpm lint`/`pnpm build` en la raiz (via turbo) sustituidos por sus
equivalentes `--filter @finops/frontend`, por una limitacion de entorno preexistente en la maquina
de desarrollo (turbo resuelve una version de pnpm distinta a la fijada en subprocesos por paquete;
confirmado que ya ocurria antes de esta tarjeta, ver `RF-093-001` en
`openspec/findings/backlog.md`). No afecta a CI, que instala pnpm limpio en cada job.

## Limitaciones declaradas

1. El type-check pasa en verde sin verificar tipos reales todavia: con `checkJs: false` (ADR-0003,
   decision 2), TypeScript resuelve el JavaScript existente pero no lo tipa. Resultado esperado y
   aprobado en el gate pre-codigo; el valor llega con F3.
2. La septima check context esta versionada pero no es obligatoria en GitHub todavia: requiere que
   un administrador reaplique el ruleset, mismo paso pendiente que dejo JUP-079.

## Pendiente

- Abrir el pull request hacia `develop` y completar este enlace y el de la ejecucion de CI.
- Gate post-review (aprobacion humana) y archivado del change OpenSpec.
- Segunda tarjeta de F2 (`reconciliar-package-json`): fusion de dependencias del origen y decision
  sobre `RF-091-002` (shadcn/ui).
- Activacion en vivo de la nueva check context por un administrador del repositorio.

## Correcciones de revision del PR #27 — 2026-09-07

[PR #27](https://github.com/EconomiconFinOps/tfm-economicon/pull/27), ajustes sobre `629afb9`:

- `tsconfig.json` limita los tipos globales del navegador con `types: []`;
  `tsconfig.node.json` conserva `types: ["node"]` para Vite.
- Corregidos los ocho enlaces rotos por el archivado de JUP-093. Verificados los
  20 enlaces Markdown relativos de los cuatro documentos afectados: ninguno roto.
- Sin cambios en fuentes ni dependencias.

Validacion local con Node `24.14.1` y pnpm `9.0.0`:

| Comprobacion | Resultado |
| --- | --- |
| `corepack pnpm install --frozen-lockfile` | Superado, lockfile sin cambios |
| `corepack pnpm --filter @finops/frontend typecheck` | Superado, ambos proyectos |
| `corepack pnpm --filter @finops/frontend build` | Superado, 89 modulos |
| `corepack pnpm --filter @finops/frontend lint` | Salida 1: las mismas 49 violaciones `react/prop-types`, sin nuevas |
| `corepack pnpm ci:check:test` | 7/7 superados |
| `corepack pnpm openspec:validate` | 21/21 elementos validos |
| `corepack pnpm jup:cleanup:check` | 383 archivos aceptados |

Sondas temporales ejecutadas con el comando real `typecheck`: un componente TSX
con props tipadas y `const timer: number = setTimeout(() => {}, 100)` compilan;
`Buffer.from("demo")` en `src` se rechaza con TS2591. Las sondas se eliminaron
tras comprobar los resultados y no forman parte del cambio.
