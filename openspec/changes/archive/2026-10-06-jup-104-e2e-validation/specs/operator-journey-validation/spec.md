## Purpose

Una validación integrada del recorrido del operador acredita, en un navegador real y contra el stack
local, que la interfaz, el backend y el processor funcionan juntos de principio a fin, y deja un
registro que otra persona puede repetir y que distingue lo comprobado de lo que no se comprobó.

## ADDED Requirements

### Requirement: El recorrido se realiza en un navegador real sin protecciones desactivadas

La validación integrada SHALL ejecutarse en un navegador real que cargue la interfaz desde su origen
publicado y hable con el backend local por la red. NO SHALL desactivar ninguna protección del
navegador, ni sustituir o interceptar las respuestas del backend, ni inyectar una sesión que no
proceda del acceso por la interfaz.

#### Scenario: Acceso por la interfaz con las protecciones intactas

- **WHEN** el operador de demostración introduce sus credenciales en la pantalla de acceso
- **THEN** la sesión se crea a partir de la respuesta real del backend
- **AND** el navegador no se ha iniciado con ninguna opción que relaje la seguridad web
- **AND** ninguna petición al backend se ha respondido desde el propio guion

#### Scenario: El entorno validado queda identificado

- **WHEN** se consulta el registro de la validación
- **THEN** figuran el commit desplegado, el navegador y su versión, el proveedor de embeddings
  activo y cómo se levantó el stack

### Requirement: El recorrido cubre el camino completo del operador

La validación integrada SHALL recorrer, en una misma sesión de navegador, el acceso, la selección y
el cambio de ámbito de cliente, el resumen de costes, la ingesta de un documento, la conversación
con el asistente, la recarga del historial y el cierre de sesión, y SHALL registrar para cada paso
qué se hizo y qué se observó.

#### Scenario: Resumen de costes del ámbito con datos

- **WHEN** el operador selecciona el ámbito de cliente con costes cargados y un periodo que los
  contiene
- **THEN** la pantalla principal muestra costes procedentes del backend para ese ámbito

#### Scenario: El cambio de ámbito cambia los datos

- **WHEN** el operador cambia a un ámbito de cliente sin costes cargados para ese mismo periodo
- **THEN** la pantalla muestra ausencia de datos y no los costes del ámbito anterior

#### Scenario: El historial de una conversación sobrevive a la recarga

- **WHEN** el operador envía un mensaje, recarga la página y vuelve a abrir la conversación
- **THEN** se muestran su mensaje y la respuesta del asistente

#### Scenario: El cierre de sesión devuelve al acceso

- **WHEN** el operador cierra la sesión e intenta abrir una pantalla protegida
- **THEN** la aplicación presenta la pantalla de acceso

### Requirement: La ingesta se acredita más allá de la aceptación en la interfaz

La validación integrada SHALL comprobar que un documento enviado desde la interfaz queda procesado.
La confirmación de aceptación que muestra la interfaz NO SHALL contarse como prueba de procesado.

#### Scenario: Documento enviado desde la interfaz

- **WHEN** el operador envía un documento desde la pantalla de ingesta con un ámbito seleccionado
- **THEN** la interfaz muestra el identificador del trabajo aceptado
- **AND** ese trabajo consta como completado en la base de datos de trabajos
- **AND** el documento, sus fragmentos y sus vectores constan en la base vectorial asociados a ese
  trabajo y a ese ámbito

#### Scenario: El trabajo no llega a completarse

- **WHEN** el trabajo no consta como completado dentro del plazo de espera fijado para la validación
- **THEN** el paso se registra como fallido con el estado observado y los registros del processor
- **AND** no se da por acreditada la ingesta

### Requirement: El contexto del asistente se acredita contra el documento ingestado y por ámbito

La validación integrada SHALL comprobar que la respuesta del asistente contiene fragmentos del
documento ingestado durante el recorrido para el ámbito de cliente activo, y que otro ámbito no los
recibe. SHALL declarar qué no acredita el proveedor de embeddings con el que se ejecutó.

#### Scenario: Pregunta en el ámbito del documento

- **WHEN** el operador pregunta al asistente en el ámbito donde ingirió el documento
- **THEN** el texto de la respuesta contiene fragmentos de ese documento
- **AND** el registro de recuperación del backend para esa pregunta identifica fragmentos de ese
  documento

#### Scenario: La misma pregunta en otro ámbito

- **WHEN** el operador hace la misma pregunta en un ámbito donde no ingirió el documento
- **THEN** la respuesta no contiene fragmentos de ese documento

#### Scenario: Límites del modo utilizado

- **WHEN** la validación se ejecuta con un proveedor de embeddings que no mide pertinencia semántica
- **THEN** el registro dice que se acredita el camino de los datos y no la calidad de la recuperación
- **AND** enumera lo que queda pendiente de acreditar con el proveedor real

### Requirement: Los datos de demostración quedan identificados en el registro

La validación integrada SHALL enumerar, pantalla por pantalla, qué bloques muestran datos servidos
por el backend y cuáles muestran datos de demostración, y si la propia interfaz lo advierte.

#### Scenario: Pantalla con datos reales y de demostración a la vez

- **WHEN** una pantalla combina un bloque servido por el backend y otro de demostración
- **THEN** el registro distingue ambos bloques y anota si la interfaz rotula el de demostración

#### Scenario: Pantalla solo de demostración

- **WHEN** una pantalla no consume ningún contrato del backend
- **THEN** el registro la identifica como demostración y anota si la interfaz lo advierte

### Requirement: Los fallos se registran con su reproducción y no se disimulan

Todo comportamiento que difiera del esperado SHALL registrarse como hallazgo con los pasos para
reproducirlo y el resultado observado. La validación NO SHALL dar por acreditado un paso que no se
ejecutó, ni modificar el producto para que el paso pase.

#### Scenario: Fallo nuevo durante el recorrido

- **WHEN** un paso produce un resultado distinto del esperado
- **THEN** se registra un hallazgo nuevo con su reproducción, el resultado esperado y el observado

#### Scenario: Hallazgo conocido que el recorrido alcanza

- **WHEN** el recorrido ejercita un comportamiento descrito por un hallazgo abierto
- **THEN** el estado de ese hallazgo se actualiza según lo observado, con la evidencia que lo
  respalda

#### Scenario: Paso no ejecutado

- **WHEN** un paso no puede ejecutarse
- **THEN** el registro lo marca como no validado e indica el motivo

### Requirement: El registro es repetible y no contiene secretos

La validación integrada SHALL dejar versionados los comandos, los datos de entrada y el guion de
navegador necesarios para que otra persona la repita, y NO SHALL registrar contraseñas, tokens,
claves ni cadenas de conexión.

#### Scenario: Otra persona repite la validación

- **WHEN** una persona del equipo sigue el registro en un clon del mismo commit
- **THEN** dispone de los comandos de arranque, el documento y la pregunta utilizados y el guion de
  navegador, sin depender de archivos que no estén versionados

#### Scenario: Credenciales en el registro

- **WHEN** se revisa el registro, el guion de navegador y las salidas guardadas
- **THEN** las credenciales aparecen solo por el nombre de la variable que las aporta
- **AND** no aparece ningún valor de contraseña, token, clave ni cadena de conexión
