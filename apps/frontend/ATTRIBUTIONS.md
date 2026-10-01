# Atribuciones y licencias de terceros del frontend

Este archivo recoge qué material de terceros **contiene el código de `apps/frontend`** y qué avisos de
licencia exige. Se creó en [JUP-099](../../openspec/changes/archive/2026-10-01-jup-099-unify-styles-assets/) al cerrar la
unificación de estilos y assets; la decisión y su verificación están en el `design.md` (decisión 7) y en
el `review.md` de ese change.

## Código copiado al repositorio: shadcn/ui (MIT)

[shadcn/ui](https://github.com/shadcn-ui/ui) no se instala como librería: sus componentes se **copian**
al proyecto y se mantienen como código propio ([ADR-0004](../../docs/adr/ADR-0004-frontend-shadcn-ui.md)).
La licencia MIT exige conservar el aviso de copyright y el texto de la licencia en las copias, y por eso
figuran aquí.

Archivos que contienen código copiado de shadcn/ui:

| Archivo | Qué es |
| --- | --- |
| `src/components/ui/dialog.tsx` | primitivo `Dialog` |
| `src/components/ui/label.tsx` | primitivo `Label` |
| `src/components/ui/select.tsx` | primitivo `Select` |
| `src/components/ui/separator.tsx` | primitivo `Separator` |
| `src/components/ui/tooltip.tsx` | primitivo `Tooltip` |
| `src/lib/utils.ts` | helper `cn` (composición de clases con `clsx` y `tailwind-merge`) |

Los nombres de los tokens de color semánticos que consumen esos primitivos (`background`, `foreground`,
`primary`, `border`, `ring`…) también siguen la convención de shadcn/ui, pero sus **valores** son los de
esta aplicación (`src/styles/theme.css`).

Texto de la licencia, copiado literalmente de
[`LICENSE.md` del repositorio de shadcn/ui](https://github.com/shadcn-ui/ui/blob/main/LICENSE.md)
(descargado y comparado el 2026-09-29):

```text
MIT License

Copyright (c) 2023 shadcn

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Lo que NO requiere atribución aquí

- **Fotografías de Unsplash.** El proyecto de origen las incluía, pero **no se portó ninguna imagen**:
  `apps/frontend` no contiene archivos de imagen (`.png`, `.jpg`, `.svg`, `.ico`…) ni `src/assets` ni
  `public/`, y ningún archivo de `src/` ni `index.html` las referencia. Verificado el 2026-09-29.
- **Fuentes.** No hay `@font-face` ni archivos de fuente (`.woff`, `.woff2`, `.ttf`), ni en el código ni
  en el CSS generado (0 reglas `@font-face`). El texto usa la pila de fuentes **del sistema** que aplica
  Tailwind por defecto (`-apple-system`, `Segoe UI`, `Roboto`, `Arial`…), y el documento de impresión de
  `ExportButton` pide `Arial`; ninguna se distribuye con la aplicación. La hoja `fonts.css` del origen
  estaba vacía y no se portó.
- **Iconos y otras dependencias de npm.** Se consumen como **paquetes**, no se copia su código al
  repositorio, y cada paquete lleva su propia licencia. Licencias declaradas por las versiones
  instaladas (leídas de su `package.json` el 2026-09-29):

  | Paquete | Versión | Licencia |
  | --- | --- | --- |
  | `lucide-react` (iconos) | 0.487.0 | ISC |
  | `recharts` (gráficas) | 2.15.2 | MIT |
  | `@radix-ui/react-dialog`, `-label`, `-select`, `-separator`, `-tooltip` | 1.1.23 / 2.1.15 / 2.3.7 / 1.1.15 / 1.2.16 | MIT |
  | `tailwindcss` | 4.3.3 | MIT |
  | `tw-animate-css` | 1.4.0 | MIT |
  | `clsx` | 2.1.1 | MIT |
  | `tailwind-merge` | 3.6.0 | MIT |

  El bundle que genera Vite incorpora el código de estos paquetes. Este archivo no sustituye a un
  inventario de licencias para una distribución externa de la aplicación: si algún día se distribuye
  fuera del equipo, ese inventario debería generarse con herramienta a partir del árbol de
  dependencias.

## Cómo mantener este archivo

Si se copia código de un tercero al repositorio (otro componente de shadcn/ui, un fragmento de otra
librería, una imagen o una fuente), añádelo aquí con su archivo, su licencia y el aviso de copyright que
esa licencia exija, en el mismo PR. Los primitivos de shadcn/ui autorizados están acotados por
[ADR-0004](../../docs/adr/ADR-0004-frontend-shadcn-ui.md).
