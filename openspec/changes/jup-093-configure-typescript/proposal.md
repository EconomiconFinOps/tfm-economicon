JUP: JUP-093
Trello: https://trello.com/c/MNgMl60p/85-jup-093-configurar-typescript-en-apps-frontend

## Why

[ADR-0003](../../../docs/adr/ADR-0003-frontend-typescript.md) (`Accepted`, JUP-092) decidió adoptar
TypeScript en `apps/frontend` con `strict: true`, `allowJs: true` durante la migración, type-check
obligatorio en CI y `tsconfig` a nivel de `apps/frontend`. **La decisión está tomada pero no está
ejecutada**: hoy no existe ningún `tsconfig.json` en el repositorio, `apps/frontend` no declara
`typescript` ni `@types/react`, y el CI (`.github/workflows/ci.yml`) solo tiene un job
`frontend-build` — no hay type-check ni lint del frontend en ninguna parte.

Mientras esa decisión no se materialice en tooling, **F3 no puede empezar**: el spike prohíbe el "big
bang" y exige avanzar por slices verificables, pero el primer archivo `.tsx` que se porte del origen
no compilaría, no se lintearía y nadie lo verificaría. Esta tarjeta es la primera de **F2 (Tooling y
dependencias)** del [spike de migración](../../../docs/spikes/frontend-migration.md) y su función es
exactamente esa: dejar el tooling instalado, configurado y en verde **antes** de que llegue una sola
línea de código del origen.

El spike registra además un requisito explícito para las tarjetas de F2 y F3: enlazar ADR-0003 desde
su `design.md` al crearse. Esta propuesta lo cumple.

## What Changes

- **Dependencias.** Añadir `typescript`, `@types/react` y `@types/react-dom` (y los tipos que
  requiera el tooling actual) como `devDependencies` de `@finops/frontend`, instaladas con
  `pnpm --filter @finops/frontend add -D`. El repo es **pnpm-only**: nunca `npm i`.
- **Configuración del compilador.** Crear `apps/frontend/tsconfig.json` con `strict: true` y
  `allowJs: true` (ADR-0003, decisiones 1 y 2), ubicado a nivel de `apps/frontend` y **no** extraído a
  `packages/shared-config` (decisión 4). Añadir `tsconfig.node.json` solo si la configuración de Vite
  lo requiere.
- **Config de Vite.** Pasar `vite.config.js` a `.ts` si el tooling lo permite sin fricción,
  conservando `host: 0.0.0.0` y el puerto `5173` que exige el monorepo.
- **Lint.** Migrar `eslint.config.js` a flat config con parser y plugin de TypeScript, manteniendo
  las reglas `react` y `react-hooks` ya vigentes, ampliando el script `lint` a `ts,tsx` y desactivando
  `react/prop-types` **únicamente** para `.ts`/`.tsx`.
- **Verificación efectiva.** Añadir el script `typecheck` (`tsc --noEmit`) en `@finops/frontend` y
  cablearlo como job de CI. Sin esto, `strict: true` sería una anotación decorativa sin consecuencia
  — es lo que exige la decisión 3 de ADR-0003, que hoy no tiene ninguna tarjeta asignada en el spike.

**No se migra código.** Ningún `.jsx` se renombra a `.tsx`, no se porta nada del origen y no se
fusionan sus dependencias. Al terminar, `apps/frontend` sigue siendo el mismo JavaScript que hoy,
pero sobre una cadena de herramientas capaz de compilar, tipar y lintear TypeScript.

## Capabilities

### New Capabilities

- `frontend-typescript-tooling`: la cadena de herramientas de `apps/frontend` verifica tipos.
  Cubre que exista una configuración de compilador conforme a ADR-0003, que el type-check sea
  ejecutable localmente y obligatorio en CI, que el lint acepte TypeScript sin perder las reglas de
  React vigentes, y que la instalación siga siendo reproducible con el lockfile del workspace.
  Es comportamiento verificable de la plataforma de build, no de producto: se archiva con
  `--skip-specs` y no se promociona a `openspec/specs/`, siguiendo el precedente de JUP-092.

### Modified Capabilities

<!-- Ninguna. No cambia ningún requisito de comportamiento del producto: `apps/frontend` renderiza
     exactamente lo mismo antes y después. Cambia solo cómo se compila, tipa y lintea. -->

## Impact

- **Nuevo:** `apps/frontend/tsconfig.json` (y `tsconfig.node.json` si procede); job de type-check en
  `.github/workflows/ci.yml`.
- **Modificado:** `apps/frontend/package.json` (devDependencies + scripts `lint` y `typecheck`),
  `apps/frontend/eslint.config.js`, `apps/frontend/vite.config.js` → `.ts`, `pnpm-lock.yaml` (raíz).
- **Solo lectura:** `apps/frontend/src/**` — no se toca ningún archivo fuente.
- **Dependencias nuevas:** solo de desarrollo (`typescript`, tipos de React, parser/plugin ESLint de
  TypeScript). Ninguna dependencia de runtime.
- **Findings.**
  - `RF-082-002` **permanece `Open`**. Las 49 violaciones de `react/prop-types` viven en 9 archivos
    `.jsx` que esta tarjeta no renombra ni migra, así que la regla les sigue aplicando y `pnpm lint`
    seguirá reportando las mismas 49 después de F2. Lo cierra F3/F5, no esta tarjeta — así lo corrigió
    la revisión de PR de JUP-092 en ADR-0003.
  - `RF-091-002` (adoptar o descartar shadcn/ui) **no se decide aquí**: corresponde a la otra tarjeta
    de F2, `reconciliar-package-json`.
