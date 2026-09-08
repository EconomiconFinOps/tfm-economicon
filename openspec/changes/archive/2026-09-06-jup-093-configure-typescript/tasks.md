## 1. Dependencias de TypeScript

- [x] 1.1 Instalar desde la raíz con
  `corepack pnpm --filter @finops/frontend add -D typescript @types/react @types/react-dom @types/node typescript-eslint`
  (pnpm-only; **nunca** `npm i`). Fijar versiones estables compatibles con `eslint ^9.5`.
  **Ajuste tras instalar:** el resolutor tomó `typescript@^7.0.2` (dist-tag `latest`) y
  `@types/react@^19.2.18`/`@types/react-dom@^19.2.7`, incompatibles entre sí:
  `typescript-eslint@8.69.0` exige `typescript` `>=4.8.4 <6.1.0`, y el runtime del paquete sigue en
  `react@^18.3.1`, no 19. Se fijó explícitamente `typescript@5.9.3` (última 5.x, dentro del rango
  soportado) y `@types/react@18.3.31`/`@types/react-dom@18.3.7` (alineados con el runtime). Sin este
  ajuste, el type-check habría verificado contra una API de React que el proyecto no usa.
- [x] 1.2 Verificar que todo lo añadido queda en `devDependencies` y que las `dependencies` de
  runtime de `@finops/frontend` son idénticas a las de antes del cambio.
- [x] 1.3 Confirmar que `pnpm-lock.yaml` (raíz) queda actualizado y versionado, y que
  `corepack pnpm install --frozen-lockfile` pasa sin modificarlo.

## 2. Configuración del compilador

- [x] 2.1 Crear `apps/frontend/tsconfig.json` con `strict: true`, `allowJs: true`,
  **`checkJs: false`**, `noEmit: true`, `jsx: react-jsx`, `moduleResolution: Bundler` y `lib` de
  navegador, con `include` sobre `src`. Ubicado en `apps/frontend/`, **no** en
  `packages/shared-config` (ADR-0003, decisión 4). Verificado empíricamente que `vite-env.d.ts` no
  hace falta todavía: con `checkJs: false` y sin ningún `.ts`/`.tsx` real aún, `tsc --noEmit` pasa
  limpio pese a que `api.js` usa `import.meta.env` y `main.jsx` importa `./styles/main.css` — F3 lo
  añadirá cuando el primer archivo tipado lo necesite de verdad.
