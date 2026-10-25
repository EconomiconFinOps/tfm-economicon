## ADDED Requirements

### Requirement: Un cambio de ámbito de cliente reinicia el estado local de cada pantalla

Al cambiar el ámbito de cliente activo, ninguna pantalla SHALL conservar formularios, selección ni
resultados de mutaciones pendientes del ámbito anterior. Una respuesta tardía de una operación
iniciada bajo el ámbito anterior NO SHALL alterar el estado observable de la pantalla una vez
activo el nuevo ámbito.

#### Scenario: Un borrador no sobrevive al cambio de ámbito

- **WHEN** se escribe en un formulario de una pantalla conectada al backend y a continuación se
  cambia el ámbito de cliente activo
- **THEN** el formulario se presenta vacío bajo el nuevo ámbito, sin el contenido escrito antes del
  cambio

#### Scenario: Una respuesta tardía no altera el nuevo ámbito

- **WHEN** una operación iniciada bajo el ámbito anterior resuelve después de haber cambiado al
  nuevo ámbito
- **THEN** esa respuesta no modifica el estado ni los datos presentados bajo el nuevo ámbito activo

### Requirement: La sesión persistida se valida antes de confiar en ella

Antes de tratar un valor recuperado del almacenamiento local como una sesión activa, la aplicación
SHALL comprobar que tiene la forma completa de una sesión válida. Un valor que no cumpla esa forma,
aunque sea JSON válido, SHALL descartarse y tratarse como ausencia de sesión.

#### Scenario: Un valor con estructura incompleta no se acepta como sesión

- **WHEN** el almacenamiento local contiene un valor JSON válido que no tiene la forma completa de
  una sesión
- **THEN** la aplicación presenta la pantalla de acceso, sin considerar iniciada ninguna sesión
- **AND** no se realiza ninguna llamada de red que dependa de esa sesión

### Requirement: Las pantallas conectadas al backend son alcanzables desde el menú

Cada pantalla que consuma el backend SHALL tener, además de una dirección propia, un enlace visible
en el menú de navegación. No SHALL depender exclusivamente de que se conozca o escriba su dirección
para alcanzarse desde una pantalla ya autenticada.

#### Scenario: Una pantalla conectada al backend se alcanza haciendo clic en el menú

- **WHEN** se está en cualquier pantalla autenticada y se hace clic en el enlace del menú
  correspondiente a una pantalla conectada al backend
- **THEN** se presenta esa pantalla, sin haber escrito su dirección directamente
