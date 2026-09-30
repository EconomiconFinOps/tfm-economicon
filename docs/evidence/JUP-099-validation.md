# Evidencia JUP-099 — Unificar el sistema de estilos y los assets del frontend

- Fecha: 2026-09-29.
- Trello: https://trello.com/c/WBnzwDHR/91-jup-099
- Rama: `feat/JUP-099-unify-styles-assets`.
- Base: `origin/develop` en `688fe2d93bb521c125e12231c29090f1f1829742`. `develop` ha avanzado un commit
  (`2efef1a`, solo documentación de OpenSpec) sin solape de archivos con esta rama: la simulación de
  fusión (`git merge-tree`) sale limpia.
- Estado verificado: `6060993` (14 commits propios, 46 archivos, +3 038 / −511).
- OpenSpec: [jup-099-unify-styles-assets](../../openspec/changes/jup-099-unify-styles-assets/) (activo; al
  archivarlo, corregir este enlace a `openspec/changes/archive/<fecha>-jup-099-unify-styles-assets/`).
- ADR: [ADR-0010](../adr/ADR-0010-frontend-color-tokens.md) (`Proposed`); aplican
  [ADR-0003](../adr/ADR-0003-frontend-typescript.md) y [ADR-0004](../adr/ADR-0004-frontend-shadcn-ui.md).
- Pull request: pendiente de abrir.
- CI de implementación: pendiente (pestaña Checks del PR).

## Fuentes verificadas

- `apps/frontend/src/styles/theme.css` de `688fe2d`: tema por defecto de shadcn (`:root` claro, bloque
  `.dark`, `@custom-variant dark (&:is(.dark *))`), 110 declaraciones de variable.
- Inventario de partida, con los comandos exactos en el `review.md` del change (§ Grupo 1): **241
  hexadecimales** en 14 `.tsx` (169 como clases arbitrarias, 42 en `fill`/`stroke` de Recharts, 18 en
  objetos `contentStyle`/`style`), 4 más en `src/data/demo/`, **229 utilidades de la paleta de Tailwind**
  en 16 archivos y 3 menciones a `main.css` en comentarios. El plan de la tarjeta hablaba de 231
  hexadecimales (conteo del 21/09): el número real era otro.
- `tailwindcss/theme.css` 4.3.3 (paleta v4, valores `oklch` copiados literalmente a los tokens).
- `LICENSE.md` de shadcn/ui, descargado con `curl` y comparado con `diff` contra el texto de
  `apps/frontend/ATTRIBUTIONS.md` (vacío). Licencias de las dependencias leídas de sus `package.json`.
- `index.html`, `src/components/ui/*.tsx`, `src/lib/utils.ts`, CSS generado por Vite (0 `@font-face`).
- Decisión 4 del `design.md` de JUP-095 (ámbito oscuro explícito) y la spec vigente
  `frontend-navigation-shell` ("La aplicación se presenta bajo un único sistema de estilos").
- Arrastre de JUP-098, verificado contra el código antes de tocarlo: las 9 referencias a configuración
  local en su evidencia y su `review.md` archivado, los 3 enlaces rotos y la fila duplicada de
  `RF-090-003` existían tal como decía la tarjeta.

## Trazabilidad con requisitos

Delta de la spec `frontend-navigation-shell` (se promueve al archivar):

| Requisito | Cómo se verifica |
| --- | --- |
| Los colores de la interfaz proceden solo de los tokens del tema | `src/test/color-tokens.guard.test.ts` (61 casos: 1 por archivo escaneado, 1 por excepción, 29 del detector, 1 de descubrimiento) |
| Un cambio de token se propaga a toda la interfaz | Demostración de propagación (§ Verificación visual): 2 tokens cambiados solo en `theme.css`, 34 de 34 escenarios cambian |
| El tema define una única paleta activa | `src/test/theme-palette.test.ts` casos (a) sin `.dark` y `@custom-variant` exacto, (b) tokens únicos, (e) `<html>` sin clase de tema |
| La unificación no altera el aspecto de las pantallas | 34 escenarios antes/después con Chromium real; 0 píxeles reales frente al estado con el tema nuevo; 4 diferencias frente al original, medidas y aceptadas |
| (vigente) Un único sistema de estilos, sin referencias al anterior | Búsqueda de `main.css` y clases del sistema anterior en `apps/frontend`: 0 resultados |

## Los 8 criterios de aceptación de la tarjeta, uno a uno

Comandos ejecutados el 2026-09-29 sobre `6060993`, desde `apps/frontend`.

