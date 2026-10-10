JUP: JUP-105
Trello: https://trello.com/c/YZvtBdGV/100-jup-105

## Why

La épica «Migrar frontend de Economicon» tiene todas sus tarjetas fusionadas y archivadas (JUP-083,
090 a 095, 097, 098, 099, 103 y 104), pero el repositorio todavía no cuenta lo que de verdad se hizo.
Quien llegue hoy al proyecto y lea el spike, el README del frontend y el backlog de hallazgos
encuentra tres cosas en las que no puede fiarse:

- **Una configuración provisional que nadie retiró.** `apps/frontend/tsconfig.json` sigue con
  `allowJs: true`, la convivencia con JavaScript que [ADR-0003](../../../../docs/adr/ADR-0003-frontend-typescript.md)
  aceptó solo «durante la migración» y que asigna expresamente a esta tarjeta endurecer. En `src/` y
  `tests/` ya no queda ningún archivo JavaScript.
- **Un spike sin cerrar.** [`docs/spikes/frontend-migration.md`](../../../../docs/spikes/frontend-migration.md)
  conserva el marcador `jup-0xx-checks-y-archive` con tres casillas sin marcar, da JUP-099, JUP-103 y
  JUP-104 por «implementadas» cuando están fusionadas, y no declara el estado final.
- **Textos que contradicen el código.** El frontend cambió mientras duraba la épica por tarjetas
  ajenas a ella (JUP-085, JUP-026, JUP-055, JUP-057, JUP-025 y JUP-047), y varios documentos siguen
  describiendo el estado anterior: que `/overview-legacy` es el único dashboard con datos reales, que
  las cinco pantallas de coste son de demostración, que `Frontend tests` es un check obligatorio.

A eso se suma una deuda documental medida y sin dueño desde el 29/09 (`RF-099-001` y `RF-099-004`) y
21 hallazgos de la épica en `Open` con «Equipo Economicon» como único responsable.

El alcance se verificó contra el código el 2026-10-08 sobre `develop` en `ff2ea6b`, antes de
proponer. Los recuentos y las diferencias con la tarjeta están en [`design.md`](design.md), sección
Context.

## What Changes

- **Endurecer `allowJs` a `false`** en `apps/frontend/tsconfig.json` y comprobar que `typecheck`,
  `lint`, `test` y `build` siguen en verde, con un control positivo que demuestre que un import de
  JavaScript hace fallar el type-check. Anotarlo en el seguimiento de ADR-0003.
- **Poner al día la spec vigente `frontend-typescript-tooling`**, que todavía describe `src/` como
  «únicamente archivos `.js` y `.jsx`», fija la línea base de lint en 49 violaciones y exige que
  ningún archivo fuente se haya migrado. No estaba en la tarjeta: apareció al verificar.
- **Cerrar el spike**: sustituir el marcador por `jup-105-close-frontend-migration` con sus casillas
  resueltas, corregir el estado de JUP-099, JUP-103 y JUP-104, enlazar los changes archivados de
  JUP-090, 091, 092 y 095, resolver la casilla pendiente de JUP-092 y añadir el punto 13 con el
  estado final de la épica.
- **Recontar las pantallas contra el código** y dejar el recuento, fechado, en un único sitio: la
  tabla de rutas de `apps/frontend/README.md`, que gana la fila de `/system-health`. El resto de
  documentos enlaza ahí en lugar de repetir cifras.
- **Corregir los textos desfasados**: `RF-095-002`, `RF-091-003`, `RF-091-004` y `RF-104-004` en el
  backlog; las filas de `/` en el mapa de carencias de JUP-097; el comentario de
  `apps/frontend/src/routes.tsx`; y una nota fechada en la evidencia de JUP-095 que remita a la guía
  de gobernanza.
- **Decidir y registrar qué pasa con el código que la épica deja sin uso**: la ruta puente
  `/overview-legacy` (su condición de retirada ya se cumple) y dos módulos que ya nadie importa. Se
  propone no retirarlos aquí y registrarlos como hallazgos con dueño (ver `design.md`, decisión 5).
- **Absorber la deuda documental** en commits propios: los 64 enlaces relativos rotos y las 42
  menciones a configuración local de herramientas de asistencia (ver `design.md`, decisión 6).
