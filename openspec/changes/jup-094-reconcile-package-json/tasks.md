## 1. Decisión sobre shadcn/ui (bloquea el resto)

- [ ] 1.1 Llevar al **gate pre-código** la decisión 1 del `design.md` (descartar shadcn/ui por ahora,
  conservando `clsx`/`tailwind-merge`/`class-variance-authority`) y registrar la resolución del
  equipo en el bloque `## Human Approval` del `proposal.md`.
- [ ] 1.2 **Solo si el equipo elige adoptar shadcn/ui:** redactar y aceptar el ADR correspondiente
  (`docs/adr/ADR-NNNN-<slug>.md` con `docs/templates/adr.md`, siguiente número libre tras ADR-0003)
  **antes** de instalar ningún paquete `@radix-ui/*`, y ajustar las tareas 2.x con el subconjunto
  acordado. Si se descarta, esta tarea se marca N/A con el motivo (decisión 2 del `design.md`).

## 2. Dependencias de ejecución

- [ ] 2.1 Registrar la línea base **antes** de instalar: contenido de `dependencies` y
  `devDependencies`, recuento de violaciones de `pnpm lint` (esperado: 49) y tamaño del bundle de
  `pnpm build` (esperado: ~203 kB de JS).
- [ ] 2.2 Instalar con `corepack pnpm --filter @finops/frontend add react-router recharts
  lucide-react clsx tailwind-merge class-variance-authority` (pnpm-only; **nunca** `npm i`).
- [ ] 2.3 Verificar que las versiones resueltas se corresponden con las que ejercita el origen
  (`react-router` 7.13.0, `recharts` 2.15.2, `lucide-react` 0.487.0) y **no** con un mayor
  incompatible que el resolutor haya traído por `latest` — precedente directo: JUP-093 recibió
  `typescript@7` y `@types/react@19` desalineados. Fijar versión explícita si hiciera falta.
- [ ] 2.4 Confirmar que `react`/`react-dom` siguen en `dependencies` con `^18.3.1` y que no ha
  aparecido ningún bloque `peerDependencies` heredado del origen.

## 3. Dependencias de build

- [ ] 3.1 Instalar con `corepack pnpm --filter @finops/frontend add -D tailwindcss @tailwindcss/vite
  tw-animate-css`.
- [ ] 3.2 Verificar que quedan en `devDependencies` y que la versión de `tailwindcss` es la serie 4
  que usa el origen (4.1.12), coherente con `@tailwindcss/vite`.
- [ ] 3.3 Confirmar que **no** se ha tocado `vite.config.ts`: Tailwind entra como dependencia pero no
  se cablea hasta F3 (`unificar-estilos-assets`). Es un Non-Goal explícito del `design.md`.

## 4. Decisión de Vite y limpieza de arrastres

- [ ] 4.1 Dejar registrada en `review.md` la comprobación que sostiene la decisión 3: los rangos
  declarados por `@tailwindcss/vite@4.1.12` (`vite ^5.2.0 || ^6 || ^7`) y por
  `@vitejs/plugin-react@4.7.0` (`^4.2.0 || ^5 || ^6 || ^7`) — ninguna dependencia entrante fuerza el
  salto a Vite 6.
- [ ] 4.2 Confirmar que `vite` sigue en `^5.3.3` y `@vitejs/plugin-react` en `^4.3.1`, y que **no**
  se ha añadido ningún bloque `pnpm.overrides` (el origen fija `6.3.5` declarando `^6.4.2`; no se
  copia).
- [ ] 4.3 Verificar que ninguna de las 48 dependencias `DESCARTAR` del inventario de JUP-091 ha
  entrado al manifiesto: 26 Radix (salvo lo que apruebe 1.2), 7 de apoyo shadcn, `react-hook-form`,
  `next-themes`, MUI/emotion (4) y las 9 sin ningún import.

## 5. Contrato del paquete y reproducibilidad

- [ ] 5.1 Verificar que el manifiesto conserva `@finops/frontend`, `"private": true`,
  `"type": "module"` y **los 7 scripts** (`dev`, `build`, `preview`, `lint`, `test`, `typecheck`,
  `docker:build`), con `dev` manteniendo literalmente `--host 0.0.0.0 --port 5173`.
- [ ] 5.2 Confirmar `pnpm-lock.yaml` actualizado y versionado, y que
  `corepack pnpm install --frozen-lockfile` pasa sin modificarlo.
- [ ] 5.3 Ejecutar `corepack pnpm --filter @finops/frontend typecheck`, `lint` y `build`: los tres en
  verde, con el lint reportando **exactamente** las 49 violaciones de la tarea 2.1 y el bundle sin
  crecimiento significativo (Tailwind aún no se cablea, nada nuevo se importa).

## 6. Cierre y verificación

- [ ] 6.1 Cerrar `RF-091-002` en `openspec/findings/backlog.md` con la decisión tomada y su motivo.
  Verificar que `RF-082-002` sigue `Open` y que `git diff --stat` sobre `apps/frontend/src/` está
  vacío.
- [ ] 6.2 Marcar en `docs/spikes/frontend-migration.md` la segunda tarjeta de F2 como completada,
  sustituyendo el placeholder `jup-0xx-reconciliar-package-json` por `jup-094-reconcile-package-json`,
  y dejar **F2 marcada como fase completa** en "Proximos pasos".
- [ ] 6.3 Ejecutar la batería: `corepack pnpm install --frozen-lockfile`,
  `corepack pnpm --filter @finops/frontend lint/build/typecheck` (sustitutos por `RF-093-001`),
  `corepack pnpm openspec:validate`,
  `corepack pnpm jup:check -- --change jup-094-reconcile-package-json` y
  `corepack pnpm jup:cleanup:check`.
- [ ] 6.4 Escribir `review.md`: resultado, decisiones tomadas (shadcn/ui y Vite) con su motivo,
  comparación antes/después del manifiesto y del bundle, aplicabilidad del ADR según la decisión 2, y
  la excepción de harness TDD que corresponda (esta tarjeta no tiene comportamiento unit-testeable:
  el frontend sigue sin test runner y no se toca `tools/`).
- [ ] 6.5 Crear `docs/evidence/JUP-094-validation.md` con los comandos exactos y sus resultados.