| # | Criterio | Resultado | Evidencia |
| --- | --- | --- | --- |
| 1 | Buscar hexadecimales de color en `src/**/*.tsx` devuelve cero resultados en las pantallas portadas, o solo casos justificados uno a uno | **Cumplido.** Solo 3 líneas de un archivo, justificadas | `grep -rnE '#[0-9a-fA-F]{3,8}\b' src --include=*.tsx --include=*.ts` (sin tests) → `ExportButton.tsx:45,47,48` (`#1e40af` ×2, `#ddd`): el `<style>` del documento HTML autónomo que se abre para imprimir y no carga `theme.css`. Además una utilidad de paleta, `bg-black/50` en `ui/dialog.tsx` (primitivo de shadcn/ui copiado tal cual). Ambas son excepciones declaradas con motivo en el guardián y verificadas como no obsoletas |
| 2 | Un cambio en un token de `theme.css` se propaga a todas las pantallas que lo usan, demostrado con al menos un token | **Cumplido.** Con dos | `--primary` → `#ff00ff` y `--card` → `#3a003a`, **solo** en `theme.css` (restaurado, `md5` idéntico): cambian los 34 escenarios; `#ff00ff` exacto aparece justo donde hay un `bg-primary` sólido o un `var(--primary)` de Recharts; el estilo en línea de los tooltips sigue a `--card` |
| 3 | No queda ninguna referencia a `main.css` ni al sistema anterior, incluidos comentarios | **Cumplido** | `grep -rniE 'main\.css\|status-pill\|metric-card\|tone-'` sobre `apps/frontend` (sin tests) → 0. Eran 3 comentarios (`MetricCard`, `SectionCard`, `StatusPill`) |
| 4 | Las 8 pantallas renderizan sin regresión visual, verificado pantalla por pantalla y registrado en `review.md` | **Cumplido**, con 4 diferencias aceptadas por Victor | 34 escenarios (las 8 pantallas y `/login`, con sus estados de error, carga, "sin tenant" y tooltips). Frente al estado con el tema nuevo: 0 píxeles reales. Frente al original: cuatro causas medidas (§ Verificación visual) |
| 5 | Los tokens sin consumidor quedan retirados o justificados | **Cumplido** | 13 retirados (8 `sidebar-*`, `card-foreground`, `destructive-foreground`, `secondary`, `secondary-foreground`, `switch-background`); 110 → 92 declaraciones; el caso (d) de `theme-palette.test.ts` (110/110) y un análisis que ignora comentarios confirman 42 tokens, 0 sin consumo real; 11 con un solo consumidor, justificados |
| 6 | Existe `ATTRIBUTIONS.md` con las atribuciones que apliquen, o queda registrado por qué ninguna aplica | **Cumplido** | [`apps/frontend/ATTRIBUTIONS.md`](../../apps/frontend/ATTRIBUTIONS.md): aplica shadcn/ui (MIT, 5 primitivos + `cn`); registrado por qué no aplican Unsplash, fuentes ni las dependencias npm |
| 7 | La decisión sobre el ámbito oscuro explícito queda registrada en `design.md` | **Cumplido** | Decisión 2 del `design.md`: una única paleta en `:root`, sin `.dark` ni `class="dark"`; `@custom-variant dark (&);` (verificado compilando con Tailwind 4.3.3). `index.html` es `<html lang="en">`; en `theme.css` `.dark` solo aparece en el comentario de cabecera. Recogido también en ADR-0010 |
| 8 | lint, typecheck y build en verde; suite de pruebas sin regresión | **Cumplido** | § Validación ejecutada: lint 0, typecheck 0 (3 configs), build correcto, suite **431/431** (los 260 previos siguen en verde) |

## Decisiones

Resumen; el razonamiento completo y las alternativas están en el `design.md` del change y en ADR-0010.

- **Tokens semánticos de shadcn con los valores reales de la aplicación** y solo los tokens nuevos
  imprescindibles, con nombre de función y el valor exacto que sustituyen; no se consolidan tonos
  parecidos (rediseño, fuera de alcance; `RF-099-003`).
- **Una única paleta en `:root`**, sin `.dark` ni `class="dark"`; `@custom-variant dark (&);` para que los
  primitivos copiados se conserven sin editar (ADR-0004).
- **Tokens sin consumidor se retiran.** Corrección durante el Red: `input-background` **se conserva**
  porque `select.tsx` lo consume (mi primera redacción lo retiraba; lo detectó el propio caso (d)).
- **Formas de uso:** utilidades de token en `className`; `var(--token)` en atributos de Recharts y
  estilos en línea; tooltip compartido en `src/components/chartTheme.ts`.
- **Clases interpoladas → mapas cerrados.** Cuatro pantallas de demostración construían clases con
  `text-${color}-400` que Tailwind no detecta y que solo existían por coincidencia; se sustituyen por
  mapas de cadenas completas (`RF-099-002`).
- **Dos tests estáticos** protegen el resultado (guardián de colores y contrato del tema).
- **Sin mutación de Stryker** sobre la migración (exención justificada; ver abajo).
- **Verificación visual con Chromium real** antes/después, fuera del repositorio.
- **`ATTRIBUTIONS.md`** con el aviso MIT de shadcn/ui verificado contra la licencia publicada.
- **ADR-0010** (`Proposed`) para la convención de tokens.
- **Arrastre de JUP-098** en commits de documentación propios, sin ninguna afirmación sobre CI (la nota
  de revisión "los tests del frontend no corren en CI" se descartó como malentendido).

## Validación ejecutada

Frontend: `corepack pnpm --filter @finops/frontend <script>` porque `RF-093-001` sigue abierto en esta
máquina (turbo resuelve un pnpm global en los subprocesos por paquete) y los scripts de la raíz no
funcionan; misma sustitución que en JUP-093/094/095/097/098. Cada comando se ejecutó en solitario.

### Ciclo Red/Green de los tests estáticos

Línea base de la suite: **46 archivos, 261 tests**. El caso de `index-html-dark-scope.test.ts` (JUP-095,
1 test) se retiró con autorización expresa de Victor porque exigía `class="dark"`, lo contrario de lo que
pide la spec nueva; su cobertura la sustituye el caso (e) de `theme-palette.test.ts`.

| Punto | Fallan / pasan (total) | Qué falla |
| --- | --- | --- |
| Red (grupo 3, commit `b9d9020`) | 41 / 374 (415) | 16 del guardián (los archivos con colores literales) + 25 de `theme-palette` (`.dark`, 34 nombres repetidos, `class="dark"`, 20 tokens sin consumidor) |
| Green del tema (grupo 4, `63f0042`) | 44 / 387 (431) | 16 del guardián + 28 casos (d) de tokens aún sin consumidor |
| Armazón y componentes (grupo 5, `0c9a8dc`) | 28 / 403 | 10 del guardián + 18 (d) |
| Pantallas conectadas (grupo 6, `f79c569`) | 24 / 407 | 6 del guardián + 18 (d) |
| Dashboards de demostración (grupo 7, `81a5e69`) | **0 / 431** | — |

Los 260 tests previos pasan en todos los puntos: **ningún test previo se rompe**. Final:
`260 previos + 61 (guardián) + 110 (tema) = 431`.

### Suite final (`test`)

```
Test Files  47 passed (47)
     Tests  431 passed (431)
  Duration  50.80s
```

0 mensajes de timeout. `RF-098-004` (tiempos de espera de `findBy*` bajo carga) es real: una ejecución
durante el grupo 5, lanzada con la CPU de la máquina al 38–74 % por procesos ajenos, dio 14 archivos y 55
tests fallando; repetida en solitario con el mismo código dio exactamente el resultado esperado. No se
conservó qué tests fallaron en esa pasada, así que la causa no queda demostrada; se anota sin más
conclusión.

