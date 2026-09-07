JUP: JUP-094

## Context

Ver [proposal.md](proposal.md) — Why. Aquí solo el estado verificado que condiciona el enfoque.

**Decisión heredada vinculante.** [ADR-0003](../../../docs/adr/ADR-0003-frontend-typescript.md)
(`Accepted`, JUP-092) sigue rigiendo: `strict: true`, `allowJs: true` durante la migración,
type-check obligatorio en CI, `tsconfig` local a `apps/frontend`. Esta tarjeta **no la reabre**; solo
añade dependencias bajo ella. El spike ([línea 170](../../../docs/spikes/frontend-migration.md))
exige que toda tarjeta de F2 y F3 lo enlace desde su `design.md`; este documento lo hace.

**Punto de partida** (tras el merge de JUP-093, `283a1d8`):

- `apps/frontend/package.json`: 3 dependencias de ejecución (`@tanstack/react-query`, `react`
  `^18.3.1`, `react-dom` `^18.3.1`) y 12 de desarrollo. `vite ^5.3.3` (resuelto a 5.4.21) y
  `@vitejs/plugin-react ^4.3.1`.
- Scripts vigentes: `dev` (`--host 0.0.0.0 --port 5173`), `build`, `preview`, `lint` (`eslint src`),
  `test` (`echo`), `typecheck` (`tsc --noEmit && tsc -p tsconfig.node.json --noEmit`),
  `docker:build`.
