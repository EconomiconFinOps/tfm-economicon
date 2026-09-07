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