### Type-check, lint, build e instalación

- `typecheck` (`tsc --noEmit` × 3 configs: app, node, test): exit 0.
- `lint` (`eslint src tests`): exit 0.
- `build` (Vite 5): correcto, 2 479 módulos; CSS `41.83 kB` (gzip `7.99 kB`) y JS `768.89 kB` (gzip
  `217.26 kB`). Frente a la evidencia de JUP-098 (CSS `39.72 kB`, JS `768.08 kB`): +2,11 kB de CSS
  (tokens y utilidades nuevas) y +0,81 kB de JS. El aviso de chunk > 500 kB es preexistente.
- `corepack pnpm install --frozen-lockfile`: `Done in 1.4s`, exit 0, el lockfile no cambia.

### Checks de trazabilidad e higiene

```
corepack pnpm openspec:validate       → 35 passed, 0 failed
corepack pnpm jup:check -- --change jup-099-unify-styles-assets → [OK] enlazado con Trello y completo
corepack pnpm jup:cleanup:check       → [OK] 683 archivos sin agentes personales, binarios ni tareas paralelas
corepack pnpm jup:check:test / jup:cleanup:test → exit 0
git diff origin/develop...HEAD --name-only | grep -E '^apps/(backend|processor)/'  → 0 archivos
```

### Mutación: exención justificada

No se ejecuta Stryker sobre la migración y **no se afirma ninguna cobertura de mutación** para este
cambio. El código de producto modificado son literales de clase y valores CSS: ninguna prueba unitaria de
comportamiento ejercita un color, así que los mutantes de cadena sobrevivirían por construcción y el
porcentaje no mediría nada útil. La protección real son los dos tests estáticos (su Red demostró que
detectan los literales actuales y los tokens huérfanos) y la comparación visual. La única lógica nueva es
un diccionario `Record<string, string>` por pantalla y `chartTooltipStyle`, sin ramas.

### Verificación visual (Chromium real, fuera del repositorio)

**Método.** Playwright 1.63.0 con Chromium 1243, `pixelmatch` 7.2.0 y `pngjs` 7.0.0 en un proyecto
temporal fuera del repositorio (no entran en `package.json`). Build de producción servido con un servidor
estático con *fallback* SPA; viewport 1440×900, `es-ES`, zona `Europe/Madrid`, movimiento reducido, API
simulada con `page.route` a partir de los datos de `tests/fixtures.ts`, `new Date()` sin argumentos fijado
(la fecha del `Layout`), espera fija de 3 s para las animaciones de Recharts y captura del viewport
ampliado a la altura del documento. Los scripts completos están en el apéndice.

**34 escenarios:** las 8 pantallas y `/login`, con sus estados de error, carga, "sin tenant", el menú de
exportación, el foco del selector, el aviso de sesión expirada y los **9 tooltips de Recharts** (su
`contentStyle` solo se pinta al pasar el ratón). Crecieron desde 14 al descubrir estados con color propio
que el primer guion no veía (`SessionGate` en carga/error, error de envío del asistente, lista vacía…).

**Dos defectos del guion, corregidos antes de dar la referencia por buena** (ambos dejaban las series de
Recharts sin pintar y habrían invalidado la comparación de `fill`/`stroke`): `fullPage: true` redimensiona
el viewport y `ResponsiveContainer` reinicia la animación; y la fecha del `Layout` hacía la captura
dependiente del día.

**Criterio de comparación.** `pixelmatch` con umbral 0, más una clasificación por magnitud: píxeles
*reales* (algún canal distinto en 2 o más niveles) frente a los de 1 nivel. Dos pasadas del **mismo build**
difieren en unos pocos píxeles de 1 nivel sobre degradados (medido: 4–31 px en `assistant` e
`ingest-success`): ruido aleatorio del rasterizador, dentro del criterio (≤ 50 px). Una diferencia de 1
nivel que se **repite igual** entre pasadas no es ruido y se explica una a una: es el caso del degradado
de Recomendaciones.

| Comparación (34 escenarios) | Resultado |
| --- | --- |
| Grupo 4 (tema nuevo, pantallas sin migrar) → final | **0 píxeles reales.** Los 2 820 px de 1 nivel son 2 × 1 410: el degradado de `recommendations` y su tooltip |
| Grupo 6 → final | 0 píxeles reales |
| Original → final | 26 escenarios con diferencias y **8 con 0 exacto** (`login`, `login-invalid-credentials`, `login-session-expired`, `operational-cost`, `tooltip-operational-cost-0/1`, `session-tenants-error`, `session-tenants-loading`). Los 7 356 701 píxeles distintos caen **todos** en cuatro causas |

Píxeles distintos original → final (F = franja, D = degradado, O = iconos y borde):

| Escenario | Total | F | D | O |
| --- | ---: | ---: | ---: | ---: |
| `anomalies`, `tooltip-anomalies-0` | 71 | – | – | 71 |
| `executive-cost`, `…-export-menu`, `…-tenant-select-focus`, `tooltip-executive-cost-0/1/2` | 615 | – | – | 615 |
| `executive-cuts`, `tooltip-executive-cuts-0/1` | 549 | – | – | 549 |
| `recommendations`, `tooltip-recommendations-0` | 2 171 | – | 1 410 | 761 |
| `assistant` | 455 040 | 455 040 | – | – |
| `assistant-empty` | 852 480 | 852 480 | – | – |
| `assistant-create-error` | 812 160 | 812 160 | – | – |
| `assistant-send-error` | 403 200 | 403 200 | – | – |
| `ingest` | 270 720 | 270 720 | – | – |
| `ingest-error` | 218 880 | 218 880 | – | – |
| `ingest-success` | 8 640 | 8 640 | – | – |
| `overview-legacy` | 267 840 | 267 840 | – | – |
| `overview-legacy-loading` | 452 160 | 452 160 | – | – |
| `overview-legacy-error`, `no-tenant-ingest`, `no-tenant-assistant`, `no-tenant-overview` | 901 440 | 901 440 | – | – |
| **Total** | **7 356 701** | **7 346 880** | **2 820** | **7 001** |

**Las cuatro causas, aceptadas por Victor (2026-09-29) tras revisar imágenes antes/después:**

