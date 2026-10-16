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
- **WHEN** un recibo verificado contiene algún fragmento de corpus sin distancia numérica medida y el evaluador no anuncia ACCEPTS_UNMEASURED_DISTANCE = True
- **THEN** la exportación indica invalid_response, con respuesta y citas vacías, y el evaluador devuelve blocked
- **AND** los originales, el suplemento y public_evidence conservan los fragmentos completos sin inventar distancias
- **AND** no presenta el bloqueo de formato como un fallo de calidad semántica

#### Scenario: Evaluador con capacidad explícita
- **WHEN** la herramienta JUP-071 importada anuncia el booleano ACCEPTS_UNMEASURED_DISTANCE = True
- **THEN** conserva respuesta, citas y fragmentos de corpus con distance: null cuando la distancia no está medida
- **AND** no inventa distancias ni admite distancias mal formadas o no finitas
- **AND** sigue verificando originales, preguntas, historial y suplementos exactos antes de exportar

### Requirement: Contrato de estado y procedencia declarada
El adaptador MUST exportar estado estructurado sin texto de acciones y procedencia
por muestra desde los recursos del servidor, marcada como no atestiguada.

#### Scenario: Respuesta verificada con procedencia
- **WHEN** los recursos revalidados incluyen estado, next_actions, prompt_version, hashes o usage
- **THEN** structured contiene status y has_next_actions sin texto de acciones
- **AND** execution.collection.server_reported conserva la procedencia disponible por sample_id con attested: false
- **AND** no inventa valores ausentes ni identifica el hash del bundle como hash del texto del prompt

### Requirement: Planes por contenido y exportación observable
Los planes nuevos MUST fijar los contenidos relevantes de JUP-071, sin invalidarse
por commits ajenos a ellos, conservando los recibos de versiones anteriores.

#### Scenario: Commit documental ajeno al plan
- **WHEN** cambia el commit de JUP-071 pero no los ficheros congelados ni los prompts de un plan de versión 2
- **THEN** el plan y sus recibos siguen siendo válidos y reexportar mantiene la identidad de comparación
- **AND** cambiar un fichero congelado o prompt exige un nuevo plan

#### Scenario: Exportar todas las repeticiones
- **WHEN** se usa all-repetitions con un directorio nuevo
- **THEN** guarda una exportación por repetición, equivalente a exportarla por separado
- **AND** no sobrescribe destinos existentes ni ejecuta nuevas lecturas HTTP o inferencias

#### Scenario: Resultado parcial en modo estricto
- **WHEN** collect o export usa strict y hay muestras ausentes, incompletas o bloqueadas según su contrato
- **THEN** conserva la evidencia y devuelve código 3 con un resumen por estado
- **AND** los errores de entrada indican un motivo seguro sin imprimir texto arbitrario de excepciones externas
