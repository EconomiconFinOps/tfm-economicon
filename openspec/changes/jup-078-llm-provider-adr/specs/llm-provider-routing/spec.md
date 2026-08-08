## Purpose

Define el acceso configurable y observable de JUP-078 a chat y embeddings reales sin acoplar Economicon a un identificador externo.

## ADDED Requirements

### Requirement: Gateway obligatorio para proveedores reales
El sistema SHALL usar alias logicos de LiteLLM y SHALL impedir que los servicios configuren directamente un identificador con namespace de proveedor.

#### Scenario: Intento de bypass
- **WHEN** un servicio configura `openai/modelo` en vez de un alias
- **THEN** el arranque falla sin realizar ninguna llamada externa

### Requirement: Configuracion real completa
El sistema SHALL exigir URL absoluta, clave interna, alias de chat y alias de embeddings al activar LiteLLM.

#### Scenario: Falta la clave del gateway
- **WHEN** cualquier proveedor se configura como `litellm` sin clave interna
- **THEN** el servicio falla durante el arranque sin exponer secretos

### Requirement: Dimension de embeddings consistente
El sistema SHALL usar 1536 dimensiones para `economicon-embedding` y SHALL rechazar una dimension incompatible.

#### Scenario: Cambio incompatible
- **WHEN** LiteLLM se activa para embeddings con una dimension distinta
- **THEN** el pipeline detiene el arranque y exige migracion y reindexacion explicitas

### Requirement: Mock limitado fuera de evaluacion
El sistema SHALL permitir mocks en pruebas y desarrollo, pero SHALL rechazarlos en el modo `evaluation`.

#### Scenario: Evaluacion oficial con mock
- **WHEN** se inicia una evaluacion con chat o embeddings mock
- **THEN** la configuracion se rechaza y no produce evidencia valida

### Requirement: Sin fallback silencioso
El gateway SHALL utilizar un unico upstream por alias y SHALL devolver un error observable cuando no este disponible.

#### Scenario: Modelo no disponible
- **WHEN** OpenRouter rechaza el modelo
- **THEN** la operacion falla de forma trazable sin cambiar de modelo ni politica de privacidad

### Requirement: Privacidad y secretos
El gateway SHALL usar OpenRouter con ZDR y denegacion de data collection; las claves SHALL permanecer fuera de logs, respuestas, commits y artefactos.

#### Scenario: Error de autenticacion
- **WHEN** el upstream devuelve un error de autenticacion
- **THEN** solo se registran codigo, alias y correlation ID

### Requirement: Telemetria y presupuesto
El sistema SHALL medir estado, latencia, alias, modelo resuelto, tokens y coste cuando esten disponibles, y SHALL aplicar una clave virtual con presupuesto aprobado.

#### Scenario: Llamada completada
- **WHEN** termina una llamada real
- **THEN** puede atribuirse su uso y coste sin almacenar prompt ni respuesta
