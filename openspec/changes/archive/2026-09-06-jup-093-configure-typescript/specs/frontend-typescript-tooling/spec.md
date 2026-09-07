## Purpose

La cadena de herramientas de `apps/frontend` verifica tipos: compila TypeScript con el rigor acordado
en ADR-0003, lo comprueba en cada pull request y lo lintea sin perder la cobertura de reglas de React
que ya existe, manteniendo la instalación reproducible desde el lockfile del workspace.

## ADDED Requirements

### Requirement: Configuración de compilador conforme a la decisión de arquitectura

`apps/frontend` SHALL declarar una configuración de compilador de TypeScript propia, alineada con las
decisiones 1, 2 y 4 de [ADR-0003](../../../../docs/adr/ADR-0003-frontend-typescript.md): rigor
máximo desde el inicio, convivencia temporal con el JavaScript aún no migrado, y ubicación local al
paquete en lugar de compartida.

#### Scenario: Rigor máximo activo desde el primer archivo

- **WHEN** se inspecciona la configuración de compilador de `apps/frontend`
- **THEN** el modo estricto está activado
- **AND** no se relaja mediante excepciones por archivo, directorio ni comentarios de supresión

#### Scenario: El JavaScript existente sigue siendo válido durante la migración

- **WHEN** el compilador procesa `apps/frontend/src/**`, que hoy contiene únicamente archivos `.js` y
  `.jsx`
- **THEN** la comprobación de tipos termina sin errores
- **AND** ningún archivo JavaScript existente necesita ser renombrado, migrado o excluido para lograrlo

#### Scenario: Configuración local al paquete, no compartida

- **WHEN** se localiza la configuración de compilador
- **THEN** reside dentro de `apps/frontend`
- **AND** no se extrae a `packages/shared-config`, que no tiene un segundo consumidor de TypeScript

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
JavaScript y JSX actuales, conservando las reglas de React y de hooks ya vigentes, y SHALL relevar la
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

- **WHEN** se ejecuta el lint del frontend tras el cambio
- **THEN** las violaciones reportadas son exactamente las 49 de la línea base heredada, registradas en
  el finding `RF-082-002`
- **AND** no aparece ninguna violación nueva atribuible a este cambio

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

### Requirement: El frontend conserva su comportamiento de arranque y build

El cambio de tooling SHALL ser transparente para el producto: `apps/frontend` SHALL seguir
arrancando en desarrollo y construyéndose para producción con el mismo contrato de red que el
monorepo espera, sin que se migre ningún archivo fuente.

#### Scenario: Arranque de desarrollo con el contrato de red del monorepo

- **WHEN** se levanta el frontend en modo desarrollo
- **THEN** queda accesible en el puerto y la interfaz de escucha que el monorepo tiene configurados
- **AND** no se producen errores de compilación ni de tipos

#### Scenario: Build de producción sin regresión

- **WHEN** se construye el frontend para producción
- **THEN** el build termina con éxito

#### Scenario: Ningún archivo fuente migrado

- **WHEN** se comparan los archivos de `apps/frontend/src/**` antes y después del cambio
- **THEN** ninguno ha sido renombrado a TypeScript ni reescrito
- **AND** el finding `RF-082-002` permanece abierto, porque los archivos que lo originan no han sido
  tipados
