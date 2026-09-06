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
