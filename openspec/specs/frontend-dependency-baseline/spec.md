# frontend-dependency-baseline Specification

## Purpose

El manifiesto de dependencias de `apps/frontend` declara lo que su código usa realmente o va a usar
de forma inmediata, sin arrastres heredados del repositorio de origen, preservando el contrato del
paquete con el monorepo y una instalación reproducible desde el lockfile del workspace.

## Requirements
### Requirement: Cada dependencia declarada responde a un consumidor real

`apps/frontend` SHALL declarar únicamente dependencias con un consumidor identificado: código que ya
las importa, o código que la fase inmediatamente siguiente de la migración va a portar. No se
declaran dependencias por el hecho de que existan en el repositorio de origen.

#### Scenario: Las dependencias del origen sin uso no se incorporan

- **WHEN** se compara el manifiesto resultante con el inventario de dependencias del origen
- **THEN** ninguna de las dependencias clasificadas como descartables en ese inventario aparece
  declarada
- **AND** tampoco se copia ninguna anulación de versión (`overrides`) del origen

#### Scenario: Cada dependencia incorporada tiene su motivo registrado

- **WHEN** se incorpora una dependencia del origen
- **THEN** el cambio deja constancia de qué la va a consumir
- **AND** en qué fase de la migración

### Requirement: La decisión sobre el sistema de componentes queda resuelta y registrada

La incorporación o el descarte de la librería de componentes del origen SHALL resolverse de forma
explícita en esta fase, con su motivo registrado en el backlog de hallazgos, de modo que ninguna
tarjeta posterior tenga que reabrirla a mitad de implementación.

#### Scenario: El hallazgo abierto queda cerrado con una decisión

- **WHEN** termina esta fase
- **THEN** el hallazgo que registraba la decisión pendiente sobre la librería de componentes deja de
  estar abierto
- **AND** su entrada recoge la opción elegida y por qué

#### Scenario: Adoptar la librería exigiría decisión de arquitectura registrada

- **WHEN** la opción elegida es incorporar la librería de componentes como sistema de diseño
- **THEN** existe un registro de decisión de arquitectura aceptado que la respalde antes de
  declararla como dependencia

### Requirement: El salto de versión mayor del bundler es una decisión deliberada

El cambio de versión mayor del bundler SHALL decidirse comprobando qué exigen realmente las
dependencias que se incorporan, y no adoptando por defecto la versión declarada en el origen.

#### Scenario: Ninguna dependencia incorporada fuerza el salto

- **WHEN** se comprueban los rangos de compatibilidad declarados por las dependencias que se
  incorporan
- **THEN** el resultado de esa comprobación queda registrado
- **AND** la versión del bundler solo cambia si alguna dependencia lo exige o si el equipo lo decide
  con un motivo propio

### Requirement: El contrato del paquete con el monorepo se conserva

La reconciliación de dependencias SHALL preservar la identidad y la superficie operativa del paquete
dentro del monorepo: su nombre, su tipo de módulo, y el conjunto completo de comandos que otras
partes del sistema invocan.

#### Scenario: Identidad y comandos intactos

- **WHEN** se compara el manifiesto antes y después del cambio
- **THEN** el nombre del paquete y su tipo de módulo son idénticos
- **AND** todos los comandos que existían siguen existiendo, incluido el de verificación de tipos
- **AND** el comando de desarrollo mantiene la interfaz de escucha y el puerto que el monorepo espera

#### Scenario: Las dependencias de ejecución se declaran como tales

- **WHEN** una dependencia es necesaria en tiempo de ejecución de la aplicación
- **THEN** se declara como dependencia de ejecución y no como dependencia entre pares

### Requirement: La instalación sigue siendo reproducible y el producto no cambia

Tras incorporar las dependencias, el workspace SHALL instalarse de forma reproducible desde su
lockfile, y la aplicación SHALL conservar su comportamiento de compilación, verificación y arranque,
dado que no se modifica ningún archivo fuente.

#### Scenario: Instalación reproducible

- **WHEN** se instala el workspace exigiendo que el lockfile no cambie
- **THEN** la instalación termina con éxito y el lockfile queda intacto

#### Scenario: Verificaciones sin regresión

- **WHEN** se ejecutan la verificación de tipos, el lint y la construcción de producción
- **THEN** las tres terminan con éxito
- **AND** el lint reporta exactamente las mismas violaciones heredadas que antes del cambio, porque
  ningún archivo fuente fue modificado

#### Scenario: Ningún archivo fuente tocado

- **WHEN** se comparan los archivos fuente de la aplicación antes y después del cambio
- **THEN** ninguno ha sido modificado, renombrado ni añadido
