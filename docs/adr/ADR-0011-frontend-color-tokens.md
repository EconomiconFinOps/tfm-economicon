# ADR-0011: Convención de tokens de color del frontend

- Estado: Proposed
- Fecha: 2026-09-29
- Tarjeta Trello: [JUP-099](https://trello.com/c/WBnzwDHR/91-jup-099)
- OpenSpec relacionado: `jup-099-unify-styles-assets`
- Sustituye a: ninguno
- Sustituido por: ninguno

## Contexto

[JUP-095](../../openspec/changes/archive/2026-09-12-jup-095-portar-codigo-fuente/) retiró el `main.css`
del scaffold y dejó el frontend sobre Tailwind v4, pero la unificación de color quedó a medias y su
propio `design.md` lo anotó como trabajo pendiente. Medido sobre `develop` (`688fe2d`) el 2026-09-29,
convivían **tres** fuentes de color en la misma pantalla:

- **241 hexadecimales escritos a mano** en 14 archivos `.tsx` (más 4 en datos demo), de solo 16 valores
  distintos (`#2d3748` aparece 68 veces).
- **229 utilidades de la paleta de Tailwind** (`text-slate-400`, `text-white`, `bg-green-500/20`…) en
  16 archivos.
- Los **tokens de `theme.css`**, que eran el tema por defecto de shadcn/ui (grises neutros) y no
  reflejaban la paleta real de la aplicación. Solo los consumían los primitivos de
  [ADR-0004](ADR-0004-frontend-shadcn-ui.md), que ninguna pantalla usaba, y por ellos se había fijado
  `class="dark"` en `<html>` como apaño de ámbito.

Cambiar un color de marca exigía tocar 14 archivos sin garantía de consistencia, y el requisito
vigente "La aplicación se presenta bajo un único sistema de estilos" (spec `frontend-navigation-shell`)
no se cumplía. Es una decisión transversal: obliga a todas las tarjetas futuras que toquen el
frontend y determina cómo se copian los primitivos de shadcn/ui.

## Decisión

1. **Ningún color literal en la interfaz.** Pantallas, armazón, componentes compartidos y datos demo
   obtienen sus colores solo de **tokens semánticos** definidos una vez en `src/styles/theme.css`. No se
   escriben hexadecimales ni utilidades de la paleta genérica de Tailwind (`text-slate-400`,
   `bg-red-500/20`…): se usa la utilidad del token (`text-muted-foreground`, `bg-danger-tint/20`).
2. **Nombres por función y valor exacto.** Cada token se llama por lo que hace (`success`,
   `danger-foreground`, `chart-axis`), no por su color, y reproduce el valor que sustituye: es un
   refactor visual, no un rediseño. Se reutilizan los nombres semánticos de shadcn/ui
   (`background`, `foreground`, `card`, `primary`, `border`, `ring`…) con los valores de la
   aplicación, y se añaden solo los que la interfaz necesita y shadcn no nombra (estados
   `success`/`danger`/`info`/`warning`/`attention` con sus variantes `-tint` y `-foreground`,
   `highlight`, `chart-*`).
3. **Una única paleta en `:root`.** La aplicación solo tiene tema oscuro: no hay bloque `.dark`, ni
   valores claros sin consumidor, ni `class="dark"` en `<html>`. `@custom-variant dark (&);` hace que
   las variantes `dark:` de los primitivos copiados apliquen siempre, de modo que **se conservan tal
   como los publica shadcn/ui** (ADR-0004: se copian, no se reescriben).
4. **Valores "v4" literales.** Los tonos que provenían de la paleta de Tailwind v4 se copian como
   literales `oklch(...)` al escribir el token, sin referenciar las variables de la paleta de Tailwind,
   para que el tema no cambie si una actualización retoca esa paleta.
5. **Dónde se usa cada forma.** Utilidades de token en `className`; `var(--token)` en atributos de
   Recharts (`stroke`, `fill`) y en estilos en línea (el tooltip comparte una constante,
   `src/components/chartTheme.ts`); `var(--chart-N)` en datos demo.
6. **Sin clases construidas por interpolación.** Tailwind solo genera utilidades que aparecen como
   literal completo: `text-${color}-400` no se detecta. Los tonos dinámicos se resuelven con **mapas
   cerrados de cadenas completas** (`Record<string, string>`).
7. **Excepciones declaradas una a una.** Solo se admite un color literal cuando el tema no puede
   alcanzarlo, y debe figurar con archivo, valor y motivo en la lista del test guardián. Hoy son dos: el
   `<style>` del documento HTML autónomo que `ExportButton` abre para imprimir (no carga `theme.css`) y
   `bg-black/50` del primitivo `Dialog` copiado tal cual.
8. **La regla se hace cumplir con tests, no con revisión.**
   `src/test/color-tokens.guard.test.ts` falla si un `.tsx` de `src/` o un `.ts` de `src/data/` escribe
   un color literal fuera de las excepciones (y si una excepción queda obsoleta);
   `src/test/theme-palette.test.ts` comprueba el contrato del tema: sin bloque `.dark`, cada token
   declarado una sola vez, cada alias resuelto, `<html>` sin clase de tema y **cada token con al menos
   un consumidor** (un token sin uso se retira).

## Consecuencias

**Se vuelve más fácil:**

- Cambiar un color se hace en un punto y llega a toda la interfaz. Demostrado en JUP-099: cambiando solo
  `--primary` y `--card` en `theme.css`, cambiaron los 34 escenarios y ningún archivo de pantalla.
- Detectar un color literal nuevo: el guardián lo señala con archivo, línea y valor.
- Copiar primitivos futuros de shadcn/ui sin editarlos.

**Se vuelve más difícil:**

- Elegir un color nuevo exige nombrarlo por su función y darle un consumidor; no se puede "probar un
  hexadecimal" en una pantalla.
- Un tono que no encaje en ningún token obliga a decidir si es un token nuevo o una excepción.

**Se vuelve más arriesgado:**

- **Tonos casi iguales como tokens distintos** (p. ej. `#94a3b8` de las gráficas frente a `slate-400` v4
  del texto secundario; cuatro verdes). Se conservaron para no cambiar píxeles; consolidarlos es una
  decisión de diseño (`RF-099-003`).
- **Un redondeo distinto en opacidades.** Con un hex arbitrario y opacidad, Tailwind calcula el color en
  tiempo de build; con un token emite `color-mix(...)` que evalúa el navegador. Mismo color, hasta 1
  nivel de canal de diferencia en degradados (medido en JUP-099, imperceptible).
- **Puntos ciegos del guardián:** no detecta `rgb(`/`hsl(`/`oklch(` literales ni clases interpoladas.
  Hoy no hay ninguno y la regla 6 los prohíbe, pero el test no lo comprueba.
- **Solo tema oscuro.** Un modo claro exigiría una segunda paleta activable por atributo y revisar la
  decisión 3; no se ha construido (fuera de alcance de JUP-099).
- Dependencia del comportamiento de Tailwind v4 sobre `@custom-variant dark (&)`; verificado
  compilando con 4.3.3.

## Alternativas consideradas

- **Espacio de nombres propio junto al de shadcn** (`--app-*`). Descartada: dejaría dos vocabularios de
  color en `theme.css` y los primitivos seguirían en otra paleta, que es justo el problema.
- **Consolidar en una paleta reducida** (un solo gris secundario, un solo verde). Descartada: menos
  tokens, pero cambia píxeles en todas las pantallas; es rediseño y queda fuera del alcance.
- **Conservar `:root` claro más `.dark`** con la paleta real en `.dark`. Descartada: mantiene unos 35
  valores sin consumidor y el apaño de ámbito con `class="dark"`.
- **Editar los primitivos para quitar sus variantes `dark:`.** Descartada: obligaría a editar cada
  primitivo copiado en el futuro.
- **Pruebas de regresión visual en CI.** Aplazada, no rechazada: exige Playwright, navegadores y
  capturas de referencia versionadas; es infraestructura de equipo que corresponde valorar en la
  validación E2E (JUP-102).

## Evidencia y seguimiento

- Verificación de JUP-099 (`docs/evidence/JUP-099-validation.md` y `review.md` del change): 34
  escenarios capturados antes y después con Chromium real, incluidos estados de error, carga, "sin
  tenant" y los tooltips de las gráficas. Entre el estado con el tema nuevo y el final, **0 píxeles
  reales** de diferencia; frente al original, todas las diferencias caen en cuatro causas medidas y
  aceptadas una a una por el equipo.
- Hallazgos registrados en `openspec/findings/backlog.md`: `RF-099-002` (clases interpoladas y tonos
  sin estilo en las pantallas de demostración) y `RF-099-003` (tonos casi iguales no consolidados).
- Seguimiento: las tarjetas de frontend que añadan o modifiquen color deben citar este ADR en su
  `design.md`, igual que ADR-0003 y ADR-0004. Pasa a `Accepted` cuando el PR de JUP-099 se apruebe.
