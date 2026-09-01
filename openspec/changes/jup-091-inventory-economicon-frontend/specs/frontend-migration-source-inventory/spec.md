## ADDED Requirements

### Requirement: Dependencias del origen clasificadas antes de reconciliar el tooling

El inventario del origen SHALL clasificar cada dependencia declarada en
`../Economicon/frontend/package.json` como `MANTENER`, `SUSTITUIR` o `DESCARTAR`, con su
justificación, antes de que ninguna tarjeta modifique `apps/frontend/package.json`.

#### Scenario: Cobertura completa de las dependencias declaradas

- **WHEN** se completa la clasificación de dependencias del origen
- **THEN** existe `docs/planning/JUP-091-economicon-source-inventory.md` con una tabla que cubre las
  59 dependencias declaradas (`dependencies`, `devDependencies` y `peerDependencies`)
- **AND** cada fila lleva exactamente una de las etiquetas `MANTENER`, `SUSTITUIR` o `DESCARTAR` con
  su motivo
- **AND** cuando una familia coherente de dependencias se clasifica en bloque, la fila nombra el
  grupo y su recuento, de forma que la suma de filas cubra el total declarado

#### Scenario: Dependencia declarada pero sin uso real

- **WHEN** la inspección detecta que una dependencia declarada no se importa en `src/`
- **THEN** se clasifica como `DESCARTAR` y el motivo indica explícitamente que no tiene uso real en
  el código del origen

### Requirement: Pantallas del origen mapeadas a los contratos del backend

El inventario del origen SHALL documentar, para cada una de las cinco rutas de
`src/app/routes.tsx`, qué datos muestra y qué contrato del backend de este repo debería
suministrarlos, marcando `SIN EQUIVALENTE` cuando ese contrato no exista.

#### Scenario: Mapeo de una pantalla con contrato disponible

- **WHEN** se documenta una ruta del origen cuyos datos puede suministrar un contrato existente
- **THEN** la fila nombra la ruta, su componente, el dato que muestra y el contrato concreto del
  backend que lo cubriría
- **AND** el contrato se toma de `apps/frontend/src/services/api.js` o de la tabla de contratos de la
  línea base de JUP-090, no del README

#### Scenario: Mapeo de una pantalla sin contrato disponible

- **WHEN** se documenta una ruta del origen cuyos datos ningún contrato del backend actual cubre
- **THEN** la fila queda marcada como `SIN EQUIVALENTE`
- **AND** el hueco se traslada a la sección de hallazgos del inventario

### Requirement: Huecos de backend registrados como findings agrupados por capacidad

El inventario SHALL registrar cada capacidad de backend ausente como un finding con ID
`RF-091-<secuencia>`, agrupando por capacidad y no por pantalla, sin resolver ninguno dentro de esta
HU.

#### Scenario: Dos pantallas que necesitan la misma capacidad ausente

- **WHEN** dos o más rutas del origen requieren el mismo contrato inexistente en el backend
- **THEN** se registra un único finding para esa capacidad, citando todas las rutas afectadas
- **AND** el finding queda en `review.md` y en `openspec/findings/backlog.md` sin resolverse aquí

#### Scenario: Inventario reproducible

- **WHEN** se publica el inventario del origen
- **THEN** el documento anota el commit inspeccionado de `../Economicon`
- **AND** ningún archivo del repositorio origen queda commiteado en este repo
