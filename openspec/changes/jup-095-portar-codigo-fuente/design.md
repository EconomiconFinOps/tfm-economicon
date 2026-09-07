JUP: JUP-095

## Context

Ver [proposal.md](proposal.md) — Why. Aquí solo el estado verificado que condiciona el enfoque.

**Decisiones heredadas vinculantes.** Esta tarjeta **no reabre** ninguna de las dos:

- [ADR-0003](../../../docs/adr/ADR-0003-frontend-typescript.md) (`Accepted`, JUP-092): `strict: true`,
  `allowJs: true` mientras dure la migración, type-check obligatorio en CI, `tsconfig` local al
  paquete. Su sección de seguimiento asigna **explícitamente a esta tarjeta** la migración a `.tsx` de
  los archivos hoy señalados por `react/prop-types`.
- [ADR-0004](../../../docs/adr/ADR-0004-frontend-shadcn-ui.md) (`Accepted`, JUP-094): se adopta
  shadcn/ui con 6 primitivos Radix, y **copiar el código de cada componente a `src/components/ui/` es
  trabajo de esta fase, componente por componente, solo cuando la pantalla que lo necesita se
  construye**.

El spike ([docs/spikes/frontend-migration.md](../../../docs/spikes/frontend-migration.md), decisión 1)
exige que toda tarjeta de F2 y F3 enlace ADR-0003 desde su `design.md`; ADR-0004 añade la misma
convención para las tarjetas que usen sus primitivos. Este documento cumple ambas.

**Punto de partida del destino** (tras el merge de JUP-094, `278769c`):

- `src/**`: 14 archivos, 11 `.jsx` y 3 `.js`. Línea base de lint: **49 violaciones exactas** de
  `react/prop-types` en 9 archivos (`RF-082-002`, `Open`).
- `vite.config.ts` declara únicamente `plugins: [react()]`: **sin plugin de Tailwind y sin alias**.
- `tsconfig.json`: `strict: true`, `allowJs: true`, `checkJs: false`, `types: []`, **sin `paths`**.
- `package.json`: `"test": "echo \"No frontend tests configured yet\""`.
- CI (`.github/workflows/ci.yml`) tiene 7 comprobaciones obligatorias, entre ellas *Frontend build* y
  *Frontend type check*. **No existe ninguna que ejecute pruebas del frontend**, y el lint sigue
  fuera por la línea base heredada (`docs/governance/github-branch-protection.md`).

**Hechos verificados sobre el origen en esta HU** (`../Economicon/frontend`, commit `1fe0030`), no
deducidos del inventario:

- El grafo de imports de las pantallas es mínimo: los 8 `.tsx` vivos importan **solo** `react`,
  `react-router`, `lucide-react`, `recharts` y `./ExportButton`. Cero imports de `ui/`, cero del alias
  `@/`, cero de `figma:asset/`.
- **`figma/ImageWithFallback.tsx` no lo importa nadie**, tampoco desde `ui/`: es código muerto igual
  que los 48 archivos de `ui/`. El conjunto realmente portable son **8 archivos**: 5 dashboards,
  `Layout`, `ExportButton` y `routes.tsx` (más `App.tsx` y `main.tsx`, de 5 y 6 líneas, que no se
  portan sino que se reconcilian con los del destino).
- `ExportButton` lo consumen los 5 dashboards (uno por pantalla, con `data` y `filename`).
- `vite.config.ts` del origen trae un plugin `figmaAssetResolver` que resuelve `figma:asset/` contra
  `src/assets` — carpeta que **no existe** en el origen — y un `assetsInclude` de `.svg`/`.csv` sin
  consumidor. `postcss.config.mjs` es un stub vacío que el propio comentario declara innecesario con
  el plugin de Tailwind.
- `src/styles/`: `index.css` (3 líneas) importa `fonts.css` (**vacío**), `tailwind.css` (4 líneas) y
  `theme.css` (181 líneas). `theme.css` define los tokens de shadcn con `:root` **en claro**
  (`--background: #ffffff`) y un bloque `.dark` alternativo, más `@theme inline` y `@layer base`.
- **Ninguna pantalla del origen aplica la clase `dark`**: el `Layout` fija el tema oscuro con valores
  hexadecimales arbitrarios de Tailwind (`bg-[#0f1419]`, `border-[#2d3748]`…), sin consumir los
  tokens. Los tokens solo los consumirían los componentes de shadcn que se copien.
- El `index.html` del origen titula `Plataforma FinOps automatizada (copia)` y añade un `<style>`
  inline de altura completa; el destino titula `FinOps Control Tower`, que la línea base de JUP-090
  manda conservar.

## Goals / Non-Goals

