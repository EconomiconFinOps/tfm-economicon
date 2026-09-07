JUP: JUP-094
Trello: https://trello.com/c/Yqg2iZsj/86-jup-094-reconciliar-packagejson-del-frontend

## Why

[JUP-093](../archive/2026-09-06-jup-093-configure-typescript/) dejó la cadena de herramientas de
`apps/frontend` lista (TypeScript, lint, type-check obligatorio en CI), pero **el paquete sigue
declarando solo lo que necesita el destino actual**: 3 dependencias de runtime y ninguna de las que
el código del origen usa de verdad. F3 no puede reemplazar `src/**` sin que estén: la primera
pantalla portada importaría `react-router`, `recharts` o `lucide-react` y no compilaría.

Esta tarjeta cierra F2 resolviendo, además, **las dos decisiones que JUP-093 aplazó explícitamente**
y que ninguna otra tarjeta tiene asignadas:

- **`RF-091-002` (shadcn/ui).** El inventario de [JUP-091](../../../docs/planning/JUP-091-economicon-source-inventory.md)
  clasificó 48 de las 61 dependencias del origen como `DESCARTAR`, de las cuales **38 son shadcn/ui y
  su soporte**. La etiqueta refleja el uso real —ninguna pantalla del origen importa esos
  componentes—, pero el destino sí necesita primitivos de formulario, así que la decisión de adoptar
  o descartar es de esta tarjeta y condiciona toda F3.
- **Vite 5 vs 6.** Las 2 dependencias `SUSTITUIR` del inventario. El origen declara `^6.4.2` pero
  fija `6.3.5` en `pnpm.overrides` — una inconsistencia suya que el spike prohíbe copiar a ciegas.

Sin cerrar F2, cada tarjeta de F3 arrastraría estas decisiones a mitad de implementación, que es
justo lo que el spike quiere evitar al separar "tooling y dependencias" de "reemplazo del código".

## What Changes

- **Fusionar las 11 dependencias `MANTENER`** en `apps/frontend/package.json`: `react-router`,
  `recharts`, `lucide-react`, `tailwindcss` + `@tailwindcss/vite`, `tw-animate-css`, y las
  utilidades de composición de clases (`clsx`, `tailwind-merge`, `class-variance-authority`).
  `react`/`react-dom` ya están en la versión exacta del origen (18.3.1): no hay salto.
- **Resolver `RF-091-002`** con una decisión explícita y su motivo, y cerrarlo en
  `openspec/findings/backlog.md`. La propuesta que se lleva al gate pre-código es **descartar
  shadcn/ui por ahora** (ver `design.md`, decisión 1); si el equipo prefiere adoptarlo, esa opción
  **exige ADR propio** antes de instalar nada.
- **Resolver el salto de Vite** manteniéndose en la serie 5. Verificado que nada del conjunto
  `MANTENER` fuerza el 6: `@tailwindcss/vite@4.1.12` declara `vite ^5.2.0 || ^6 || ^7` y
  `@vitejs/plugin-react@4.7.0` declara `^4.2.0 || ^5 || ^6 || ^7`.
- **No arrastrar ninguna de las 48 `DESCARTAR`**, ni el `pnpm.overrides` del origen.
- **Declarar `react`/`react-dom` en `dependencies`** de forma consciente: el origen las tiene solo
  como `peerDependencies`, patrón de librería que no aplica a una aplicación del monorepo.
- **Conservar intacto** el contrato del paquete con el monorepo: nombre `@finops/frontend`,
  `type: module`, puerto 5173 y **todos** los scripts, incluido el `typecheck` de JUP-093.
- **Lockfile actualizado y versionado**, con `pnpm install --frozen-lockfile` reproducible.

**No se porta código.** `src/**` sigue intacto: al terminar, `apps/frontend` renderiza exactamente lo
mismo que hoy, pero su `package.json` ya sostiene lo que F3 va a importar.

## Capabilities

### New Capabilities

- `frontend-dependency-baseline`: el manifiesto de dependencias de `apps/frontend` declara lo que el
  código realmente usa o va a usar de forma inmediata, con cada entrada justificada por un consumidor
  previsto, sin arrastres del origen y sin romper el contrato del paquete con el monorepo
  (nombre, tipo de módulo, scripts, puerto) ni la reproducibilidad del lockfile. Es comportamiento
  verificable de la plataforma de build, complementario a
  [`frontend-typescript-tooling`](../../specs/frontend-typescript-tooling/spec.md) (JUP-093), que
  cubre la verificación de tipos.

### Modified Capabilities

