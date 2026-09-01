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

### Clasificación · stack de UI

| Dependencia / grupo | Nº | Clasificación | Motivo |
| --- | --- | --- | --- |
| `tailwindcss` 4.1.12 + `@tailwindcss/vite` | 2 | `MANTENER` | Sistema de estilos que la migración adopta; el destino solo tiene un `main.css` plano marcado `REEMPLAZAR` en la línea base de JUP-090. Salto de mayor (v4) sin equivalente en el destino. |
| `tw-animate-css` 1.3.8 | 1 | `MANTENER` | Referenciada desde `src/styles/tailwind.css`; acompaña a Tailwind v4 y es de coste nulo. |
| `lucide-react` 0.487.0 | 1 | `MANTENER` | Único set de iconos del origen, con 6 usos reales en los dashboards. El destino no tiene iconos: es capacidad nueva, no duplicada. |
| `clsx` · `tailwind-merge` · `class-variance-authority` | 3 | `MANTENER` | Utilidades genéricas de composición de clases Tailwind; útiles con o sin shadcn/ui, y el destino las necesitará al pasar a Tailwind. |
| **G3** · primitivos `@radix-ui/*` | 26 | `DESCARTAR` | Ninguno se importa fuera de `src/app/components/ui/`, que a su vez no usa ninguna pantalla. Ver la salvedad de abajo y `RF-091-002`. |
| `cmdk` · `embla-carousel-react` · `input-otp` · `react-day-picker` · `react-resizable-panels` · `sonner` · `vaul` | 7 | `DESCARTAR` | Paleta de comandos, carrusel, OTP, datepicker, paneles redimensionables, toasts y drawer: funciones que ni el origen renderiza ni el destino tiene. No las pide ninguna pantalla conocida de la épica. |
| `react-hook-form` 7.55.0 | 1 | `DESCARTAR` | Solo la importa `ui/form.tsx`, componente muerto. Los formularios del destino (login, ingesta, chat) usan estado controlado de React sin librería; migrarlos a react-hook-form sería alcance nuevo, no paridad. |
| `next-themes` 0.4.6 | 1 | `DESCARTAR` | Alterna tema claro/oscuro. El destino tiene un **único** tema oscuro fijo y la épica no plantea conmutador de tema; adoptarlo sería funcionalidad nueva. |
| `@mui/material` · `@mui/icons-material` · `@emotion/react` · `@emotion/styled` | 4 | `DESCARTAR` | **MUI 7 no se usa en absoluto**: cero imports en todo el árbol. `@emotion/*` solo existe como peer de MUI. Contradice el supuesto T5 de JUP-083. Ver `RF-091-001`. |
| | **46** | | |

**Salvedad sobre G3 + shadcn/ui (entrada para F2, no decisión de esta HU).** La etiqueta `DESCARTAR`
refleja el **uso actual en el origen**, donde nada renderiza esos componentes. Pero el destino sí
necesita primitivos de formulario: sus pantallas usan hoy 8 `<button>`, 6 `<label>`, 5 `<input>`,
2 `<textarea>` y 1 `<select>` en HTML plano. Si F2 decide adoptar shadcn/ui deliberadamente como
sistema de diseño —opción razonable al pasar a Tailwind v4—, el subconjunto de Radix realmente
necesario para login, selector de tenant, ingesta y chat sería del orden de **4-6 paquetes**
(`label`, `select`, `slot`, `separator` y quizá `dialog`/`tooltip`), no los 26 declarados. La
decisión es de F2; aquí solo se documenta el coste de cada camino (`RF-091-002`).

### Clasificación · runtime, routing, build y sobrantes

| Dependencia / grupo | Nº | Clasificación | Motivo |
| --- | --- | --- | --- |
| `react` 18.3.1 · `react-dom` 18.3.1 | 2 | `MANTENER` | Misma versión exacta que el destino (`^18.3.1`): sin salto ni riesgo de dos Reacts en el árbol. En el origen están en `peerDependencies`; al integrarse en el monorepo pasan a `dependencies` como ya lo están en `@finops/frontend`. |
| `react-router` 7.13.0 | 1 | `MANTENER` | Dependencia **nueva** para el destino, que hoy navega con estado manual `activeView` en `App.jsx`. El spike ya decidió adoptar el routing del origen (T2 de JUP-083). |
| `recharts` 2.15.2 | 1 | `MANTENER` | Única librería de gráficos, con uso real en los 5 dashboards. El destino no tiene gráficos: capacidad nueva, no duplicada. |
| `vite` ^6.4.2 (override 6.3.5) · `@vitejs/plugin-react` 4.7.0 | 2 | `SUSTITUIR` | El destino usa Vite **5** (`^5.3.3`) y plugin 4.3.1. Salto de mayor 5→6 que F2 debe resolver explícitamente; no se arrastra la versión del origen sin decidirlo. Ojo al `pnpm.overrides` que fija 6.3.5 pese a declarar `^6.4.2`: es una inconsistencia del origen que no debe copiarse a ciegas. |
| `date-fns` 3.6.0 | 1 | `DESCARTAR` | Cero imports propios; solo existe como dependencia transitiva esperada por `react-day-picker`, que a su vez se descarta. |
| `motion` 12.23.24 | 1 | `DESCARTAR` | Librería de animación sin ningún import. El origen no anima nada. |
| `canvas-confetti` 1.9.4 | 1 | `DESCARTAR` | Sin imports. Efecto decorativo ajeno a un producto FinOps. |
| `react-dnd` · `react-dnd-html5-backend` | 2 | `DESCARTAR` | Drag and drop sin imports; ninguna pantalla del origen ni del destino lo requiere. |
| `@popperjs/core` · `react-popper` | 2 | `DESCARTAR` | Posicionamiento de popovers sin imports; Radix ya trae el suyo si se adoptara shadcn. |
| `react-responsive-masonry` · `react-slick` | 2 | `DESCARTAR` | Layout masonry y carrusel sin imports; sin equivalente ni necesidad en la épica. |
| | **15** | | |

