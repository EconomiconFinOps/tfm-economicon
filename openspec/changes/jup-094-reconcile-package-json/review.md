# Review: jup-094-reconcile-package-json

## Result

Accepted (pendiente del gate post-review de Victor antes de archivar).

## Scope Reviewed

- `apps/frontend/package.json` — 15 dependencias nuevas fusionadas (9 `MANTENER` del inventario de
  JUP-091 + 6 `@radix-ui/*` de ADR-0004), sin tocar scripts, nombre ni tipo de módulo.
- `pnpm-lock.yaml` (raíz) — actualizado por las tres rondas de instalación.
- `docs/adr/ADR-0004-frontend-shadcn-ui.md` (nuevo, `Accepted`).
- `openspec/findings/backlog.md` — `RF-091-002` cerrado (`Fixed`); `RF-082-002` verificado sin
  cambios (sigue `Open`).
- `docs/spikes/frontend-migration.md` — F2 marcada completa (JUP-093 + JUP-094).
- `openspec/changes/jup-094-reconcile-package-json/{proposal,design,specs,tasks}.md` — `design.md` y
  `proposal.md` revisados a mitad de `apply` (ver "Revisión de la decisión de shadcn/ui" abajo).
- `apps/frontend/src/**` — en **solo lectura**: cero archivos tocados, verificado con `git diff`.

## Checklist

- [x] Los 5 requisitos de `specs/frontend-dependency-baseline/spec.md` se cumplen de forma
  observable (consumidor real por dependencia, decisión de componentes registrada, salto de bundler
  deliberado, contrato del paquete conservado, instalación reproducible sin tocar fuentes).
- [x] Las 11 dependencias `MANTENER` del inventario fusionadas; ninguna de las 48 `DESCARTAR` entró,
  salvo el subconjunto de 6 Radix que autoriza ADR-0004.
- [x] `RF-091-002` cerrado con la decisión final y su motivo registrados en el backlog.
- [x] `RF-082-002` permanece `Open`: verificado que `src/**` no tiene ni un archivo tocado.
- [x] Vite se mantiene en la serie 5, con el hecho verificado (no una preferencia) que lo sostiene.
- [x] ADR-0004 redactado y aceptado **antes** de instalar ningún paquete `@radix-ui/*` — el orden
  real de ejecución respetó el gate que el propio `design.md` fijó.
- [x] `tasks.md` marcado 22/22 (20 originales + 2 añadidas durante la revisión: 2.5/2.6).
- [x] Checks de la batería completa en verde.
- [x] Ningún archivo de `.claude/` colado en ningún commit (`jup:cleanup:check`).

## Revisión de la decisión de shadcn/ui durante el `apply`

La decisión 1 aprobada en el gate pre-código (descartar shadcn/ui) se revirtió el mismo día, durante
la implementación, **antes de instalar ningún paquete Radix**. Cronología:

1. Al llegar a la tarea 1.2, Victor pidió cambiar la decisión a adoptar shadcn/ui.
2. Primer motivo propuesto ("el origen ya tiene pantallas construidas sobre shadcn/ui") se descartó
   por **factualmente incorrecto**: el inventario de JUP-091 confirma que tampoco el origen renderiza
   esos componentes — es código muerto ahí también, no solo en el destino previsto.
3. Motivo real fijado: **facilidad de desarrollo**. F3 va a construir varias pantallas (login,
   selector de tenant, ingesta, chat) que necesitan primitivos accesibles de formulario y
   superposición; construirlos a mano en HTML plano por cada pantalla traslada el coste de
   accesibilidad a cada componente nuevo, uno por uno.
4. Redactado y aceptado [ADR-0004](../../../docs/adr/ADR-0004-frontend-shadcn-ui.md) (aprobación
   verbal inmediata en la misma sesión; sin fase `Proposed` intermedia comiteada por separado, a
   diferencia del ciclo de dos commits de ADR-0003).
5. `design.md` y `proposal.md` revisados: el razonamiento original ("descartar") se conserva íntegro
   en el primero, marcado como superado, no borrado; el segundo lleva una adenda que documenta la
   revisión sin reescribir el bloque de aprobación original.
