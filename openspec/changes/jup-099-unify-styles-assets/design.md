JUP: JUP-099 — ADR aplicables: [ADR-0003](../../../docs/adr/ADR-0003-frontend-typescript.md)
(TypeScript strict), [ADR-0004](../../../docs/adr/ADR-0004-frontend-shadcn-ui.md) (shadcn/ui). ADR
nuevo propuesto: `docs/adr/ADR-0010-frontend-color-tokens.md` (decisión 8).

## Context

Motivación e inventario en `proposal.md` (Why). Hechos del código, verificados sobre `688fe2d`, que
condicionan el enfoque:

- **Tailwind v4 compila los tokens en utilidades.** `theme.css` declara variables CSS y las expone
  en `@theme inline` como `--color-*`, así que `bg-card` o `text-muted-foreground/20` funcionan con
  modificador de opacidad (Tailwind genera `color-mix(in oklab, …)`, igual que con la paleta propia).
- **Los colores actuales vienen de dos paletas de Tailwind distintas.** Las utilidades
  (`text-slate-400`) usan la paleta v4 en `oklch`; los hexadecimales de las gráficas (`#94a3b8`,
  `#10b981`, `#ef4444`, `#64748b`) son la paleta v3 del origen. **No son el mismo color**: por
  ejemplo, `slate-400` v4 es `oklch(70.4% 0.04 256.788)` y `#94a3b8` es el `slate-400` de v3. Hoy
  conviven en pantalla y se distinguen a simple vista solo con esfuerzo, pero un diff de píxeles sí
  los separa.
- **Recharts recibe colores como atributos o como objetos de estilo** (`stroke`, `fill`,
  `contentStyle`). Ambos aceptan `var(--…)`: los atributos de presentación SVG admiten variables CSS
  en los navegadores soportados, y `contentStyle` es un `style` en línea.
- **`ExportButton` genera un documento HTML independiente** para imprimir a PDF, con su propio
  `<style>`. Ese documento se abre en otra ventana y no carga `theme.css`.
- **Los 6 primitivos de `src/components/ui/` no tienen consumidor en pantallas** (solo sus tests).
  `select.tsx` usa tres variantes `dark:` (`dark:bg-input/30`, `dark:hover:bg-input/50`,
  `dark:aria-invalid:ring-destructive/40`); `dialog.tsx` usa `bg-black/50` para el velo.
- **`@layer base` aplica `bg-background text-foreground` a `body` y `border-border` a `*`.** Hoy
  esos valores son los grises de shadcn; cambiar los tokens cambia el fondo del `body` y el color de
  borde por defecto allí donde una pantalla no los fije.
- **Ningún test comprueba clases de color.** La suite actual no debería cambiar con la migración; lo
  que protege el resultado son los tests nuevos de la decisión 5 y la comparación visual.
- **`index-html-dark-scope.test.ts` (JUP-095) exige `class="dark"`** y está protegido contra edición
  en el entorno local: cambiarlo requiere autorización explícita de Victor.

## Goals / Non-Goals

**Goals:**

- Que cada color de la interfaz tenga una única definición y un nombre por su función.
- Que el resultado sea **idéntico en píxeles** salvo diferencias explicadas una a una.
- Que la regresión (un hexadecimal o `text-red-400` nuevo) la detecte la batería de pruebas, no la
  revisión humana.

**Non-Goals:**

- Consolidar tonos parecidos (`slate-400` v3/v4, `green-400`/`emerald-400`). Es rediseño: se
  registra como candidato para una tarjeta propia, no se hace aquí.
- Preparar un modo claro más allá de lo que da gratis tener los colores en tokens.
- Automatizar la comparación visual en CI (decisión 6).

## Decisions

### 1. Los tokens de shadcn toman los valores reales; solo se añaden los que faltan

Se reutilizan los nombres semánticos que ya existen en `theme.css` y que consumen los primitivos
(`background`, `foreground`, `card`, `popover`, `primary`, `accent`, `muted`, `muted-foreground`,
`border`, `input`, `ring`, `destructive`), con los valores de la aplicación. Lo que la interfaz usa y
shadcn no nombra se añade con nombres de función, no de color:

