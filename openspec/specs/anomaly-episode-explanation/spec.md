# anomaly-episode-explanation Specification

## Purpose
Explica con palabras y cifras exactas por qué se marcó una anomalía de coste guardada, cuánto lleva
y en qué estado está, dentro de una conversación del asistente, de forma determinista y con
evidencia guardada, sin atribuir causa ni ahorro (JUP-038).
## Requirements
### Requirement: Selección autorizada de una anomalía guardada

El sistema DEBE (SHALL) aceptar, en un mensaje de una conversación del asistente, la selección de
una anomalía guardada por su identificador (`anomaly_query` con `episode_id`). La selección queda
limitada al cliente activo de la sesión y a la conversación de quien pregunta; el cliente y el
usuario salen de la sesión y nunca del cuerpo del mensaje. El texto de la pregunta no se interpreta
como filtro ni como autorización. La selección de una anomalía y la selección de costes por
propiedad son excluyentes en un mismo mensaje.

#### Scenario: Anomalía del cliente activo
- **WHEN** un usuario envía a una conversación suya un mensaje con el identificador de una anomalía guardada de su cliente activo
- **THEN** la respuesta es 201 con el mensaje del usuario y un mensaje del asistente que explica esa anomalía
- **AND** los dos mensajes quedan guardados en la conversación

#### Scenario: Anomalía de otro cliente o inexistente
- **WHEN** el identificador tiene el formato correcto pero pertenece a otro cliente o no existe
- **THEN** la respuesta es en los dos casos el mismo `404 {"detail":{"code":"anomaly_episode_not_found"}}`
- **AND** no se guarda ningún mensaje

#### Scenario: Selección inválida
- **WHEN** el identificador no tiene el formato de un episodio, la selección lleva campos adicionales (incluido un cliente o un usuario) o el mensaje trae a la vez una selección de costes por propiedad
- **THEN** la petición se rechaza con 422 antes de leer ninguna anomalía y antes de guardar ningún mensaje

#### Scenario: Conversación ajena
- **WHEN** la conversación pertenece a otro usuario o a otro cliente
- **THEN** la respuesta es el 404 de conversación no encontrada y no se lee ninguna anomalía

### Requirement: Explicación de por qué se marcó

La explicación DEBE (SHALL) decir el día de apertura, el coste observado ese día, la referencia
diaria con la que se comparó, la subida absoluta y la relativa, y que la regla marca un día solo
cuando supera las dos condiciones a la vez, con los umbrales y la versión de reglas guardados en
el episodio. Las cifras DEBEN (SHALL) calcularse con los valores exactos guardados, no con importes
ya redondeados. La explicación no vuelve a ejecutar la detección, no lee registros de coste y no
cambia ningún episodio.

#### Scenario: Subida que supera las dos condiciones
- **WHEN** se explica un episodio abierto el 2026-09-08 con referencia 400.00 EUR al día y coste observado 550.00 EUR
- **THEN** la explicación dice que el coste subió 150.00 EUR (37.50 %) sobre la referencia
- **AND** dice que la regla `jup019-daily-v1` exige superar lo esperado en más de 100.00 y en más de un 20 %, las dos condiciones a la vez

#### Scenario: Cifra redondeada igual al umbral
- **WHEN** la subida exacta del día de apertura es 100.004 y se muestra como 100.00
- **THEN** la explicación mantiene que la condición se cumple y dice que el valor exacto supera el umbral y que la cifra se muestra redondeada a dos decimales

#### Scenario: Explicar no detecta
- **WHEN** se pide la explicación de una anomalía
- **THEN** no se abre, continúa ni cambia ningún episodio y la fecha «Revisado hasta» del cliente no se mueve

### Requirement: Impacto, criticidad y seguimiento

La explicación DEBE (SHALL) decir el impacto acumulado en la moneda del episodio, cuántos días
cuenta y hasta qué día, la criticidad con el tramo de impacto que la determina, el estado de
seguimiento y si la subida se sigue observando. Cuando existan, DEBE (SHALL) decir también desde
qué día ya no se observa, el motivo y la fecha de cierre y la anomalía anterior del mismo servicio.

#### Scenario: Anomalía en seguimiento
- **WHEN** se explica un episodio nuevo con 400.00 EUR de impacto acumulado en 2 días hasta el 2026-09-09
- **THEN** la explicación dice ese impacto, esos días y esa fecha, criticidad P3 por estar por debajo de 500.00, estado «Nueva» y que se sigue observando

#### Scenario: Subida que ya no se observa
- **WHEN** el episodio está marcado como ya no observado desde un día
- **THEN** la explicación dice desde qué día y que la anomalía sigue abierta hasta que una persona la cierre

