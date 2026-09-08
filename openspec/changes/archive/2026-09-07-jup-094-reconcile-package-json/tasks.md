## 1. Decisión sobre shadcn/ui (bloquea el resto)

- [x] 1.1 Llevar al **gate pre-código** la decisión 1 del `design.md` y registrar la resolución del
  equipo en el bloque `## Human Approval` del `proposal.md`. Hecho: aprobado por Victor el
  2026-09-07 (commit `d0da663`), descartando shadcn/ui. **Revisado durante el `apply`, mismo día**:
  el equipo cambió a adoptar un subconjunto de 6 paquetes Radix, por facilidad de desarrollo y
  consistencia visual sin reescribir primitivos accesibles a mano (no por paridad con el origen, que
  tampoco los usa). Ver adenda en el `## Human Approval` de `proposal.md` y `design.md`, decisión 1.
- [x] 1.2 Redactar y aceptar [ADR-0004](../../../docs/adr/ADR-0004-frontend-shadcn-ui.md)
  (adopción de shadcn/ui, subconjunto de 6 paquetes Radix) **antes** de instalar ningún paquete
  `@radix-ui/*`. Aceptado por Victor el 2026-09-07, en commit separado del de redacción (mismo
  patrón de dos commits que ADR-0003).

## 2. Dependencias de ejecución

- [x] 2.1 Registrar la línea base **antes** de instalar: contenido de `dependencies` y
  `devDependencies`, recuento de violaciones de `pnpm lint` (esperado: 49) y tamaño del bundle de
  `pnpm build` (esperado: ~203 kB de JS). **Confirmado: 49 problems (49 errors), JS 203.37 kB / gzip
  63.38 kB, CSS 5.60 kB.**
- [x] 2.2 Instalar con `corepack pnpm --filter @finops/frontend add react-router recharts
  lucide-react clsx tailwind-merge class-variance-authority` (pnpm-only; **nunca** `npm i`).
- [x] 2.3 Verificar que las versiones resueltas se corresponden con las que ejercita el origen
  (`react-router` 7.13.0, `recharts` 2.15.2, `lucide-react` 0.487.0) y **no** con un mayor
  incompatible que el resolutor haya traído por `latest` — precedente directo: JUP-093 recibió
  `typescript@7` y `@types/react@19` desalineados. Fijar versión explícita si hiciera falta.
  **Ocurrió de nuevo: el resolutor trajo `react-router@8.3.1` (exige `react >=19.2.7`, incompatible
  con el runtime `^18.3.1`; `pnpm` avisó `unmet peer`). Re-instalado fijando `react-router@7.13.0`,
  `recharts@2.15.2` y `lucide-react@0.487.0` explícitos — las tres versiones exactas del origen.**
  `clsx`/`tailwind-merge`/`class-variance-authority` no tienen versión de origen documentada (el
  inventario solo las agrupa) ni generaron aviso de peer dependency: se dejan en lo que resolvió el
  instalador (`clsx@2.1.1`, `tailwind-merge@3.6.0`, `class-variance-authority@0.7.1`).
- [x] 2.4 Confirmar que `react`/`react-dom` siguen en `dependencies` con `^18.3.1` y que no ha
  aparecido ningún bloque `peerDependencies` heredado del origen. Confirmado.
- [x] 2.5 Tras aceptar ADR-0004, instalar con `corepack pnpm --filter @finops/frontend add
  @radix-ui/react-label @radix-ui/react-select @radix-ui/react-slot @radix-ui/react-separator
  @radix-ui/react-dialog @radix-ui/react-tooltip`.
- [x] 2.6 Verificar que las 6 dependencias Radix quedan en `dependencies` (no `devDependencies`) y
  que ninguna trae un peer de React incompatible con `^18.3.1`. Confirmado: las 6 en `dependencies`,
  sin ningún aviso de peer dependency nuevo (solo persiste el de `eslint-plugin-react-hooks`,
  preexistente y ajeno a esta tarjeta). `typecheck`, `build` (bundle idéntico, 203.37 kB) e
  `install --frozen-lockfile` en verde.

## 3. Dependencias de build

- [x] 3.1 Instalar con `corepack pnpm --filter @finops/frontend add -D tailwindcss @tailwindcss/vite
  tw-animate-css`.
- [x] 3.2 Verificar que quedan en `devDependencies` y que la versión de `tailwindcss` es la serie 4
  que usa el origen (4.1.12), coherente con `@tailwindcss/vite`. Resolvió `^4.3.3` (minor dentro de
  la misma serie 4, no un mayor incompatible): se deja tal cual, coherente con la regla de la
  decisión 5 de `design.md` (fijar solo ante un **mayor** incompatible).