1. **Franja bajo el contenido, `#0a0a0a → #0f1419`.** El fondo del `body` era el `oklch(0.145)` de shadcn y
   ahora es el `background` de la aplicación, el mismo color del resto de la pantalla. Solo se ve en
   páginas más cortas que el viewport; es un efecto deseado del tema.
2. **Iconos sin color propio, `#fafafa → #ffffff`** (5 niveles). Los iconos de Lucide usan `currentColor` y
   heredan `foreground`. Imperceptible.
3. **Un borde por defecto, `#262626 → #2d3748`** (88 px + antialias, en `executive-cuts`): una caja de
   icono con `border` sin color usaba el borde por defecto de shadcn y ahora usa el de la aplicación.
4. **Degradado del panel de agentes de Recomendaciones, 1 nivel de canal** (1 410 px, sistemático).
   Tailwind resuelve `from-[#0078d4]/20` en build a un literal `oklab(...)` redondeado; con un token emite
   `color-mix(in oklab, var(--primary) 20%, transparent)`, evaluado por el navegador con precisión completa.
   Mismo color con otro redondeo; inherente al uso de tokens con opacidad.

**Demostración de propagación (criterio 2).** `--primary: #0078d4 → #ff00ff` y `--card: #1a1f2e →
#3a003a` (este último cubre también el `contentStyle` en línea de los tooltips), solo en `theme.css`,
build fuera del repositorio y archivo restaurado con `md5` idéntico y `git diff` vacío; durante la prueba
`git status` mostró un único archivo modificado. Resultado: cambian **34 de 34** escenarios y `#3a003a`
exacto aparece en los 34; `#ff00ff` exacto aparece en `login`, `ingest*`, `assistant*`,
`session-tenants-error`, `executive-cost*` y `operational-cost*` (los que usan un `bg-primary` sólido o un
`var(--primary)` de Recharts) y **no** en `executive-cuts`, `anomalies`, `overview-legacy*` ni
`no-tenant-*` (que no lo usan). En cada pantalla con gráficas, el escenario con tooltip tiene más píxeles
`#3a003a` exactos que el mismo sin tooltip (+5 312 a +21 913): el estilo en línea también sigue al tema.

### Tokens sin consumidor

`theme.css` final: `:root` con 46 variables (4 no cromáticas y 42 de color), `@theme inline` con 42
`--color-*` y 4 `--radius-*`. **13 tokens retirados** (con su `--color-*`), **21 añadidos** con nombre de
función. Se conservan 11 con un solo consumidor, justificados: los de los primitivos de shadcn
(`popover`, `popover-foreground`, `accent-foreground`, `input`, `input-background`, `primary-foreground`,
`destructive`), y `positive`, `warning-foreground`, `chart-1` y `chart-3`.

**Comprobación de mi propio análisis.** El caso (d) del test contaría como consumidor un token citado solo
en un comentario. Se repitió el análisis ignorando comentarios (`consumers.mjs`): 42 tokens, 0 sin consumo
real. Un primer intento dio 7 tokens sin consumo; era un fallo del script (el shell colapsó las barras `\\`
de una expresión regular escrita en un *heredoc*), no del código; un `grep` directo ya mostraba 30+ usos.

### Arrastre de JUP-098 (commits de documentación propios)

- **A.** `RF-098-004` registrado (tiempos de espera bajo carga, suite completa), sin ninguna afirmación
  sobre CI ni corrección. No reproducido en esta rama con la suite ejecutada en solitario.
- **B.** 9 referencias a configuración local del agente retiradas de `docs/evidence/JUP-098-validation.md` y
  del `review.md` archivado de JUP-098, sustituidas por comandos reproducibles (Stryker sin archivo de
  configuración, **verificada de nuevo con `--dryRunOnly`**: 109 mutantes en `api.ts`, 233 tests iniciales
  en verde). 0 menciones restantes.
- **C (opcionales elegidos):** 3 enlaces rotos corregidos, fila duplicada de `RF-090-003` eliminada (eran
  idénticas byte a byte), y 10 comentarios de test neutralizados (solo comentarios: 0 líneas de código
  cambiadas, suite igual). `RF-098-003` quedó fuera (cambia comportamiento, no presentación).

### Hallazgos registrados en `openspec/findings/backlog.md`

| ID | Qué |
| --- | --- |
| `RF-098-004` | Tiempos de espera de `findBy*`/`waitFor` bajo carga (arrastre de JUP-098) |
| `RF-099-001` | 42 menciones a herramientas locales en 11 archivos versionados fuera de JUP-098 |
| `RF-099-002` | Clases interpoladas que Tailwind no detecta; tonos `purple`/`orange` sin estilo (preexistente) |
| `RF-099-003` | Tonos casi iguales no consolidados (grises, cuatro verdes, rojos, azules, ámbares) |
| `RF-099-004` | 71 enlaces relativos rotos por el archivado (18 hacia changes archivados + 53 dentro de archivados), con causa clasificada y arreglo mecánico comprobado |

### Incidencias del proceso

- Varias cifras y afirmaciones propias se corrigieron al verificarlas antes de darlas por buenas:
  recuentos escritos sin medir en una primera versión de `RF-099-001` (que además rompía la tabla), la
  cifra de tokens con un solo consumidor (12 → 11), un desglose de enlaces rotos incompleto, y una
  afirmación sobre las fuentes que no se había comprobado en el CSS generado.
- El `tester` detectó un error del diseño (`input-background`); el `coder` detectó las clases
  interpoladas. Ambos se documentaron y resolvieron.
- El `coder` usó `git stash` una vez para comparar; se verificó después que `git stash list` estaba vacío y
  que el árbol tenía exactamente los archivos esperados.

## Reproducir la verificación visual

1. Crear un proyecto temporal **fuera** del repositorio e instalar `playwright`, `pixelmatch` y `pngjs`
   (`npm install`; Chromium con `npx playwright install chromium` si no está).
2. Construir cada estado a comparar a una carpeta propia:
   `corepack pnpm --filter @finops/frontend exec vite build --outDir <carpeta> --emptyOutDir`
   (el estado original con `git switch --detach 688fe2d`; el actual en la rama).