- **Revisar los 21 hallazgos abiertos de la épica**: cuáles cierra, cuáles sobreviven, con qué motivo
  y con qué dueño. Pedir a Alejandro y a Paris la confirmación que le falta a `RF-093-001`.
- **Ejecutar la batería completa desde la raíz** y dejar la evidencia en
  `docs/evidence/JUP-105-validation.md`, con lo que no se validó y por qué.

No se construye ninguna capacidad nueva, no se conecta ninguna pantalla a datos reales, no se rotulan
las pantallas de demostración y no se retira ninguna ruta, página, hook ni prueba.

## Capabilities

### New Capabilities

<!-- Ninguna. El cierre de la épica es documentación, evidencia y un endurecimiento de configuración;
     no introduce comportamiento que no esté ya cubierto por una spec vigente. -->

### Modified Capabilities

- `frontend-typescript-tooling`: el compilador deja de admitir JavaScript en el código fuente del
  frontend (antes lo admitía como convivencia temporal); la línea base de lint pasa de 49 violaciones
  heredadas a cero; y el requisito de arranque y build deja de exigir que ningún archivo fuente se
  haya migrado, que solo era cierto mientras duraba JUP-093.

## Impact

- **Configuración y código (sin cambio de comportamiento):** `apps/frontend/tsconfig.json` (un
  valor), el comentario de cabecera de `apps/frontend/src/routes.tsx` y un comentario de
  `apps/frontend/vite.config.ts`.
- **Documentación viva:** `apps/frontend/README.md`, `docs/spikes/frontend-migration.md`,
  `openspec/findings/backlog.md`, `docs/planning/JUP-097-frontend-data-gap-map.md` y el seguimiento
  de `docs/adr/ADR-0003-frontend-typescript.md`.
- **Registros históricos, solo enlaces y referencias:** 25 archivos de `openspec/changes/archive/`
  y 5 evidencias de `docs/evidence/` (JUP-013, 085, 093, 095 y 097). No se cambia ningún resultado,
  cifra ni veredicto.
- **Nuevo:** `docs/evidence/JUP-105-validation.md` y, al archivar, la spec
  `openspec/specs/frontend-typescript-tooling/spec.md` actualizada.
- **Solo lectura:** `package.json`, `turbo.json`, `pnpm-lock.yaml`, `.github/**`, `tools/**`,
  `apps/backend/**`, `apps/processor/**` y el resto de `apps/frontend/src/**` y sus pruebas.
- **CI:** sin cambios en los jobs. El check `Frontend type check` pasa a rechazar un import de
  JavaScript desde el código fuente.
- **Findings:** `RF-099-001` y `RF-099-004` pasan a `Fixed`; `RF-091-004` se propone cerrar;
  `RF-093-001` pasa a `Fixed` solo si confirman Alejandro y Paris. Se registran hallazgos nuevos
  `RF-105-NNN` para lo que la tarjeta decide no hacer.
- **Archivos compartidos:** el spike y el backlog los tocan casi todos los pull requests abiertos. Se
  editan al final, después de traer `develop`.
- **Pull requests que pueden cruzarse:** #66 (JUP-017) añade un panel a `/` y #69 (JUP-036) cambia la
  pantalla del asistente. Si alguno se fusiona antes del cierre, se repite el recuento de pantallas.
- **ADR:** no aplica uno nuevo. Se ejecuta la decisión 2 de ADR-0003, ya aceptada (ver `design.md`,
  decisión 9).

## Human Approval

- Change: jup-105-close-frontend-migration
- Approval type: pre-code
- Decision: approved
- Approver: Victor
- Date: 2026-10-08
- Carril: light
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Scope adjustment approved: la tarjeta dejaba dos decisiones para este gate y la verificación contra
  el código (2026-10-08, `develop` en `ff2ea6b`) añadió una tercera. **Alcance 5 de la tarjeta:** no
  se retira `/overview-legacy` ni los módulos sin uso; se registran como hallazgos. **Alcance 7:** la
  deuda documental de `RF-099-001` y `RF-099-004` se absorbe aquí, en commits propios. **Añadido al
  proponer, fuera de la tarjeta:** la spec vigente `frontend-typescript-tooling` se pone al día en
  tres requisitos, porque uno contradice el endurecimiento de `allowJs` y los otros dos describen el
  estado de JUP-093. También se incorporan al alcance el segundo módulo sin uso
  (`src/hooks/useCostKpis.ts`), el estado desfasado de JUP-103 en el spike y la frase desfasada de
  `RF-104-004`.