#### Scenario: Anomalía cerrada
- **WHEN** el episodio está resuelto o marcado como falso positivo
- **THEN** la explicación dice el estado, la fecha de cierre y el motivo que se registró al cerrarla

#### Scenario: Impacto redondeado igual al límite del tramo
- **WHEN** el impacto exacto es 499.996 y se muestra como 500.00
- **THEN** la explicación dice criticidad P3 y que la cifra se muestra redondeada

#### Scenario: Anomalía anterior del mismo servicio
- **WHEN** el episodio enlaza con uno anterior
- **THEN** la explicación dice que el servicio ya tuvo una anomalía anterior y da su identificador

### Requirement: Candidata, sin causa ni ahorro

La explicación DEBE (SHALL) presentar la anomalía como candidata para investigar, con la causa no
establecida, y DEBE (SHALL) incluir sus limitaciones. NO DEBE (SHALL NOT) atribuir una causa,
estimar un ahorro, convertir monedas ni sumar importes de monedas distintas. La respuesta se obtiene
sin modelo generativo, sin embeddings y sin recuperación documental. Cuando el cliente tiene datos
sintéticos de demostración, la explicación DEBE (SHALL) avisarlo.

#### Scenario: Sin causa atribuida
- **WHEN** se explica cualquier anomalía
- **THEN** la explicación dice que la causa no está establecida y enumera las limitaciones de la regla
- **AND** no menciona despliegues, uso, tráfico ni ahorro como hechos

#### Scenario: Datos sintéticos
- **WHEN** el cliente tiene alguna ingesta completada marcada como sintética
- **THEN** la explicación avisa de que los datos del cliente incluyen datos sintéticos de demostración

#### Scenario: Recuperación documental no disponible
- **WHEN** el proveedor de embeddings o el almacén vectorial no responden
- **THEN** la explicación de una anomalía se responde igual, sin contexto documental

#### Scenario: Otra moneda
- **WHEN** el episodio está en USD
- **THEN** todos los importes se muestran en USD, sin conversión

### Requirement: Los datos del cliente no suplantan la respuesta

El nombre del servicio y el motivo de cierre son datos del cliente. La explicación DEBE (SHALL)
mostrarlos entrecomillados en una sola línea, con los caracteres de control e invisibles
escapados, y el sistema NO DEBE (SHALL NOT) escribirlos en sus registros.

#### Scenario: Nombre de servicio con saltos de línea
- **WHEN** el nombre del servicio contiene un salto de línea seguido de una frase con aspecto de respuesta
- **THEN** la explicación lo muestra entre comillas en una sola línea y con el salto escapado

#### Scenario: Episodio sin servicio
- **WHEN** el episodio agrupa registros sin servicio informado
- **THEN** la explicación lo dice con un texto propio y no con un nombre vacío

#### Scenario: Registros del servidor
- **WHEN** se explica una anomalía
- **THEN** ningún registro del servidor contiene el nombre del servicio ni el motivo de cierre

### Requirement: Evidencia guardada y fotografía del episodio

El sistema DEBE (SHALL) guardar con el mensaje del asistente la evidencia de la explicación: el
episodio tal como estaba al explicarlo, los operandos exactos, las cifras derivadas, las
limitaciones, la marca de datos sintéticos, la fecha y hora de la explicación y un identificador
que depende del cliente y de esa fotografía. Esta evidencia se guarda separada de las citas
documentales y de la evidencia de costes por propiedad.

#### Scenario: Recarga y conversación mixta
- **WHEN** una conversación con una pregunta documental, una consulta de propiedad y una explicación de anomalía se vuelve a abrir
- **THEN** cada mensaje conserva su propia evidencia y las cifras de la explicación no cambian

#### Scenario: Mismo estado, mismo identificador
- **WHEN** la misma anomalía se explica dos veces sin que el episodio haya cambiado
- **THEN** las dos evidencias tienen el mismo identificador y distinta fecha y hora

#### Scenario: El episodio cambia después
- **WHEN** el episodio acumula más impacto o cambia de estado y se vuelve a explicar
- **THEN** la explicación nueva tiene otro identificador y refleja el estado nuevo
- **AND** la explicación anterior guardada no cambia

#### Scenario: Evidencia ligada al cliente
- **WHEN** dos clientes tienen episodios con los mismos valores
- **THEN** los identificadores de sus evidencias son distintos

### Requirement: Explicación no disponible sin inventar

Cuando el episodio no se puede explicar con las reglas que el sistema conoce o sus datos guardados
son incoherentes, el sistema DEBE (SHALL) responder `409 {"detail":{"code":"anomaly_explanation_unavailable"}}` sin guardar ningún
mensaje, en lugar de generar una explicación parcial o aproximada.