| Token | Valor (exacto, el que sustituye) | Sustituye a | Uso |
|---|---|---|---|
| `background` | `#0f1419` | `[#0f1419]` | fondo de página |
| `card`, `popover` | `#1a1f2e` | `[#1a1f2e]` | tarjetas, menús, tooltip de gráficas |
| `accent` | `#232834` | `[#232834]` | fin de degradado de tarjeta, `hover` |
| `border`, `input`, `muted` | `#2d3748` | `[#2d3748]` | bordes, separadores, rejilla de gráficas, pistas de progreso |
| `foreground` (y `*-foreground` de card/popover/primary/accent) | `#ffffff` | `white`, `#fff` | texto principal |
| `muted-foreground` | `slate-400` v4 | `slate-400` | texto secundario |
| `subtle-foreground` | `slate-300` v4 | `slate-300` | texto intermedio |
| `neutral` | `slate-500` v4 | `slate-500` | texto tenue, insignia neutra |
| `primary`, `ring` | `#0078d4` | `[#0078d4]` | marca, foco, relleno de área |
| `highlight` | `#00bcf2` | `[#00bcf2]` | navegación activa, fin de degradado de marca, líneas |
| `success` / `success-tint` / `success-foreground` | `green-400` / `green-500` / `green-300` v4 | `green-*` | texto o icono / fondo y borde traslúcido, barra / texto sobre fondo traslúcido |
| `danger` / `danger-tint` / `danger-foreground` | `red-400` / `red-500` / `red-300` v4 | `red-*` | ídem; `destructive` = `danger-tint` |
| `info` / `info-tint` / `info-foreground` | `blue-400` / `blue-500` / `blue-300` v4 | `blue-*` | ídem; también el brillo `shadow-blue-500/*` |
| `warning` / `warning-tint` / `warning-foreground` | `amber-400` / `yellow-500` / `yellow-300` v4 | `amber-400`, `yellow-*` | aviso de sesión, tono cálido, severidad media |
| `attention-tint` / `attention-foreground` | `orange-500` / `orange-300` v4 | `orange-*` | estado "Investigando", proveedor AWS |
| `positive` | `emerald-400` v4 | `emerald-400` | tono de éxito de `MetricCard` |
| `chart-1` … `chart-5` | `#3b82f6`, `#10b981`, `#f59e0b`, `#8b5cf6`, `#ff8c00` | hex de series | series de gráficas y datos demo |
| `chart-negative` | `#ef4444` | `#ef4444` | serie "pendiente"/"coste actual" |
| `chart-baseline` | `#64748b` | `#64748b` | series de objetivo/patrón (discontinuas) |
| `chart-axis` | `#94a3b8` | `#94a3b8` | ejes y etiquetas de gráficas |

Los valores "v4" se copian literalmente de `tailwindcss/theme.css` (4.3.3) al escribir el token; no
se referencian las variables de la paleta de Tailwind, para que el tema no dependa de ella. Cuando
dos funciones comparten valor (`card`/`popover`, `border`/`input`/`muted`), cada token se define
una vez y el alias se escribe como `var(--otro)`. Los nombres son vinculantes salvo colisión técnica
descubierta al implementar, que se registra en `review.md`.

**Ajustes hechos en el Green (grupo 4), sin cambio de valores:** (a) `card-foreground` **no se
define**: ningún primitivo ni pantalla lo consume y el test de consumidores exige uno por token;
`secondary*`, `destructive-foreground`, `sidebar-*` y `switch-background` tampoco. (b) `border` es la
definición literal y `muted` e `input` son alias de `var(--border)`, porque `border` lo consume la
capa base y así retirar `muted` (si acaba sin consumidor) no arrastra a los otros dos. (c) Los
alias de `*-foreground` apuntan a `var(--foreground)`. (d) Cambiar el tema tiene tres efectos
visuales inevitables sobre lo que no lleva color propio, medidos en la captura del grupo 4 (ver
`review.md`): el fondo del `body` pasa de `#0a0a0a` a `#0f1419`; los iconos que heredan el color del
texto pasan de `#fafafa` (`oklch(0.985)`) a `#ffffff`; y el borde por defecto de la capa base pasa
de `#262626` a `#2d3748`.

