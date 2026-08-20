## Context

La épica de migración del frontend (Economicon → tfm-economicon) está diseñada en el spike
[docs/spikes/frontend-migration.md](../../../docs/spikes/frontend-migration.md) con estrategia de
**reemplazo completo** y **adopción de TypeScript**. El spike deja 6 supuestos `[ASUNCION]` sobre el
frontend de Economicon que no se pueden confirmar sin inspeccionar el repositorio origen. Economicon
está disponible como **carpeta hermana fuera del repo** (`../Economicon`).

Esta HU (`jup-083`, carril `light`, doc-only) resuelve esos supuestos mediante inspección en solo
lectura y documenta los hallazgos, sin tocar código de producto.

## Goals / Non-Goals

**Goals:**
- Confirmar con datos reales cada `[ASUNCION]` del spike: versión de React/Vite, routing, librería
  de datos/estado, auth/sesión, sistema de estilos, assets, variables `VITE_*`.
- Reemplazar cada `[ASUNCION]` en el spike por el dato confirmado y actualizar el checklist.
- Dejar un **inventario detallado** del frontend de Economicon en este `design.md`.

**Non-Goals:**
- Migrar, copiar o commitear código de Economicon en tfm-economicon (eso es F3 de la épica).
- Instalar dependencias, adoptar TypeScript o crear el ADR de TS (HU posterior de tooling, F2).
- Modificar el backend o los contratos de API.

## Decisions

- **Inspección en solo lectura, fuera del repo.** Economicon se lee desde `../Economicon`; nada suyo
  entra en el árbol de git de tfm-economicon. Alternativa descartada: clonarlo dentro con `.gitignore`
  (más riesgo de commitearlo por error).
- **Doble registro de hallazgos.** El dato corto y confirmado va al spike (reemplaza el `[ASUNCION]`);
  el detalle e evidencia va al inventario de este `design.md`. Da trazabilidad sin ensuciar el spike.
- **Un commit por supuesto.** Cada tarea de `tasks.md` resuelve un supuesto y se commitea aparte,
  para historial limpio y revisión granular.
- **Sin ADR.** No hay decisión de arquitectura nueva aquí; la adopción de TypeScript (con su ADR)
  pertenece a una HU posterior. Se declarará "ADR no aplicable" en la review.
- **Doc-only → archivar con `--skip-specs`.** No hay capability de producto; el spec de esta HU es
  un spec mínimo de proceso que no se promociona a `openspec/specs/`.
- **Snapshot del origen.** Se anota el commit hash de `../Economicon` inspeccionado, para que el
  inventario sea reproducible aunque Economicon cambie después.

## Risks / Trade-offs

- [Economicon expone endpoints que el backend de este repo no tiene] → Registrar como *finding* en
  `review.md` y en `openspec/findings/backlog.md`; no se resuelve aquí, alimenta la épica.
- [Un supuesto confirmado cambia el alcance de la épica (ej. no es React 18, o usa otro bundler)]
  → Documentar el impacto en el spike y avisar; puede requerir replanificar HUs posteriores.
- [El inventario queda obsoleto si Economicon evoluciona] → Mitigado anotando el commit hash del
  origen inspeccionado.

## Inventario del frontend de Economicon

> Esta sección se rellena durante `/opsx:apply` (una entrada por tarea). Estructura a completar:

- **Snapshot del origen:** ruta `../Economicon`, rama `main`, commit
  `1fe0030c054d81787bfd0c410f238a6f87a688f6`. El frontend vive en `Economicon/frontend/`
  (paquete `finops-dashboard-frontend`, generado con Figma Make).
- **T1 · React / Vite:** React **18.3.1** (`peerDependencies` react/react-dom 18.3.1) →
  compatible con el destino. Vite **6** (`devDependencies` `^6.4.2`, fijado a `6.3.5` vía
  `pnpm.overrides`), con `@vitejs/plugin-react` 4.7.0. **Salto de major respecto al destino**
  (Vite 5, `^5.3.3`): habrá que decidir versión de Vite al reconciliar el tooling.
- **T2 · Routing:** **react-router 7.13.0** con `createBrowserRouter` (API de data router).
  `src/app/routes.tsx` define 5 rutas anidadas bajo un `Layout`: index → `ExecutiveCostDashboard`,
  `/operational`, `/cuts`, `/anomalies`, `/recommendations`. Dependencia **nueva** respecto al
  destino, que hoy navega con estado manual `activeView` en `App.jsx` (sin router).
- **T3 · Librería de datos/estado:** **Ninguna.** No hay TanStack Query, Redux ni SWR; tampoco
  `fetch`, `axios` ni `import.meta.env` en `src` (0 coincidencias). Los dashboards renderizan
  **datos estáticos/mock** (export de Figma Make). Solo `react-hook-form` 7.55 para formularios.
  → El destino usa TanStack Query; la migración deberá **añadir toda la capa de datos** (traer el
  patrón `services/api.js` + fetching del destino a la UI de Economicon). **Finding para la épica.**
- **T4 · Auth / sesión:** **Ninguna.** No hay login, token, `Bearer` ni manejo de tenant en el
  origen (0 coincidencias). El destino tiene login (`POST /auth/login`), `Authorization: Bearer`,
  `X-Tenant-Id` y sesión en `localStorage` (`finops.session`, `finops.activeTenant`). → La migración
  deberá **añadir todo el flujo de auth/sesión/tenant** del destino sobre la UI de Economicon.
  **Finding para la épica.**
- **T5 · Sistema de estilos:** **Tailwind CSS v4** (`@tailwindcss/vite` + `tailwindcss` 4.1.12,
  `tw-animate-css`, `tailwind-merge`, `class-variance-authority`, `clsx`) + **shadcn/ui** (primitivos
  Radix UI, carpeta `src/app/components/ui/`) + **MUI 7** (`@mui/material` + `@emotion`) +
  `next-themes` para theming. Estilos en `src/styles/` (`fonts.css`, `index.css`, `tailwind.css`,
  `theme.css`); config vía `postcss.config.mjs` y el plugin Tailwind de Vite. → El destino usa un
  único `src/styles/main.css` plano (tema oscuro); adoptar este stack trae **muchas dependencias
  nuevas** y un tema propio a reconciliar.
- **T6 · Assets:** Mínimos. **Iconos** vía `lucide-react` (24 usos; `@mui/icons-material` está en
  deps pero no se usa). **Sin `src/assets`** materializado: el plugin `figmaAssetResolver` de
  `vite.config.ts` apunta a `src/assets` pero no hay imágenes (0 imports `figma:asset`);
  `ImageWithFallback` recurre a Unsplash. `src/styles/fonts.css` está **vacío** (sin fuentes
  propias). **Licencias** (`ATTRIBUTIONS.md`): shadcn/ui bajo MIT; fotos de Unsplash bajo su licencia
  → revisar la licencia de Unsplash si se usan imágenes reales en producción.
- **T7 · Variables de entorno `VITE_*`:** **Ninguna.** El origen no lee `import.meta.env` ni define
  variables `VITE_*` (0 coincidencias), coherente con la ausencia de capa de datos. El destino usa
  `VITE_API_BASE_URL` (def. `http://localhost:8000`) → se añadirá al integrar el fetching del destino.