3. Capturar: `node capture.mjs <carpeta-dist> <carpeta-capturas>` (34 escenarios; `ONLY=a,b` para un
   subconjunto). Repetir dos veces el mismo build para medir el ruido.
4. Comparar: `node compare.mjs <antes> <despues>` y clasificar con `node classify.mjs <antes> <despues>`.
5. Propagación: cambiar los dos tokens en `theme.css`, construir a otra carpeta, **restaurar el archivo**,
   capturar y `node propagation.mjs <final> <propagacion>`.
6. Tokens sin consumo real: `node consumers.mjs apps/frontend/src`.

Las capturas no se versionan.

## Pendiente

- Gate post-review: **registrado** (2026-09-29) en el `review.md` del change, con `Archive decision:
  archive`.
- **Orden acordado con Victor para esta tarjeta:** el PR a `develop` se abre y se revisa con el change de
  OpenSpec **todavía activo**; el archivado (con la promoción del delta de `frontend-navigation-shell`),
  su push y el merge se hacen después de que el PR esté revisado y validado, cuando Victor lo indique.
- **Al archivar, corregir en el mismo paso los enlaces que bajan un nivel:** el enlace al change en esta
  evidencia (cabecera) y en `docs/spikes/frontend-migration.md` deben apuntar a
  `openspec/changes/archive/<fecha>-jup-099-unify-styles-assets/`, y los enlaces relativos del propio
  `review.md`, `design.md` y `proposal.md` archivados necesitan un `../` más (`RF-099-004`).
- Rellenar aquí el enlace del PR y el resultado de CI cuando se abra.
- ADR-0010 pasa de `Proposed` a `Accepted` con la aprobación del PR.
- `RF-099-001` a `RF-099-004` quedan `Open` sin dueño asignado, disponibles para tarjetas propias.
- El E2E completo en navegador contra el backend real corresponde a JUP-102; esta tarjeta verifica el
  aspecto con datos simulados.

## Apéndice: scripts

Copiados literalmente de los archivos ejecutados.

### `capture.mjs` — Captura de los 34 escenarios

Uso: `node capture.mjs <dist> <salida>`; con `ONLY=a,b` solo los indicados.

````js
// Captura de referencia/verificacion visual de JUP-099 (decision 6 de design.md).
// Uso: node capture.mjs <carpeta-dist> <carpeta-salida>
// Sirve un build de produccion con un servidor estatico con fallback SPA y recorre
// los estados de las 9 pantallas contra una API simulada con page.route.
// Determinismo: viewport 1440x900, reloj/zona/idioma fijos, movimiento reducido,
// espera fija tras la carga para que terminen las animaciones de Recharts.
import { chromium } from "playwright";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";

const [distDir, outDir] = process.argv.slice(2).map((p) => path.resolve(p));
fs.mkdirSync(outDir, { recursive: true });

const API = "http://localhost:8000";
const SETTLE_MS = 3000;

// Datos sinteticos identicos a apps/frontend/tests/fixtures.ts.
const operator = { id: "user-operator", email: "operator@example.com", full_name: "Test Operator", role: "operator" };
const tenants = [
  { id: "tenant-north", name: "North Operations", slug: "north", plan: "enterprise" },
  { id: "tenant-south", name: "South Operations", slug: "south", plan: "starter" }
];
const conversation = {
  id: "conversation-cost-review", tenant_id: "tenant-north", user_id: operator.id,
  title: "September costs", created_at: "2026-09-08T10:00:00Z", updated_at: "2026-09-08T10:05:00Z"
};
const messages = [
  { id: "m1", role: "user", content: "Where can we reduce compute costs?", metadata: {}, created_at: "2026-09-08T10:05:00Z" },
  { id: "m2", role: "assistant", content: "The billing document identifies idle compute instances.", metadata: {}, created_at: "2026-09-08T10:05:01Z" }
];
const billing = { monthly_spend: 12345, savings_identified: 678, open_ingestions: 2, currency: "USD" };
const health = { status: "ok", services: { database: "ok", rabbitmq: "ok", vector_store: "ok" }, checked_at: "2026-09-08T10:00:00Z" };
const session = { accessToken: "test-access-token", user: operator };

const json = (route, data, status = 200) =>
  route.fulfill({ status, contentType: "application/json", headers: { "access-control-allow-origin": "*" }, body: JSON.stringify(data) });

// `overrides` permite cambiar la respuesta de un endpoint concreto por escenario.
async function mockApi(page, overrides = {}) {
  await page.route(`${API}/**`, async (route) => {
    const req = route.request();
    if (req.method() === "OPTIONS") {
      return route.fulfill({ status: 204, headers: {
        "access-control-allow-origin": "*", "access-control-allow-headers": "*", "access-control-allow-methods": "*" } });
    }
    const key = `${req.method()} ${new URL(req.url()).pathname}`;
    if (overrides[key]) return overrides[key](route);
    switch (key) {
      case "GET /me": return json(route, operator);
      case "GET /tenants": return json(route, { items: tenants });
      case "GET /health": return json(route, health);
      case "GET /billing/summary": return json(route, billing);
      case "GET /assistant/conversations": return json(route, { items: [conversation] });
      case `GET /assistant/conversations/${conversation.id}`: return json(route, { conversation, messages });
      default: return json(route, { detail: `sin simular: ${key}` }, 404);
    }
  });
}

