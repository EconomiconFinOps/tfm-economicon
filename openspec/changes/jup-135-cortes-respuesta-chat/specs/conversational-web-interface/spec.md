## MODIFIED Requirements

### Requirement: Tres reintentos funcionales adicionales

Por Paris PM21:33:08/21:46:22, el backend SHALL permitir inicial más tres retries automáticos, máximo cuatro intentos por operación,120s por intento y480s activos. Transporte/gateway SHALL mantener retries0 para no multiplicarlos. Interrupciones transitorias SHALL programar otro intento si queda; errores permanentes, Stop voluntario y desconexión de lector SHALL quedar diferenciados. Por decisión humana PM23:05:12, cada solicitud SHALL disponer de dos presupuestos independientes acumulados:120s de espera automática local y120s de espera automática del proveedor. Retry/resume/recuperación de la misma operación SHALL conservar sus consumidos y contador, sin reinicio. El máximo240s de esperas automáticas SHALL distinguirse del tiempo total hasta respuesta y del presupuesto120s de ejecución por intento. Retry-After SHALL respetarse: si excede saldo proveedor restante, pausa visible conservando solicitud/contador/retry_at y reanudación explícita solo desde fecha mínima, sin renovar presupuestos ni anticipar envío. Una respuesta del modelo que el procesador rechaza con la categoria `invalid_response` SHALL tratarse como fallo reintentable dentro del mismo maximo de cuatro intentos y del mismo presupuesto de tiempo; los rechazos propios del backend (citas sin resolver, `ResponseValidationError`, `CalculationError`), un flujo mal formado y los errores de configuracion SHALL seguir siendo permanentes. El primer intento SHALL decodificar con temperatura 0 y los reintentos SHALL usar temperatura creciente acotada (0,2 por intento adicional, maximo 0,6) para no reproducir la misma salida degenerada.

#### Scenario: Cuatro interrupciones

- **WHEN** cuatro intentos de una operación fallan transitoriamente
- **THEN** no se ejecuta un quinto, cada intento usa ID/buffer propios, pregunta única y error final saneado

#### Scenario: Espera y cancelación

- **WHEN** el proveedor indica Retry-After o el usuario pulsa Stop durante espera
- **THEN** la espera automática solo se programa si cabe en el saldo proveedor acumulado restante; en otro caso hay pausa visible y resume explícito solo≥retry_at, sin reset de saldos/contador; Stop confirmado cancela programación y nunca se envía antes de fecha permitida

#### Scenario: Salida rechazada por el validador

- **WHEN** el intento 1 termina con una respuesta que el procesador rechaza como `invalid_response`
- **THEN** se programa otro intento con la misma pregunta mientras queden intentos y presupuesto, y la operacion solo termina `failed` tras agotarlos

#### Scenario: Reintento tras salida desbocada

- **WHEN** un intento termina `incomplete` por agotar el tope de salida
- **THEN** el reintento usa una temperatura mayor que 0

### Requirement: Instruccion explicita para respuestas no accionables

El prompt de chat SHALL indicar que los estados no_data, insufficient_data, unsupported, refused y error requieren metrics y recommendations vacios. Las sugerencias no financieras para conseguir informacion SHALL expresarse en next_actions. Los validadores existentes SHALL permanecer activos sin reparacion silenciosa del candidato. La unica reparacion admitida es omitir de `metrics`, con el aviso visible «Se omitio una cifra financiera que no pudo verificarse con la consulta de costes.» en `limitations`, una metrica financiera cuyo nombre, valor y unidad no coincidan con el registro autorizado; las referencias a evidencia inexistentes, los estados no accionables con metricas o recomendaciones y las divergencias de periodo o suscripciones SHALL seguir rechazando la respuesta.

#### Scenario: Pantalla sin costes disponibles

- **WHEN** el proveedor responde no_data ante una pantalla vacia
- **THEN** devuelve metrics y recommendations como listas vacias y puede explicar como obtener informacion en next_actions; una respuesta que incumpla esta regla sigue siendo rechazada sin persistir una respuesta parcial

#### Scenario: Cifra anadida por el modelo

- **WHEN** el modelo devuelve una metrica que no figura en el registro autorizado de la consulta de costes
- **THEN** la respuesta se persiste sin esa metrica y con la limitacion visible, y nunca se muestra la cifra no verificada

## ADDED Requirements

### Requirement: Segmentos de interpretacion vacios

Un segmento `inference` vacio o formado solo por espacios SHALL omitirse sin aportar texto. Si tras omitirlo no queda texto renderizado, la respuesta SHALL seguir rechazandose como texto vacio, y un segmento `inference` que no sea una cadena SHALL seguir rechazandose.

#### Scenario: Interpretacion en blanco entre segmentos validos

- **WHEN** la respuesta contiene un segmento `inference` en blanco entre segmentos con contenido
- **THEN** el segmento se omite y el resto de la respuesta se conserva

### Requirement: Envio tras un fallo sin respuesta

Cuando una operacion termina `failed` o `cancelled`, la interfaz SHALL cargar el estado de memoria de la conversacion para que el envio se desbloquee si la memoria no esta comprimiendo ni bloqueada, tambien cuando esa operacion fue la primera pregunta de una conversacion nueva.

#### Scenario: Primera pregunta fallida

- **WHEN** la primera pregunta de una conversacion recien creada termina `failed`
- **THEN** la interfaz solicita el resumen de memoria y, si la cola esta ociosa, habilita el envio sin reabrir la conversacion desde el historial
