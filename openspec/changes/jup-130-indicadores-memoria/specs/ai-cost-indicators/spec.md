## ADDED Requirements

### Requirement: Coste de IA por consulta y por modelo desde el registro del gateway
El sistema DEBE (SHALL) calcular, a partir de `/spend/logs` del gateway aislado, el coste total, el número de consultas y el coste por consulta, en conjunto y por alias de modelo, para una ventana temporal indicada. Una consulta es una fila de chat (`acompletion`) terminada con éxito. El coste por consulta estimado es la suma del gasto de esas filas dividida por su número, y es una contabilidad derivada de la tarifa por token, no una factura. Las filas de embeddings (`aembedding`) se informan aparte como coste estimado y nunca entran en el coste por consulta, porque no llevan identificador de generación de OpenRouter y no se pueden contrastar. La herramienta solo DEBE (SHALL) leer el gasto y los metadatos técnicos, nunca el contenido de las consultas.

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

#### Scenario: Consulta correcta con gasto cero
- **WHEN** una consulta de chat terminó con éxito y el gateway registra gasto cero
- **THEN** su coste estimado es cero medido solo si OpenRouter lo confirma, y si no lo confirma queda como no confirmada
- **AND** el recuento de consultas con gasto estimado cero se informa aparte

#### Scenario: Embeddings
- **WHEN** la ventana contiene llamadas de embeddings
- **THEN** su coste estimado se informa en una fila propia y no se suma al coste por consulta ni a la cobertura

### Requirement: Coste facturado por OpenRouter y diferencia con la estimación
El sistema DEBE (SHALL) consultar a OpenRouter el coste facturado (`/api/v1/generation`) de cada generación de la ventana cuyo identificador conste en el registro del gateway, y calcular el coste facturado total, el coste facturado por consulta, la cobertura (generaciones con coste confirmado / generaciones de la ventana) y la diferencia entre el coste estimado por el gateway y el facturado sobre las generaciones confirmadas. El coste por consulta del indicador DEBE (SHALL) salir del importe facturado cuando exista, y el estimado del gateway se informa siempre con la etiqueta «estimado». Una generación que OpenRouter no devuelve (por ejemplo, 404) NO DEBE (SHALL NOT) contarse como coste 0: cuenta como no confirmada y reduce la cobertura. El `usage` acumulado de la clave (`/api/v1/key`) NO DEBE (SHALL NOT) usarse como coste de la ventana.

#### Scenario: Todas las generaciones confirmadas
- **WHEN** OpenRouter devuelve el coste de todas las generaciones de la ventana
- **THEN** la cobertura es 1, el coste por consulta es el facturado y se informa la diferencia con la estimación del gateway con su signo

#### Scenario: Una generación sin respuesta
- **WHEN** OpenRouter responde 404 para una generación de la ventana
- **THEN** esa generación cuenta como no confirmada y la cobertura baja
- **AND** su estimación del gateway queda fuera del cálculo de la diferencia

#### Scenario: OpenRouter no alcanzable
- **WHEN** OpenRouter no responde o la clave del proveedor no está definida
- **THEN** el coste facturado, la cobertura y la diferencia son `not_measured`, el coste estimado sigue medido y se declara que no está contrastado

#### Scenario: Registro del gateway sin identificador de generación
- **WHEN** una fila del gateway no trae identificador de generación
- **THEN** no se consulta a OpenRouter por ella y cuenta como no confirmada

#### Scenario: Gasto acumulado de la clave
- **WHEN** el `usage` de la clave supera lo facturado por las generaciones de la ventana
- **THEN** la diferencia no se atribuye a la ventana ni se suma al coste

### Requirement: Rechazos del gateway y errores del proveedor por separado
El sistema DEBE (SHALL) informar, como proporciones de las peticiones de la ventana con su numerador y su denominador, la tasa de rechazos 429 del propio gateway (límite por clave, `ProxyRateLimitError`) y la tasa de errores del proveedor (códigos 5xx de `APIError`), sin mezclarlas ni llamar «del proveedor» a un 429 del gateway. Un cero medido se distingue de la ausencia de datos.

#### Scenario: Rechazo por límite de la clave
- **WHEN** una petición falla con código 429 y clase `ProxyRateLimitError`
- **THEN** cuenta en la tasa de rechazos del gateway y no en la de errores del proveedor

#### Scenario: Error del proveedor
- **WHEN** una petición falla con código 5xx y clase `APIError`
- **THEN** cuenta en la tasa de errores del proveedor y no en la de rechazos del gateway

#### Scenario: Sin fallos en la ventana
- **WHEN** hay peticiones y ninguna falló
- **THEN** ambas tasas son 0 medido con su denominador

#### Scenario: Fallo de otra clase
- **WHEN** una petición falla con un código o una clase que no es ninguna de las dos
- **THEN** cuenta en el recuento total de fallos pero en ninguna de las dos tasas

#### Scenario: Sin peticiones
- **WHEN** la ventana no tiene peticiones
- **THEN** ambas tasas son `not_measured`

### Requirement: Secretos y contenido fuera del informe
El sistema DEBE (SHALL) leer la clave de administración del gateway y la clave de OpenRouter de una variable de entorno o de un fichero cada una, y nunca imprimirlas, escribirlas en el informe, en el manifiesto ni en la tabla de la memoria. Los informes solo DEBEN (SHALL) contener recuentos, sumas e identificadores permitidos por el contrato `rows-v1`, sin prompts, respuestas, identificadores de generación ni mensajes de error del proveedor.

#### Scenario: Clave ausente
- **WHEN** alguna de las dos claves no está definida
- **THEN** la herramienta lo comunica sin mostrar valores y lo que dependa de esa clave queda como no medido

#### Scenario: Comprobación de fuga
- **WHEN** se ejecutan las pruebas con claves de prueba
- **THEN** ni el informe ni la tabla ni la salida estándar contienen el valor de ninguna de las dos claves ni identificadores de generación

### Requirement: Salida de la medición de coste de IA
El sistema DEBE (SHALL) emitir un informe `rows-v1` con fuente `JUP-130`, grupo `ai_cost` y tipo B, con la ventana y el commit, y una tabla Markdown reproducible. DEBE (SHALL) declarar que el gasto es local a la máquina que ejecutó las consultas y que no demuestra el coste de un uso real.

#### Scenario: Declaración de límites
- **WHEN** se lee la tabla de la memoria
- **THEN** indica el origen del gasto, la ventana y que el coste de pruebas no es el de producción