// Servidor estatico con fallback a index.html (rutas del cliente).
function serve(dir) {
  const types = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml" };
  const server = http.createServer((req, res) => {
    let file = path.join(dir, decodeURIComponent(new URL(req.url, "http://x").pathname));
    if (!file.startsWith(dir) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(dir, "index.html");
    res.writeHead(200, { "content-type": types[path.extname(file)] ?? "application/octet-stream" });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve(server)));
}

const server = await serve(distDir);
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch();

async function scenario(name, { authed = true, overrides = {}, run, after }) {
  if (process.env.ONLY && !process.env.ONLY.split(",").includes(name)) return;
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1,
    locale: "es-ES", timezoneId: "Europe/Madrid", reducedMotion: "reduce", colorScheme: "dark"
  });
  const page = await context.newPage();
  // Solo `new Date()` sin argumentos (la fecha del Layout) se fija; `Date.now` sigue real porque
  // Recharts anima con el reloj y `page.clock.setFixedTime` lo congelaba (series sin pintar).
  await context.addInitScript(() => {
    const RealDate = Date;
    const FIXED = new RealDate("2026-09-29T10:00:00Z").getTime();
    globalThis.Date = class extends RealDate {
      constructor(...args) { args.length ? super(...args) : super(FIXED); }
    };
  });
  if (authed) {
    await context.addInitScript((s) => {
      localStorage.setItem("finops.session", JSON.stringify(s));
      localStorage.setItem("finops.activeTenant", "tenant-north");
    }, session);
  }
  await mockApi(page, overrides);
  await run(page);
  // `fullPage` redimensiona el viewport en la propia captura y ResponsiveContainer reinicia la
  // animacion de Recharts (series sin pintar). Se amplia el viewport a la altura del documento,
  // se espera a que termine la animacion y se captura el viewport tal cual.
  const height = await page.evaluate(() => Math.max(900, document.documentElement.scrollHeight));
  await page.setViewportSize({ width: 1440, height });
  await page.waitForTimeout(SETTLE_MS);
  // `after`: acciones posteriores al asentamiento (p. ej. hover sobre una grafica para el tooltip).
  if (after) { await after(page); await page.waitForTimeout(500); }
  await page.screenshot({ path: path.join(outDir, `${name}.png`) });
  await context.close();
  console.log("captura", name);
}

const go = (route, ready) => async (page) => {
  await page.goto(`${base}${route}`);
  await page.waitForSelector(ready ?? "header", { timeout: 15000 });
};

await scenario("login", { authed: false, run: go("/login", "form") });

await scenario("login-invalid-credentials", {
  authed: false,
  overrides: { "POST /auth/login": (r) => json(r, { detail: "Invalid email or password." }, 401) },
  run: async (page) => {
    await go("/login", "form")(page);
    await page.fill("#login-email", "operator@example.com");
    await page.fill("#login-password", "wrong-password");
    await page.click("button[type=submit]");
    await page.waitForSelector("text=Invalid email or password");
  }
});

await scenario("login-session-expired", {
  overrides: { "GET /billing/summary": (r) => json(r, { detail: "expired" }, 401) },
  run: async (page) => {
    await page.goto(`${base}/overview-legacy`);
    await page.waitForSelector("[role=status]:has-text('Your session has expired')", { timeout: 15000 });
  }
});

await scenario("executive-cost", { run: go("/") });
await scenario("executive-cost-export-menu", {
  run: async (page) => {
    await go("/")(page);
    await page.click("text=Exportar Resultados");
    await page.waitForSelector("text=Exportar");
  }
});
await scenario("executive-cost-tenant-select-focus", {
  run: async (page) => {
    await go("/")(page);
    await page.focus("select[aria-label='Ambito de cliente']");
  }
});
await scenario("operational-cost", { run: go("/operational") });
await scenario("executive-cuts", { run: go("/cuts") });
await scenario("anomalies", { run: go("/anomalies") });
await scenario("recommendations", { run: go("/recommendations") });
await scenario("overview-legacy", { run: go("/overview-legacy") });
await scenario("ingest", { run: go("/ingest") });
await scenario("ingest-error", {
  overrides: { "POST /jobs/ingest": (r) => json(r, { detail: "Ingestion unavailable" }, 500) },
  run: async (page) => {
    await go("/ingest")(page);
    await page.fill("#ingest-source", "billing");
    await page.fill("#ingest-artifact-uri", "s3://billing/report.csv");
    await page.fill("#ingest-text-content", "Idle compute instances cost 678 USD this month.");
    await page.click("button[type=submit]");
    await page.waitForSelector("text=Ingestion unavailable");
  }
});
await scenario("assistant", {
  run: async (page) => {
    await go("/assistant")(page);
    await page.click(`text=${conversation.title}`);
    await page.waitForSelector("text=idle compute instances");
    await page.fill("textarea", "Que recomiendas?");
  }
});

// --- Estados sin cobertura en el primer guion (anadidos antes del grupo 5): carga y error del
// bootstrap de tenants (SessionGate), carga y error del resumen, exito de ingesta y error de envio.
const never = () => new Promise(() => {});
await scenario("session-tenants-loading", {
  overrides: { "GET /tenants": never },
  run: async (page) => { await page.goto(base + "/"); await page.waitForSelector("text=Cargando tenants disponibles"); }
});
await scenario("session-tenants-error", {
  overrides: { "GET /tenants": (r) => json(r, { detail: "Tenants unavailable" }, 500) },
  run: async (page) => { await page.goto(base + "/"); await page.waitForSelector("text=No se han podido cargar los tenants", { timeout: 40000 }); }
});
await scenario("overview-legacy-loading", {
  overrides: { "GET /billing/summary": never },
  run: async (page) => { await go("/overview-legacy")(page); await page.waitForSelector("text=Connecting to the FinOps control plane"); }
});
await scenario("overview-legacy-error", {
  overrides: { "GET /billing/summary": (r) => json(r, { detail: "Billing unavailable" }, 500) },
  run: async (page) => { await go("/overview-legacy")(page); await page.waitForSelector("text=Backend unavailable", { timeout: 40000 }); }
});
await scenario("ingest-success", {
  overrides: { "POST /jobs/ingest": (r) => json(r, { job_id: "job-billing-document", status: "queued", queue: "ingest.jobs" }, 202) },
  run: async (page) => {
    await go("/ingest")(page);
    await page.fill("#ingest-source", "billing");
    await page.fill("#ingest-artifact-uri", "s3://billing/report.csv");
    await page.fill("#ingest-text-content", "Idle compute instances cost 678 USD this month.");
    await page.click("button[type=submit]");
    await page.waitForSelector("text=Job accepted");
  }
});
await scenario("assistant-send-error", {
  overrides: { [`POST /assistant/conversations/${conversation.id}/messages`]: (r) => json(r, { detail: "Assistant unavailable" }, 500) },
  run: async (page) => {
    await go("/assistant")(page);
    await page.click(`text=${conversation.title}`);
    await page.waitForSelector("text=idle compute instances");
    await page.fill("textarea", "Que recomiendas?");
    await page.click("button:has-text('Send')");
    await page.waitForSelector("text=Assistant unavailable");
  }
});

