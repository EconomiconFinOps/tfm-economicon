## ADDED Requirements

### Requirement: Configuración de compilador con código fuente solo en TypeScript

`apps/frontend` SHALL declarar una configuración de compilador de TypeScript propia, alineada con las
decisiones 1, 2 y 4 de ADR-0003 (`docs/adr/ADR-0003-frontend-typescript.md`): rigor máximo, código
fuente exclusivamente en TypeScript una vez cerrada la migración, y ubicación local al paquete en
lugar de compartida.

#### Scenario: Rigor máximo activo

- **WHEN** se inspecciona la configuración de compilador de `apps/frontend`
- **THEN** el modo estricto está activado
- **AND** no se relaja mediante excepciones por archivo, directorio ni comentarios de supresión

#### Scenario: El código fuente ya no admite JavaScript

- **WHEN** se inspecciona la configuración de compilador de `apps/frontend`
- **THEN** la convivencia con JavaScript está desactivada para el código fuente y para las pruebas
- **AND** la comprobación de tipos termina sin errores sobre `apps/frontend/src/**` y
  `apps/frontend/tests/**`, que no contienen ningún archivo JavaScript

#### Scenario: Un import de JavaScript hace fallar la comprobación de tipos

- **WHEN** un archivo TypeScript del código fuente importa un módulo JavaScript sin tipos
- **THEN** la comprobación de tipos termina con error
- **AND** el cambio no puede integrarse mientras el check obligatorio de tipos esté en rojo

#### Scenario: Configuración local al paquete, no compartida

- **WHEN** se localiza la configuración de compilador
- **THEN** reside dentro de `apps/frontend`
- **AND** no se extrae a `packages/shared-config`, que no tiene un segundo consumidor de TypeScript

### Requirement: El frontend arranca y se construye con el contrato de red del monorepo

Los cambios de tooling SHALL ser transparentes para el producto: `apps/frontend` SHALL seguir
arrancando en desarrollo y construyéndose para producción con el mismo contrato de red que el
monorepo espera.

#### Scenario: Arranque de desarrollo con el contrato de red del monorepo

- **WHEN** se levanta el frontend en modo desarrollo
- **THEN** queda accesible en el puerto y la interfaz de escucha que el monorepo tiene configurados
- **AND** no se producen errores de compilación ni de tipos

#### Scenario: Build de producción sin regresión

- **WHEN** se construye el frontend para producción
- **THEN** el build termina con éxito

## MODIFIED Requirements

### Requirement: El lint acepta TypeScript sin perder la validación vigente de React

La configuración de lint de `apps/frontend` SHALL analizar archivos TypeScript y TSX además de los
JavaScript y JSX, conservando las reglas de React y de hooks ya vigentes, y SHALL relevar la
validación de props en tiempo de ejecución únicamente en los archivos que la verificación de tipos ya
cubre.

#### Scenario: El lint analiza TypeScript sin romperse

- **WHEN** se ejecuta el lint del frontend
- **THEN** los archivos TypeScript y TSX quedan dentro del conjunto analizado
- **AND** el comando termina con éxito

#### Scenario: Las reglas de React y hooks siguen aplicándose

- **WHEN** el lint procesa un componente de React
- **THEN** las reglas de React y de hooks vigentes antes de este cambio siguen activas sobre él

#### Scenario: La validación de props en runtime se releva solo donde hay tipos

- **WHEN** el lint procesa un archivo TypeScript o TSX
- **THEN** no exige validación de props en tiempo de ejecución, porque la verificación de tipos ya la
  sustituye
- **AND** cuando procesa un archivo `.jsx` sin tipar, sigue exigiéndola

#### Scenario: La línea base de violaciones no empeora

- **WHEN** se ejecuta el lint del frontend sobre el código fuente migrado
- **THEN** no reporta ninguna violación
- **AND** la línea base heredada de 49 violaciones del finding `RF-082-002` ya no existe, porque los
  archivos que la originaban fueron tipados o retirados

## REMOVED Requirements

### Requirement: Configuración de compilador conforme a la decisión de arquitectura

**Reason**: Describía la convivencia temporal con JavaScript durante la migración, con un escenario
que daba por hecho que `apps/frontend/src/**` solo contenía archivos `.js` y `.jsx`. La migración
terminó y el compilador deja de admitir JavaScript, tal como prevé la decisión 2 de ADR-0003.

**Migration**: Sustituido por «Configuración de compilador con código fuente solo en TypeScript», que
conserva los escenarios de rigor máximo y de configuración local al paquete.

### Requirement: El frontend conserva su comportamiento de arranque y build

**Reason**: Incluía el escenario «Ningún archivo fuente migrado», que solo era cierto mientras duró
JUP-093: exigía que ningún archivo se hubiera renombrado a TypeScript y que `RF-082-002` siguiera
abierto. Hoy todo el código fuente es TypeScript y ese finding está en `Fixed`.

**Migration**: Sustituido por «El frontend arranca y se construye con el contrato de red del
monorepo», que conserva los escenarios de arranque de desarrollo y de build de producción.