- `tsconfig.json` declara `"types": []` (corrección de la revisión del PR #27): **ningún paquete de
  tipos globales entra automáticamente**. `tsconfig.node.json` conserva `"types": ["node"]`.
- `src/**`: 14 archivos `.js`/`.jsx` intactos. Línea base de lint: **49 violaciones exactas** de
  `react/prop-types` (`RF-082-002`, `Open`).
- Inventario del origen ([JUP-091](../../../docs/planning/JUP-091-economicon-source-inventory.md)):
  61 declaradas → **11 `MANTENER`, 2 `SUSTITUIR`, 48 `DESCARTAR`**.

**Hechos verificados en esta HU** (no supuestos), decisivos para la decisión 3:

- `@tailwindcss/vite@4.1.12` declara `peerDependencies: { vite: "^5.2.0 || ^6 || ^7" }`.
- `@vitejs/plugin-react@4.7.0` (la del origen) declara `{ vite: "^4.2.0 || ^5.0.0 || ^6.0.0 || ^7.0.0" }`.

## Goals / Non-Goals

**Goals:**

- Dejar el manifiesto capaz de sostener todo lo que F3 va a importar, sin que F3 tenga que parar a
  instalar nada ni a decidir nada de dependencias.
- Cerrar `RF-091-002` con una decisión argumentada, no con un aplazamiento más.
- Que cada dependencia añadida tenga un consumidor nombrado; ninguna "por si acaso".

**Non-Goals (además de los de la propuesta):**

- **No se cablea Tailwind en el build.** Entra la dependencia; configurar el plugin en
  `vite.config.ts`, crear las hojas de estilo y retirar `main.css` es de F3
  (`unificar-estilos-assets`). Instalarla ahora evita que F3 tenga que tocar `package.json`.
- **No se añade `vite-env.d.ts`** ni ninguna referencia de tipos ambientales: hasta que exista un
  `.ts`/`.tsx` real que los consuma, sería adelantar trabajo de F3 (mismo criterio que aplicó
  JUP-093, verificado entonces empíricamente).
- **No se toca `src/**`, `tsconfig*`, `eslint.config.js` ni `vite.config.ts`.**

## Decisions

### 1. shadcn/ui: **descartar por ahora**, conservando las utilidades de clases

Se propone **no** incorporar ningún paquete `@radix-ui/*` en esta tarjeta. Sí entran `clsx`,
`tailwind-merge` y `class-variance-authority`, que el inventario ya clasifica `MANTENER` y que son
útiles con Tailwind plano, con o sin shadcn/ui.

*Por qué:*

- **Lo que el destino necesita hoy lo cubre HTML nativo.** Sus pantallas usan 8 `<button>`,
  6 `<label>`, 5 `<input>`, 2 `<textarea>` y 1 `<select>`. Los elementos nativos ya son accesibles
  por defecto: `<select>` y `<label>` traen semántica, foco y navegación por teclado sin librería.
  Radix gana valor cuando hay que construir controles que el navegador **no** ofrece (combobox
  custom, modal, tooltip), y hoy no hay ninguno.
- **Ninguna pantalla del origen los usa.** Los 48 componentes de `ui/` son código muerto
  (`RF-091-002`): adoptarlos sería importar un sistema de diseño que ni siquiera el origen ejercita.
- **F3 todavía no ha definido una sola necesidad de componente.** Elegir el sistema de diseño antes
  de conocer el primer requisito real es exactamente la abstracción prematura que ADR-0003 rechazó
  para `packages/shared-config` ("extraer para un solo consumidor... se pospone hasta que haya un
  segundo consumidor real"). El mismo criterio aplica aquí.
- **La decisión es barata de revertir en la dirección que importa.** Añadir 4-6 paquetes Radix
  cuando F3 tropiece con una necesidad concreta es una tarjeta pequeña y con evidencia; quitar un
  sistema de diseño ya extendido por todas las pantallas, no.

*Alternativa considerada — adoptar el subconjunto de 4-6 paquetes* (`label`, `select`, `slot`,
`separator`, quizá `dialog`/`tooltip`): defendible al pasar a Tailwind v4, y evitaría una segunda
instalación más adelante. Se descarta ahora por falta de un requisito que la justifique, no por
coste. **Si el equipo la prefiere en el gate pre-código, cambia también la decisión 2.**

### 2. ADR: **no aplica si se descarta; obligatorio si se adopta**

Con la decisión 1 tal como se propone, **no se necesita un ADR nuevo**: "no añadimos todavía una
dependencia que nadie consume" es un aplazamiento reversible y de bajo compromiso, que se registra
en este `design.md` y en el cierre de `RF-091-002`.

Si el gate pre-código elige **adoptar** shadcn/ui, la naturaleza de la decisión cambia: pasa a ser un
patrón compartido que ata todos los componentes de F3 y el cierre de F5 — exactamente lo que
[docs/adr/README.md](../../../docs/adr/README.md) exige registrar como ADR, con el precedente directo
de JUP-092 (ADR-0003) antes de que JUP-093 pudiera tocar el tooling. En ese caso: **el ADR se redacta
y acepta antes de instalar ningún paquete Radix**, sea dentro de esta tarjeta o en una tarjeta ADR
que la preceda.

Dejar la aplicabilidad del ADR **condicionada a la decisión** es deliberado: evita redactar un ADR
para justificar una no-adopción, y evita adoptar sin registrarlo.

### 3. Vite: **mantenerse en la serie 5**

*Por qué:* ninguna dependencia que entra fuerza el salto — es un hecho verificado, no una
preferencia: `@tailwindcss/vite@4.1.12` acepta `^5.2.0`, y `@vitejs/plugin-react@4.7.0` acepta `^5`.
El destino ya corre 5.4.21. Un salto de mayor sin ninguna dependencia que lo pida añade riesgo de
build a una tarjeta cuyo objetivo es *no* romper nada, y lo añade justo antes de que F3 reemplace
todo `src/**`: si algo fallara después, no se sabría si es el bundler o el código portado.

Además, el `pnpm.overrides` del origen fija `6.3.5` mientras declara `^6.4.2`: evidencia de que su
propio Vite 6 no estaba bajo control. Copiarlo sería heredar esa inconsistencia.

*Alternativa considerada — subir a Vite 6 ahora:* concentraría los cambios de tooling en F2 y
evitaría un salto durante F3. Se descarta porque no hay ninguna presión técnica que lo pida hoy; si
F3 o F4 encuentran una (una dependencia que exija 6, o un problema real de build), ese será el
momento, con un motivo concreto. Se deja registrado como seguimiento, no como deuda oculta.

*Consecuencia:* `@vitejs/plugin-react` se mantiene en la serie 4 actual del destino. No se adopta el
4.7.0 del origen en esta tarjeta: sin cambio de Vite no aporta nada, y cada versión que se toca hay
que justificarla.

### 4. Ubicación de cada dependencia: ejecución vs. desarrollo

- **Ejecución** (`dependencies`): `react-router`, `recharts`, `lucide-react`, `clsx`,
  `tailwind-merge`, `class-variance-authority` — todas se importan desde código de aplicación.
- **Desarrollo** (`devDependencies`): `tailwindcss`, `@tailwindcss/vite`, `tw-animate-css` — actúan
  en tiempo de build; el CSS resultante se emite en el bundle.
- `react`/`react-dom` **ya están** en `dependencies` y se quedan ahí: el patrón de
  `peerDependencies` del origen es propio de una librería, no de una aplicación (nota explícita del
  inventario de JUP-091), y adoptarlo dejaría el árbol a merced de quien instale.

### 5. Rangos de versión: `^` sobre la versión del origen, sin `overrides`

Se declara cada dependencia con rango `^` partiendo de la versión que usa el origen (la que su
código ha ejercitado), salvo que el resolutor traiga un mayor incompatible — el caso que ya ocurrió
en JUP-093 con `typescript@7` y `@types/react@19`, y que obliga a **revisar lo instalado, no a
confiar en `latest`**. No se replica el `pnpm.overrides` del origen.

## Risks / Trade-offs

- **Descartar shadcn/ui puede obligar a una segunda instalación en F3** si aparece una necesidad real
  de componente → asumido y barato: sería una tarjeta pequeña, con el requisito concreto delante, y
  el inventario ya tiene identificado el subconjunto (4-6 paquetes) y su coste.
- **El resolutor puede traer mayores incompatibles** (precedente directo: JUP-093 recibió
  `typescript@7` y tipos de React 19 desalineados del runtime) → mitigación: verificar el
  `package.json` resultante dependencia por dependencia tras instalar, y fijar versión explícita si
  el rango resuelto no corresponde con lo que el origen ejercitó.
- **Tailwind entra pero no se cablea**, así que queda instalado sin efecto hasta F3 → es intencional
  (Non-Goal) y se declara: el criterio de aceptación es que `build` siga pasando **sin** que Tailwind
  altere la salida todavía.
- **Añadir dependencias de ejecución engorda el bundle** aunque `src/**` aún no las importe → no:
  Vite solo empaqueta lo que se importa; el bundle actual (203 kB) no debería moverse. Se verifica
  comparando el tamaño de salida antes y después.
- **`"types": []` en `tsconfig.json`** hace que ningún tipo global entre solo → ninguna de las
  dependencias de esta tarjeta aporta tipos ambientales necesarios hoy; si F3 los necesita
  (`vite/client` para assets), los referenciará entonces.

## Migration Plan

1. Instalar las de ejecución con `corepack pnpm --filter @finops/frontend add <paquetes>`.
2. Instalar las de build con `... add -D tailwindcss @tailwindcss/vite tw-animate-css`.
3. Revisar el `package.json` resultante: versiones coherentes con el inventario, nada colado en el
   bloque equivocado, `dependencies` de runtime sin `peerDependencies`.
4. `pnpm install --frozen-lockfile`, `typecheck`, `lint` (49 exactas), `build` (tamaño comparado).
5. Cerrar `RF-091-002` en `openspec/findings/backlog.md` con la decisión y su motivo.
6. Marcar F2 completa en el spike.

**Rollback:** revert del commit de dependencias y del lockfile. No hay migración de datos ni de
código; `src/**` nunca se toca.

## Open Questions

- Ninguna que bloquee. La única decisión abierta de verdad —adoptar o descartar shadcn/ui— se lleva
  resuelta como propuesta al **gate pre-código** (decisión 1), con su consecuencia sobre el ADR
  explícita (decisión 2). Si el equipo elige adoptar, cambian las tareas 1.x y aparece una tarea de
  ADR previa; el resto del plan no se ve afectado.