// --- Anadidos antes del grupo 6: ramas de las pantallas conectadas que aun no se veian.
await scenario("assistant-empty", {
  overrides: { "GET /assistant/conversations": (r) => json(r, { items: [] }) },
  run: async (page) => { await go("/assistant")(page); await page.waitForSelector("text=Create a conversation to start"); }
});
await scenario("assistant-create-error", {
  overrides: {
    "GET /assistant/conversations": (r) => json(r, { items: [] }),
    "POST /assistant/conversations": (r) => json(r, { detail: "Cannot create" }, 500)
  },
  run: async (page) => {
    await go("/assistant")(page);
    await page.click("button:has-text(\"New\")");
    await page.waitForSelector("text=Cannot create");
  }
});
for (const [name, route, marker] of [
  ["no-tenant-ingest", "/ingest", "text=Tenant required"],
  ["no-tenant-assistant", "/assistant", "text=Tenant required"],
  ["no-tenant-overview", "/overview-legacy", "text=Select a tenant"]
]) {
  await scenario(name, {
    overrides: { "GET /tenants": (r) => json(r, { items: [] }) },
    run: async (page) => { await go(route)(page); await page.waitForSelector(marker, { timeout: 15000 }); }
  });
}

// --- Anadidos antes del grupo 7: tooltips de Recharts (contentStyle solo se pinta al hacer hover).
// Se pasa el raton por el centro de cada grafica (.recharts-wrapper) y se captura con el tooltip abierto.
const hoverChart = (i) => async (page) => { await page.locator(".recharts-wrapper").nth(i).hover(); };
for (const [name, route, count] of [
  ["executive-cost", "/", 3], ["operational-cost", "/operational", 2], ["executive-cuts", "/cuts", 2],
  ["anomalies", "/anomalies", 1], ["recommendations", "/recommendations", 1]
]) {
  for (let i = 0; i < count; i++) {
    await scenario(`tooltip-${name}-${i}`, { run: go(route), after: hoverChart(i) });
  }
}

await browser.close();
server.close();
````

### `compare.mjs` — Comparación con `pixelmatch` (umbral 0) y separación de píxeles reales

Uso: `node compare.mjs <antes> <despues> [carpeta-diff]`.

````js
// Compara dos carpetas de capturas. Umbral 0 (cualquier diferencia se cuenta) y, ademas, mide la
// magnitud: `reales` = pixeles con algun canal distinto en 2 o mas niveles; el resto (delta 1) es
// ruido de rasterizado de degradados, medido con dos pasadas del MISMO build (ver review.md).
// Uso: node compare.mjs <carpeta-a> <carpeta-b> [carpeta-diff]
import fs from "node:fs"; import path from "node:path";
import { PNG } from "pngjs"; import pixelmatch from "pixelmatch";
const [a, b, diffDir] = process.argv.slice(2);
if (diffDir) fs.mkdirSync(diffDir, { recursive: true });
let total = 0, reales = 0;
for (const f of fs.readdirSync(a).filter((n) => n.endsWith(".png")).sort()) {
  const A = PNG.sync.read(fs.readFileSync(path.join(a, f)));
  const B = PNG.sync.read(fs.readFileSync(path.join(b, f)));
  if (A.width !== B.width || A.height !== B.height) { console.log(f.padEnd(44), `TAMAÑO DISTINTO ${A.width}x${A.height} vs ${B.width}x${B.height}`); total++; reales++; continue; }
  const diff = new PNG({ width: A.width, height: A.height });
  const n = pixelmatch(A.data, B.data, diff.data, A.width, A.height, { threshold: 0, includeAA: true });
  let r = 0, maxDelta = 0;
  if (n) for (let i = 0; i < A.data.length; i += 4) {
    const d = Math.max(Math.abs(A.data[i] - B.data[i]), Math.abs(A.data[i+1] - B.data[i+1]), Math.abs(A.data[i+2] - B.data[i+2]), Math.abs(A.data[i+3] - B.data[i+3]));
    if (d > maxDelta) maxDelta = d; if (d >= 2) r++;
  }
  if (diffDir && n) fs.writeFileSync(path.join(diffDir, f), PNG.sync.write(diff));
  console.log(f.padEnd(44), `${A.width}x${A.height}`.padEnd(11), `${n} px distintos`.padEnd(20), n ? `reales(delta>=2): ${r}, delta max: ${maxDelta}` : "");
  total += n; reales += r;
}
console.log("TOTAL", total, "| reales (delta>=2):", reales);
````

### `classify.mjs` — Clasificación de los píxeles distintos por causa conocida

Uso: `node classify.mjs <antes> <despues>`.

````js
// Clasifica cada pixel distinto entre dos carpetas de capturas por causa conocida, para la tabla de 8.1.
// Uso: node classify.mjs <antes> <despues>
//  franja   : #0a0a0a -> #0f1419 (fondo del body, paginas mas cortas que el viewport)
//  degradado: diferencia de 1 nivel dentro del panel de agentes de Recomendaciones (redondeo de color-mix)
//  otros    : el resto (iconos que heredan foreground, borde por defecto y sus antialias)
import fs from "node:fs";
import path from "node:path";
import { PNG } from "pngjs";

