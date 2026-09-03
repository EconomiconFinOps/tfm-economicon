JUP: JUP-092
Trello: https://trello.com/c/R5t2PL2F/84-jup-092-adr-de-adopción-de-typescript-en-el-frontend

## Why

El spike de migración fija como **decisión número 1** la adopción de TypeScript en `apps/frontend` y
la califica de "decisión transversal y duradera (afecta tooling, build, lint y todas las tareas
futuras del frontend)", exigiendo un ADR **antes** de implementar la feature de tooling.
[docs/adr/README.md](../../../docs/adr/README.md) lo respalda: los patrones compartidos que afectan a
varios módulos o tareas futuras requieren ADR.

El punto de partida real —verificado, no supuesto— es que **hoy no existe verificación de tipos en
ningún lado**:

- El **destino** (`apps/frontend`) es JavaScript con JSX y no declara `typescript` ni paquetes de
  tipos.
- El **origen** (Economicon) llega en TSX pero **tampoco tiene type-check**: no declara `typescript`
  ni incluye `tsconfig.json` (JUP-083, y confirmado en el inventario de JUP-091, donde `typescript`
  no figura entre las 61 dependencias declaradas). Su TSX lo transpila esbuild sin verificar nada.

Adoptar TypeScript no es, por tanto, "conservar lo que trae el origen": es **introducir verificación
de tipos donde no la hay**, y sería el primer código tipado del repo en el lado JavaScript (backend y
processor son Python).

Sin esa decisión acordada, **F2 queda bloqueada**: `jup-0xx-configurar-typescript` no puede instalar
dependencias ni crear `tsconfig` sin saber qué nivel de rigor se exige, cómo encaja con CI y cómo
convive con el JavaScript existente.

## What Changes

- Crear `docs/adr/ADR-0003-frontend-typescript.md` con
  [docs/templates/adr.md](../../../docs/templates/adr.md). `0003` es el siguiente número libre
  (existen `ADR-0001` y `ADR-0002`).
- Resolver en el ADR, de forma inequívoca, las cuatro decisiones que hoy bloquean F2:
  1. **Nivel de rigor**: `strict` completo desde el inicio o adopción gradual.
  2. **Estrategia de convivencia**: migración completa a `.ts`/`.tsx` o `allowJs` con coexistencia
     temporal de JavaScript.
  3. **Encaje con CI**: si el type-check pasa a ser check obligatorio, y qué ocurre con el finding
     `RF-082-002` — **49 violaciones de `react/prop-types`** (recuento verificado hoy) que mantienen
     el lint del frontend fuera de los checks obligatorios
     ([docs/governance/github-branch-protection.md](../../../docs/governance/github-branch-protection.md)).
     Los tipos de TypeScript sustituyen a `prop-types` como mecanismo de validación, así que esta
     decisión determina si ese finding se cierra, se transforma o se mantiene.
  4. **Ubicación del `tsconfig`**: a nivel de `apps/frontend` o compartido en
     `packages/shared-config`.
- Registrar al menos dos alternativas descartadas con su motivo (seguir en JavaScript; JSDoc +
  `checkJs` como vía intermedia).
- Llevar el ADR de `Proposed` a `Accepted` tras la aprobación del equipo.
- Enlazar el ADR desde `docs/spikes/frontend-migration.md`, dejándolo disponible para que las
  tarjetas de F2 y F3 lo citen en su `design.md`.

**No se implementa la decisión**: sin instalar `typescript` ni tipos, sin crear `tsconfig`, sin
migrar `eslint.config.js`, sin renombrar archivos y sin tocar código de `apps/frontend`. Todo eso es
F2.

## Capabilities

### New Capabilities

- `frontend-typescript-adoption`: capability de **proceso** (no de producto) que exige que la
  adopción de TypeScript en el frontend esté registrada como decisión de arquitectura aceptada,
  con sus cuatro puntos resueltos sin ambigüedad y enlazada desde las tarjetas que la implementarán,
  antes de que ninguna toque el tooling. Es el spec mínimo requerido por OpenSpec; se archiva con
  `--skip-specs` y no se promociona a `openspec/specs/`.

### Modified Capabilities

<!-- Ninguna. No cambia ningún requisito de comportamiento del producto: esta HU produce una
     decisión de arquitectura documentada, no código. -->

## Impact

- **Nuevo:** `docs/adr/ADR-0003-frontend-typescript.md` — decisión duradera, vinculante para F2 y F3.
- **Modificado:** `docs/spikes/frontend-migration.md` (tarjeta F1 marcada + enlace al ADR).
- **Posiblemente modificado:** `openspec/findings/backlog.md`, si la decisión sobre CI cambia el
  estado de `RF-082-002`.
- **Solo lectura:** `apps/frontend/**`, `docs/governance/github-branch-protection.md`,
  `.github/workflows/ci.yml` y los inventarios de JUP-090 y JUP-091, como fuente del contexto.
- **Sin código de producto, sin dependencias nuevas, sin `specs/` de producto.**
- Consumidores posteriores: F2 (`configurar-typescript`, `reconciliar-package-json`) y F3
  (`portar-codigo-fuente`, `reconciliar-capa-api`) quedan desbloqueadas y deben citar este ADR.
- A diferencia de JUP-090 y JUP-091, esta tarjeta es de carril **`standard`**: produce una decisión
  de arquitectura, no un inventario.