- [x] 3.3 Confirmar que **no** se ha tocado `vite.config.ts`: Tailwind entra como dependencia pero no
  se cablea hasta F3 (`unificar-estilos-assets`). Es un Non-Goal explícito del `design.md`.
  Confirmado: `git diff --stat` sobre el archivo, vacío.

## 4. Decisión de Vite y limpieza de arrastres

- [x] 4.1 Dejar registrada en `review.md` la comprobación que sostiene la decisión 3: los rangos
  declarados por `@tailwindcss/vite@4.1.12` (`vite ^5.2.0 || ^6 || ^7`) y por
  `@vitejs/plugin-react@4.7.0` (`^4.2.0 || ^5 || ^6 || ^7`) — ninguna dependencia entrante fuerza el
  salto a Vite 6. Ya registrada en `design.md` (sección Context); se traslada a `review.md` en 6.4.
- [x] 4.2 Confirmar que `vite` sigue en `^5.3.3` y `@vitejs/plugin-react` en `^4.3.1`, y que **no**
  se ha añadido ningún bloque `pnpm.overrides` (el origen fija `6.3.5` declarando `^6.4.2`; no se
  copia). Confirmado: ambos sin cambio, sin `overrides` en ningún `package.json`/`pnpm-workspace.yaml`
  del repo.
- [x] 4.3 Verificar que ninguna de las 48 dependencias `DESCARTAR` del inventario de JUP-091 ha
  entrado al manifiesto **salvo el subconjunto de 6 Radix que autoriza ADR-0004**: de los 26
  primitivos del origen, los otros 20 siguen fuera; también fuera los 7 paquetes de apoyo a shadcn
  distintos de los propios primitivos, `react-hook-form`, `next-themes`, MUI/emotion (4) y las 9 sin
  ningún import. Confirmado listando `dependencies`/`devDependencies` completos: exactamente los 15
  `MANTENER`/ADR-0004 esperados, ni uno más.

## 5. Contrato del paquete y reproducibilidad

- [x] 5.1 Verificar que el manifiesto conserva `@finops/frontend`, `"private": true`,
  `"type": "module"` y **los 7 scripts** (`dev`, `build`, `preview`, `lint`, `test`, `typecheck`,
  `docker:build`), con `dev` manteniendo literalmente `--host 0.0.0.0 --port 5173`. Confirmado.
- [x] 5.2 Confirmar `pnpm-lock.yaml` actualizado y versionado, y que
  `corepack pnpm install --frozen-lockfile` pasa sin modificarlo. Confirmado.
- [x] 5.3 Ejecutar `corepack pnpm --filter @finops/frontend typecheck`, `lint` y `build`: los tres en
  verde, con el lint reportando **exactamente** las 49 violaciones de la tarea 2.1 y el bundle sin
  crecimiento significativo (Tailwind aún no se cablea, nada nuevo se importa). Confirmado: 49/49,
  bundle idéntico (203.37 kB / gzip 63.38 kB).

## 6. Cierre y verificación

- [x] 6.1 Cerrar `RF-091-002` en `openspec/findings/backlog.md` con la decisión tomada y su motivo.
  Verificar que `RF-082-002` sigue `Open` y que `git diff --stat` sobre `apps/frontend/src/` está
  vacío. Confirmado: `RF-091-002` → `Fixed`; `RF-082-002` sin cambios; diff de `src/` vacío.
- [x] 6.2 Marcar en `docs/spikes/frontend-migration.md` la segunda tarjeta de F2 como completada,
  sustituyendo el placeholder `jup-0xx-reconciliar-package-json` por `jup-094-reconcile-package-json`,
  y dejar **F2 marcada como fase completa** en "Proximos pasos".
- [x] 6.3 Ejecutar la batería: `corepack pnpm install --frozen-lockfile`,
  `corepack pnpm --filter @finops/frontend lint/build/typecheck` (sustitutos por `RF-093-001`),
  `corepack pnpm openspec:validate`,
  `corepack pnpm jup:check -- --change jup-094-reconcile-package-json` y
  `corepack pnpm jup:cleanup:check`. Los 7 controles en verde.
- [x] 6.4 Escribir `review.md`: resultado, decisiones tomadas (shadcn/ui y Vite) con su motivo,
  incluida la revisión de la decisión de shadcn/ui durante el `apply` y el ADR-0004 resultante
  (`Proposed` → `Accepted`), comparación antes/después del manifiesto y del bundle, y la excepción de
  harness TDD que corresponda (esta tarjeta no tiene comportamiento unit-testeable: el frontend sigue
  sin test runner y no se toca `tools/`).
- [x] 6.5 Crear `docs/evidence/JUP-094-validation.md` con los comandos exactos y sus resultados.
