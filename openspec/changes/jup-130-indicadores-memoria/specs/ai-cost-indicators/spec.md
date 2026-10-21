## ADDED Requirements

### Requirement: Coste de IA por consulta y por modelo desde el registro del gateway
El sistema DEBE (SHALL) calcular, a partir de `/spend/logs` del gateway aislado, el coste total, el número de consultas y el coste por consulta, en conjunto y por alias de modelo, para una ventana temporal indicada. El coste por consulta es la suma del gasto de las filas de la ventana dividida por el número de filas con consulta terminada. La herramienta solo DEBE (SHALL) leer el gasto y los metadatos técnicos, nunca el contenido de las consultas.

#### Scenario: Ventana con consultas
- **WHEN** la ventana contiene consultas registradas
- **THEN** el informe recoge coste total, número de consultas, coste por consulta y los mismos valores por alias de modelo, con la divisa del gateway

#### Scenario: Gateway no alcanzable
- **WHEN** el gateway no responde o no está levantado
- **THEN** todas las filas de coste de IA son `not_measured` con la causa registrada como identificador
- **AND** la herramienta termina sin error de carga y sin escribir ceros

#### Scenario: Ventana sin consultas
- **WHEN** el gateway responde pero la ventana no tiene consultas
- **THEN** el coste por consulta es `not_measured` y no 0, y el coste total es 0 medido

#### Scenario: Fila con gasto cero
- **WHEN** una fila de fallo tiene gasto cero o ausente
- **THEN** no se interpreta como una llamada gratuita y se cuenta aparte en el recuento de fallos

### Requirement: Tasa de 429 del proveedor
El sistema DEBE (SHALL) informar la tasa de respuestas 429 como proporción de las peticiones de la ventana, con su numerador y su denominador, distinguiendo un cero medido de la ausencia de datos.

#### Scenario: Sin 429 en la ventana
- **WHEN** hay peticiones y ninguna terminó en 429
- **THEN** la tasa es 0 medido con su denominador

#### Scenario: Sin peticiones
- **WHEN** la ventana no tiene peticiones
- **THEN** la tasa es `not_measured`

### Requirement: Secretos y contenido fuera del informe
El sistema DEBE (SHALL) leer la clave de administración del gateway de una variable de entorno o de un fichero y nunca imprimirla, escribirla en el informe, en el manifiesto ni en la tabla de la memoria. Los informes solo DEBEN (SHALL) contener identificadores, recuentos y sumas, sin prompts, respuestas ni mensajes de error del proveedor.

#### Scenario: Clave ausente
- **WHEN** la clave no está definida
- **THEN** la herramienta lo comunica sin mostrar valores y las filas quedan como no medidas

#### Scenario: Comprobación de fuga
- **WHEN** se ejecutan las pruebas con una clave de prueba
- **THEN** ni el informe ni la tabla ni la salida estándar contienen el valor de la clave

### Requirement: Salida de la medición de coste de IA
El sistema DEBE (SHALL) emitir un informe `rows-v1` con fuente `JUP-130`, grupo `ai_cost` y tipo B, con la ventana y el commit, y una tabla Markdown reproducible. DEBE (SHALL) declarar que el gasto es local a la máquina que ejecutó las consultas y que no demuestra el coste de un uso real.

#### Scenario: Declaración de límites
- **WHEN** se lee la tabla de la memoria
- **THEN** indica el origen del gasto, la ventana y que el coste de pruebas no es el de producción
