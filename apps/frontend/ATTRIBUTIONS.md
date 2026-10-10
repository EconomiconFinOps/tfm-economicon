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

## Marca Economicon y fuentes (JUP-112, 2026-10-10)

El logotipo es material del proyecto Economicon, procedente del dossier de marca de Lucía:
`materiales/05-marketing/economicon_dossier.pptx`, diapositiva 5, en el workspace de proyecto.
Se conservan los PNG originales, sin recoloración, recorte ni efectos; no se les atribuye una licencia
abierta no declarada. El componente `src/components/BrandMark.tsx` mantiene el espacio del original,
presenta el nombre como texto accesible y trata el símbolo adyacente como decorativo.

| Archivo distribuido | Origen dentro del PPTX | SHA-256 |
| --- | --- | --- |
| `src/assets/brand/economicon-primary.png` | `ppt/media/image2.png` | `3d642d739a7550827c60f32d281b8ad4d79df0fab9d1a5e683ae0bd96085d93e` |
| `src/assets/brand/economicon-inverse.png` | `ppt/media/image1.png` | `bb7aa6b5158edc020ccf92eec77a322a231efa3ac60dd8ca52806404cc61062e` |

Se empaquetan **Inter Variable** (UI) y **Space Grotesk Variable** (títulos), mediante las dependencias
`@fontsource-variable/inter` y `@fontsource-variable/space-grotesk`, con carga por rangos Unicode. Vite distribuye sus
archivos WOFF2 localmente; no se consulta Google Fonts ni una CDN al abrir la aplicación. Ambas fuentes
usan SIL Open Font License 1.1; las versiones exactas están fijadas en `pnpm-lock.yaml` y los paquetes
incluyen sus avisos en `LICENSE`. Se distribuyen copias literales en
`public/licenses/inter-OFL.txt` y `public/licenses/space-grotesk-OFL.txt`: Vite las conserva en
`dist/licenses/` junto al build. Fuentes y licencia originales:
[Inter](https://github.com/rsms/inter/blob/master/LICENSE.txt) y
[Space Grotesk](https://github.com/floriankarsten/space-grotesk/blob/master/OFL.txt).
El documento autónomo de impresión de `ExportButton` mantiene su fallback Arial y no descarga fuentes;
usa los mismos valores índigo y borde de la marca mediante las excepciones documentadas del guardián.

## Otras atribuciones

- **Fotografías de Unsplash.** No se portaron las fotografías del scaffold. Los únicos assets de marca
  incorporados por JUP-112 son los PNG oficiales anteriores.
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
