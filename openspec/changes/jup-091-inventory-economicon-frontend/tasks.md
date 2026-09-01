## 1. Preparación

- [x] 1.1 Crear `docs/planning/JUP-091-economicon-source-inventory.md` con la cabecera: JUP, enlace
  Trello, rama, commit base de este repo, **commit snapshot de `../Economicon`** y el alcance
  excluido (`node_modules` y artefactos generados del origen).

## 2. Inventario de dependencias (una tarea = un bloque = un commit)

- [ ] 2.1 Extraer las 61 dependencias declaradas de `../Economicon/frontend/package.json`
  (`dependencies`, `devDependencies`, `peerDependencies`) y agrupar las familias coherentes
  (p. ej. los primitivos `@radix-ui/*`), dejando constancia del recuento de cada grupo.
- [ ] 2.2 Clasificar el stack de UI —Tailwind v4, shadcn/ui + Radix, MUI 7, `lucide-react`,
  `next-themes` y utilidades de estilo (`clsx`, `tailwind-merge`, `class-variance-authority`)— como
  `MANTENER` / `SUSTITUIR` / `DESCARTAR` con su motivo.
- [ ] 2.3 Clasificar el resto: React, Vite, `react-router`, `react-hook-form` y demás dependencias
  de runtime y desarrollo no cubiertas en 2.2.
- [ ] 2.4 Verificar uso real buscando imports en `../Economicon/frontend/src/`; marcar `DESCARTAR`
  las declaradas sin uso (JUP-083 ya detectó `@mui/icons-material`) y comprobar que la suma de filas
  y grupos cubre las 61 declaradas.

## 3. Mapeo pantalla → contrato del backend

- [ ] 3.1 Documentar, leyendo cada componente, qué datos muestra cada una de las 5 rutas:
  `index` → `ExecutiveCostDashboard`, `/operational` → `OperationalCostDashboard`, `/cuts` →
  `ExecutiveCutDashboard`, `/anomalies` → `AnomaliesPanel`, `/recommendations` →
  `RecommendationsPanel`.
- [ ] 3.2 Mapear cada pantalla al contrato del backend que debería alimentarla —tomándolo de
  `apps/frontend/src/services/api.js` y de la tabla de contratos de
  `docs/planning/JUP-090-frontend-migration-baseline.md`, no del README— o marcarla
  `SIN EQUIVALENTE`.
- [ ] 3.3 Agrupar los huecos detectados **por capacidad de backend ausente** (no por pantalla),
  citando en cada uno todas las rutas afectadas.

## 4. Cierre y verificación

- [ ] 4.1 Enlazar `docs/planning/JUP-091-economicon-source-inventory.md` desde
  `docs/spikes/frontend-migration.md` y marcar como completados los tres ítems de la tarjeta F1
  `inventariar-frontend-economicon`.
- [ ] 4.2 Verificar cobertura: la clasificación cubre las 61 dependencias declaradas y las 5 rutas
  están todas mapeadas con contrato o con `SIN EQUIVALENTE`.
- [ ] 4.3 Registrar en `review.md` y en `openspec/findings/backlog.md` (ID `RF-091-<secuencia>`) cada
  capacidad de backend ausente, sin resolverla aquí; anotar como riesgo si el resultado obliga a
  replanificar el alcance de F3.
- [ ] 4.4 Ejecutar `corepack pnpm openspec:validate` y
  `corepack pnpm jup:check -- --change jup-091-inventory-economicon-frontend`; registrar el resultado
  en `review.md` junto con la excepción doc-only del harness TDD (sin tester/coder/mutación).