<!-- Ninguna. `frontend-typescript-tooling` sigue cumpliéndose sin cambios en sus requisitos: esta
     tarjeta no toca `tsconfig`, ni el lint, ni el job de CI. El producto tampoco cambia de
     comportamiento: no se toca `src/**`. -->

## Impact

- **Modificado:** `apps/frontend/package.json` (solo el bloque de dependencias) y `pnpm-lock.yaml`
  (raíz).
- **Solo lectura:** `apps/frontend/src/**`, `tsconfig*.json`, `eslint.config.js`,
  `vite.config.ts` — ninguno se toca.
- **Dependencias nuevas:** 9 (las `MANTENER` que aún no están). Solo `tailwindcss`,
  `@tailwindcss/vite` y `tw-animate-css` son de desarrollo/build; el resto son de runtime.
- **Findings.**
  - `RF-091-002` se **cierra** aquí: es la tarjeta que el propio finding designa.
  - `RF-082-002` permanece `Open`: no se migra ningún `.jsx`, y `pnpm lint` debe seguir reportando
    exactamente las mismas 49 violaciones.
- **Riesgo de ADR:** si el gate pre-código elige **adoptar** shadcn/ui en lugar de descartarlo, esa
  decisión sí es transversal y duradera (ata todos los componentes de F3 y F5) y exigiría un ADR
  antes de implementar, con el precedente de JUP-092 → JUP-093. Ver `design.md`, decisión 2.
- **Desbloquea F3 por completo:** `portar-codigo-fuente`, `reconciliar-capa-api`,
  `reconciliar-auth-tenant` y `unificar-estilos-assets` ya podrán importar lo que necesiten.
- **Aún no:** cablear Tailwind v4 en el build ni unificar el sistema de estilos (F3,
  `unificar-estilos-assets`); aquí solo entra la dependencia.

## Human Approval

- Change: jup-094-reconcile-package-json
- Approval type: pre-code
- Decision: approved
- Approver: Victor
- Date: 2026-09-07
- Carril: standard
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Decisions approved: se aprueban las cinco decisiones del `design.md`. (1) **shadcn/ui se descarta por ahora**, conservando `clsx`/`tailwind-merge`/`class-variance-authority` (ya `MANTENER` en el inventario): lo que el destino usa hoy —8 `<button>`, 6 `<label>`, 5 `<input>`, 2 `<textarea>`, 1 `<select>`— lo cubre HTML nativo, que ya es accesible por defecto; Radix gana valor solo cuando hay que construir controles que el navegador no ofrece (combobox, modal, tooltip), y F3 no ha definido todavía ni una sola necesidad de ese tipo. Es el mismo criterio de abstracción prematura que ADR-0003 aplicó a `packages/shared-config`, y la asimetría de coste lo respalda: añadir 4-6 paquetes Radix cuando aparezca un requisito concreto es una tarjeta pequeña; retirar un sistema de diseño ya extendido por todas las pantallas, no. (2) **El ADR queda condicionado a esa decisión**: descartar es un aplazamiento reversible que se registra en `design.md` y en el cierre de `RF-091-002`, sin ADR nuevo; si el equipo hubiera elegido adoptar, el ADR sería obligatorio **antes** de instalar ningún `@radix-ui/*`, con el precedente JUP-092 → JUP-093. La condicionalidad es deliberada: ni se redacta un ADR para justificar una no-adopción, ni se adopta sin registrarlo. (3) **Vite se mantiene en la serie 5**, decisión sostenida por un hecho verificado en esta HU y no por preferencia: `@tailwindcss/vite@4.1.12` declara `vite ^5.2.0 || ^6 || ^7` y `@vitejs/plugin-react@4.7.0` declara `^4.2.0 || ^5 || ^6 || ^7` — ninguna dependencia entrante fuerza el salto. `@vitejs/plugin-react` se queda por tanto en la serie 4 del destino. (4) **Reparto ejecución/desarrollo**: `react-router`, `recharts`, `lucide-react` y las tres utilidades de clases van a `dependencies`; `tailwindcss`, `@tailwindcss/vite` y `tw-animate-css` a `devDependencies`; `react`/`react-dom` permanecen en `dependencies` y no se replica el patrón de `peerDependencies` del origen. (5) **Rangos `^` sobre la versión que ejercita el origen**, revisando lo que el resolutor instala en vez de confiar en `latest`, y sin copiar el `pnpm.overrides` del origen.
- Main risks: el riesgo principal es de **decisión, no de ejecución**: descartar shadcn/ui puede obligar a una segunda instalación en F3 si aparece una necesidad real de componente. Se acepta por ser barato y reversible en la dirección que importa, y el inventario de JUP-091 ya deja identificado el subconjunto (4-6 paquetes Radix) y su coste, así que esa tarjeta futura entraría con evidencia delante. Riesgo secundario con precedente directo: **el resolutor puede traer mayores incompatibles** — en JUP-093 trajo `typescript@7` (fuera del rango que soporta `typescript-eslint`) y `@types/react@19` desalineado de un runtime React 18; mitigación: revisar el `package.json` resultante dependencia por dependencia tras instalar y fijar versión explícita cuando el rango resuelto no corresponda con lo que el origen ejercitó (tarea 2.3). Riesgo terciario: **Tailwind entra instalado pero sin cablear** hasta F3, así que queda inerte; es intencional y se declara, con el criterio de aceptación de que `build` siga pasando sin que Tailwind altere todavía la salida ni el tamaño del bundle.
- Required changes before execution: none
- Notes: cierra **F2 (Tooling y dependencias)** junto a JUP-093. No es doc-only —modifica `package.json` y el lockfile— pero **tampoco tiene comportamiento unit-testeable**: el frontend sigue sin test runner (su script `test` es un `echo`) y esta tarjeta no toca `tools/`, así que no hay superficie donde aplicar el ciclo Red/Green del harness, a diferencia de JUP-093, que sí la tenía en `tools/ci-workflow.test.mjs`. La verificación recae en los comandos reales (`typecheck`, `lint`, `build`, `install --frozen-lockfile`) y la excepción se documentará en `review.md`. Sí lleva `docs/evidence/JUP-094-validation.md`. Quedan explícitamente fuera: reemplazar `src/**`, reconciliar `index.html`/entrypoint y migrar `.jsx` a `.tsx` (F3); cablear Tailwind y unificar estilos (F3, `unificar-estilos-assets`); tocar la capa API (F3); y endurecer `allowJs` a `false` (cierre de F5). **`RF-082-002` permanece `Open`** —ningún `.jsx` se migra, y `pnpm lint` debe seguir reportando exactamente 49 violaciones—, mientras que **`RF-091-002` se cierra aquí**, por ser la tarjeta que el propio finding designa. La verificación local usa los sustitutos `--filter @finops/frontend` por la limitación de entorno preexistente `RF-093-001`.

