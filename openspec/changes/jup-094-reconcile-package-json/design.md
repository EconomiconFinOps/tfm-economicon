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

### 1. shadcn/ui: **adoptar** un subconjunto de 6 paquetes Radix

> **Revisado durante el `apply` (2026-09-07).** La posición original de esta decisión —descartar
> shadcn/ui por ahora— quedó aprobada en el gate pre-código, pero el equipo la revirtió antes de
> instalar nada de la tarea 3. Se conserva el razonamiento original íntegro más abajo, marcado como
> superado, porque sigue siendo evidencia real (documenta por qué HTML nativo parecía suficiente) y
> porque el ADR-0004 resultante lo cita como la alternativa descartada.

Se incorporan 6 paquetes Radix — `@radix-ui/react-label`, `@radix-ui/react-select`,
`@radix-ui/react-slot`, `@radix-ui/react-separator`, `@radix-ui/react-dialog`,
`@radix-ui/react-tooltip` — como dependencias de `package.json`. **Solo la dependencia**: copiar el
código fuente de cada componente a `src/components/ui/` (convención de shadcn/ui, no se consume como
librería opaca) es trabajo de F3, componente por componente, cuando la pantalla que lo necesita se
construye. Coherente con el Non-Goal de arriba: esta tarjeta no toca `src/**`. `clsx`,
`tailwind-merge` y `class-variance-authority` (ya `MANTENER` en el inventario) son las utilidades que
shadcn/ui usa para componer variantes de clases; se mantienen tal como estaban previstas.

*Por qué el cambio:* el motivo no es que el origen use shadcn/ui — el inventario de JUP-091 confirma
que **tampoco** lo usa en sus pantallas reales, así que ese argumento nunca aplicó. El motivo es de
desarrollo hacia adelante: F3 va a construir varias pantallas (login, selector de tenant, ingesta,
chat) que necesitan primitivos accesibles de formulario y superposición, y construirlos a mano en
HTML plano por cada pantalla traslada el coste de accesibilidad (foco, teclado, ARIA) a cada
componente nuevo, uno por uno, en vez de resolverlo una sola vez.

**Alcance acotado, no el `ui/` completo del origen.** Los 20 primitivos Radix restantes que el
inventario clasifica `DESCARTAR` siguen sin consumidor conocido en el destino y no se incorporan.
Detalle completo de la decisión y sus consecuencias en
[ADR-0004](../../../docs/adr/ADR-0004-frontend-shadcn-ui.md).

<details>
<summary>Razonamiento original (descartar), superado por la revisión de arriba</summary>

Se proponía **no** incorporar ningún paquete `@radix-ui/*` en esta tarjeta, porque lo que el destino
necesitaba hoy lo cubría HTML nativo: sus pantallas usan 8 `<button>`, 6 `<label>`, 5 `<input>`,
2 `<textarea>` y 1 `<select>`, y los elementos nativos ya son accesibles por defecto. Elegir el
sistema de diseño antes de conocer el primer requisito real parecía la misma abstracción prematura
que ADR-0003 rechazó para `packages/shared-config`. La alternativa ya identificada entonces —adoptar
el subconjunto de 4-6 paquetes (`label`, `select`, `slot`, `separator`, quizá `dialog`/`tooltip`)— es
esencialmente el subconjunto que esta revisión termina adoptando, con `dialog` y `tooltip`
confirmados en vez de "quizá".

</details>

### 2. ADR: **ADR-0004**, `Proposed` hasta la aceptación del equipo

La decisión 1 es ahora una adopción de sistema de diseño: un patrón compartido que ata todos los
componentes de F3 y el cierre de F5. Exactamente lo que
[docs/adr/README.md](../../../docs/adr/README.md) exige registrar como ADR, con el precedente directo
de JUP-092 (ADR-0003) antes de que JUP-093 pudiera tocar el tooling.

**Redactado como [ADR-0004](../../../docs/adr/ADR-0004-frontend-shadcn-ui.md)**, en estado `Proposed`.
Pasa a `Accepted` en un commit separado, tras la aprobación del equipo — mismo patrón de dos commits
que usó ADR-0003. **Ningún paquete `@radix-ui/*` se instala antes de esa aceptación.**

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
  `tailwind-merge`, `class-variance-authority`, y los 6 paquetes `@radix-ui/*` de ADR-0004
  (`react-label`, `react-select`, `react-slot`, `react-separator`, `react-dialog`,
  `react-tooltip`) — todas son de ejecución: los primitivos Radix se renderizan en el navegador tanto
  como `react-router` o `recharts`, aunque su código de composición (los componentes copiados de
  shadcn/ui) todavía no exista en `src/**`.
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

- **Elegir el subconjunto de 6 paquetes Radix antes de que F3 escriba una pantalla** es una apuesta
  sobre qué primitivos hacen falta de verdad (ADR-0004, "se vuelve más arriesgado") → si falta un
  séptimo, es una instalación pequeña de seguimiento; si `dialog`/`tooltip` no llegan a usarse, quedan
  como peso muerto hasta que se retiren. No se instalan los otros 20 primitivos del origen: la
  apuesta se acota a lo que las pantallas conocidas del destino (login, tenant, ingesta, chat)
  previsiblemente necesitan.
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

1. **Aceptar ADR-0004** (`Proposed` → `Accepted`, commit separado del de redacción) antes de instalar
   ningún paquete `@radix-ui/*`.
2. Instalar las de ejecución con `corepack pnpm --filter @finops/frontend add <paquetes>`, incluidos
   los 6 `@radix-ui/*` de ADR-0004.
3. Instalar las de build con `... add -D tailwindcss @tailwindcss/vite tw-animate-css`.
4. Revisar el `package.json` resultante: versiones coherentes con el inventario, nada colado en el
   bloque equivocado, `dependencies` de runtime sin `peerDependencies`.
5. `pnpm install --frozen-lockfile`, `typecheck`, `lint` (49 exactas), `build` (tamaño comparado).
6. Cerrar `RF-091-002` en `openspec/findings/backlog.md` con la decisión y su motivo.
7. Marcar F2 completa en el spike.

**Rollback:** revert del commit de dependencias y del lockfile. No hay migración de datos ni de
código; `src/**` nunca se toca. Si además se revirtiera ADR-0004, seguiría el mismo patrón de
`Superseded` que exige `docs/adr/README.md`, no un borrado.

## Open Questions

- Ninguna que bloquee. La decisión sobre shadcn/ui se revisó durante el `apply` (ver decisiones 1 y
  2, y [ADR-0004](../../../docs/adr/ADR-0004-frontend-shadcn-ui.md)): el equipo pasó de descartarlo a
  adoptar un subconjunto de 6 paquetes, con el ADR como bloqueante de la instalación hasta que se
  acepte. El resto del plan no se ve afectado por el cambio.
