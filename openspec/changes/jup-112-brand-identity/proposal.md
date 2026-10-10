JUP: JUP-112
Trello: https://trello.com/c/XTZU3vj3

## Why

El frontend se presenta con una identidad heredada del prototipo (tema oscuro azul, "FinOps AI Platform", icono genérico) que no coincide con la imagen de marca de Economicon que ya usan el dossier y el resto del proyecto. Con la entrega del hito M7 cerca, la aplicación debe parecer parte del mismo producto y, además, necesita colores de estado (alarmas, avisos, éxito) que convivan con la marca sin confundirse con ella.

## What Changes

- El tema pasa a la paleta de marca sobre fondo claro: blanco roto como base, índigo para cabecera y texto de marca, lila para tarjetas, violeta solo en botones y llamadas a la acción, coral como único acento cálido para ahorro e insights, casi negro para el texto.
- Se define, con criterio de diseño, una paleta de estados (éxito, aviso, peligro, información, neutro) y de series de gráficas que sea coherente con la marca, distinguible del coral y legible sobre fondos claros.
- Titulares en Space Grotesk y cuerpo en Inter, empaquetadas con la aplicación (sin pedirlas a un CDN en ejecución).
- Armazón con el monograma E (versión inversa sobre la cabecera índigo, primaria sobre fondos claros), nombre "Economicon", título de la pestaña y favicon de marca.
- Las pantallas existentes, los componentes compartidos y el documento de impresión de `ExportButton` adoptan los nuevos tokens; se corrigen los usos que asumían fondo oscuro.
- Se ajustan los tests guardianes del tema y se añade una comprobación de contraste de los pares texto/fondo.
- **BREAKING** (visual): desaparece el tema oscuro actual; el modo oscuro de la aplicación queda fuera de alcance. ADR-0012 se enmienda en su decisión 3 (paleta única, ahora clara).

## Capabilities

### New Capabilities
- `frontend-brand-identity`: la aplicación presenta la identidad de Economicon (paleta, tipografía, logotipo, uso del violeta y del coral) y define los colores de estado y de gráficas con legibilidad comprobada.

### Modified Capabilities
- `frontend-navigation-shell`: el armazón muestra la marca de Economicon; se retira el requisito de que la unificación de colores conserve el aspecto del tema oscuro anterior, que era propio de aquella migración.

## Impact

- `apps/frontend/src/styles/theme.css`, `index.html`, `src/layouts/Layout.tsx`, la pantalla de acceso, `components/chartTheme.ts`, `ExportButton.tsx`, pantallas con tonos que asumían fondo oscuro y datos demo con `var(--chart-N)`.
- Nuevos assets de marca (monograma primario e inverso, favicon) y dos dependencias de fuentes empaquetadas con licencia OFL, a registrar en `ATTRIBUTIONS.md`.
- Tests: `color-tokens.guard.test.ts`, `theme-palette.test.ts` y los tests de pantallas que comprueben clases concretas.
- Docs: `docs/adr/ADR-0012-frontend-color-tokens.md` (enmienda), `docs/continuidad/` y evidencia de capturas.
- Existe un borrador paralelo (PR #102) sobre la misma tarjeta; este cambio parte de cero por decisión de Lucia y no reutiliza ese trabajo.