- **Gobernanza:** marcar el type-check como check obligatorio en la protección de rama afecta a
  [docs/governance/github-branch-protection.md](../../../docs/governance/github-branch-protection.md)
  (territorio de JUP-079). El `design.md` decide si esa activación entra en el alcance o queda
  registrada como seguimiento.
- **Desbloquea:** la segunda tarjeta de F2 (`reconciliar-package-json`) y toda F3, que ya podrán
  portar `.tsx` con verificación real.
- **Aún no:** `allowJs` pasa a `false` en el cierre de F5, no aquí.

## Human Approval

- Change: jup-093-configure-typescript
- Approval type: pre-code
- Decision: approved
- Approver: Victor
- Date: 2026-09-06
- Carril: standard
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Decisions approved: se aprueban las seis decisiones del `design.md`. (1) **Dos configuraciones de compilador**: `tsconfig.json` para `src/**` con destino navegador y `tsconfig.node.json` para `vite.config.ts` con destino Node, ambas en `apps/frontend/` (ADR-0003, decisión 4); se descarta el layout de tres archivos con `references` de la plantilla `react-ts` de Vite por ceremonia excesiva para 14 archivos. (2) **`allowJs: true` con `checkJs: false`**, que es la lectura precisa de la decisión 2 del ADR: TypeScript resuelve los `.js`/`.jsx` aún sin migrar pero no los verifica, porque con `checkJs: true` el type-check fallaría en el primer commit y F2 se convertiría de facto en F3 — el "big bang" que el spike prohíbe. (3) **`vite.config.js` → `.ts`**, por coherencia y porque el origen ya llega con su config en TS; el host `0.0.0.0` y el puerto `5173` no se tocan porque viven en los flags del script `dev`, no en ese archivo. (4) **ESLint con `typescript-eslint` en modo no type-aware** sobre un bloque nuevo `src/**/*.{ts,tsx}`, dejando intacto el bloque `{js,jsx}`, y moviendo la selección de extensiones del flag `--ext` a los globs de la flat config; `react/prop-types` se desactiva únicamente en el bloque TS. (5) **Check context propia `Frontend type check`**, job separado en lugar de un paso dentro de `Frontend build`, versionada de forma coherente en los cuatro sitios (workflow, `develop.json`, `main.json`, documento de gobernanza) pero **no activada en vivo**: la reaplicación del ruleset queda como paso de administrador, siguiendo el patrón de JUP-079. (6) **Orden de ejecución**: dependencias y `tsconfig` primero, CI después, rulesets al final.
- Main risks: el riesgo principal es de **eficacia, no de ejecución**: con `checkJs: false` el type-check pasará en verde sin verificar nada de sustancia mientras no exista ningún `.ts`/`.tsx`, así que esta tarjeta instala una red que no atrapa nada hasta F3. Se acepta conscientemente —el valor es que la red esté puesta y sea obligatoria *antes* de que llegue el código, no que encuentre errores hoy— y se declara como limitación explícita en `review.md`, no se presenta como verificación efectiva. Riesgo secundario: `typescript-eslint` puede alterar la línea base de lint al convivir con `eslint-plugin-react`; mitigado con un criterio medible y binario —`pnpm lint` debe reportar **exactamente 49** violaciones, ni una más ni una menos— y con la prohibición explícita de silenciar reglas para cuadrar el número. Riesgo terciario: tocar `.github/rulesets/*.json` entra en territorio de JUP-079 y puede generar deriva entre el ruleset versionado y el vivo; mitigado manteniendo los cuatro sitios coherentes en el mismo commit y dejando la activación como paso de administrador documentado. No hay riesgo de auto-bloqueo del PR, porque el workflow de la rama publica la context y el ruleset solo la exige cuando alguien lo reaplica. La conversión de `vite.config` es la parte más prescindible del alcance y tiene revert previsto sin bloquear nada más.
- Required changes before execution: none
- Notes: primera tarjeta de **F2 (Tooling y dependencias)** y primera que ejecuta —no decide— ADR-0003; el `design.md` lo enlaza, cumpliendo el requisito que el spike fija en su línea 170 para todas las tarjetas de F2 y F3. Reemplaza el placeholder `jup-0xx-configurar-typescript` del spike. Alcance ampliado respecto a las cuatro viñetas del spike con una quinta derivada de la decisión 3 de ADR-0003 —script `typecheck` y job de CI—, que hoy no tenía ninguna tarjeta asignada y sin la cual `strict: true` sería decorativo. **No es doc-only**: sí lleva `docs/evidence/JUP-093-validation.md`, y el harness TDD aplica con un ciclo Red/Green real sobre `tools/ci-workflow.test.mjs`, que hoy asevera seis check contexts y pasará a siete — la única superficie testeable de la tarjeta, dado que `apps/frontend` no tiene runner de tests (su script `test` es un `echo`). Quedan explícitamente fuera: migrar cualquier `.jsx` a `.tsx` o portar código del origen (F3), fusionar las dependencias del origen y decidir `RF-091-002`/shadcn/ui (tarjeta `reconciliar-package-json` de F2), decidir Vite 5 vs 6 (misma tarjeta), introducir runner de tests en el frontend (tarjeta propia), y endurecer `allowJs` a `false` (cierre de F5). **`RF-082-002` permanece `Open` por diseño**: las 49 violaciones de `react/prop-types` viven en 9 archivos `.jsx` que esta tarjeta no renombra, así que la regla les sigue aplicando y `pnpm lint` reportará las mismas 49 después de F2; lo cierra F3/F5, tal como corrigió la revisión de PR de JUP-092 en ADR-0003.
