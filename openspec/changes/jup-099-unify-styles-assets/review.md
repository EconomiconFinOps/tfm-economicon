# Review — JUP-099 unify-styles-assets

## Grupo 1. Línea base

**1.1 — Línea base de la suite.** Sustituto usado (RF-093-001 sigue abierto: turbo resuelve un pnpm
global en subprocesos por paquete en esta máquina, así que no se pasa por turbo):
`corepack pnpm --filter @finops/frontend test`, sobre `7eef7ca` (`688fe2d` + solo artefactos del
change; `git diff 688fe2d HEAD -- apps/frontend` vacío).

```
Test Files  46 passed (46)
     Tests  261 passed (261)
```

Línea base: **261 PASS / 0 FAIL**, 46 archivos. Cada grupo posterior debe mantener 261 PASS más los
tests nuevos de los grupos 3 en adelante (los guardianes del grupo 3 fallan a propósito hasta que se
migra cada archivo).

**1.2 — Inventario de partida** (`apps/frontend/src`, excluidos los `*.test.*`; ejecutado el
2026-09-29 sobre `7eef7ca`):

| Medida | Resultado | Comando |
| --- | --- | --- |
| Hexadecimales en `.tsx` | **241** en **14** archivos | `grep -rnoE '#[0-9a-fA-F]{3,8}\b' --include=*.tsx . \| grep -v '\.test\.tsx' \| wc -l` (y `grep -rlE` para los archivos) |
| Hexadecimales en datos demo | **4** (`data/demo/executiveCostDashboard.ts`) | `grep -rnoE '#[0-9a-fA-F]{6}\b' data/demo/*.ts \| wc -l` |
| Utilidades de la paleta de Tailwind | **229** en **16** archivos | `grep -rhoE '\b(text\|bg\|border\|ring\|fill\|stroke\|from\|to\|via\|outline\|divide\|placeholder\|shadow\|decoration\|accent\|caret)-(slate\|gray\|zinc\|neutral\|stone\|red\|orange\|amber\|yellow\|lime\|green\|emerald\|teal\|cyan\|sky\|blue\|indigo\|violet\|purple\|fuchsia\|pink\|rose\|white\|black)(-[0-9]{2,3})?(/[0-9]+)?\b' --include=*.tsx . --exclude=*.test.tsx \| wc -l` |
| Referencias a `main.css` | **3** (comentarios de `MetricCard`, `SectionCard`, `StatusPill`) | `grep -rniE 'main\.css' apps/frontend --exclude-dir=node_modules --exclude-dir=dist` |
| Variables declaradas en `theme.css` | **110** (`:root` + `.dark`; 34 expuestas como `--color-*` en `@theme inline`) | `grep -cE '^\s+--[a-z0-9-]+:' src/styles/theme.css` |

Los 241 hexadecimales son 16 valores distintos: `#2d3748` ×68, `#1a1f2e` ×39, `#0078d4` ×32,
`#232834` ×29, `#0f1419` ×19, `#94a3b8` ×16, `#00bcf2` ×12, `#fff` ×9, `#10b981` ×5, `#64748b` ×3 y el
resto ×1-2. Formas de uso: 169 clases arbitrarias (`bg-[#…]`), 42 atributos `fill`/`stroke` de
Recharts, 18 objetos `contentStyle`/`style`, más el HTML de exportación de `ExportButton`. Ninguno
de los 46 archivos de test comprueba clases de color (solo `rounded-md`, `shrink-0`, `text-sm`), así
que la suite no debería cambiar con la migración.

Utilidades de paleta más repetidas: `text-slate-400` ×66, `text-white` ×65, `text-red-400` ×11,
`text-slate-300` ×10, `text-green-400` ×6. `src/components/ui/dialog.tsx` aporta 1 (`bg-black/50`,
excepción prevista, decisión 5 de `design.md`).

**1.3 — Guion de captura preparado.** Proyecto temporal **fuera del repositorio** (`npm install
playwright pixelmatch pngjs`; Playwright 1.63.0, Chromium 1243 ya presente en el caché local, sin
descargas nuevas). Nada entra en `package.json`. Dos archivos: `capture.mjs` (sirve un build de
producción con servidor estático y fallback SPA, API simulada con `page.route`, viewport 1440×900,
`es-ES`, zona `Europe/Madrid`, movimiento reducido, espera fija de 3 s) y `compare.mjs`
(`pixelmatch`, umbral 0, `includeAA`). Se copian íntegros a `docs/evidence/JUP-099-validation.md`
en la tarea 10.3.

Dos problemas del guion descubiertos y corregidos **antes** de dar la referencia por buena (ambos
dejaban las series de Recharts sin pintar, lo que habría hecho inútil la comparación de los
`fill`/`stroke`):

1. `fullPage: true` redimensiona el viewport durante la captura; `ResponsiveContainer` re-renderiza
   y Recharts reinicia su animación justo antes de la foto. Se amplía el viewport a la altura del
   documento, se espera y se captura el viewport tal cual.
2. La fecha del `Layout` (`new Date()`) hace la captura dependiente del día. Se fija solo `new Date()`
   sin argumentos; `Date.now` se deja real (`page.clock.setFixedTime` lo congela, y se descartó por
   sospecha de afectar a la animación; el arreglo real fue el punto 1).

**1.4 — Referencia "antes" capturada** sobre el build de `7eef7ca` (frontend idéntico a `688fe2d`).
14 capturas cubriendo las 9 pantallas y sus estados con color propio:

| Captura | Pantalla / estado |
| --- | --- |
| `login`, `login-invalid-credentials`, `login-session-expired` | `/login`; error en rojo (`text-red-400`); aviso ámbar de JUP-098 (`text-amber-400`) |
| `executive-cost`, `executive-cost-export-menu`, `executive-cost-tenant-select-focus` | `/`; menú de `ExportButton` abierto; foco del selector de ámbito (`focus:border-[#00bcf2]`) |
| `operational-cost`, `executive-cuts`, `anomalies`, `recommendations` | `/operational`, `/cuts`, `/anomalies`, `/recommendations` |
| `overview-legacy` | `/overview-legacy` |
| `ingest`, `ingest-error` | `/ingest`; error de la mutación en rojo |
| `assistant` | `/assistant` con conversación seleccionada y borrador |

**Determinismo verificado:** dos pasadas seguidas sobre el mismo build → `TOTAL 0` píxeles distintos
en las 14 capturas (`node compare.mjs shots-before-1 shots-before-2`). Sin esto no se podría atribuir
ninguna diferencia posterior a la migración.

**Diferencia esperada anotada desde ya (para explicarla en 8.1, no es un fallo del guion):** en las
pantallas más cortas que el viewport (`ingest`, `ingest-error`, `assistant`, `overview-legacy`) la
franja bajo el contenido es el fondo del `body`, hoy `#0a0a0a` (`oklch(0.145 0 0)` de shadcn). El
`Layout` pinta `#0f1419` solo hasta donde llega su contenido. Al mapear `background` a `#0f1419`, la
franja pasará a `#0f1419`: cambio visible, deliberado y coherente con el resto de la pantalla, pero
una diferencia real que se declarará y aceptará en la tarea 8.1.

**Checkpoint:** grupo sin código de producto ni tests nuevos (solo medición y capturas fuera del
repositorio) → sin ciclo Red/Green ni mutación (excepción doc-only). Único cambio en el repositorio:
este `review.md` y las casillas de `tasks.md`.
