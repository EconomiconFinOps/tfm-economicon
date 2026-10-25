## ADDED Requirements

### Requirement: Los colores de la interfaz proceden solo de los tokens del tema

Toda pantalla, armazón y componente compartido de la aplicación SHALL obtener sus colores de los
tokens semánticos que define el tema, y NO SHALL escribir un valor de color literal ni un color de
una paleta genérica. Solo SHALL admitirse las excepciones declaradas una a una con su motivo, y un
código que no esté en esa lista y escriba un color literal SHALL hacer fallar la batería de pruebas
del frontend.

#### Scenario: Una pantalla solo usa colores del tema

- **WHEN** se inspecciona el código de cualquiera de las pantallas, del armazón o de los componentes
  compartidos
- **THEN** cada color que aplica es una referencia a un token del tema
- **AND** no aparece ningún valor de color hexadecimal ni ningún color de la paleta genérica

#### Scenario: Un color literal nuevo rompe la batería de pruebas

- **WHEN** un cambio introduce un color hexadecimal o un color de la paleta genérica en una pantalla,
  en el armazón o en un componente compartido, fuera de las excepciones declaradas
- **THEN** la batería de pruebas del frontend falla señalando el archivo y el valor

#### Scenario: Las excepciones están declaradas

- **WHEN** un color literal se conserva porque el tema no puede alcanzarlo (por ejemplo, un documento
  generado para imprimir fuera de la aplicación)
- **THEN** figura en la lista de excepciones con el archivo y el motivo

### Requirement: Un cambio de token se propaga a toda la interfaz

El valor de cada color SHALL definirse en un único punto del tema, de forma que modificar un token
cambie el color en todas las pantallas que lo consumen sin tocar ninguna de ellas.

#### Scenario: Se cambia un token de ejemplo

- **WHEN** se modifica el valor de un token del tema consumido por varias pantallas y se reconstruye
  la aplicación
- **THEN** todas esas pantallas muestran el color nuevo
- **AND** ningún archivo de pantalla ni de componente cambia

### Requirement: El tema define una única paleta activa

El tema SHALL definir una única paleta de colores, activa sin depender de ninguna clase ni atributo
en el documento. NO SHALL existir una segunda paleta ni un ámbito alternativo sin consumidor.

#### Scenario: La paleta no depende de un ámbito declarado

- **WHEN** se carga la aplicación sin ninguna clase de tema en el documento
- **THEN** pantallas y componentes compartidos se presentan con la paleta de la aplicación

#### Scenario: No hay paleta paralela

- **WHEN** se inspecciona la definición del tema
- **THEN** cada token de color tiene una sola definición
- **AND** no existe un bloque alternativo de tokens para otro tema

### Requirement: La unificación de colores no altera el aspecto de las pantallas

La sustitución de colores literales por tokens SHALL conservar el aspecto de cada pantalla: cada
token SHALL reproducir el valor que sustituye, sin consolidar tonos distintos en uno.

#### Scenario: Comparación antes y después

- **WHEN** se captura cada pantalla de la aplicación con los mismos datos antes y después de la
  unificación
- **THEN** las capturas coinciden, o cada diferencia queda explicada y aceptada una a una
