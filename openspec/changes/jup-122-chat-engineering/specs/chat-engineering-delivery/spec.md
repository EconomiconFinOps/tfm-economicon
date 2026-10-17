## ADDED Requirements

### Requirement: Entrega de ingeniería con activación controlada
El sistema MUST mantener el chat desactivado por defecto hasta aceptar la
entrega semántica JUP-123, sin iniciar inferencias ni recuperación automática.

#### Scenario: Runtime desactivado
- **WHEN** CHAT_ENABLED no se activa expresamente en el arranque
- **THEN** no se crea el planificador del chat
- **AND** generate, resume y summary/retry devuelven 503 sin contactar al proveedor

#### Scenario: Disponibilidad autenticada del chat
- **WHEN** una sesion valida con tenant autorizado consulta GET /assistant/capabilities
- **THEN** recibe solo chat_enabled booleano desde el estado efectivo del backend y Cache-Control no-store
- **AND** la consulta no crea conversaciones, planificador ni inferencias

#### Scenario: Acceso condicionado al backend
- **WHEN** el estado es pendiente, falso, invalido o la consulta falla
- **THEN** no se monta el panel ni su acceso
- **AND** antes de crear una conversacion o enviar una pregunta se comprueba de nuevo la disponibilidad sin reutilizar respuestas de otra sesion o tenant

#### Scenario: Chat habilitado
- **WHEN** el backend confirma chat_enabled true para la sesion y el tenant activos
- **THEN** se conserva el recorrido del chat habilitado y sus guardas de autorizacion

### Requirement: Recuperación y streaming coherentes
El sistema MUST conservar estados duraderos y cerrar el stream correctamente
cuando la confirmación SQL y la publicación RAM ocurran en cualquier orden.

#### Scenario: Estado confirmado antes del evento
- **WHEN** una operación está completed, failed, paused o waiting antes de publicar
- **THEN** el observador recibe el estado final o de espera correspondiente
- **AND** no queda esperando indefinidamente ni persiste texto parcial

#### Scenario: Fallo transitorio del planificador
- **WHEN** la recuperación de operaciones o resúmenes lanza una excepción de BD
- **THEN** el planificador sobrevive y vuelve a intentar la recuperación
- **AND** no registra SQL, credenciales ni contenido de conversaciones

### Requirement: Truncación y Unicode
El gateway MUST distinguir truncación transitoria de respuesta inválida y
conservar caracteres UTF-8 de cuatro bytes a través de fragmentos arbitrarios.

#### Scenario: Búsqueda requerida truncada
- **WHEN** la fase nativa requerida termina con finish_reason length
- **THEN** devuelve 502 incomplete y permite reintento sin historial parcial

#### Scenario: Emoji fragmentado byte a byte
- **WHEN** un carácter fuera del BMP llega en fragmentos de un byte
- **THEN** streaming y respuesta final conservan exactamente el mismo carácter

### Requirement: Compatibilidad de integración
La entrega MUST preservar migraciones de chat y anomalías, demo JUP-119 y
provisión idempotente del secreto HMAC en CD.

#### Scenario: Raíz CD existente
- **WHEN** se prepara una revisión con un secreto válido ya provisionado
- **THEN** se reutiliza sin rotación ni copia al árbol del release
- **AND** un secreto inválido se rechaza

#### Scenario: Release actual y candidato coexistentes
- **WHEN** CD prepara los slots 0 y 1 y mantiene el release actual mientras comprueba el candidato
- **THEN** cada slot recibe una subred privada distinta y una IP del processor perteneciente a esa subred
- **AND** ambos conservan red interna, puerto privado sin publicar y el mismo HMAC valido sin rotacion

#### Scenario: Explicacion de anomalia integrada con historial atomico
- **WHEN** una conversacion autorizada solicita la explicacion determinista de JUP-038
- **THEN** conserva el snapshot del tenant y su evidencia de anomalia, con una sola pareja atomica y correlacion de historial
- **AND** una conversacion ocupada o un fallo de persistencia no deja mensajes parciales ni incrementa consultas completadas

#### Scenario: Evidencias coexistentes
- **WHEN** la respuesta contiene fuentes documentales validas, costes o evidencia de anomalia
- **THEN** la interfaz conserva la prioridad documental, costes y anomalia sin mezclar fuentes incompatibles
- **AND** las fuentes documentales mantienen su presentacion compacta y no se muestra un aviso redundante cuando no hay fuentes

### Requirement: Tokenizer fijo incluido durante build
El tokenizer MUST quedar fuera de Git y descargarse solo durante build o
preparacion explicita, desde la revision oficial fija y con SHA256 y tamano
verificados. El artefacto efectivo y sus pins MUST permanecer identicos.

#### Scenario: Cache verificada y runtime offline
- **WHEN** existe cache verificada o se construye una imagen con el recurso descargado
- **THEN** la cache se reutiliza sin red y runtime usa el tokenizer incluido sin descargarlo

#### Scenario: Descarga corrupta
- **WHEN** el recurso descargado no coincide con el SHA256 o tamano fijado
- **THEN** la preparacion falla sin reemplazar un archivo existente por el recurso corrupto
- **AND** backend, processor y CI no aceptan ese recurso para iniciar sus comprobaciones

### Requirement: Secretos locales excluidos del release
El copiado de releases y los contextos Docker MUST excluir .secrets en cualquier
nivel y preservar la provision y permisos actuales del HMAC privado de CD.

#### Scenario: Fuente con secretos locales
- **WHEN** el arbol de origen contiene .secrets en raiz o subdirectorios
- **THEN** ningun secreto de esos directorios se copia al release o al contexto Docker
- **AND** el HMAC valido del directorio privado sigue intacto y los symlinks siguen rechazados

### Requirement: Fixture SQL reproducible y finalizacion real
Las pruebas SQL MUST crear su propio escenario en la base configurada, esperar
la tarea de limpieza real sin cancelarla y mantener las aserciones del producto.

#### Scenario: HTTP terminado con limpieza pendiente
- **WHEN** una respuesta de timeout llega antes de settled y el cierre fisico
- **THEN** la prueba espera con shield y limite acotado la tarea propietaria antes de comprobar finalizacion
- **AND** la espera no cambia los deadlines del producto ni cancela la tarea de limpieza

#### Scenario: Base SQL aislada configurada
- **WHEN** las pruebas obligatorias reciben una base CockroachDB desechable configurada
- **THEN** crean datos sinteticos propios, los limpian y ejecutan los escenarios sin omisiones
- **AND** no dependen de nombres o filas historicas del equipo del autor