#### Scenario: Versión de reglas desconocida
- **WHEN** el episodio se abrió con una versión de reglas distinta de las que el sistema sabe explicar
- **THEN** la respuesta es ese 409 y no se guarda ningún mensaje

#### Scenario: Cifras que no cumplen la regla guardada
- **WHEN** los valores guardados del día de apertura no superan las dos condiciones de la regla del episodio
- **THEN** la respuesta es ese 409 y no se guarda ningún mensaje

#### Scenario: Episodio con datos incoherentes
- **WHEN** el estado guardado no es uno de los cuatro conocidos, el episodio está cerrado sin fecha o sin motivo de cierre, o consta como ya no observado sin la fecha desde la que no se observa
- **THEN** la respuesta es ese 409 y no se guarda ningún mensaje, en lugar de un error del servidor o un texto con valores vacíos

#### Scenario: Datos guardados que no pueden ser de un episodio real
- **WHEN** el episodio guardado tiene una observación distinta de `observed` y `no_longer_observed`, una moneda que sus reglas no evalúan, un número de días de impacto menor que 1, una fecha final del impacto anterior a la de inicio, un impacto acumulado menor que el exceso del día de apertura o un motivo de cierre vacío en un estado cerrado
- **THEN** la respuesta es ese 409 y no se guarda ningún mensaje, en lugar de una explicación con una cifra imposible

#### Scenario: Operandos no finitos o fuera de rango
- **WHEN** algún operando guardado no es un número finito (`NaN`, infinito), es negativo o excede la cota práctica de los costes de origen, `DECIMAL(38,12)` (más de 38 dígitos, más de 26 cifras enteras o más de 12 decimales, incluidos los exponentes negativos enormes como `1E-150`)
- **THEN** la respuesta es ese 409 y no se guarda ningún mensaje, en lugar de un error del servidor

#### Scenario: Fila guardada que la lectura no puede redondear
- **WHEN** la base guarda en una columna de importe del episodio (`DECIMAL` sin precisión) un valor `NaN`, infinito o enorme que la lectura del episodio no sabe redondear
- **THEN** la respuesta es ese 409 y no se guarda ningún mensaje, igual que si lo hubiera detectado el explicador, y no un error del servidor

### Requirement: Pedir y leer la explicación en el asistente

El redactor de mensajes del asistente DEBE (SHALL) ofrecer el modo «Explicar una anomalía», que
lista las anomalías guardadas del cliente activo con su servicio, moneda, día de inicio, criticidad
y estado, y envía la elegida junto con la pregunta. Este modo y el de costes por propiedad son
excluyentes. La respuesta DEBE (SHALL) mostrar la evidencia de la explicación en un bloque propio;
si la evidencia guardada no tiene la forma conocida, la interfaz DEBE (SHALL) decir que no está
disponible sin mostrar cifras parciales.

#### Scenario: Elegir y enviar
- **WHEN** el usuario activa «Explicar una anomalía», elige una y envía
- **THEN** la conversación muestra su pregunta y la explicación con el bloque de evidencia

#### Scenario: Cliente sin anomalías guardadas
- **WHEN** el cliente activo no tiene ninguna anomalía guardada
- **THEN** el modo lo dice, indica que se detectan desde el panel de Anomalías y no permite enviar

#### Scenario: La lista no se puede cargar
- **WHEN** la lista de anomalías falla al cargar
- **THEN** el modo muestra el error y no permite enviar

#### Scenario: Anomalía indicada en la dirección
- **WHEN** el asistente se abre con una anomalía del cliente activo indicada en la dirección
- **THEN** el modo aparece activado con esa anomalía elegida, en cuanto hay una conversación seleccionada

#### Scenario: Anomalía de la dirección que no está en el cliente activo
- **WHEN** la anomalía indicada en la dirección no está entre las del cliente activo
- **THEN** el modo lo avisa y no deja ninguna anomalía elegida

#### Scenario: Modos excluyentes
- **WHEN** el usuario activa uno de los dos modos estando activo el otro
- **THEN** el otro se desactiva y el mensaje enviado lleva una sola selección

#### Scenario: Error al pedir la explicación
- **WHEN** el backend responde que la anomalía no existe o que no se puede explicar
- **THEN** el redactor muestra el error, conserva la pregunta y no añade ninguna respuesta a la conversación

#### Scenario: Evidencia irreconocible
- **WHEN** un mensaje guardado trae una evidencia de explicación con otra versión o con campos que no cumplen el contrato
- **THEN** la interfaz muestra el texto del mensaje y dice que la evidencia de la explicación no está disponible