`#8884d8` (`fill` por defecto del `Pie` de `ExecutiveCostDashboard`) queda oculto por los `Cell`
con color propio. Se elimina si la comparación visual confirma que no se pinta; si se pinta, se
asigna a un `chart-*`. **Resuelto en el grupo 7:** se eliminó el atributo y la comparación de las
34 capturas (incluidas las del `Pie`) da 0 píxeles reales de diferencia: no se pintaba.

- **Alternativa descartada: espacio de nombres propio junto al de shadcn** (`--app-*`). Dejaría dos
  vocabularios de color en `theme.css` y los primitivos seguirían en otra paleta: es el problema que
  la tarjeta viene a cerrar.
- **Alternativa descartada: consolidar en una paleta reducida** (un solo gris secundario, un solo
  verde). Menos tokens, pero cambia píxeles en todas las pantallas: rediseño, fuera de alcance.

### 2. Una única paleta en `:root`; `dark:` se declara siempre activo

La aplicación solo tiene tema oscuro. Todos los tokens pasan a `:root`; se eliminan el bloque
`.dark` y los valores claros de shadcn (ningún consumidor: `index.html` siempre llevaba
`class="dark"`), y se retira `class="dark"` de `index.html`. Esto responde al criterio 7: el ámbito
explícito de JUP-095 deja de ser necesario porque la paleta ya no depende de ningún ancestro.

`@custom-variant dark` no se borra: se redefine como `@custom-variant dark (&);`, que hace que las
variantes `dark:` apliquen siempre. Así los primitivos de shadcn se conservan tal como los publica
el proyecto (ADR-0004: se copian, no se reescriben) y un primitivo futuro copiado con variantes
`dark:` se comporta bien sin editarlo. Sin esa línea, Tailwind v4 interpretaría `dark:` como
`prefers-color-scheme` y el `select` cambiaría según el sistema operativo.

- **Alternativa descartada: conservar `:root` claro + `.dark`** con la paleta real en `.dark`.
  Mantiene ~35 valores sin consumidor (criterio 5) y un apaño de ámbito que la tarjeta pide revisar.
- **Alternativa descartada: quitar las variantes `dark:` de `select.tsx`.** Funciona, pero obliga a
  editar cada primitivo copiado en el futuro.

### 3. Tokens sin consumidor se retiran

Tras migrar, se retiran los tokens sin ninguna utilidad que los consuma en `src/`: los 8
`sidebar-*` (no hay barra lateral de shadcn), `switch-background` (no hay `switch`),
`secondary`/`secondary-foreground`, `destructive-foreground` y `accent-foreground` si ningún
primitivo ni pantalla los usa, y los `chart-*` que resulten sin serie. Los tokens no cromáticos
(`--radius`, `--font-size`, pesos de fuente) no entran en este criterio y se conservan. El test de la
decisión 5 lo comprueba de forma automática.

**Corrección durante el Red (grupo 3):** la primera redacción de esta decisión retiraba también
`input-background`. Es un error: `src/components/ui/select.tsx` lo consume (`bg-input-background`),
y la decisión 2 prohíbe editar los primitivos copiados. Se **conserva** con su valor actual
(`#f3f3f5`). No tiene efecto visible: con `@custom-variant dark (&)` la variante `dark:bg-input/30`
del mismo primitivo siempre aplica y prevalece, y el `Select` no lo usa ninguna pantalla todavía.

### 4. Cómo se escribe cada forma de uso

- Clases arbitrarias → utilidad de token: `bg-[#1a1f2e]` → `bg-card`,
  `from-[#1a1f2e] to-[#232834]` → `from-card to-accent`, `bg-[#0078d4]/10` → `bg-primary/10`,
  `shadow-blue-500/30` → `shadow-info-tint/30`.