## Addendum: revisión de la decisión de shadcn/ui durante el `apply` (2026-09-07)

Mismo día de la aprobación de arriba, durante la implementación y **antes de instalar ninguna
dependencia Radix**, el equipo revirtió la decisión 1: en vez de descartar shadcn/ui, se adopta un
subconjunto de 6 paquetes (`@radix-ui/react-label`, `-select`, `-slot`, `-separator`, `-dialog`,
`-tooltip`).

**Motivo, revisado dos veces antes de fijarse:**

1. Primer motivo propuesto ("el origen ya tiene pantallas construidas sobre shadcn/ui") se descartó
   por ser **factualmente incorrecto**: el inventario de JUP-091 confirma que ninguna pantalla del
   origen renderiza esos componentes tampoco — es código muerto ahí también, no solo en el destino.
2. **Motivo real fijado**: facilidad de desarrollo. F3 va a construir varias pantallas (login,
   selector de tenant, ingesta, chat) que necesitan primitivos accesibles de formulario y
   superposición; construirlos a mano en HTML plano por cada pantalla traslada el coste de
   accesibilidad (foco, teclado, ARIA) a cada componente nuevo, uno por uno, en vez de resolverlo una
   sola vez. No es paridad con el origen — es una decisión de desarrollo hacia adelante.

**Consecuencia sobre el ADR (decisión 2 original):** al ser ahora una adopción, y no un descarte, el
ADR pasa de "no aplica" a **obligatorio**, tal como la propia decisión 2 ya anticipaba condicionalmente.
Redactado como [ADR-0004](../../../docs/adr/ADR-0004-frontend-shadcn-ui.md), en estado `Proposed`.
**Ningún paquete `@radix-ui/*` se instala hasta que se acepte** (tarea 1.2/2.5 de `tasks.md`).

**Alcance sin cambios en lo demás:** las decisiones 3, 4 y 5 (Vite en la serie 5, reparto
ejecución/desarrollo, rangos `^` sobre la versión del origen) no se ven afectadas. El alcance sigue
siendo **solo la dependencia**: copiar el código fuente de cada componente shadcn a
`src/components/ui/` sigue siendo trabajo de F3, componente por componente — esta tarjeta no toca
`src/**`.

- Approval type: pre-code (revisión)
- Decision: approved
- Approver: Victor
- Date: 2026-09-07
