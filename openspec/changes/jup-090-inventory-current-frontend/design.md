JUP: JUP-090

## Context

La épica *Migrar frontend del repositorio Economicon* (spike
[docs/spikes/frontend-migration.md](../../../docs/spikes/frontend-migration.md)) adopta estrategia de
**reemplazo completo** de `apps/frontend`, conservando el pegamento del monorepo. El spike ya fija la
frontera a nivel conceptual ("se reemplaza" / "se preserva") y una tabla de conflictos, pero **no a
nivel de archivo**, y sus criterios de paridad no son ejecutables.

Estado actual del destino (verificado): `apps/frontend/` contiene `Dockerfile`, `README.md`,
`eslint.config.js`, `index.html`, `package.json`, `vite.config.js` y `src/{components,hooks,layouts,pages,services,styles}`
más `App.jsx` y `main.jsx`. Es JavaScript, sin router, con `services/api.js` como capa HTTP única y
sesión/tenant en `localStorage`.

JUP-083 confirmó que el **origen no aporta** capa de datos, auth ni tenant: son dashboards estáticos.
Por tanto el destino es la **única** fuente de esas capas y perderlas por sobrescritura sería
irreversible sin rehacerlas.

Esta HU (`jup-090`, carril `light`, **doc-only**) produce la línea base escrita que consumirán F2–F5.
No toca código de producto.

## Goals / Non-Goals

**Goals:**

- Clasificar **cada archivo** de `apps/frontend/**` y los puntos de integración del monorepo en
  `PRESERVAR` / `REEMPLAZAR` / `RECONCILIAR`, con justificación y evidencia (ruta + línea).
- Documentar qué se preserva del destino con evidencia verificable, no de memoria: nombre de paquete,
  scripts, host/puerto, Docker, `docker-compose.yml`, `VITE_API_BASE_URL`, turbo, workspace pnpm y
  los contratos del backend.
- Definir criterios de aceptación de paridad funcional login → selección de tenant → dashboard como
  **pasos verificables**, reutilizables tal cual como guion E2E en F5.
- Dejar la línea base en una ubicación estable que sobreviva al archivado del change.

**Non-Goals:**

- Modificar código, configuración o dependencias de `apps/frontend` (F2 y F3).
- Adoptar TypeScript ni redactar su ADR (tarjeta propia de F1).
- Clasificar las dependencias del **origen** (tarjeta `inventariar-frontend-economicon` de F1).
- Ejecutar la validación E2E (F5); aquí solo se **definen** sus criterios.
- Modificar el backend o sus contratos.

## Decisions

- **La línea base vive en `docs/planning/JUP-090-frontend-migration-baseline.md`, no en este
  `design.md`.** La consumen cuatro features posteriores (F2–F5) durante semanas; un documento de
  planificación compartido y commiteado es más localizable que un change archivado.
  *Alternativa descartada:* replicar el patrón de JUP-083 (inventario dentro de `design.md`); allí el
  inventario era el entregable terminal de una HU aislada, aquí es una referencia viva. La carpeta
  `docs/planning/` ya alberga documentos con este mismo patrón de nombre (`JUP-080-delivery-roadmap.md`).

- **Clasificación ternaria `PRESERVAR` / `REEMPLAZAR` / `RECONCILIAR`, no binaria.** La tabla de
  conflictos del spike demuestra que archivos como `package.json`, `eslint.config.js`,
  `vite.config.js` e `index.html` no admiten decisión binaria: requieren fusión dirigida.
  *Alternativa descartada:* preservar/reemplazar a secas, que obligaría a decidir la fusión durante la
  implementación, justo el problema que esta HU evita.

- **Inventario por inspección real del repo, con evidencia.** Cada fila cita ruta y, donde importe,
  línea concreta (p. ej. el puerto en el script `dev`, el servicio `frontend` de `docker-compose.yml`).
  El spike es *diseño*; esta línea base es *hecho verificado*. Si ambos discrepan, se corrige el spike
  y se anota la discrepancia.

- **Los contratos se toman del código, no solo del README.** `apps/frontend/README.md` lista los
  endpoints, pero la fuente de verdad es lo que `src/services/api.js` llama y lo que el backend
  expone. Cualquier divergencia entre README y código se registra como finding en lugar de resolverse
  aquí.

- **Criterios de paridad escritos como guion ejecutable.** Cada criterio se redacta con acción,
  endpoint implicado y resultado observable, con el seed `operator@example.com` / `secret`, para que
  F5 los ejecute sin reinterpretarlos.

- **Rollback explícito en la línea base.** Se documenta que el scaffold actual no se borra hasta que
  F5 valide E2E, y qué se necesita para revertir (rama dedicada, scaffold intacto en `develop`).

- **ADR no aplicable en esta HU.** No introduce ninguna decisión de arquitectura duradera: solo
  documenta el estado existente. La decisión duradera de la épica —adopción de TypeScript— tiene su
  propio ADR en la tarjeta correspondiente de F1, que esta línea base enlazará cuando exista.

- **Doc-only → archivar con `--skip-specs`.** No hay capability de producto; el spec de esta HU es un
  spec de proceso que no se promociona a `openspec/specs/`. Se omiten tester/coder/mutación del
  harness TDD y se documenta la excepción en `review.md`.

## Risks / Trade-offs

- **La línea base se desactualiza si F2/F3 cambian el destino antes de leerla.** → El documento fija
  el commit base sobre el que se hizo el inventario; las tarjetas posteriores comparan contra ese
  commit y anotan derivas.
- **Criterios de paridad demasiado vagos harían inútil la HU.** → Cada criterio debe nombrar endpoint
  y resultado observable; un criterio sin ambos no se acepta en la review.
- **Inventario incompleto por archivos generados o ignorados** (`node_modules`, cachés de Vite). → Se
  clasifican explícitamente como fuera de inventario, con la nota de limpiar `node_modules/.vite`
  tras el cambio de tooling.
- **Sobreingeniería del documento.** Es carril `light` y doc-only: el valor está en la tabla de
  clasificación y en los criterios de paridad, no en prosa. → Límite práctico: si una sección no la
  va a consumir una tarjeta de F2–F5, no se escribe.
- **El README del frontend puede contradecir al backend real.** → No se corrige aquí; se registra
  como finding `RF-090-<secuencia>` en `openspec/findings/backlog.md`.

## Migration Plan

1. Inventariar y clasificar sobre el commit base de la rama `docs/JUP-090-inventory-current-frontend`.
2. Publicar `docs/planning/JUP-090-frontend-migration-baseline.md` y enlazarlo desde el spike.
3. Las tarjetas F2–F5 consumen la línea base; cualquier desviación se anota en la review de esa
   tarjeta, no editando el histórico de esta.
4. **Rollback de esta HU:** revertir los dos ficheros de documentación. No hay impacto en runtime,
   build ni dependencias.

## Open Questions

- El número del ADR de adopción de TypeScript aún no existe; la línea base dejará el enlace como
  pendiente hasta que se cree la tarjeta correspondiente de F1.
- Queda por decidir en F2 si el salto de Vite 5 → Vite 6 se hace en la misma tarjeta de tooling o en
  una aparte; la línea base solo registra la divergencia, no la resuelve.