**Goals:**

- Dejar la aplicación navegando por rutas reales sobre las pantallas del origen **sin perder ninguna
  capacidad del destino**, para que JUP-096 y JUP-097 reconcilien datos y auth sobre una UI que ya
  existe.
- Que cada slice deje la aplicación arrancable, de modo que un fallo se atribuya al slice que lo
  introdujo y no a un merge acumulado.
- Cerrar la excepción al ciclo Red/Green que arrastran JUP-093 y JUP-094.

**Non-Goals (además de los de la propuesta):**

- **No se corrige el desajuste de datos del origen.** Las pantallas migradas siguen mostrando datos de
  demostración; conectarlas depende de `RF-091-003`, que es decisión de épica.
- **No se rediseña la UI del destino.** Login, ingesta y asistente se reconstruyen sobre el sistema de
  estilos nuevo conservando su comportamiento, no su aspecto.
- **No se copian los primitivos de `ui/` que ninguna pantalla use todavía**, aunque ADR-0004 haya
  instalado su dependencia: la propia decisión ordena copiarlos uno a uno cuando aparece el consumidor.
- **No se toca el `Dockerfile` ni `docker-compose.yml`** (F4), ni el guion E2E automatizado (F5).

## Decisions

### 1. Frontera con la lógica del destino: entra presentación y enrutado, no datos ni sesión

`src/services/api.js`, `src/hooks/useDashboardData.js` y la lógica de sesión/tenant/logout se
preservan **verbatim**. Solo cambian de extensión si el enrutado obliga a tocarlas, y en ese caso el
cambio es de tipado, nunca de comportamiento.

*Por qué:* el spike separó deliberadamente "reemplazar el código" de "reconciliar la capa API" y
"reconciliar auth/tenant" en tres tarjetas. Si esta abre la lógica, JUP-096 y JUP-097 se quedan sin
alcance propio y la migración vuelve a ser el *big bang* que el spike prohíbe. Además `api.js` es hoy
la **única** capa HTTP del monorepo y el único punto donde viven `Authorization` y `X-Tenant-Id`:
tocarla aquí mezclaría un fallo de enrutado con uno de contrato.

*Alternativa considerada:* portar todo `src/**` de una vez, incluida la capa API. Descartada por lo
anterior y porque dejaría un único commit gigante imposible de revisar contra los criterios de paridad
de JUP-090.

### 2. Qué entra del origen y qué se deja fuera

Entran los **8 `.tsx` vivos** y las hojas de estilo. **No entran**, por carecer de consumidor
verificado: los 48 archivos de `ui/` salvo los primitivos que una pantalla use de verdad,
`figma/ImageWithFallback.tsx`, el plugin `figmaAssetResolver`, el `assetsInclude` de `.svg`/`.csv`,
`postcss.config.mjs` y `fonts.css` (vacío).

*Por qué:* es el mismo criterio con el que JUP-091 clasificó las dependencias y JUP-094 rechazó las 48
`DESCARTAR` — se porta lo que tiene consumidor, no lo que trae la carpeta. Arrastrar el resolutor de
`figma:asset` sería especialmente dañino: apunta a una carpeta inexistente y solo puede fallar en
silencio.

*Consecuencia sobre ADR-0004:* de los 6 primitivos instalados, en esta tarjeta se copian a
`src/components/ui/` únicamente los que las pantallas reconstruidas usen. Si al terminar alguno sigue
sin consumidor, se declara en `review.md` como peso muerto identificado, exactamente el riesgo que
ADR-0004 aceptó por escrito.

### 3. Mapa de rutas: el acceso queda fuera del armazón

Bajo el `Layout`: `/` (coste global), `/operational`, `/cuts`, `/anomalies`, `/recommendations` del
origen, más `/ingest` y `/assistant` del destino. `/login` se presenta **fuera** del `Layout`, y
`/overview-legacy` conserva temporalmente el resumen de facturación actual (decisión 6).

*Por qué el acceso fuera:* el `Layout` muestra navegación, identidad de sesión y selector de ámbito —
los tres carecen de sentido sin sesión. Es también la forma más barata de conservar el comportamiento
actual, en el que la aplicación presenta el acceso y nada más mientras no hay sesión.

*Alternativa considerada:* montar todo bajo el `Layout` y ocultar sus piezas cuando no hay sesión.
Descartada: mezcla la responsabilidad del armazón con la del control de acceso, que es de JUP-097.

### 4. Estilos: se adopta el sistema del origen y se fija el ámbito oscuro explícitamente

Entran `tailwind.css` y `theme.css`; se cablea `@tailwindcss/vite` en `vite.config.ts`. `main.css` se
retira en el **último** slice, cuando la aplicación ya renderiza sobre el sistema nuevo.