**Nota sobre `dependencies` vs `peerDependencies`.** El origen declara React y React-DOM solo como
`peerDependencies`, algo propio de una librería, no de una aplicación: sin `dependencies` ni
lockfile propio coherente, el árbol se resuelve por lo que instale quien lo consuma. Al integrarse en
el monorepo esa distinción desaparece —`@finops/frontend` ya las lleva en `dependencies`— pero
conviene que F2 lo haga de forma consciente y no por arrastre.

### Resumen de la clasificación

| Clasificación | Nº | Detalle |
| --- | --- | --- |
| `MANTENER` | 11 | React (2), react-router, recharts, lucide-react, Tailwind (2), tw-animate-css, utilidades de clases (3) |
| `SUSTITUIR` | 2 | Vite y `@vitejs/plugin-react` (salto de mayor 5→6 a decidir en F2) |
| `DESCARTAR` | 48 | 26 Radix + 7 apoyo shadcn + react-hook-form + next-themes + MUI/emotion (4) + 9 sin ningún import |
| **Total** | **61** | Coincide con lo declarado |

### Método de verificación

El uso real no se dedujo del `package.json` sino leyendo el código, y la cobertura se comprobó de
forma automática para que no dependa de un recuento a ojo:

1. **Detección de uso.** Se concatenó el contenido de todos los `.ts`, `.tsx`, `.css` y `.mjs` bajo
   `src/`, más `vite.config.ts`, `postcss.config.mjs` e `index.html`, y se buscó cada nombre
   declarado como especificador de import (entre comillas, seguido de `/` o de cierre). Resultado:
   **13 dependencias sin una sola referencia** en todo el árbol —las de G5—, incluidas las cuatro de
   MUI/Emotion.
2. **Alcance del uso.** Para separar "lo usa la aplicación" de "lo usa código muerto", se repitió la
   búsqueda restringida a las pantallas reales (`App`, `routes`, `Layout`, los 5 dashboards,
   `ExportButton`, `main`) y por separado a `src/app/components/ui/`. Confirmó que **38 paquetes**
   solo los alcanza `ui/`, que ninguna pantalla importa.
3. **Cobertura.** Se verificó que cada uno de los 61 nombres declarados aparece en este documento
   —los `@radix-ui/*` a través de su entrada de grupo—. Resultado: **0 dependencias sin clasificar**.

Reproducible sobre el commit `1fe0030` del origen indicado en el snapshot.

## Mapeo de pantallas a contratos del backend

### Qué muestra cada pantalla

Las 5 rutas de `src/app/routes.tsx`, todas anidadas bajo `Layout`. Los datos son constantes estáticas
declaradas en el propio componente (confirmado en T3 de JUP-083): no hay `fetch` en ninguna.

| Ruta | Componente | Datos que renderiza (constantes del archivo) |
| --- | --- | --- |
| `index` | `ExecutiveCostDashboard` | `monthlyData`: serie mensual de coste total desglosado en compute/storage/network · `serviceData`: reparto porcentual por servicio · `kpiData`: 4 KPIs (coste total mensual, coste por servicio, ahorro potencial, recursos activos) con variación y tendencia |
| `/operational` | `OperationalCostDashboard` | `detailedData`: filas por servicio con proyecto, coste, % de uso, tendencia y **proveedor** (AWS/Azure/GCP) · `hourlyData`: coste por franja horaria · `providerData`: coste por proveedor desglosado en compute/storage/network |
| `/cuts` | `ExecutiveCutDashboard` | `savingsData`: ahorro mensual objetivo vs. alcanzado vs. pendiente · `cutActions`: acciones de recorte con impacto en €, estado, **responsable** y fecha · `kpiData` |
| `/anomalies` | `AnomaliesPanel` | `anomalies`: incidencias con tipo, servicio/región, severidad y descripción · `trendData`: evolución de anomalías · `stats` |
| `/recommendations` | `RecommendationsPanel` | `recommendations`: recomendaciones con título, categoría, descripción y **ahorro estimado** · `savingsByCategory` · `stats` |

Tres rasgos transversales de los datos del origen que condicionan el mapeo:

- **Multi-cloud.** El origen modela AWS, Azure y GCP (`proveedor` en `detailedData` y `providerData`).
  El backend de este repo solo ingiere Azure (`apps/azure-cost-api`, JUP-072 a JUP-077).
- **Granularidad temporal y por recurso.** Series mensuales, por hora y filas por servicio/proyecto.
  El backend expone un único resumen agregado sin dimensión temporal.
- **Entidades de gestión inexistentes.** Acciones de recorte con responsable y estado, anomalías y
  recomendaciones son entidades de negocio que el backend no modela en absoluto.

<!-- El mapeo a contratos se completa en la tarea 3.2 -->

## Hallazgos

<!-- Se completa en la tarea 4.3 -->
