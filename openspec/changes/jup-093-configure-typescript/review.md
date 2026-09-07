# Review: jup-093-configure-typescript

## Result

Accepted (pendiente del gate post-review de Victor antes de archivar).

## Scope Reviewed

- `apps/frontend/package.json` — devDependencies de TypeScript, scripts `typecheck` y `lint`.
- `apps/frontend/tsconfig.json`, `apps/frontend/tsconfig.node.json` (nuevos).
- `apps/frontend/vite.config.ts` (renombrado desde `.js`, contenido idéntico).
- `apps/frontend/eslint.config.js` — bloque nuevo `src/**/*.{ts,tsx}`.
- `package.json` (raíz) y `turbo.json` — script/entrada `typecheck` (añadido no listado
  originalmente en `tasks.md`, necesario para que `check-dod.mjs` deje de omitir el gate de tipos).
- `pnpm-lock.yaml` (raíz) — actualizado por la instalación de dependencias.
- `.github/workflows/ci.yml` — job nuevo `frontend-typecheck` (`Frontend type check`).
- `.github/rulesets/develop.json`, `.github/rulesets/main.json` — séptima context.
- `tools/ci-workflow.test.mjs` — dos tests ampliados de 6 a 7 contexts (Red/Green, ver abajo).
- `docs/governance/github-branch-protection.md` — lista de checks obligatorios actualizada.
- `docs/spikes/frontend-migration.md` — tarjeta de F2 marcada completa, placeholder sustituido.
- `openspec/findings/backlog.md` — `RF-082-002` verificado sin cambios (sigue `Open`, correcto);
  `RF-093-001` nuevo (limitación de entorno, ver "Review Findings").
- `apps/frontend/src/**` — en **solo lectura**: cero archivos tocados, verificado con `git diff --stat`.

## Checklist

- [x] Los 5 requisitos de `specs/frontend-typescript-tooling/spec.md` se cumplen de forma observable
  (compilador conforme a ADR-0003, type-check ejecutable y obligatorio en CI, lint TS sin perder
  React, instalación reproducible, dev/build sin regresión).
- [x] `strict: true` y `allowJs: true`/`checkJs: false` implementados exactamente como aprobó el gate
  pre-código (ADR-0003, decisiones 1 y 2); `tsconfig` a nivel de `apps/frontend`, no compartido
  (decisión 4).
- [x] Type-check obligatorio en CI (decisión 3): job `frontend-typecheck` + séptima context
  versionada en los 4 sitios de gobernanza.
- [x] `RF-082-002` permanece `Open`: verificado que ningún `.jsx` fue renombrado ni migrado.
- [x] TDD aplicado donde había comportamiento unit-testeable (grupo 5, único con red real): Red
  (tester) → Green (coder) → QA (`accept`) sobre `tools/ci-workflow.test.mjs`.
- [x] Grupos 1-4 y 6 (tooling/config sin test runner en el frontend — ver `design.md`, Non-Goals):
  sin tester/coder/QA por tarea, mismo criterio que JUP-092; verificación vía los comandos reales
  (`typecheck`, `lint`, `build`, `dev`, `install --frozen-lockfile`).
- [x] Mutación: N/A en todos los grupos, con dos justificaciones distintas (ver "Mutación" abajo).
- [x] `tasks.md` marcado 24/24.
- [x] ADR-0003 enlazado desde `proposal.md`, `design.md` y ahora desde el spike (tarjeta F2).
- [x] Checks de la batería completa en verde (con sustitución documentada, ver "Validation").
- [x] Ningún archivo de `.claude/` colado en el commit (`jup:cleanup:check`).

ADR aplicable: no se produce uno nuevo — esta tarjeta **ejecuta** ADR-0003 (JUP-092), no toma
decisiones de arquitectura nuevas.

## TDD — Red/Green (grupo 5, tarea 5.1-5.5)

Único grupo con comportamiento unit-testeable (el frontend no tiene test runner; ver `design.md`,
Non-Goals). Ciclo completo sobre `tools/ci-workflow.test.mjs`:

**Red** (tester) — `corepack pnpm ci:check:test`:
```
✖ keeps the seven branch-protection check contexts stable
  TypeError: Cannot read properties of undefined (reading 'name')
✖ requires the same seven stable CI checks in both branch rulesets
  AssertionError: actual (6 elementos) no coincide con expected (7 elementos)
```

**Green** (coder) — mismo comando, tras añadir el job `frontend-typecheck` a `ci.yml` y la context a
ambos rulesets:
```
✔ 7 tests, 7 pass, 0 fail
```

**Incidencia de proceso durante Red:** `.claude/hooks/lock-committed-tests.mjs` bloqueó al tester al
intentar editar `tools/ci-workflow.test.mjs` (ya commiteado desde JUP-081) — por diseño, sin
distinguir el rol que llama ("los tests commiteados son inmutables"). La alternativa que el propio
hook sugiere (archivo de test nuevo) no servía: la tarea exige que un `deepEqual` existente pase de
6 a 7 elementos exactos, y un archivo nuevo no puede invalidar esa aserción vieja, que además corre
dentro del job `OpenSpec` de CI — dejarla como estaba habría roto esa misma PR en cuanto los
rulesets llegaran a 7 contexts. Resuelto con Victor: bypass puntual del hook (mover
`.claude/settings.json` fuera, aplicar el diff ya preparado para el tester, restaurar el archivo, y
**confirmar funcionalmente** que el candado volvía a bloquear antes de continuar). El archivo
duplicado que el tester había creado como cobertura alternativa se eliminó por quedar redundante.

**QA** (grupo 5): veredicto `accept`. Verificó independientemente (no solo el reporte del coder):
comandos re-ejecutados, consistencia de los 4 sitios de gobernanza, que el coder no tocó el test, y
—el punto que más se le pidió auditar— la solidez de la excepción de mutación (ver abajo). Sin
escalados a tester ni coder.

