## ADDED Requirements

### Requirement: La admisión rechaza un origen que el procesamiento no aceptaría

El backend DEBE (SHALL) rechazar en `POST /jobs/ingest` todo `source` que, tras quitar los espacios de
los extremos y pasarlo a minúsculas, no cumpla el identificador de origen que exige el processor:
`^[a-z0-9][a-z0-9._-]{0,63}$`. El rechazo usa el 422 saneado vigente y no tiene efectos. Un `source`
admitido se guarda y se publica tal como se envió. Backend y processor deben dar el mismo veredicto
para la tabla de casos compartida `docs/api/ingest-source-contract-cases.json`.

#### Scenario: Origen con caracteres no admitidos

- **WHEN** un usuario autenticado envía `POST /jobs/ingest` con `source` igual a
  `Azure Cost Management`
- **THEN** la respuesta es 422 con el cuerpo
  `{"detail":[{"type":"validation_error","msg":"Invalid request value"}]}`
- **AND** no se crea ningún trabajo, no se reserva publicación y no se publica ningún mensaje
- **AND** ni la respuesta ni los registros del backend contienen el valor enviado.

#### Scenario: Origen demasiado largo

- **WHEN** el `source` normalizado tiene 65 caracteres admitidos
- **THEN** la respuesta es el mismo 422 saneado y sin efectos
- **AND** con 64 caracteres admitidos la respuesta es 202.

#### Scenario: Origen admitido con relleno y mayúsculas

- **WHEN** el `source` es ` Azure-Cost `, que normalizado es `azure-cost`
- **THEN** la respuesta es 202
- **AND** el trabajo guardado y el mensaje publicado contienen el valor literal ` Azure-Cost `.

#### Scenario: Los dos servicios aplican la misma regla

- **WHEN** se evalúa cada caso de `docs/api/ingest-source-contract-cases.json` en el backend y en el
  processor
- **THEN** el backend admite exactamente los valores que el processor acepta y rechaza los demás.

### Requirement: Un fallo permanente de entrada se registra y se descarta en una entrega

El processor DEBE (SHALL) tratar como permanente el rechazo de un trabajo válido y autorizado por las
reglas de entrada del agente. El trabajo queda `failed` con el motivo `ingestion_failed` y el mensaje
se descarta sin reencolar en la misma entrega en que se detecta, sea o no una reentrega.

#### Scenario: Trabajo guardado con un origen no admitido

- **WHEN** llega la entrega de un trabajo ya guardado cuyo `source` no cumple la regla de admisión
- **THEN** el trabajo queda `failed` con `ingestion_failed` y el mensaje se descarta sin reencolar
- **AND** no se llama al proveedor ni se escriben documentos, fragmentos o embeddings
- **AND** el contador de trabajos fallidos aumenta en una unidad.

#### Scenario: El trabajo siguiente no queda retenido

- **WHEN** detrás de un trabajo rechazado por su entrada hay en la cola un trabajo válido de otro
  tenant
- **THEN** el trabajo válido se procesa y queda `completed`.

#### Scenario: Diagnóstico sin datos del trabajo

- **WHEN** el worker descarta un trabajo por un fallo permanente de entrada
- **THEN** registra un evento con un motivo de vocabulario cerrado y el identificador de correlación
- **AND** ni el evento ni la excepción contienen el `source`, el contenido o la causa original.

### Requirement: Un fallo no clasificado se reintenta como máximo una vez

El processor DEBE (SHALL) reencolar un fallo de procesamiento no clasificado solo cuando la entrega no
viene marcada por el broker como reentrega. Si la entrega es una reentrega y vuelve a fallar, el
trabajo queda `failed` y el mensaje se descarta. Un fallo no clasificado es el que ocurre después de
validar y autorizar el mensaje y no es un mensaje inválido, un fallo de proveedor ni un fallo
permanente de entrada.

#### Scenario: Primer fallo no clasificado

- **WHEN** la primera entrega de un trabajo válido falla con un error no clasificado
- **THEN** el trabajo queda `failed` con `ingestion_failed` y el mensaje se reencola
- **AND** el reintento conserva el sobre original y el identificador de correlación.

#### Scenario: El reintento se completa

- **WHEN** la reentrega de ese trabajo se procesa sin error
- **THEN** el trabajo queda `completed` y el worker confirma el mensaje.

#### Scenario: El reintento vuelve a fallar

- **WHEN** una entrega marcada como reentrega falla con un error no clasificado
- **THEN** el trabajo queda `failed` con `ingestion_failed` y el mensaje se descarta sin reencolar
- **AND** el worker registra el agotamiento con un motivo de vocabulario cerrado, sin el `source`,
  el contenido ni la causa
- **AND** el siguiente mensaje de la cola se procesa.

#### Scenario: Reentrega sin fallo anterior registrado

- **WHEN** el broker reentrega un mensaje porque la entrega anterior se interrumpió sin respuesta
  del worker, y esa reentrega falla con un error no clasificado
- **THEN** se descarta igual que un reintento agotado: el tope es de una reentrega como máximo y no
  garantiza ninguna.

### Requirement: Un mensaje solo se descarta con el trabajo en estado terminal o por ser inválido

El processor DEBE (SHALL) reencolar la entrega, sea o no una reentrega, cuando no puede leer el trabajo
guardado o no puede registrar su estado. Solo descarta un mensaje cuando es inválido o cuando el
trabajo tiene registrado `completed` o `failed`. Este caso no tiene tope de reintentos.

#### Scenario: Estado del trabajo no disponible

- **WHEN** la lectura del trabajo o el registro de su estado fallan porque el almacén no responde,
  en una entrega marcada como reentrega
- **THEN** el mensaje se reencola y no se descarta
- **AND** salvo en los mensajes inválidos, el worker no descarta el mensaje de un trabajo que sigue
  en `queued` o `running`.

#### Scenario: El fallo no se pudo registrar

- **WHEN** el procesamiento falla y además falla el registro de `failed`
- **THEN** el mensaje se reencola aunque la entrega sea una reentrega.

### Requirement: La reentrega de un trabajo completado exige un resultado con forma de objeto

El processor DEBE (SHALL) devolver el resultado guardado de un trabajo `completed` solo cuando es un
objeto, y un objeto vacío cuando no hay resultado. Un resultado que no se puede decodificar o que
tiene otra forma convierte la entrega en un mensaje inválido.

#### Scenario: Resultado corrupto

- **WHEN** se reentrega un trabajo `completed` cuyo resultado guardado es texto que no se puede
  decodificar, como una cadena vacía o `not json`
- **THEN** el mensaje se rechaza como inválido y se descarta sin reencolar
- **AND** la fila del trabajo no cambia y no se ejecuta el pipeline
- **AND** la excepción no contiene el resultado guardado.

#### Scenario: Resultado que no es un objeto

- **WHEN** el resultado guardado decodifica a una lista, un texto, un número o un booleano
- **THEN** el mensaje se rechaza como inválido, con las mismas garantías que el resultado corrupto.

#### Scenario: Resultado ausente o nulo

- **WHEN** el trabajo `completed` no tiene resultado o su resultado decodifica a nulo
- **THEN** la reentrega termina con un objeto vacío, sin ejecutar el pipeline ni cambiar la fila.

#### Scenario: Resultado con forma de objeto

- **WHEN** el resultado guardado es un objeto, llegue como texto o ya decodificado
- **THEN** la reentrega devuelve ese objeto sin ejecutar el pipeline ni cambiar la fila.
