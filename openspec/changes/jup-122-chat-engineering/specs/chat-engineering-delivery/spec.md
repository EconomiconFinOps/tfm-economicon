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
