# Inventario del frontend origen — Economicon (JUP-091)

JUP: JUP-091
Trello: https://trello.com/c/pVfcfvhu/83-jup-091-inventariar-dependencias-y-endpoints-del-frontend-economicon-origen
OpenSpec change: `openspec/changes/jup-091-inventory-economicon-frontend/`
Rama: `docs/JUP-091-inventory-economicon-frontend`
Commit base de este repo: `b0c11f9`

## Snapshot del origen

- Ruta: `../Economicon/frontend` (carpeta hermana, **fuera** de este repo).
- Paquete: `finops-dashboard-frontend` (generado con Figma Make).
- Rama: `main` · Commit: `1fe0030c054d81787bfd0c410f238a6f87a688f6`.

Es el **mismo commit** que inspeccionó JUP-083, así que los 7 supuestos confirmados allí siguen
vigentes y este inventario los extiende en lugar de revisarlos.

## Alcance

Este documento completa las dos tareas de inventario del **origen** que el spike
[docs/spikes/frontend-migration.md](../spikes/frontend-migration.md) dejó abiertas en F1:

1. **Dependencias** clasificadas como `MANTENER` / `SUSTITUIR` / `DESCARTAR`.
2. **Pantallas → contratos** del backend de este repo, o `SIN EQUIVALENTE`.

Significado de las etiquetas de dependencia, fijado para que F2 no las reinterprete:

| Etiqueta | Significado |
| --- | --- |
| `MANTENER` | Entra al monorepo tal cual; el destino no tiene equivalente y la función es necesaria. |
| `SUSTITUIR` | El destino ya cubre esa función con otra librería, o exige cambio de versión mayor. |
| `DESCARTAR` | No aplica aquí: mock, dependencia sin uso real en el código, o función que la migración no porta. |

**Fuera de inventario:** `../Economicon/frontend/node_modules/**` y cualquier artefacto generado del
origen. Tampoco se inventaría el destino: eso es la
[línea base de JUP-090](JUP-090-frontend-migration-baseline.md).

## Clasificación de dependencias

### Inventario y agrupación

El origen declara **61 dependencias**: 55 en `dependencies`, 4 en `devDependencies` y 2 en
`peerDependencies`. Además fija `pnpm.overrides` con `vite: 6.3.5`, pese a declarar `^6.4.2`.

Se agrupan en cinco familias con decisión homogénea. El uso real se verificó leyendo todos los
`.ts/.tsx/.css/.mjs` de `src/` más `vite.config.ts`, `postcss.config.mjs` e `index.html`, no solo el
`package.json`.

| # | Grupo | Nº | Uso real verificado |
| --- | --- | --- | --- |
| G1 | Runtime de las pantallas | 5 | Importado por los 5 dashboards, `Layout`, `App` y `main` |
| G2 | Tooling y estilos | 5 | Usado por la config de build y `src/styles/` |
| G3 | shadcn/ui — primitivos Radix | 26 | Importado **solo** desde `src/app/components/ui/` |
| G4 | shadcn/ui — librerías de apoyo | 12 | Importado **solo** desde `src/app/components/ui/` |
| G5 | Declaradas sin ningún import | 13 | **Cero** referencias en todo el árbol inspeccionado |
| | **Total** | **61** | |

**G1 · Runtime de las pantallas (5)**
`react` 18.3.1 · `react-dom` 18.3.1 (ambas en `peerDependencies`) · `react-router` 7.13.0 ·
`recharts` 2.15.2 · `lucide-react` 0.487.0

**G2 · Tooling y estilos (5)**
`vite` ^6.4.2 (override a 6.3.5) · `@vitejs/plugin-react` 4.7.0 · `tailwindcss` 4.1.12 ·
`@tailwindcss/vite` 4.1.12 · `tw-animate-css` 1.3.8 (referenciada desde `src/styles/tailwind.css`)

**G3 · shadcn/ui — primitivos Radix (26)**
`@radix-ui/react-*`: accordion, alert-dialog, aspect-ratio, avatar, checkbox, collapsible,
context-menu, dialog, dropdown-menu, hover-card, label, menubar, navigation-menu, popover, progress,
radio-group, scroll-area, select, separator, slider, slot, switch, tabs, toggle, toggle-group,
tooltip

**G4 · shadcn/ui — librerías de apoyo (12)**
`class-variance-authority` · `clsx` · `tailwind-merge` · `cmdk` · `embla-carousel-react` ·
`input-otp` · `next-themes` · `react-day-picker` · `react-hook-form` · `react-resizable-panels` ·
`sonner` · `vaul`

**G5 · Declaradas sin ningún import (13)**
`@mui/material` · `@mui/icons-material` · `@emotion/react` · `@emotion/styled` · `@popperjs/core` ·
`react-popper` · `canvas-confetti` · `date-fns` · `motion` · `react-dnd` · `react-dnd-html5-backend` ·
`react-responsive-masonry` · `react-slick`

### Hecho decisivo: la carpeta `ui/` no la usa nadie

Los 5 dashboards, `Layout` y `ExportButton` **no importan ni un solo componente** de
`src/app/components/ui/`; su único import relativo es `./ExportButton`. Los **48 archivos** de esa
carpeta son código muerto del export de Figma Make, y con ellos los **38 paquetes** de G3+G4 que solo
esa carpeta referencia.

En términos prácticos: de 61 dependencias declaradas, solo **10** (G1+G2) sostienen lo que hoy
renderiza la aplicación.

Esto **corrige a JUP-083**, cuyo supuesto T5 describía el stack como "Tailwind v4 + shadcn/ui +
MUI 7 + next-themes": MUI nunca se usa (G5) y shadcn/ui solo existe como código muerto. Ver
`RF-091-001` y `RF-091-002` en la sección de hallazgos.

<!-- La clasificación MANTENER/SUSTITUIR/DESCARTAR se completa en las tareas 2.2-2.4 -->

## Mapeo de pantallas a contratos del backend

<!-- Se completa en las tareas 3.1-3.3 -->

## Hallazgos

<!-- Se completa en la tarea 4.3 -->