- [x] 2.2 Crear `apps/frontend/tsconfig.node.json` para `vite.config.ts` con destino Node y
  `@types/node`. **Orden resuelto:** su `include` apunta a `vite.config.ts`, que no existe hasta la
  tarea 3.1; el archivo se crea ya (inerte) pero **no** se encadena en el script `typecheck` hasta
  que 3.1 renombre `vite.config.js`, tal como prevé el propio texto de 2.3 ("cubriendo ambos
  proyectos si existen los dos").
- [x] 2.3 Añadir el script `typecheck` a `apps/frontend/package.json` (`tsc --noEmit`; el segundo
  proyecto se encadena en 3.1) y comprobar que `corepack pnpm --filter @finops/frontend typecheck`
  termina en verde sobre los 14 archivos `.js`/`.jsx` actuales, sin renombrar ni excluir ninguno.
  **Añadido no listado originalmente:** también se agregó `"typecheck": "turbo run typecheck"` al
  `package.json` raíz y la entrada `typecheck` a `turbo.json`, para que `check-dod.mjs` deje de
  omitir el gate de tipos (hoy solo lo ejecuta si existe ese script en la raíz). **Limitación de
  entorno descubierta (preexistente, no introducida aquí):** en esta máquina, `corepack pnpm
  typecheck`/`lint`/`test` en la raíz fallan porque turbo resuelve pnpm v11.9.0 en los subprocesos
  por paquete, pese a que `packageManager: pnpm@9.0.0` resuelve correctamente en shell interactiva
  (`corepack pnpm --version` y `pnpm --version` dan 9.0.0). Confirmado que ya ocurría antes de esta
  tarjeta: `pnpm lint` y `pnpm build` (raíz) fallan igual sobre `@finops/backend`/`@finops/processor`,
  paquetes no tocados. Decisión (con Victor): usar `corepack pnpm --filter @finops/frontend
  typecheck/lint/build` como verificación sustituta durante todo este change; ver limitación
  documentada en `review.md`.

## 3. Configuración de Vite

- [x] 3.1 Convertir `apps/frontend/vite.config.js` en `vite.config.ts` conservando el contenido
  (`defineConfig({ plugins: [react()] })`). Coste trivial: `git mv` + contenido sin cambios, TS lo
  acepta tal cual. Se aprovecha para encadenar el segundo proyecto en el script `typecheck`
  (`tsc --noEmit && tsc -p tsconfig.node.json --noEmit`), pendiente desde la tarea 2.2/2.3 porque
  `tsconfig.node.json` no tenía aún su archivo objetivo.
- [x] 3.2 Verificar que el script `dev` conserva literalmente `--host 0.0.0.0 --port 5173` y que
  `corepack pnpm --filter @finops/frontend dev` arranca sin errores de compilación ni de tipos.
  Verificado arrancando el proceso, confirmando `HTTP 200` en `http://localhost:5173/` y deteniéndolo.
- [x] 3.3 Verificar que `corepack pnpm --filter @finops/frontend build` sigue pasando.

## 4. Lint con soporte TypeScript

- [x] 4.1 Registrar la línea base **antes** de tocar nada: ejecutar `corepack pnpm lint` y anotar el
  recuento exacto de violaciones de `react/prop-types` (esperado: 49, finding `RF-082-002`).
  **Confirmado: 49 problems (49 errors, 0 warnings)**, todas `react/prop-types`, en los 9 `.jsx` ya
  identificados por el finding.
- [x] 4.2 Migrar `apps/frontend/eslint.config.js` añadiendo `typescript-eslint` en modo **no
  type-aware** sobre un bloque nuevo `files: ["src/**/*.{ts,tsx}"]`, dejando **intacto** el bloque
  `src/**/*.{js,jsx}` y sus reglas de `react`/`react-hooks`. Las reglas de `tseslint.configs.recommended`
  se fusionan con `Object.assign` sobre todas sus entradas (la librería las reparte en varios objetos)
  en vez de indexar el array, para no depender del orden interno de una versión concreta.
- [x] 4.3 Desactivar `react/prop-types` **únicamente** en el bloque `{ts,tsx}`; los `.jsx` la
  conservan. **Verificado con un archivo `.tsx` desechable** (creado, probado con
  `eslint src/__eslint_probe.tsx` y borrado antes de commitear, sin dejar rastro en `src/`): confirma
  que `@typescript-eslint/no-unused-vars` se activa, que `react/prop-types` NO se activa sobre una
  prop sin tipar, y que el parser resuelve JSX en `.tsx` sin errores — el bloque nuevo nunca se había
  ejercido de verdad porque hoy no existe ningún `.ts`/`.tsx` real en `src/`.
- [x] 4.4 Mover la selección de extensiones del script a la flat config: el script `lint` pasa de
  `eslint src --ext js,jsx` a `eslint src`.
- [x] 4.5 Ejecutar `corepack pnpm lint` y confirmar que el recuento es **exactamente** el de 4.1: ni
  violaciones nuevas, ni violaciones desaparecidas. No silenciar reglas para cuadrar el número.
  **Confirmado: 49 problems (49 errors, 0 warnings)**, idéntico a la línea base.

## 5. Type-check obligatorio en integración continua

- [x] 5.1 **Red** — actualizar `tools/ci-workflow.test.mjs` para que espere la séptima check context
  `Frontend type check` (hoy asevera seis, en `keeps the six branch-protection check contexts stable`
  y en la lista de contexts de los rulesets) y demostrar que `corepack pnpm ci:check:test` falla.
  **Incidencia de proceso:** el hook `.claude/hooks/lock-committed-tests.mjs` bloquea la edición de
  cualquier test ya commiteado sin distinguir el rol que llama — el agente **tester** lo confirmó
  intentando este mismo cambio y quedó bloqueado igual que lo estaría el coder. Es un diseño
  deliberado del hook ("los tests commiteados son inmutables"), no un bug. Se decidió con Victor
  (bypass puntual y verificado: mover `.claude/settings.json` fuera, aplicar el diff exacto ya
  preparado para el tester, restaurar el archivo y **confirmar funcionalmente que el candado volvía
  a bloquear** antes de continuar) en vez de dejar cobertura duplicada en un archivo nuevo — la
  alternativa que el propio hook sugiere (`agrega casos nuevos` en archivo aparte) no servía aquí
  porque el `expected` array de la tarea 5.5 exige `deepEqual` exacto: un archivo nuevo no puede
  invalidar la aserción vieja de "6 exactos", que además corre dentro del job `OpenSpec` de CI (via
  `ci:check:test`) y habría roto esa PR en cuanto los rulesets llegaran a 7. Evidencia Red con el
  comando real: `corepack pnpm ci:check:test` → `TypeError: Cannot read properties of undefined
  (reading 'name')` en `keeps the seven...` y `AssertionError` (6 recibidos vs. 7 esperados) en
  `requires the same seven...`.
- [x] 5.2 **Green** — añadir el job `frontend-typecheck` (nombre `Frontend type check`) a
  `.github/workflows/ci.yml`, con el mismo patrón que `frontend-build`: checkout con
  `persist-credentials: false`, Node 22, `corepack pnpm install --frozen-lockfile` y
  `corepack pnpm --filter @finops/frontend typecheck`. Mismos SHA pineados de
  `actions/checkout`/`actions/setup-node` que `frontend-build`, verificado que no rompe el test de
  pineado/permisos (itera todos los jobs automáticamente).
- [x] 5.3 Añadir la context `Frontend type check` a `.github/rulesets/develop.json` y
  `.github/rulesets/main.json`. `corepack pnpm ci:check:test` → 7/7 verde.
- [x] 5.4 Actualizar la lista "Required status checks" de
  `docs/governance/github-branch-protection.md` con la nueva context, manteniendo la nota vigente
  sobre por qué el lint del frontend **sigue** sin ser obligatorio, y añadiendo que a diferencia del
  lint, el type-check no arrastra deuda heredada (nace limpio) y que está versionado pero pendiente
  de que un administrador reaplique el ruleset en vivo (mismo patrón que JUP-079).
- [x] 5.5 Confirmar que `corepack pnpm ci:check:test` vuelve a verde y que los cuatro sitios
  (workflow, dos rulesets, documento de gobernanza) enumeran el mismo conjunto de contexts.
  **QA (`accept`):** verificado independientemente (comandos re-ejecutados, no solo el reporte del
  coder), incluida la consistencia de orden en los 4 sitios y que el diff no toca nada fuera de
  alcance. **Mutación:** sin runner aplicable — el artefacto bajo test es configuración YAML/JSON
  parseada (`ci.yml`, rulesets), no código JS/TS que Stryker/mutmut puedan mutar; QA verificó a mano
  los dos mutantes hipotéticos más plausibles (borrar el job dejando la entrada en el ruleset; typo
  en el nombre) y confirmó que los tests actuales los detectan igualmente. Categoría correcta para
  `review.md`: **no** "doc-only" (sí toca `ci.yml`/rulesets), sino su propia excepción justificada
  ("sin runner de mutación aplicable a config YAML/JSON declarativa").

## 6. Cierre y verificación

- [x] 6.1 Verificar que `apps/frontend/src/**` no tiene ni un archivo renombrado ni reescrito
  (`git diff --stat` sobre `src/`), y que `RF-082-002` sigue `Open` en
  `openspec/findings/backlog.md`, con nota de que F2 no lo cierra. Confirmado: diff vacío sobre
  `src/` en todo el change; el finding ya reflejaba este resultado desde su redacción en JUP-092
  (sin necesidad de editarlo).
- [x] 6.2 Marcar en `docs/spikes/frontend-migration.md` la tarjeta de F2 como completada,
  sustituyendo el placeholder `jup-0xx-configurar-typescript` por `jup-093-configure-typescript` y
  enlazando esta tarjeta. Añadida entrada 5 en "Proximos pasos" con el resumen y la tarjeta pendiente
  de F2 (`reconciliar-package-json`).
- [x] 6.3 Ejecutar la batería completa. **Sustitución acordada con Victor** (limitación de entorno
  preexistente, tarea 2.3): `corepack pnpm lint`/`build` (raíz, vía turbo) por
  `corepack pnpm --filter @finops/frontend lint`/`build`. Resultado, los 7 controles en verde:
  `install --frozen-lockfile` (sin tocar el lockfile), `lint` (49/49, línea base intacta), `build`,
  `typecheck` (`--filter`, ambos proyectos), `ci:check:test` (7/7), `openspec:validate` (21/21),
  `jup:check --change jup-093-configure-typescript` (OK), `jup:cleanup:check` (380 archivos limpios).
- [x] 6.4 Escribir `review.md` con el resultado, la evidencia Red/Green de la tarea 5.1, el recuento
  de lint antes/después, y **dos limitaciones declaradas explícitamente**: que el type-check pasa en
  verde sin verificar nada de sustancia mientras no haya archivos `.ts`/`.tsx` (`checkJs: false`), y
  que la context nueva no es obligatoria en vivo hasta que un administrador reaplique los rulesets.
  Incluye además el registro del hallazgo `RF-093-001` (limitación de entorno, nuevo en
  `openspec/findings/backlog.md`) y la doble justificación de la excepción de mutación (config sin
  comportamiento testeable vs. artefacto YAML/JSON sin runner aplicable).
- [x] 6.5 Crear `docs/evidence/JUP-093-validation.md` con los comandos exactos y sus resultados: esta
  tarjeta **no** es doc-only, así que la evidencia compartida sí aplica.