- Utilidades de paleta → utilidad de token: `text-slate-400` → `text-muted-foreground`,
  `bg-red-500/20 text-red-300 border-red-500/30` → `bg-danger-tint/20 text-danger-foreground
  border-danger-tint/30`.
- Atributos de Recharts y `contentStyle` → `var(--…)` con el nombre de la variable de `:root`
  (`stroke="var(--chart-axis)"`). El `contentStyle` repetido en 9 gráficas se extrae a una constante
  compartida para no repetir 9 veces el mismo objeto.
- Datos demo (`src/data/demo/executiveCostDashboard.ts`) → `var(--chart-N)`.
- Mapas cerrados de clases (`VALUE_TONE_CLASSES` de `MetricCard`) se conservan como mapas cerrados:
  Tailwind no detecta clases construidas por interpolación.
- **Descubierto en el grupo 7: cuatro pantallas de demostración interpolaban clases**
  (`text-${color}-400`, `bg-${color}-500/20 border-${color}-500/30`). Tailwind no las detecta y solo
  se generaban por coincidencia, porque el literal completo (`text-blue-400`, `bg-red-500/20`…)
  aparecía en otra línea de `src/`. Al migrar esos literales a tokens, las clases interpoladas habrían
  dejado de generarse y las pantallas habrían cambiado de aspecto sin que ningún test lo viera. Se
  sustituyen por **mapas cerrados de cadenas completas** (`Record<string, string>`) en cada página.
  Los tonos que antes no generaban clase (`purple` en todos los casos y `orange` en el texto de
  iconos y valores) siguen sin ella, para que el resultado sea idéntico; ver `RF-099-002`. La
  constante compartida del tooltip vive en `src/components/chartTheme.ts` y se usa en las 9 gráficas.

### 5. Dos tests estáticos protegen el resultado

Siguiendo el patrón de `index-html-dark-scope.test.ts` (leer archivos con `node:fs`, sin renderizar):

- **Guardián de colores** (`src/test/color-tokens.guard.test.ts`): recorre `src/**/*.tsx` y
  `src/data/**/*.ts` (sin tests) y falla si encuentra un hexadecimal de color o una utilidad de la
  paleta de Tailwind (`(bg|text|border|from|to|via|shadow|ring|fill|stroke|divide|outline)-(slate|
  gray|…|white|black)`), salvo lo que figure en una lista de excepciones con `{ archivo, valor,
  motivo }`. Un caso por archivo (`it.each`), para que cada grupo de migración ponga en verde sus
  archivos y el mensaje de fallo diga archivo y valor. Excepciones previstas: el `<style>` del
  documento de exportación de `ExportButton` (`#1e40af`, `#ddd`), que no carga `theme.css`, y el
  velo `bg-black/50` de `src/components/ui/dialog.tsx`, que se conserva tal como lo publica shadcn/ui
  por la misma razón que la decisión 2 (los primitivos se copian, no se reescriben).
- **Contrato del tema** (`src/test/theme-palette.test.ts`, sustituye a
  `index-html-dark-scope.test.ts`): `theme.css` no tiene bloque `.dark`, cada token de color se
  define una sola vez, cada `var(--x)` de `@theme inline` apunta a un token definido, cada
  `--color-*` expuesto tiene al menos un consumidor en `src/` (decisión 3), y el `<html>` de
  `index.html` no depende de una clase de tema.

**Mutación.** El cambio de producto son literales de clase y valores CSS; ninguna prueba comprueba
clases, así que los mutantes `StringLiteral` de Stryker sobre esos archivos sobrevivirían por
construcción y el porcentaje no mediría nada útil. Se documenta como excepción en `review.md`: la
protección real son los dos tests estáticos (su Red demuestra que detectan los literales actuales)
y la comparación visual. No se afirma cobertura de mutación sobre este cambio.

### 6. Comparación visual antes/después con Playwright efímero

