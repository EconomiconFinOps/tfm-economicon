## ADDED Requirements

### Requirement: Línea base del frontend destino antes del reemplazo

La épica de migración del frontend SHALL disponer de una línea base escrita y commiteada que
clasifique cada archivo de `apps/frontend/**` y cada punto de integración del monorepo como
`PRESERVAR`, `REEMPLAZAR` o `RECONCILIAR`, con evidencia de ruta, antes de que ninguna tarjeta
modifique el tooling o el código fuente del frontend.

#### Scenario: Clasificación completa y con evidencia

- **WHEN** se completa el inventario del destino para esta HU
- **THEN** existe `docs/planning/JUP-090-frontend-migration-baseline.md` con una tabla en la que cada
  archivo de `apps/frontend/**` (excluyendo artefactos generados) tiene exactamente una de las
  etiquetas `PRESERVAR`, `REEMPLAZAR` o `RECONCILIAR`
- **AND** cada fila cita la ruta del archivo y, cuando la decisión depende de un detalle concreto, la
  línea que lo respalda
- **AND** los puntos de integración del monorepo —nombre `@finops/frontend`, scripts, host/puerto
  5173, `Dockerfile`, servicio `frontend` de `docker-compose.yml`, `VITE_API_BASE_URL`, turbo y
  workspace pnpm— aparecen clasificados de forma explícita

#### Scenario: Ningún archivo del destino queda sin decisión

- **WHEN** una tarjeta posterior de la épica necesita saber si un archivo del destino se conserva
- **THEN** la línea base contiene ese archivo con su etiqueta y su justificación
- **AND** si el archivo no está inventariado, la tarjeta lo registra como deriva en su propia review
  en lugar de decidirlo de forma implícita

### Requirement: Criterios de paridad funcional verificables

La línea base SHALL definir los criterios de aceptación de paridad funcional del recorrido
login → selección de tenant → dashboard como pasos verificables, de forma que la validación E2E de la
épica pueda ejecutarlos sin reinterpretarlos.

#### Scenario: Criterio con endpoint y resultado observable

- **WHEN** se redacta un criterio de paridad en la línea base
- **THEN** el criterio nombra la acción del usuario, el endpoint del backend implicado y el resultado
  observable esperado
- **AND** el recorrido cubre como mínimo autenticación con el seed `operator@example.com` / `secret`,
  obtención del perfil, listado y selección de tenant, y carga del dashboard con
  `X-Tenant-Id` propagado

#### Scenario: Regla de rollback registrada

- **WHEN** se publica la línea base
- **THEN** el documento declara que el scaffold actual de `apps/frontend` no se elimina hasta que la
  validación E2E de la épica pase
- **AND** describe qué se necesita para revertir la migración

### Requirement: Huecos entre origen y contratos registrados como findings

El inventario SHALL registrar como finding toda divergencia detectada entre la documentación del
frontend, su código y los contratos del backend, en lugar de resolverla dentro de esta HU.

#### Scenario: Divergencia entre README y código

- **WHEN** el inventario detecta que `apps/frontend/README.md` describe un endpoint que
  `src/services/api.js` no llama, o que el backend no expone
- **THEN** la divergencia se registra en el `review.md` de la HU y en `openspec/findings/backlog.md`
  con un ID `RF-090-<secuencia>`
- **AND** no se modifica el README ni la capa API dentro de esta HU
