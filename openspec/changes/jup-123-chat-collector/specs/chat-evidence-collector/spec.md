## ADDED Requirements

### Requirement: Recogida sin inferencia
El colector MUST usar exclusivamente GET sobre operaciones existentes y conservar
estado, recursos y fallos sin generar, reanudar o reintentar una respuesta.

#### Scenario: Operación terminal coherente
- **WHEN** pregunta, historial, resultado, IDs de citas y estados antes/después coinciden
- **THEN** el recibo indica VERIFIED_PUBLIC_SNAPSHOT con recursos y hash
- **AND** no declara calidad semántica, proveedor, runtime o coste verificados

#### Scenario: Fallo o evidencia incompleta
- **WHEN** falla una lectura, la operación sigue viva o una cita carece de evidencia
- **THEN** se conserva una recogida incompleta sin otro envío al modelo

### Requirement: Suplemento de recuperación exacto
El adaptador MUST conservar el recibo original y verificar operación, evidencia
ordenada y hash del payload antes de admitir un suplemento de RAG.

#### Scenario: Fragmento alterado
- **WHEN** el suplemento difiere del manifest del resultado
- **THEN** el original permanece intacto y la exportación queda bloqueada

### Requirement: Reutilización del banco JUP-071
El adaptador MUST usar los 29 casos originales y perturbados del evaluador de JUP-071 de
una copia local explícita, manteniendo prompts, hashes y rúbricas bajo su autoridad.

#### Scenario: Tres repeticiones
- **WHEN** se prepara N3
- **THEN** el plan contiene 87 muestras con identidad caso/repetición y prompt exacto
- **AND** conversaciones u operaciones reutilizadas se rechazan antes de consultar el API

#### Scenario: Exportación compatible
- **WHEN** se exporta una repetición con recibos verificables
- **THEN** el evaluador de JUP-071 acepta raw_version: 1 y live_unverified
- **AND** fallos técnicos quedan blocked, ausentes not_run y juicios pendientes
- **AND** reexportar la misma repetición conserva el mismo artefacto

#### Scenario: Corpus sin distancia medida
- **WHEN** un recibo verificado contiene algún fragmento de corpus sin distancia numérica medida
- **THEN** la exportación indica invalid_response, con respuesta y citas vacías, y el evaluador devuelve blocked
- **AND** los originales, el suplemento y public_evidence conservan los fragmentos completos sin inventar distancias
- **AND** no presenta el bloqueo de formato como un fallo de calidad semántica