Criterio 4 y requisito "La unificación de colores no altera el aspecto". Se capturan las 9
pantallas (las 8 del armazón y `/login`, más el aviso de sesión expirada) **antes de tocar ningún
archivo de producto**, y otra vez al terminar, con el mismo guion:

- Build de producción servido con `vite preview`; Chromium de Playwright, viewport fijo
  1440×900, API simulada con `page.route` a partir de los datos de `tests/fixtures.ts`, espera fija
  tras la carga para que terminen las animaciones de Recharts.
- Comparación con `pixelmatch`, umbral 0; se registra el número de píxeles distintos por pantalla y
  se explica cada diferencia no nula. **Precisión hecha en el grupo 5:** dos pasadas del MISMO build
  difieren en unos pocos píxeles (medido: ≤ 15 por escenario, en `assistant` e `ingest-success`),
  siempre de **1 nivel de canal** sobre píxeles de degradado, es decir, ruido del rasterizador y no
  un cambio. Por eso `compare.mjs` separa los píxeles con algún canal distinto en **2 o más
  niveles** (`reales`) de los de 1 nivel. Criterio de "sin regresión": **0 reales** y no más de 50
  píxeles de 1 nivel por escenario. Un cambio de color de verdad (un token equivocado, un tono
  desplazado) afecta a áreas enteras y a más de 1 nivel, no a una decena de píxeles.
  **Matiz añadido en el grupo 7:** ese umbral solo describe el ruido **aleatorio**, el que cambia
  entre pasadas del mismo build (`ingest-success`: 7, 24 y 31 px). Una diferencia de 1 nivel que se
  **repite igual** en cada pasada (misma pareja de builds, mismas coordenadas) no es ruido, aunque
  supere o no los 50 px: es sistemática y se explica y acepta una a una. Se distingue capturando cada
  build dos veces (mismo build = 0, o pocos px cambiantes; builds distintos = siempre el mismo
  número). Caso real en el grupo 7: `RecommendationsPanel` da 1 410 px de 1 nivel de forma
  reproducible; ver `review.md`.
- Los escenarios pasan de 14 a **34**: 6 añadidos en el grupo 5 (carga y error del bootstrap de
  tenants, carga y error del resumen, éxito de ingesta, error de envío del asistente), 5 en el grupo 6
  (lista de conversaciones vacía, error al crear y las tres ramas "sin tenant") y 9 en el grupo 7
  (**tooltips de Recharts**, abiertos pasando el ratón por el centro de cada gráfica; el
  `contentStyle` solo se pinta al hacer hover).
- Playwright y `pixelmatch` se instalan en un proyecto temporal fuera del repositorio, como hizo
  JUP-095; no entran en `package.json`. El guion completo se copia en
  `docs/evidence/JUP-099-validation.md` para que cualquiera lo reproduzca. Las capturas no se
  commitean.
- **Demostración de propagación (criterio 2):** con el build final, se cambia temporalmente
  `--primary` a un valor llamativo, se recaptura y se registra qué pantallas cambian; después se
  revierte. Ningún archivo de pantalla se toca en la demostración.

- **Alternativa descartada: pruebas de regresión visual en CI.** Exige añadir Playwright,
  navegadores y capturas de referencia versionadas: es infraestructura de equipo, candidata a
  JUP-102 (E2E), no a esta tarjeta.
- **Alternativa descartada: revisión a ojo pantalla por pantalla.** No detecta la deriva v3/v4 de
  la decisión 1, justo el tipo de cambio que un refactor de color puede introducir sin querer.

### 7. Licencias: `apps/frontend/ATTRIBUTIONS.md`

El origen incluía atribuciones de shadcn/ui (MIT) y de fotos de Unsplash. En este repositorio:

- **shadcn/ui sí aplica**: `src/components/ui/` contiene código copiado del proyecto, y la licencia
  MIT exige conservar el aviso de copyright en las copias. Se crea `apps/frontend/ATTRIBUTIONS.md`
  con el aviso, verificando el texto contra la licencia publicada.
