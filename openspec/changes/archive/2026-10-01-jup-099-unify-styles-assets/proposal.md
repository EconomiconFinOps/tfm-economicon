JUP: JUP-099
Trello: https://trello.com/c/WBnzwDHR/91-jup-099

## Why

JUP-095 retiró `main.css` y dejó el frontend sobre Tailwind v4 con `src/styles/theme.css`, pero la
unificación quedó a medias (su propio `design.md`: "reescribir los tokens es trabajo de la tarjeta de
estilos"). Verificado sobre `develop` (`688fe2d`) el 2026-09-29, hoy conviven **tres** fuentes de
color en la misma pantalla:

- **241 hexadecimales escritos a mano** en 14 archivos `.tsx` (169 como clases arbitrarias
  `bg-[#1a1f2e]`, 42 como `fill`/`stroke` de Recharts, 18 en objetos `contentStyle`, más el HTML de
  exportación) y 4 más en `src/data/demo/executiveCostDashboard.ts`. Solo 16 valores distintos:
  `#2d3748` aparece 68 veces, `#1a1f2e` 39, `#0078d4` 32.
- **229 utilidades de la paleta de Tailwind** escritas a mano en 16 archivos (`text-slate-400` ×66,
  `text-white` ×65, `text-red-400`, `bg-green-500/20`…), entre ellas el `text-amber-400` que añadió
  JUP-098.
- **Los tokens de `theme.css`**, que son el tema por defecto de shadcn/ui (grises neutros en `:root`
  claro y en `.dark`) y no reflejan la paleta real de la aplicación. Solo los consumen los 6
  primitivos de `src/components/ui/`, que **ninguna pantalla usa todavía**; por ellos JUP-095 fijó
  `class="dark"` en `index.html` como apaño (decisión 4 de su `design.md`).

Cambiar un color de marca exige hoy tocar 14 archivos, y el requisito vigente "La aplicación se
presenta bajo un único sistema de estilos" (`frontend-navigation-shell`) se incumple incluso en su
letra: `MetricCard`, `SectionCard` y `StatusPill` siguen citando `main.css` en comentarios. Es la
tarjeta más aislada de la épica y conviene cerrarla antes del E2E (JUP-102), que fotografiará las
pantallas.

## What Changes

- **Una sola paleta, en `theme.css`.** Los tokens semánticos que ya define shadcn/ui (`background`,
  `card`, `primary`, `muted-foreground`, `border`, `ring`…) toman los valores reales de la
  aplicación, y se añaden solo los que la interfaz necesita y shadcn no tiene (superficie elevada,
  acento de marca, estados de éxito/aviso/peligro/información y series de gráfico). Todos viven en
  `:root`: la aplicación solo tiene tema oscuro.
- **Se retira el ámbito oscuro explícito.** Desaparecen el bloque `.dark`, `@custom-variant dark` y
  `class="dark"` de `index.html`; el test de JUP-095 que lo exige se sustituye por uno que comprueba
  la paleta única. Queda registrado en `design.md` (criterio 7 de la tarjeta).
- **Las pantallas consumen solo tokens.** Los 241 hexadecimales y las 229 utilidades de paleta de
  las 9 pantallas (las 8 del armazón y el acceso), del `Layout`, de `SessionGate` y de los
  componentes compartidos pasan a clases de token (`bg-card`, `text-muted-foreground`,
  `border-border`…) o a `var(--…)` donde Recharts o un `style` exigen un valor. Excepciones
  justificadas una a una en `review.md` (p. ej. el HTML autónomo que genera `ExportButton` para
  imprimir, que no carga `theme.css`).
- **Un test guardián impide la regresión**: falla si un `.tsx` de `src/` vuelve a escribir un
  hexadecimal o una utilidad de paleta fuera de la lista de excepciones.
- **Refactor visual, no rediseño.** Cada token reproduce exactamente el valor que sustituye; no se
  consolidan tonos parecidos. Las 9 pantallas se comparan con capturas antes/después.
- **Tokens sin consumidor**: los que sigan sin uso tras la migración se retiran o se justifican.
- **Assets y licencias**: se crea `apps/frontend/ATTRIBUTIONS.md` con lo que aplica (el código de
  shadcn/ui copiado en `src/components/ui/`, MIT) y se registra por qué no aplican las fotos de
  Unsplash del origen ni fuentes o imágenes (no se portaron).
- **Referencias al sistema anterior**: se eliminan las menciones a `main.css` de los comentarios.
- **ADR nuevo** para la convención de tokens de color, que obliga a todas las tarjetas futuras.

**Arrastre de JUP-098** (acordado tras fusionar el PR #50; commits de documentación propios con
prefijo `JUP-099` citando JUP-098):

- **A.** Registrar `RF-098-004` en el backlog: tests que fallan por el límite de 1 s de
  `findBy`/`waitFor` con varias suites en paralelo o máquina cargada. Solo se registra; no se
  corrige. Sin ninguna afirmación sobre CI: la nota de revisión de que "los tests del frontend no
  corren en CI" se descartó como malentendido (2026-09-29).
- **B.** Sustituir las 9 referencias a configuración local del agente en
  `docs/evidence/JUP-098-validation.md` y en el `review.md` archivado de JUP-098 por comandos
  reproducibles desde el repositorio (Stryker sin archivo de configuración, lista real de comandos
  en lugar del comprobador local) y redacción neutral.
- **C (opcionales elegidos al proponer).** Corregir los 3 enlaces rotos por archivados antiguos (spike
  líneas 185 y 206; enlace a la review de JUP-085 en el backlog), eliminar la fila duplicada de
  `RF-090-003` y neutralizar los 10 comentarios de tests que citan el hook o la configuración local
  del harness. `RF-098-003` (JSON crudo en el error de login) **no** entra: cambia comportamiento de
  la capa de acceso, no presentación.

**Fuera de alcance:** rediseñar la interfaz; modo claro o conmutador de tema; sustituir shadcn/ui o
ampliar sus 6 primitivos (ADR-0004); backend y capa de datos; `RF-098-003`.

## Capabilities

### New Capabilities

_Ninguna._

### Modified Capabilities

- `frontend-navigation-shell`: se añaden requisitos a "un único sistema de estilos": los colores de
  la interfaz proceden solo de los tokens del tema (con excepciones declaradas), un cambio de token
  se propaga a todas las pantallas que lo usan, y el tema define una única paleta activa sin ámbito
  paralelo. El requisito vigente no cambia.

## Impact

- **Código de producto (frontend):** `src/styles/theme.css`, `index.html`, `src/layouts/Layout.tsx`,
  `src/layouts/SessionGate.tsx`, las 9 páginas de `src/pages/`, `src/components/{ExportButton,
  MetricCard,SectionCard,StatusPill}.tsx`, `src/data/demo/executiveCostDashboard.ts`. Los primitivos
  de `src/components/ui/` no cambian de código; sí de aspecto, porque sus tokens pasan a la paleta
  real.
- **Pruebas:** test guardián de colores nuevo; test de paleta única que sustituye a
  `src/test/index-html-dark-scope.test.ts` (commiteado y protegido: se edita con autorización);
  comentarios en 10 archivos de test (sin cambiar aserciones). Ninguna prueba actual comprueba
  clases de color, así que la suite existente no debería cambiar.
- **Documentación:** `docs/adr/ADR-0012-…` y su índice, `apps/frontend/ATTRIBUTIONS.md`,
  `apps/frontend/README.md` si describe estilos, `docs/spikes/frontend-migration.md`,
  `openspec/findings/backlog.md`, `docs/evidence/JUP-098-validation.md`, el `review.md` archivado de
  JUP-098 y `docs/evidence/JUP-099-validation.md`.
- **Backend, APIs, dependencias:** sin cambios. La verificación visual usa Playwright vía `dlx`, sin
  añadirlo a `package.json`.
- **ADR:** aplican ADR-0003 (TypeScript strict) y ADR-0004 (shadcn/ui); se propone ADR-0012.
- **Carril:** `standard` (el spike proponía `light`; con ~470 ocurrencias en 16 archivos y riesgo de
  regresión visual en 9 pantallas se eleva, como sugería la tarjeta).

## Human Approval

- Change: jup-099-unify-styles-assets
- Approval type: pre-code
- Decision: approved
- Approver: Victor
- Date: 2026-09-29
- Carril: standard
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Scope adjustment approved: el alcance se amplía respecto al criterio 1 de la tarjeta Trello, que
  solo exige retirar los hexadecimales. Se migran también las 229 utilidades de la paleta de
  Tailwind escritas a mano, porque sin ellas seguirían conviviendo dos sistemas de color (alcance 1
  de la tarjeta). El conteo de partida es 241 hexadecimales en 14 `.tsx` y 4 en `src/data/demo/`,
  no los 231 del 21/09. Del arrastre de JUP-098 entran A y B y, de los opcionales C, los 3 enlaces
  rotos, la fila duplicada de `RF-090-003` y los 10 comentarios de tests que citan el harness local;
  `RF-098-003` queda fuera por cambiar comportamiento de la capa de acceso.
- Decisions approved: se aprueban las nueve decisiones del `design.md`. (1) **Los tokens semánticos
  de shadcn toman los valores reales de la aplicación** y solo se añaden los que faltan, con nombre de
  función y valor exacto al que sustituyen (los `v4` copiados de `tailwindcss/theme.css` 4.3.3); no se
  consolidan tonos parecidos. (2) **Una única paleta en `:root`**: se retiran el bloque `.dark`, los
  valores claros de shadcn y `class="dark"` de `index.html`; `@custom-variant dark (&);` mantiene los
  primitivos tal como los publica shadcn/ui. (3) **Se retiran los tokens de color sin consumidor.**
  (4) Clases arbitrarias y de paleta pasan a utilidades de token; Recharts, `contentStyle` y datos
  demo usan `var(--…)`, con el estilo de tooltip en una constante compartida. (5) **Dos tests
  estáticos** (guardián de colores con excepciones declaradas y contrato del tema, que sustituye a
  `index-html-dark-scope.test.ts`); **sin mutación de Stryker** sobre la migración de clases, como
  excepción justificada y sin afirmar cobertura. (6) **Comparación visual antes/después** con
  Playwright y `pixelmatch` efímeros fuera del repositorio, umbral 0, referencia capturada antes de
  tocar producto y demostración de propagación con `--primary`. (7) `apps/frontend/ATTRIBUTIONS.md`
  con el aviso MIT de shadcn/ui; Unsplash, fuentes y dependencias npm no aplican. (8) **ADR-0010**
  para la convención de tokens de color, en `Proposed` durante la revisión. (9) El arrastre de
  JUP-098 va en commits de documentación propios, sin afirmar nada sobre CI hasta la respuesta de
  Lucía.
- Constraints: ningún archivo de `apps/backend/**` ni `apps/processor/**` en el diff; sin `any`
  nuevo ni `@ts-ignore` (ADR-0003); subconjunto de 6 primitivos sin cambios (ADR-0004); ciclo
  Red/Green por grupo con parada para commit; los tests protegidos (`index-html-dark-scope.test.ts`
  y los 10 con comentarios del harness) solo se editan con autorización explícita en cada tarea;
  ninguna ruta de configuración local del agente en documentación versionada.