6. Instalado el subconjunto de 6 paquetes Radix recién entonces.

Alcance sin cambios en lo demás: las decisiones sobre Vite, el reparto ejecución/desarrollo y los
rangos de versión no se vieron afectadas. El alcance sigue siendo **solo la dependencia**: copiar el
código fuente de cada componente shadcn a `src/components/ui/` queda para F3, componente por
componente — esta tarjeta no tocó `src/**` en ningún momento, ni antes ni después de la revisión.

## Validation

Batería completa (tarea 6.3), 7 controles, todos en verde:

```txt
corepack pnpm install --frozen-lockfile -> PASS (lockfile sin cambios)
corepack pnpm --filter @finops/frontend lint -> PASS: 49 problems (49 errors), identico a la linea base (RF-082-002)
corepack pnpm --filter @finops/frontend build -> PASS (bundle identico: JS 203.37 kB / gzip 63.38 kB, CSS 5.60 kB)
corepack pnpm --filter @finops/frontend typecheck -> PASS (ambos proyectos)
corepack pnpm openspec:validate -> PASS: 22 items (4 specs, 18 changes)
corepack pnpm jup:check -- --change jup-094-reconcile-package-json -> PASS: enlazado con Trello y completo
corepack pnpm jup:cleanup:check -> PASS: 389 archivos sin agentes personales, binarios ni tareas paralelas
```

**Sustitución documentada** (mismo criterio que JUP-093, `RF-093-001`): `corepack pnpm lint`/`build`
en la raíz (vía turbo) sustituidos por `--filter @finops/frontend`, por la limitación de entorno
preexistente en esta máquina.

**Incidencias con el resolutor de dependencias** (segunda vez tras JUP-093, mismo patrón):
`react-router` resolvió a `8.3.1` (exige `react >=19.2.7`, incompatible con el runtime `^18.3.1`).
Corregido fijando `react-router@7.13.0`, `recharts@2.15.2` y `lucide-react@0.487.0` — las versiones
exactas que ejercita el origen. `tailwindcss` resolvió `^4.3.3` (minor dentro de la serie 4 de
`4.1.12`, sin incompatibilidad): se dejó tal cual, conforme a la regla de fijar solo ante un mayor
incompatible.

## Excepción de harness TDD

Esta tarjeta **no es doc-only** (modifica `package.json` y el lockfile) pero **tampoco tiene
comportamiento unit-testeable**: el frontend sigue sin test runner (su script `test` es un `echo`) y
ningún archivo de `tools/` se tocó, así que no hay superficie donde aplicar el ciclo Red/Green del
harness — a diferencia de JUP-093, que sí la tenía en `tools/ci-workflow.test.mjs`. Sin
tester/coder/QA por tarea; verificación vía los comandos reales (`typecheck`, `lint`, `build`,
`install --frozen-lockfile`), documentada arriba. Mutación: N/A por el mismo motivo — sin
comportamiento testeable no hay mutante que generar.

## Review Findings

- **`RF-091-002` cerrado (`Fixed`)**: decisión final registrada en el backlog y en ADR-0004.
- Ninguno nuevo sobre `RF-082-002` ni `RF-093-001`: esta tarjeta no cambia su estado, solo lo
  confirma (`RF-082-002` sigue `Open`; `RF-093-001` sigue documentando la limitación de entorno que
  ya existía).

## Risks / Follow-Ups

- **Elegir el subconjunto de 6 paquetes Radix antes de que F3 escriba una pantalla** es una apuesta
  (ADR-0004, "se vuelve más arriesgado"): si falta un séptimo, es una instalación pequeña de
  seguimiento; si alguno no llega a usarse, queda como peso muerto hasta que se retire.
- **Copiar el código fuente de cada componente shadcn a `src/components/ui/` queda pendiente de
  F3**, componente por componente — esta tarjeta solo deja la dependencia instalada.
- **F3 y el cierre de F5 deben citar ADR-0003 y ADR-0004** en su `design.md` al crearse, misma
  convención que ya exigía el spike para ADR-0003.
- **Activación en vivo de la check context de JUP-093** sigue pendiente de un administrador
  (sin relación con esta tarjeta, heredado de JUP-093/JUP-079).