- **Unsplash no aplica**: no se portó ninguna imagen (no existe `src/assets` ni `public/`).
- **Fuentes**: ninguna (no hay `@font-face` ni archivos de fuente; `fonts.css` estaba vacío).
- **Iconos y dependencias** (`lucide-react`, Radix, Recharts): se consumen como paquetes npm, que
  llevan su propia licencia; no se copia su código. Se menciona en el archivo para dejar escrito
  por qué no llevan atribución propia.

### 8. ADR-0010 para la convención de tokens de color

La regla "ningún color literal en pantallas; cada color es un token con nombre de función; paleta
única en `:root`" obliga a todas las tarjetas futuras que toquen el frontend y cambia cómo se copian
primitivos de shadcn (decisión 2). Es un patrón compartido que afecta a trabajo futuro, uno de los
supuestos de `docs/adr/README.md`. Se redacta `ADR-0010-frontend-color-tokens.md` en estado
`Proposed` durante la revisión, enlazado desde aquí y desde ADR-0004.

### 9. El arrastre de JUP-098 va en commits de documentación separados

Ver `proposal.md`. Tres criterios de redacción:

- **B:** Stryker se documenta con la invocación sin archivo de configuración verificada el
  2026-09-29 (`--mutate`, `--testRunner vitest`, `--plugins`, `--coverageAnalysis perTest`); el
  umbral 80 se describe como criterio de lectura del resultado, porque no tiene opción de línea de
  comandos. El comprobador local de DoD se sustituye por la lista real
  (`corepack pnpm --filter @finops/frontend lint|typecheck|test|build` y
  `corepack pnpm jup:cleanup:check`). Ninguna ruta de configuración local queda en documentación
  versionada.
- **C (comentarios de tests):** se reescriben los 10 comentarios con redacción neutral ("el test
  estaba protegido contra edición en el entorno local"), sin tocar aserciones ni código de test.
  Requiere desbloquear archivos commiteados con autorización de Victor.
- **A:** `RF-098-004` se registra sin ninguna afirmación sobre CI (la nota de que "los tests del
  frontend no corren en CI" se descartó como malentendido).

## Risks / Trade-offs

- [El fondo de `body` y el borde por defecto de `*` cambian al cambiar `background`/`border`] →
  la comparación visual lo detecta; si alguna pantalla depende del fondo de `body`, la diferencia se
  explica y se acepta (el nuevo valor es el de la aplicación) o se corrige.
- [Recharts calcula colores internamente a partir de `fill`/`stroke` (p. ej. leyendas, puntos
  activos) y podría no resolver `var(--…)`] → la comparación visual lo detecta pantalla por
  pantalla; si ocurre, se lee el valor del token con `getComputedStyle` en un único punto y se
  registra como decisión en `review.md`.
- [Redondeo de `color-mix` distinto entre hex en clase arbitraria y variable] → diferencias de 1
  unidad por canal; se aceptan si `pixelmatch` las marca solo con umbral 0 y se documentan.
- [Animaciones de Recharts introducen ruido en las capturas] → espera fija y mismo guion antes y
  después; si persiste, se captura con animación desactivada en ambas pasadas.
- [Los tokens `v4` duplican a mano valores de Tailwind] → si una actualización de Tailwind cambia su
  paleta, la aplicación no cambia (es lo deseado); queda escrito en ADR-0010.
- [30 tokens son más de los que "necesita" una paleta limpia] → es el precio de no rediseñar; la
  consolidación queda propuesta como tarjeta propia en `review.md`.
- [Editar tests protegidos (JUP-095 y comentarios)] → solo con autorización explícita, restaurando
  la protección al terminar y registrándolo en `review.md`.

## Migration Plan

Sin despliegue ni migración de datos. Orden de implementación en `tasks.md`: capturas de referencia
antes de cualquier cambio de producto; tests en Red; tema; migración por grupos de archivos;
capturas finales y demostración de propagación; licencias y ADR; arrastre de JUP-098 en commits de
documentación propios. Rollback: revertir los commits de la rama; ningún otro paquete depende de
estos archivos.