**Hay que aplicar el ámbito oscuro de forma explícita.** `theme.css` define `:root` en claro y `.dark`
como variante, y el origen nunca aplica esa clase porque sus pantallas no consumen los tokens: fijan
el color a mano. Los componentes de shadcn que se copien **sí** los consumen, así que sin declarar el
ámbito oscuro se renderizarían en claro sobre pantallas oscuras.

*Por qué así y no reescribiendo los tokens:* declarar el ámbito es una línea; reescribir `theme.css`
para que su `:root` sea oscuro toca 181 líneas de tokens que ninguna pantalla ejercita todavía, y ese
trabajo pertenece a JUP-098 (`unificar-estilos-assets`), que es quien unifica el sistema de verdad.
Aquí solo se garantiza que lo copiado se vea coherente.

### 5. Alias `@/`: se añade en `tsconfig.json` y en `vite.config.ts`

*Por qué:* los componentes de shadcn/ui se copian con sus imports `@/components/ui/...` y
`@/lib/utils`; es la convención del patrón que ADR-0004 adoptó. El destino no tiene alias hoy, y las
pantallas del origen tampoco lo usan, así que el alias entra **por** los componentes copiados, no por
el código portado. Debe declararse en los dos sitios: `paths` en `tsconfig.json` para que el
type-check lo resuelva, y `resolve.alias` en `vite.config.ts` para que lo resuelva el build. Declararlo
en uno solo produce el fallo clásico de "compila pero no arranca", o al revés.

*Alternativa considerada:* reescribir los imports de cada componente copiado a rutas relativas.
Descartada: rompe la convención de shadcn/ui y obliga a reeditar cada componente futuro.

### 6. El resumen de facturación actual sobrevive en `/overview-legacy`

*Por qué:* es hoy **la única pantalla que consume datos reales** (`GET /billing/summary` y
`GET /health` vía `useDashboardData`). El `index` del origen que ocupa su lugar solo muestra datos de
demostración, y conectarlo es JUP-096. Sin esta ruta puente, `develop` quedaría con el único dashboard
real degradado durante dos tarjetas, lo que contradice la regla de rollback del spike: no perder nada
verificable hasta que la validación E2E de F5 lo respalde.

*Coste y retirada:* una entrada de ruta. JUP-096 la elimina al conectar el nuevo Overview; queda
anotada como deuda con dueño y fecha de vencimiento, no como ruta permanente.

*Alternativa considerada:* conectar aquí mismo los dos únicos campos con contrato al `index` del
origen. Descartada: es exactamente el alcance de JUP-096 y rompería la decisión 1.

### 7. Runner de pruebas: Vitest + Testing Library, con job propio en CI

Se adopta **Vitest** con `@testing-library/react` y un entorno DOM, y el script `test` pasa a
ejecutarlo de verdad.

*Por qué Vitest:* es el runner que comparte configuración y cadena de transformación con Vite, ya
presente; cualquier otro obligaría a mantener una segunda tubería de build solo para pruebas.

*Por qué no requiere ADR:* no es un patrón transversal ni difícil de revertir — no ata el diseño del
código de producto, no cambia el modelo de build y sustituirlo sería reescribir invocaciones, no
arquitectura. Es la diferencia con ADR-0003 (que cambió el lenguaje de todo el frontend) y ADR-0004
(que ata el vocabulario de componentes de F3 y F5). Se registra aquí, que es donde
`docs/adr/README.md` deja las decisiones acotadas a una tarjeta.