## Mutación

Dos justificaciones distintas, no una sola "doc-only" genérica:

- **Grupos 1-4 y 6** (tsconfig, package.json, eslint.config.js, vite.config.ts, docs): sin
  comportamiento unit-testeable y sin test runner en el frontend — mismo criterio que JUP-092.
- **Grupo 5** (`ci.yml` + rulesets): **sí** tiene comportamiento testeable (el propio ciclo Red/Green
  lo demuestra), pero el artefacto bajo test es configuración YAML/JSON parseada, no código JS/TS.
  Ningún runner disponible en el repo (Stryker para JS/TS, mutmut para Python — ver
  `.claude/harness/mutation.md`) muta claves de un mapa YAML/JSON. QA verificó a mano los dos
  mutantes hipotéticos más plausibles (borrar el job dejando la entrada en el ruleset; typo en el
  nombre del job/context) y confirmó que los tests actuales los detectan igualmente pese a la
  ausencia de mutación automatizada.

## Validation

Batería completa (tarea 6.3), 7 controles, todos en verde:

```txt
corepack pnpm install --frozen-lockfile -> PASS (lockfile sin cambios)
corepack pnpm --filter @finops/frontend lint -> PASS: 49 problems (49 errors), identico a la linea base (RF-082-002)
corepack pnpm --filter @finops/frontend build -> PASS
corepack pnpm --filter @finops/frontend typecheck -> PASS (ambos proyectos: src y tsconfig.node.json)
corepack pnpm ci:check:test -> PASS: 7/7
corepack pnpm openspec:validate -> PASS: 21 items (3 specs, 19 changes)
corepack pnpm jup:check -- --change jup-093-configure-typescript -> PASS: enlazado con Trello y completo
corepack pnpm jup:cleanup:check -> PASS: 380 archivos sin agentes personales, binarios ni tareas paralelas
```

**Sustitución documentada** (acordada con Victor, tarea 2.3): `corepack pnpm lint`/`build` en la raíz
(vía turbo) sustituidos por sus equivalentes `--filter @finops/frontend`. Motivo: limitación de
entorno preexistente en esta máquina (`RF-093-001`), confirmada anterior a esta tarjeta —
`pnpm lint`/`pnpm build` en la raíz ya fallaban igual sobre paquetes no tocados aquí
(`@finops/backend`, `@finops/processor`).

Verificación adicional por tarea, no repetida en la batería:
- `pnpm --filter @finops/frontend dev` arranca en `0.0.0.0:5173` (`HTTP 200` confirmado, proceso
  detenido tras la comprobación).
- El bloque TypeScript de `eslint.config.js` se probó con un `.tsx` desechable (creado, ejecutado
  con `eslint src/__eslint_probe.tsx`, borrado antes de commitear, sin rastro en `git status`):
  confirma `@typescript-eslint/no-unused-vars` activo y `react/prop-types` inactivo en `.tsx`.
- Verificado empíricamente que `vite-env.d.ts` no hace falta todavía (`tsc --noEmit` pasa limpio con
  `checkJs: false` pese a que `api.js`/`main.jsx` ya usan `import.meta.env`/CSS) — se deja para F3.

## Limitaciones declaradas

1. **El type-check pasa en verde sin verificar nada de sustancia todavía.** Con `checkJs: false`
   (ADR-0003, decisión 2), TypeScript resuelve los 14 archivos `.js`/`.jsx` actuales pero no los
   tipa. Es el resultado esperado y aprobado en el gate pre-código: el valor de esta tarjeta es que
   la red esté puesta y sea obligatoria *antes* de que llegue el código de F3, no que encuentre
   errores hoy.
2. **La context `Frontend type check` no es obligatoria en vivo todavía.** Está versionada en
   `ci.yml` y en ambos `.github/rulesets/*.json`, pero aplicarla al ruleset real de GitHub requiere
   que un administrador lo reaplique — mismo paso pendiente que dejó JUP-079 documentado en
   "Administrator activation checklist".

## Review Findings

- **`RF-093-001` (nuevo, `Open`, Low, fuera de scope):** en esta máquina, `corepack pnpm <script>`
  en la raíz falla para cualquier script orquestado por turbo — no solo `typecheck`, también
  `lint`/`build`/`test`, confirmado preexistente a esta tarjeta. Registrado en
  `openspec/findings/backlog.md` para que el equipo confirme si es local a esta máquina o más
  extendido; no bloquea esta tarjeta porque `--filter @finops/frontend` funciona correctamente y es
  lo que ya especificaban `tasks.md`/`design.md` como comando de verificación.
- Ninguno nuevo sobre `RF-082-002`, `RF-091-002` ni el resto de findings heredados de F1: esta
  tarjeta no cambia su estado, solo lo confirma.

## Risks / Follow-Ups

- **El coste real de `strict: true` sigue siendo desconocido** hasta que F3 porte el primer archivo
  real — riesgo ya reconocido en ADR-0003 y en el gate pre-código de esta tarjeta, no resuelto ni
  agravado aquí.
- **`vite-env.d.ts` es trabajo pendiente de F3**, no de esta tarjeta: en cuanto el primer `.tsx` use
  `import.meta.env` o importe un asset no-JS, hará falta añadirlo.
- **La segunda tarjeta de F2 (`reconciliar-package-json`) sigue pendiente**: decide `RF-091-002`
  (shadcn/ui) y fusiona las dependencias del origen, ninguna de las cuales entra en esta tarjeta.
- **Activación en vivo de la nueva check context** (limitación 2 de arriba): acción de administrador
  fuera del alcance de esta tarjeta, igual que dejó JUP-079.
