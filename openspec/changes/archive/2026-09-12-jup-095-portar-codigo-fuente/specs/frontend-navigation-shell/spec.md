## Purpose

El frontend presenta sus pantallas bajo un armazón único y las hace alcanzables por direcciones
estables, conservando a lo largo de la navegación la identidad de la sesión y el ámbito de cliente
activo, y manteniendo separados los datos de demostración que acompañan a las pantallas migradas de
los datos que sirve el backend.

## ADDED Requirements

### Requirement: Cada pantalla es alcanzable por una dirección propia

El frontend SHALL exponer cada una de sus pantallas en una dirección estable y compartible. Navegar
de una pantalla a otra NO SHALL recargar la aplicación ni descartar el estado de sesión ya
establecido.

#### Scenario: Abrir directamente la dirección de una pantalla

- **WHEN** se abre la aplicación directamente en la dirección de una pantalla concreta, con sesión
  establecida
- **THEN** se presenta esa pantalla, no la pantalla inicial
- **AND** el armazón de la aplicación la acompaña

#### Scenario: Navegar entre pantallas conserva la sesión

- **WHEN** se navega de una pantalla a otra
- **THEN** la sesión y el ámbito de cliente activo siguen siendo los mismos
- **AND** la aplicación no se recarga por completo

#### Scenario: Sin sesión establecida se presenta el acceso

- **WHEN** se abre cualquier dirección de la aplicación sin sesión establecida
- **THEN** se presenta la pantalla de acceso

### Requirement: Un armazón único conserva identidad y ámbito de cliente

Toda pantalla que requiera sesión SHALL presentarse dentro de un armazón común que muestre la
identidad de la sesión activa, permita seleccionar el ámbito de cliente y ofrezca el cierre de
sesión. El ámbito seleccionado SHALL permanecer vigente al cambiar de pantalla.

#### Scenario: El armazón acompaña a toda pantalla autenticada

- **WHEN** se presenta cualquier pantalla que requiere sesión
- **THEN** el armazón muestra la navegación entre pantallas, la identidad de la sesión y el ámbito de
  cliente activo

#### Scenario: El ámbito seleccionado sobrevive a la navegación

- **WHEN** se selecciona un ámbito de cliente y a continuación se cambia de pantalla
- **THEN** el ámbito seleccionado sigue siendo el activo
- **AND** las consultas que dependen de él lo siguen usando

#### Scenario: El cierre de sesión devuelve al acceso

- **WHEN** se cierra la sesión desde el armazón
- **THEN** se descarta la sesión y el ámbito activo persistidos
- **AND** se presenta de nuevo la pantalla de acceso

### Requirement: Las capacidades servidas por el backend sobreviven a la migración

La incorporación de las pantallas del repositorio de origen NO SHALL dejar inalcanzable ninguna
pantalla que consuma el backend. El acceso, la ingesta, el asistente y el resumen de facturación
SHALL conservar dirección propia y comportamiento equivalente al previo a la migración.

#### Scenario: El recorrido de referencia sigue completándose

- **WHEN** se recorre acceso, selección de ámbito de cliente y consulta del resumen de facturación
- **THEN** cada paso se completa con el mismo resultado observable que antes de la migración

#### Scenario: Ninguna pantalla con backend queda huérfana

- **WHEN** se enumeran las direcciones publicadas por la aplicación
- **THEN** cada pantalla que consumía el backend antes de la migración tiene una dirección que la
  presenta

### Requirement: Los datos de demostración se declaran aparte de los servidos

Las pantallas migradas que todavía no tienen contrato en el backend SHALL alimentarse de un origen de
datos de demostración declarado en un lugar único e identificable, separado de los componentes que lo
presentan. Ninguna pantalla SHALL presentar datos de demostración como si procedieran del backend sin
que ese origen quede declarado.

#### Scenario: El origen de demostración es localizable

- **WHEN** se busca de dónde toma sus datos una pantalla migrada sin contrato
- **THEN** el dato procede de un origen de demostración declarado aparte
- **AND** no está incrustado dentro del componente que lo presenta

#### Scenario: Las pantallas con datos reales no cambian de origen

- **WHEN** se inspecciona una pantalla que ya consumía el backend
- **THEN** sigue tomando sus datos del backend
- **AND** no se le sustituyen por datos de demostración

### Requirement: La aplicación se presenta bajo un único sistema de estilos

La aplicación SHALL presentarse con un solo sistema de estilos. Al completarse la migración NO SHALL
quedar cargado ni referenciado el sistema de estilos anterior.

#### Scenario: No conviven dos sistemas de estilos

- **WHEN** se carga cualquier pantalla de la aplicación
- **THEN** los estilos aplicados proceden del sistema adoptado en la migración
- **AND** no se carga ninguna hoja de estilos del armazón anterior

#### Scenario: No quedan referencias al sistema anterior

- **WHEN** se busca en el código del frontend cualquier referencia al sistema de estilos anterior
- **THEN** no se encuentra ninguna
