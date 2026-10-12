## MODIFIED Requirements

### Requirement: Cada pantalla es alcanzable por una dirección propia

El frontend SHALL exponer cada una de sus pantallas publicadas en una dirección estable y compartible. Navegar de una pantalla a otra NO SHALL recargar la aplicación ni descartar el estado de sesión ya establecido. Una dirección que no corresponda a ninguna pantalla publicada, incluidas las de pantallas ocultas del MVP, NO SHALL presentar una pantalla de error del enrutador: SHALL llevar a la pantalla inicial.

#### Scenario: Abrir directamente la dirección de una pantalla

- **WHEN** se abre la aplicación directamente en la dirección de una pantalla concreta, con sesión establecida
- **THEN** se presenta esa pantalla, no la pantalla inicial
- **AND** el armazón de la aplicación la acompaña

#### Scenario: Navegar entre pantallas conserva la sesión

- **WHEN** se navega de una pantalla a otra
- **THEN** la sesión y el ámbito de cliente activo siguen siendo los mismos
- **AND** la aplicación no se recarga por completo

#### Scenario: Sin sesión establecida se presenta el acceso

- **WHEN** se abre cualquier dirección de la aplicación sin sesión establecida, publicada o no
- **THEN** se presenta la pantalla de acceso

#### Scenario: Una dirección no publicada lleva a la pantalla inicial

- **WHEN** se abre, con sesión establecida, la dirección de una pantalla que no está publicada (por ejemplo la de Coste Detallado, Corte Global o Recomendaciones, o una dirección que no existe)
- **THEN** se presenta la pantalla inicial dentro del armazón
- **AND** no se presenta ninguna pantalla de error del enrutador
- **AND** el ámbito de cliente activo sigue siendo el mismo

### Requirement: Las pantallas conectadas al backend son alcanzables desde el menú

Cada pantalla publicada que consuma el backend SHALL tener, además de una dirección propia, un enlace visible en el menú de navegación, con la única excepción de la vista heredada del resumen de facturación, que conserva su dirección y NO SHALL tener enlace en el menú. Ninguna otra pantalla conectada al backend SHALL depender exclusivamente de que se conozca o escriba su dirección para alcanzarse desde una pantalla ya autenticada.

#### Scenario: Una pantalla conectada al backend se alcanza haciendo clic en el menú

- **WHEN** se está en cualquier pantalla autenticada y se hace clic en el enlace del menú correspondiente a una pantalla conectada al backend
- **THEN** se presenta esa pantalla, sin haber escrito su dirección directamente

#### Scenario: La vista heredada del resumen de facturación se alcanza solo por su dirección

- **WHEN** se abre con sesión establecida la dirección de la vista heredada del resumen de facturación
- **THEN** se presenta esa pantalla con su armazón
- **AND** el menú de navegación no contiene ningún enlace a ella

## ADDED Requirements

### Requirement: Ninguna pantalla de demostración se publica en el MVP

El frontend NO SHALL publicar, ni con dirección ni con enlace en el menú, ninguna pantalla cuyos datos procedan solo de un origen de demostración. Su código y sus datos de demostración PUEDEN conservarse en el repositorio siempre que ninguna dirección ni enlace los presente. Las pantallas de Coste Detallado, Corte Global y Recomendaciones SHALL quedar no publicadas.

#### Scenario: El menú solo enlaza pantallas conectadas al backend

- **WHEN** se muestra el menú de navegación con sesión establecida
- **THEN** no contiene ningún enlace a Coste Detallado, Corte Global ni Recomendaciones
- **AND** cada enlace que contiene lleva a una pantalla que consulta el backend

#### Scenario: Las pantallas de demostración no tienen dirección

- **WHEN** se enumeran las direcciones publicadas por la aplicación
- **THEN** ninguna presenta Coste Detallado, Corte Global ni Recomendaciones

#### Scenario: Ocultar no cambia las pantallas con datos reales

- **WHEN** se inspeccionan Coste Global, Anomalías, Ingestions, Assistant y Salud del sistema
- **THEN** siguen en sus mismas direcciones y con los mismos enlaces del menú
- **AND** siguen tomando sus datos del backend
