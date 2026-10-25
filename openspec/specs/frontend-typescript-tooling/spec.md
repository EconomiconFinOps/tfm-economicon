# frontend-typescript-tooling Specification

## Purpose

La cadena de herramientas de `apps/frontend` verifica tipos: compila TypeScript con el rigor acordado
en ADR-0003, lo comprueba en cada pull request y lo lintea sin perder la cobertura de reglas de React
que ya existe, manteniendo la instalación reproducible desde el lockfile del workspace.
## Requirements
### Requirement: La verificación de tipos es ejecutable y obligatoria en integración continua

El repositorio SHALL exponer un comando de verificación de tipos del frontend que cualquier
integrante pueda ejecutar localmente, y ese mismo comando SHALL ejecutarse en la integración continua
de cada pull request, de modo que el rigor del compilador tenga consecuencia real y no sea una
anotación decorativa (ADR-0003, decisión 3).

#### Scenario: Comprobación local disponible como comando del paquete

- **WHEN** se invoca el comando de verificación de tipos del frontend desde la raíz del workspace
- **THEN** la comprobación se ejecuta sin generar artefactos de build
- **AND** termina con éxito sobre el estado actual de `apps/frontend`

#### Scenario: La integración continua rechaza un error de tipos

- **WHEN** un pull request introduce en `apps/frontend` código que no supera la comprobación de tipos
- **THEN** la integración continua ejecuta esa comprobación
- **AND** el pull request queda con el resultado en rojo en lugar de pasar inadvertido

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

### Requirement: La instalación del workspace sigue siendo reproducible

Las dependencias de TypeScript SHALL incorporarse como dependencias de desarrollo del paquete del
frontend mediante el gestor de paquetes del monorepo, dejando el lockfile del workspace actualizado y
versionado, de modo que una instalación reproducible no requiera modificarlo.

#### Scenario: Instalación desde el lockfile sin desviaciones

- **WHEN** se instala el workspace exigiendo que el lockfile no cambie
- **THEN** la instalación termina con éxito
- **AND** el lockfile queda intacto

#### Scenario: Ninguna dependencia de runtime nueva

- **WHEN** se comparan las dependencias del paquete del frontend antes y después del cambio
- **THEN** las dependencias de runtime son idénticas
- **AND** todo lo añadido lo es como dependencia de desarrollo

### Requirement: La verificación automática incluye ejecución de pruebas

La cadena de verificación de `apps/frontend` SHALL ejecutar pruebas automáticas reales mediante el
comando de pruebas estándar del paquete, informando de cuántas se han ejecutado. Un marcador que no
ejecuta nada NO SHALL considerarse verificación de pruebas. El comando SHALL terminar con estado de
error cuando alguna prueba falle, de modo que la verificación no pueda pasar en falso.

#### Scenario: El comando de pruebas ejecuta pruebas reales

- **WHEN** se invoca el comando de pruebas del paquete del frontend
- **THEN** se ejecutan las pruebas declaradas en el paquete
- **AND** el resultado informa de cuántas se han ejecutado

#### Scenario: Una prueba fallida detiene la verificación

- **WHEN** una de las pruebas del frontend falla
- **THEN** el comando de pruebas termina con estado de error

#### Scenario: Las pruebas se ejecutan en integración continua

- **WHEN** se propone un cambio que toca el frontend
- **THEN** la integración continua ejecuta las pruebas del frontend sobre ese cambio
- **AND** su resultado es visible junto al resto de comprobaciones de la propuesta

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