const [a, b] = process.argv.slice(2);
const hex = (d, i) => "#" + [0, 1, 2].map((k) => d[i + k].toString(16).padStart(2, "0")).join("");
const rows = [];
let tot = { franja: 0, degradado: 0, otros: 0 };
for (const f of fs.readdirSync(a).filter((n) => n.endsWith(".png")).sort()) {
  const A = PNG.sync.read(fs.readFileSync(path.join(a, f)));
  const B = PNG.sync.read(fs.readFileSync(path.join(b, f)));
  const c = { franja: 0, degradado: 0, otros: 0 };
  for (let y = 0; y < A.height; y++) {
    for (let x = 0; x < A.width; x++) {
      const i = (y * A.width + x) * 4;
      if (A.data[i] === B.data[i] && A.data[i + 1] === B.data[i + 1] && A.data[i + 2] === B.data[i + 2]) continue;
      const delta = Math.max(Math.abs(A.data[i] - B.data[i]), Math.abs(A.data[i + 1] - B.data[i + 1]), Math.abs(A.data[i + 2] - B.data[i + 2]));
      if (hex(A.data, i) === "#0a0a0a" && hex(B.data, i) === "#0f1419") c.franja++;
      else if (delta <= 1 && f.includes("recommendations") && y >= 1737 && y <= 1879 && x >= 29 && x <= 1404) c.degradado++;
      else c.otros++;
    }
  }
  const sum = c.franja + c.degradado + c.otros;
  tot.franja += c.franja; tot.degradado += c.degradado; tot.otros += c.otros;
  rows.push(`${f.replace(".png", "").padEnd(40)} ${String(sum).padStart(8)}   franja ${String(c.franja).padStart(7)} | degradado ${String(c.degradado).padStart(5)} | otros ${String(c.otros).padStart(4)}`);
}
console.log(rows.join("\n"));
console.log(`\nTOTAL franja ${tot.franja} | degradado ${tot.degradado} | otros ${tot.otros}`);
````

### `propagation.mjs` — Demostración de propagación de tokens

Uso: `node propagation.mjs <final> <propagacion>`.

````js
// Demostracion de propagacion (criterio 2): compara el build final con el build con --primary y --card
// cambiados. Por escenario: pixeles distintos y pixeles que adoptan EXACTAMENTE cada color nuevo.
// Uso: node propagation.mjs <capturas-final> <capturas-prop>
import fs from "node:fs";
import path from "node:path";
import { PNG } from "pngjs";

const [a, b] = process.argv.slice(2);
const MAGENTA = [0xff, 0x00, 0xff]; // --primary
const CARD = [0x3a, 0x00, 0x3a]; // --card
const eq = (d, i, c) => d[i] === c[0] && d[i + 1] === c[1] && d[i + 2] === c[2];

let changed = 0;
const unchanged = [];
for (const f of fs.readdirSync(a).filter((n) => n.endsWith(".png")).sort()) {
  const A = PNG.sync.read(fs.readFileSync(path.join(a, f)));
  const B = PNG.sync.read(fs.readFileSync(path.join(b, f)));
  let diff = 0, magenta = 0, card = 0, magentaAntes = 0, cardAntes = 0;
  for (let i = 0; i < A.data.length; i += 4) {
    if (A.data[i] !== B.data[i] || A.data[i + 1] !== B.data[i + 1] || A.data[i + 2] !== B.data[i + 2]) diff++;
    if (eq(B.data, i, MAGENTA)) magenta++;
    if (eq(B.data, i, CARD)) card++;
    if (eq(A.data, i, MAGENTA)) magentaAntes++;
    if (eq(A.data, i, CARD)) cardAntes++;
  }
  const name = f.replace(".png", "");
  if (diff === 0) { unchanged.push(name); continue; }
  changed++;
  console.log(`${name.padEnd(40)} ${String(diff).padStart(8)} px distintos | #ff00ff exactos: ${String(magenta).padStart(6)} (antes ${magentaAntes}) | #3a003a exactos: ${String(card).padStart(7)} (antes ${cardAntes})`);
}
console.log(`\n${changed} escenarios cambian; ${unchanged.length} no cambian: ${unchanged.join(", ")}`);
````

### `consumers.mjs` — Consumidores reales de cada token, ignorando comentarios

Uso: `node consumers.mjs apps/frontend/src`.

````js
// Para cada token --color-* de theme.css, cuenta consumidores IGNORANDO comentarios (// y /* */),
// para detectar un token que solo aparezca citado en un comentario (falso verde del caso (d) de
// theme-palette.test.ts). Uso: node consumers.mjs <apps/frontend/src>
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(process.argv[2]);
const walk = (d) =>
  fs.readdirSync(d, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? (e.name === "test" ? [] : walk(path.join(d, e.name))) : [path.join(d, e.name)]
  );
const files = walk(root).filter((f) => /\.(tsx?|css)$/.test(f) && !/\.test\./.test(f));

// Quita comentarios de bloque y de linea (sin tocar `://` de URLs ni cadenas con comillas).
const strip = (s) =>
  s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:"'`])\/\/.*$/gm, (_m, p1) => p1);

const theme = fs.readFileSync(path.join(root, "styles/theme.css"), "utf8");
const themeInline = theme.match(/@theme inline\s*\{([\s\S]*?)\n\}/)[1];
const tokens = [...themeInline.matchAll(/--color-([a-z0-9-]+):/g)].map((m) => m[1]);

const codes = files.map((f) => {
  let s = fs.readFileSync(f, "utf8");
  // En theme.css solo cuenta lo que queda fuera de :root y de @theme inline.
  if (f.endsWith("theme.css")) {
    s = s.replace(/:root\s*\{[\s\S]*?\n\}/, "").replace(/@theme inline\s*\{[\s\S]*?\n\}/, "");
  }
  return { f: path.relative(root, f), s: strip(s) };
});

const PREFIX = "(?:bg|text|border|ring|ring-offset|fill|stroke|from|to|via|shadow|divide|outline|decoration|accent|caret|placeholder)";
let sinConsumo = 0;
for (const t of tokens) {
  // Los guiones del nombre no necesitan escape fuera de una clase de caracteres.
  const util = new RegExp("(?<![\\w-])" + PREFIX + "-" + t + "(?:/[0-9]+)?(?![\\w-])");
  const cssVar = new RegExp("var[(]--(?:color-)?" + t + "[)]");
  const hits = codes.filter((c) => util.test(c.s) || cssVar.test(c.s)).map((c) => c.f);
  if (hits.length === 0) {
    sinConsumo++;
    console.log("SIN CONSUMO REAL:", t);
  } else {
    console.log(t.padEnd(26), String(hits.length).padStart(2), "archivo(s)", hits.length <= 2 ? "-> " + hits.join(", ") : "");
  }
}
console.log(`\n${tokens.length} tokens; sin consumo real (ignorando comentarios): ${sinConsumo}`);
````