- Decisions approved: se aprueban las once decisiones del `design.md`. (1) **`allowJs` pasa a
  `false`** cambiando solo ese valor, con un control positivo; no se añade test guardián. (2) **La
  spec se corrige en tres requisitos**, no solo en el del compilador: dos se retiran y se sustituyen
  y el de lint se modifica en el sitio, por exigencia de `openspec validate`. (3) **El recuento de
  pantallas vive en la tabla de rutas de `apps/frontend/README.md`**; los demás documentos enlazan.
  (4) **Lo vivo se corrige y lo histórico se anota** con nota fechada. (5) **`/overview-legacy` y los
  dos módulos sin uso no se retiran**: `RF-105-001` y `RF-105-002`; solo se corrige el comentario de
  `routes.tsx`. (6) **La deuda documental se absorbe**: guion de enlaces de un solo uso, sin
  versionar como herramienta y con su texto en la evidencia; menciones sustituidas con las
  equivalencias de JUP-099; en los registros archivados cambia la referencia, nunca un resultado; la
  falta de comprobación automática queda como `RF-105-003`. (7) **Disposición de los 21 hallazgos**:
  `RF-099-001` y `RF-099-004` a `Fixed`; `RF-091-004` a `Fixed` tras comprobarlo en el backend, con
  el cálculo de ahorro trasladado a `RF-091-003`; `RF-093-001` a `Fixed` solo si confirman Alejandro
  y Paris; el resto sobrevive en `Open` con motivo y con quién da el siguiente paso. (8) **El estado
  final se declara en el punto 13 del spike.** (9) **No aplica ADR nuevo**; se anota el seguimiento
  de ADR-0003. (10) **Sin ciclo Red/Green**; la excepción se deja escrita en `review.md`. (11)
  **Orden de trabajo**: consulta al equipo primero, archivos compartidos al final.
- Constraints: en `apps/**` solo cambian `apps/frontend/tsconfig.json` (un valor), el comentario de
  cabecera de `apps/frontend/src/routes.tsx`, un comentario de `apps/frontend/vite.config.ts` y
  `apps/frontend/README.md`. Sin cambios en `package.json`, `turbo.json`, `pnpm-lock.yaml`,
  `.github/**` ni `tools/**`. No se retira ninguna ruta, página, hook ni prueba. El backlog y el
  spike se editan después de traer `develop`. No se cita configuración local de herramientas de
  asistencia en documentos versionados. No se da por validado nada que no se haya ejecutado, y la
  evidencia lista lo que no se validó.
- Main risks: (a) `allowJs: false` puede romper una herramienta que lee `tsconfig.json`; la prueba en
  seco solo cubre `tsc`. Si falla `lint`, `test` o `build`, se revierte y se registra por qué no
  puede endurecerse todavía. (b) El guion de enlaces puede cambiar más de lo debido: se revisa el
  diff completo y se compara el recuento (de 66 a 2). (c) Alejandro o Paris pueden no contestar a
  tiempo: `RF-093-001` se queda en `Open` con el nombre de quien falta. (d) `develop` puede avanzar
  (#66 o #69 fusionados): se repiten el recuento de pantallas, el recorrido de enlaces y la búsqueda
  de menciones. (e) Los hallazgos `RF-105-NNN` pueden quedarse sin tarjeta, como les pasó a los dos
  que esta tarjeta absorbe: se piden al líder al abrir el pull request.
- Required changes before execution: none
- Notes: última tarjeta de la épica de migración del frontend. Lleva `review.md` y
  `docs/evidence/JUP-105-validation.md`. Dos tareas no las puede ejecutar la herramienta de
  implementación: 1.2 (consulta a Alejandro y a Paris, la envía Victor) y 6.1 (traer `develop`).
  Queda una pregunta abierta que no cambia las tareas: qué persona figura como dueño de cada hallazgo
  que sobrevive; mientras no haya respuesta figura como «decisión de producto del equipo» o «tarjeta
  pedida», porque Trello es la fuente de verdad de los responsables.
