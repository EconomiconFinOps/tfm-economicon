## ADDED Requirements

### Requirement: Decisión de adopción de TypeScript registrada como ADR aceptado

La épica de migración del frontend SHALL registrar la adopción de TypeScript en `apps/frontend` como
un ADR en estado `Accepted` dentro de `docs/adr/`, antes de que ninguna tarjeta instale dependencias
de TypeScript, cree un `tsconfig` o modifique la configuración de lint del frontend.

#### Scenario: ADR creado con la estructura y numeración del repositorio

- **WHEN** se completa la redacción de la decisión
- **THEN** existe `docs/adr/ADR-0003-frontend-typescript.md` siguiendo la estructura de
  `docs/templates/adr.md`
- **AND** el registro enlaza el identificador `JUP-092`, la URL directa de su tarjeta Trello y el
  change OpenSpec correspondiente
- **AND** el número `0003` es correlativo respecto a los ADR existentes

#### Scenario: Transición de estado revisable

- **WHEN** el ADR se redacta por primera vez
- **THEN** su estado es `Proposed`
- **AND** solo pasa a `Accepted` después de que el equipo apruebe las decisiones que contiene

### Requirement: Las cuatro decisiones que bloquean el tooling quedan resueltas sin ambigüedad

El ADR SHALL resolver de forma inequívoca el nivel de rigor del compilador, la estrategia de
convivencia con JavaScript, el encaje del type-check con CI y la ubicación del `tsconfig`, de modo
que la tarjeta de tooling pueda ejecutarse sin reabrir ninguna de ellas.

#### Scenario: Decisión ejecutable sin consulta adicional

- **WHEN** se redacta cualquiera de las cuatro decisiones
- **THEN** el ADR indica la opción elegida y su motivo
- **AND** no la deja condicionada a una evaluación posterior en otra tarjeta

#### Scenario: Relación con las violaciones de prop-types existentes

- **WHEN** el ADR resuelve el encaje del type-check con CI
- **THEN** declara explícitamente qué ocurre con el finding `RF-082-002` y sus 49 violaciones de
  `react/prop-types`: si se cierra, se transforma o se mantiene abierto
- **AND** justifica esa postura en relación con que los tipos de TypeScript sustituyen a `prop-types`
  como mecanismo de validación

### Requirement: Decisión auditable con consecuencias y alternativas

El ADR SHALL documentar las consecuencias negativas de la decisión y al menos dos alternativas
descartadas con su motivo, de forma que un tercero pueda evaluar el razonamiento y no solo el
resultado.

#### Scenario: Consecuencias en ambas direcciones

- **WHEN** se redacta la sección de consecuencias
- **THEN** recoge qué se vuelve más difícil o más arriesgado, además de qué se vuelve más fácil
- **AND** menciona que el TSX del origen nunca ha sido verificado y que aflorarán errores latentes al
  compilarlo por primera vez

#### Scenario: Alternativas descartadas registradas

- **WHEN** se publica el ADR
- **THEN** recoge al menos dos alternativas descartadas con el motivo de su descarte
- **AND** el ADR queda enlazado desde `docs/spikes/frontend-migration.md` para que las tarjetas de F2
  y F3 puedan citarlo
