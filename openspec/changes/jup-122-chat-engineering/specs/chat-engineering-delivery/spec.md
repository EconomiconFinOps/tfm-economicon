## ADDED Requirements

### Requirement: Entrega de ingeniería con activación controlada
El sistema MUST mantener el chat desactivado por defecto hasta aceptar la
entrega semántica JUP-123, sin iniciar inferencias ni recuperación automática.

#### Scenario: Runtime desactivado
- **WHEN** CHAT_ENABLED no se activa expresamente en el arranque
- **THEN** no se crea el planificador del chat
- **AND** generate, resume y summary/retry devuelven 503 sin contactar al proveedor

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
