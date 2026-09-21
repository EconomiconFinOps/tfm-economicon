# frontend-api-layer Specification

## Purpose
Garantizar que el acceso del frontend al backend ocurra por un único punto centralizado, cuyas
operaciones se correspondan una a una con contratos reales del backend y transporten en cada petición
autenticada la identidad del operador y el ámbito de cliente activo, de modo que ninguna pantalla
presente como servido un dato que no lo es ni queden extremos huérfanos en ninguna de las dos
direcciones.
## Requirements
### Requirement: El acceso al backend ocurre por un único punto declarado

Todo acceso de red del frontend al backend SHALL producirse a través de un único módulo declarado
como capa de acceso. Ninguna pantalla, armazón ni utilidad SHALL emitir peticiones de red al backend
por su cuenta.

#### Scenario: No hay accesos de red fuera de la capa declarada

- **WHEN** se enumeran los puntos del frontend que emiten peticiones de red al backend
- **THEN** todos pertenecen al módulo declarado como capa de acceso
- **AND** ninguna pantalla ni armazón emite peticiones por su cuenta

#### Scenario: La dirección base del backend es configurable por entorno

- **WHEN** se despliega el frontend contra un backend en una dirección distinta de la de desarrollo
- **THEN** la dirección base se toma de la configuración del entorno
- **AND** no hay direcciones de backend fijadas en el código de las pantallas

### Requirement: Cada operación expuesta corresponde a un contrato real del backend

Cada operación que la capa de acceso exponga SHALL corresponderse con un contrato que el backend
sirve realmente, coincidiendo en dirección, método, cuerpo de la petición y forma de la respuesta.
Ninguna operación SHALL declarar una forma de respuesta que el backend no devuelve.

#### Scenario: Cada operación coincide con el contrato que dice consumir

- **WHEN** se compara cada operación expuesta con el contrato del backend al que dice corresponder
- **THEN** coinciden en dirección, método, cuerpo de la petición y forma de la respuesta

#### Scenario: Una necesidad sin contrato se registra en lugar de inventarse

- **WHEN** el frontend necesita una capacidad que el backend no sirve
- **THEN** esa carencia queda registrada como hallazgo con la capacidad nombrada
- **AND** la capa de acceso no expone una operación que simule servirla

### Requirement: Ninguna operación expuesta queda sin consumidor

La capa de acceso NO SHALL exponer operaciones que ninguna pantalla ni armazón invoque. Una operación
sin consumidor SHALL conectarse a quien la necesite o retirarse; conservarla inerte no es un
desenlace admisible.

#### Scenario: Toda operación expuesta tiene al menos un consumidor

- **WHEN** se enumeran las operaciones que la capa de acceso expone
- **THEN** cada una es invocada al menos desde una pantalla o desde el armazón

#### Scenario: Una operación sin consumidor no sobrevive a la revisión

- **WHEN** se detecta una operación expuesta que nadie invoca
- **THEN** o se conecta a quien la necesita o se retira de la capa de acceso

### Requirement: Toda petición autenticada transporta identidad y ámbito de cliente

Cada petición a un contrato que exija autenticación SHALL transportar la credencial de la sesión
activa y el identificador del ámbito de cliente seleccionado. Ninguna petición autenticada SHALL
emitirse sin ámbito de cliente cuando el contrato lo exija.

#### Scenario: Una petición autenticada lleva credencial y ámbito

- **WHEN** se emite una petición a un contrato que exige autenticación
- **THEN** la petición transporta la credencial de la sesión activa
- **AND** transporta el identificador del ámbito de cliente seleccionado

#### Scenario: Sin ámbito seleccionado no se consulta un contrato que lo exige

- **WHEN** no hay ámbito de cliente seleccionado
- **THEN** no se emite ninguna petición a un contrato que exija ámbito
- **AND** la pantalla lo comunica en vez de mostrar un resultado vacío indistinguible de un dato real

### Requirement: Las pantallas servidas por el backend comunican carga y error

Toda pantalla alimentada por la capa de acceso SHALL comunicar de forma observable que su dato está
en curso de obtención y SHALL comunicar el fallo cuando la obtención no se complete. Un fallo de
obtención NO SHALL presentarse como ausencia de datos.

#### Scenario: La obtención en curso es observable

- **WHEN** una pantalla servida por el backend está obteniendo su dato
- **THEN** la pantalla comunica que la obtención está en curso

#### Scenario: Un fallo se comunica y no se disfraza de dato vacío

- **WHEN** la obtención del dato de una pantalla servida por el backend falla
- **THEN** la pantalla comunica el fallo de forma observable
- **AND** no presenta el fallo como una ausencia de datos

#### Scenario: Un cambio de ámbito de cliente reconsulta el dato

- **WHEN** se cambia el ámbito de cliente activo estando en una pantalla servida por el backend
- **THEN** la pantalla obtiene de nuevo su dato para el ámbito nuevo
- **AND** no presenta en ningún momento el dato del ámbito anterior como propio del nuevo

### Requirement: Cada pantalla sin contrato declara la capacidad que le falta

Cada pantalla que se alimente de datos de demostración por no existir contrato SHALL tener declarada,
de forma localizable y nombrada, la capacidad de backend concreta que necesitaría para servirse de
datos reales. Declarar únicamente que el dato no es real NO SHALL bastar.

#### Scenario: La carencia está nombrada, no solo señalada

- **WHEN** se consulta qué le falta a una pantalla que se alimenta de datos de demostración
- **THEN** existe una declaración localizable que nombra la capacidad de backend ausente
- **AND** esa declaración no se limita a indicar que el dato no procede del backend

#### Scenario: El conjunto de carencias es enumerable

- **WHEN** se quiere decidir qué capacidad de backend construir primero
- **THEN** las carencias de todas las pantallas sin contrato pueden enumerarse desde un único lugar

