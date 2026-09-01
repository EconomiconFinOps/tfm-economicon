JUP: JUP-091

## Context

La épica de migración del frontend ya tiene inventariados el destino (JUP-090,
[línea base](../../../docs/planning/JUP-090-frontend-migration-baseline.md)) y los supuestos del
origen (JUP-083). Falta el inventario **detallado** del origen, que el spike dejó como dos ítems
abiertos de la tarjeta `inventariar-frontend-economicon`.

Estado verificado del origen (`../Economicon/frontend`, paquete `finops-dashboard-frontend`):

- **61 dependencias declaradas**: 55 en `dependencies`, 4 en `devDependencies`, 2 en
  `peerDependencies` (react/react-dom 18.3.1).
- **5 rutas** en `src/app/routes.tsx` con `createBrowserRouter`, todas anidadas bajo `Layout`:
  `index` → `ExecutiveCostDashboard`, `/operational` → `OperationalCostDashboard`, `/cuts` →
  `ExecutiveCutDashboard`, `/anomalies` → `AnomaliesPanel`, `/recommendations` →
  `RecommendationsPanel`.
- Sin capa de datos: las 5 pantallas renderizan datos estáticos/mock (confirmado en T3 de JUP-083).

Contra eso, el backend de este repo expone un único contrato de costes (`GET /billing/summary`, con
`monthly_spend` y `savings_identified`). El desajuste entre 5 dashboards de analítica y un endpoint
de resumen es la hipótesis que esta HU debe cuantificar.

Esta HU (`jup-091`, carril `light`, **doc-only**) produce ese inventario. No toca código de producto.

## Goals / Non-Goals

**Goals:**

- Clasificar las **61 dependencias** del origen como `MANTENER` / `SUSTITUIR` / `DESCARTAR` con
  justificación, de forma que F2 pueda reconciliar `package.json` sin decidir caso a caso.
- Mapear cada una de las **5 pantallas** del origen al contrato del backend que debería alimentarla,
  o marcarla `SIN EQUIVALENTE`.
- Cuantificar el hueco real entre la UI del origen y el backend actual, como insumo de planificación
  para F3 y para la decisión de si hace falta backend nuevo.
- Dejar el inventario en una ubicación estable que sobreviva al archivado del change.

**Non-Goals:**

- Decidir **si** se construye el backend faltante, o con qué prioridad: eso es otra épica/tarjeta.
- Instalar, actualizar o resolver versiones de dependencias (F2).
- Migrar, copiar o commitear código del origen (F3).
- Reconciliar la capa API o el flujo de auth (F3).
- Repetir el checklist de supuestos ya cerrado en JUP-083.

## Decisions

- **El inventario vive en `docs/planning/JUP-091-economicon-source-inventory.md`.** Mismo criterio
  que JUP-090: lo consumen F2 y F3 durante semanas, así que un documento de planificación commiteado
  es más localizable que un change archivado. *Alternativa descartada:* el patrón de JUP-083
  (inventario dentro de `design.md`), que allí funcionó porque era el entregable terminal de una HU
  aislada.

- **Taxonomía ternaria `MANTENER` / `SUSTITUIR` / `DESCARTAR`.** Es literalmente la que pide el spike
  ("clasificarlas (mantener / sustituir / descartar)"). Significados fijados para que F2 no
  reinterprete: `MANTENER` = entra al monorepo tal cual; `SUSTITUIR` = el destino ya cubre esa
  función con otra librería, o hay que cambiar de versión mayor; `DESCARTAR` = no aplica aquí (mock,
  backend ficticio, o dependencia sin uso real en el código).

- **Clasificación por grupo cuando la familia es coherente, por dependencia cuando no.** 61 filas
  individuales sería ruido en un carril `light`: los ~25 primitivos `@radix-ui/*` que shadcn/ui
  arrastra comparten exactamente la misma decisión. Se clasifican en bloque, nombrando el grupo y su
  recuento, y se desglosan individualmente solo las que tengan decisión propia (React, Vite, MUI,
  react-router, Tailwind, lucide-react, react-hook-form…). Cada fila cita el motivo.

- **Verificar uso real, no solo declaración.** Una dependencia declarada puede no usarse: JUP-083 ya
  detectó que `@mui/icons-material` está en `dependencies` pero no se importa en el código. La
  clasificación se apoya en búsqueda de imports en `src/`, no solo en `package.json`.

- **El mapeo va de pantalla a contrato, con el código como fuente de verdad.** Para cada ruta se
  documenta qué muestra leyendo su componente, y se contrasta contra los contratos reales de
  `apps/frontend/src/services/api.js` y la tabla de contratos de la línea base de JUP-090 — no contra
  el README, que JUP-090 ya demostró que puede divergir (`RF-090-003`).

- **Un finding por capacidad de backend ausente, no por pantalla.** Si dos pantallas necesitan el
  mismo endpoint inexistente, es un solo hueco, no dos. Agrupar por capacidad evita inflar el backlog
  y refleja mejor el trabajo real que implicaría cerrarlo.

- **Snapshot del origen.** Se anota el commit hash inspeccionado de `../Economicon`, igual que
  JUP-083, para que el inventario sea reproducible aunque el origen cambie después.

- **ADR no aplicable.** No introduce ninguna decisión de arquitectura duradera: documenta el estado
  de un repositorio externo. La decisión duradera de la épica —adopción de TypeScript— tiene su
  propio ADR en la tarjeta correspondiente de F1.

- **Doc-only → archivar con `--skip-specs`.** No hay capability de producto; el spec de esta HU es de
  proceso y no se promociona a `openspec/specs/`. Se omiten tester/coder/mutación del harness TDD y
  se documenta la excepción en `review.md`.

## Risks / Trade-offs

- **El hueco backend puede resultar enorme** (hipótesis: 4 de 5 pantallas sin equivalente). → No se
  resuelve aquí; se cuantifica y se registra como findings. Si el resultado invalida el alcance de F3
  tal como está escrito en el spike, se anota como riesgo para replanificar, igual que hizo JUP-083
  con `RF-083-002`.
- **Clasificar 61 dependencias puede desbordar un carril `light`.** → Mitigado por la clasificación
  en bloque de familias coherentes; el criterio de corte es que cada fila aporte una decisión, no un
  dato.
- **El inventario queda obsoleto si Economicon evoluciona.** → Mitigado anotando el commit hash del
  origen inspeccionado.
- **Riesgo de invadir F2/F3.** Es tentador decidir versiones o diseñar endpoints al ver los huecos. →
  El documento clasifica y mapea; toda decisión de implementación se deja explícitamente a su
  tarjeta.

## Migration Plan

1. Inventariar sobre el commit base de la rama `docs/JUP-091-inventory-economicon-frontend` y el
   commit snapshot de `../Economicon`.
2. Publicar `docs/planning/JUP-091-economicon-source-inventory.md` y enlazarlo desde el spike.
3. F2 y F3 consumen el inventario; cualquier desviación se anota en la review de esa tarjeta.
4. **Rollback de esta HU:** revertir los tres ficheros de documentación. Sin impacto en runtime,
   build ni dependencias.

## Open Questions

- Si el mapeo confirma que la mayoría de pantallas no tienen backend, queda por decidir (fuera de
  esta HU) si F3 porta esas pantallas con datos mock a la espera de backend, o si se recortan del
  alcance de la migración.
- El número del ADR de adopción de TypeScript aún no existe; el inventario dejará el enlace pendiente
  hasta que se cree la tarjeta correspondiente de F1.