*Por qué además un job en CI:* un runner que no corre en integración continua se pudre. Se añade el
job *Frontend tests* a `ci.yml` y **se promueve a comprobación obligatoria** en
`.github/rulesets/develop.json` y `main.json`, con su entrada en
`docs/governance/github-branch-protection.md`. Es el precedente literal de JUP-093, que añadió así
*Frontend type check* aplicando la decisión 3 de ADR-0003 ("de lo contrario `strict` es solo una
anotación decorativa"); el mismo razonamiento vale para unas pruebas que nadie ejecuta. Como entonces,
**versionar el ruleset no lo activa**: la activación remota es acción de administrador y se registra
como pendiente en `review.md`.

*Alternativa considerada:* job en CI sin promoverlo a obligatorio. Deja pasar PRs con pruebas en rojo
y reproduce la situación del lint, que lleva desde JUP-082 fuera de los checks obligatorios por una
deuda que nadie ha cerrado.

### 8. Orden de los slices, elegido para que cada uno arranque

`(1)` runner y primera prueba → `(2)` estilos y Tailwind cableados → `(3)` primitivos shadcn que
hagan falta → `(4)` componentes del origen y datos de demostración → `(5)` enrutado e injerto del
selector de ámbito y la sesión en el `Layout` → `(6)` `index.html` y entrypoint → `(7)` migración
`.tsx` restante y limpieza.

*Por qué este orden:* los estilos van antes que los componentes porque estos se apoyan en clases de
Tailwind y sin el plugin cableado renderizarían sin estilo, haciendo imposible distinguir "portado
mal" de "sin estilos". El enrutado va después de los componentes porque necesita destinos que montar.
La limpieza (`main.css`, `PlaceholderPage`) va la última porque es el punto sin retorno: hasta
entonces, revertir un slice devuelve la aplicación al estado anterior sin tocar nada más.

### 9. `strict: true` sobre código nunca verificado: prohibido silenciar

El código del origen entra bajo `strict` sin haber pasado nunca un type-check. Los errores se
resuelven **tipando**: prohibido `any` nuevo y `@ts-ignore`. Si el volumen desborda la tarjeta, se
aplica el criterio de escape que ADR-0003 ya fijó — se documenta el desbordamiento y se supersede el
ADR con uno nuevo, sin relajar la configuración en silencio ni por conveniencia local.

## Risks / Trade-offs

- **El volumen de errores de tipo del código del origen es desconocido hasta intentarlo** (riesgo que
  ADR-0003 declara como el que más puede obligar a revisar la decisión) → mitigación: el orden de
  slices lo expone pronto (slice 4, antes del enrutado) y las pantallas son pequeñas —unas 950 líneas
  entre las 8—, con un grafo de imports de solo cuatro librerías.
- **Injertar el selector de ámbito y la sesión en un `Layout` ajeno** puede degradar el flujo actual →
  mitigación: los escenarios de `frontend-navigation-shell` fijan como criterio que el ámbito
  sobreviva a la navegación y que el cierre de sesión devuelva al acceso; el recorrido de paridad de
  JUP-090 se repasa a mano antes de cerrar la tarjeta.
- **Los tokens de `theme.css` llegan en claro** y las pantallas fijan el color a mano → mitigación:
  decisión 4, ámbito oscuro declarado explícitamente; la unificación real es JUP-098.
- **Datos de demostración entran en la ruta de producto** → mitigación: aislados en un origen único y
  señalizado, y registrados como finding nuevo con dueño (JUP-096 y `RF-091-003`).
- **Promover *Frontend tests* a comprobación obligatoria puede bloquear PRs del equipo** si la suite
  es inestable → mitigación: la suite nace pequeña y determinista (render y enrutado, sin red); y como
  la activación remota es acción de administrador, hay una ventana natural para revisarla antes de que
  empiece a bloquear.
- **`/overview-legacy` puede quedarse para siempre** si JUP-096 no la retira → mitigación: se declara
  en `review.md` como deuda con dueño explícito y se enuncia en el alcance de JUP-096.

## Migration Plan

1. Slice 1: runner de pruebas, script `test` real, job de CI y ruleset; primera prueba en verde.
2. Slice 2: `@tailwindcss/vite` cableado, hojas del origen incorporadas, ámbito oscuro declarado,
   alias `@/` en `tsconfig.json` y `vite.config.ts`. `main.css` **sigue en su sitio**.
3. Slice 3: primitivos de shadcn/ui que las pantallas vayan a usar, copiados uno a uno.
4. Slice 4: los 8 `.tsx` del origen, con sus constantes extraídas al origen de datos de demostración.
5. Slice 5: enrutado con el mapa de la decisión 3 e injerto del selector de ámbito y la sesión en el
   `Layout`; retirada del `activeView`.
6. Slice 6: `index.html` (título del destino, `<div id="root">`) y entrypoint con ambos proveedores.
7. Slice 7: migración `.tsx` restante, retirada de `main.css` y `PlaceholderPage`, nueva línea base de
   lint registrada.

Tras cada slice: `typecheck`, `lint`, `test`, `build` y arranque, con parada y commit propuesto antes
de empezar el siguiente.

**Rollback:** cada slice es un commit revertible y ninguno destruye nada hasta el 7. Revertir la
tarjeta entera equivale a descartar la rama: `develop` conserva el scaffold actual intacto, tal como
exige la regla de rollback del spike, que prohíbe borrar el scaffold hasta la validación E2E de F5.

## Open Questions

- Ninguna que bloquee el arranque. La única incógnita real —cuántos errores de tipo trae el código del
  origen— no cambia ni las specs, ni el enfoque, ni el desglose de tareas: cambia el esfuerzo del
  slice 4, y ADR-0003 ya fija qué hacer si desborda (decisión 9).
