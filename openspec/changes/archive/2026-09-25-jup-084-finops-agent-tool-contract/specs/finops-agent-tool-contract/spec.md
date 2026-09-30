## Purpose

Define la frontera verificable de funciones y herramientas que el agente FinOps
puede solicitar sin delegar autorizacion ni calculos financieros al LLM.

## ADDED Requirements

### Requirement: Registro explicito y reducido de herramientas

El sistema SHALL mantener un registro de herramientas con nombre estable,
schema de entrada, schema de salida, lifecycle y disponibilidad; el orquestador
SHALL anunciar al modelo unicamente herramientas registradas y habilitadas.

#### Scenario: Herramienta futura deshabilitada

- **WHEN** `evaluate_budget` no dispone de un repositorio de presupuestos
- **THEN** no se incluye en la lista de herramientas enviada al modelo

#### Scenario: Nombre no registrado

- **WHEN** el modelo solicita una funcion ausente del registro habilitado
- **THEN** el orquestador rechaza la llamada sin ejecutar codigo ni red

### Requirement: Contexto de autorizacion fuera de los argumentos LLM

El sistema SHALL inyectar tenant, usuario, roles y correlation ID desde la
sesion autenticada; esos campos SHALL permanecer fuera de los argumentos que
puede proponer el modelo.

#### Scenario: Suscripcion de otro tenant

- **WHEN** una llamada solicita una suscripcion que no pertenece al tenant de la sesion
- **THEN** la herramienta devuelve `forbidden` sin consultar ni revelar datos

#### Scenario: El modelo intenta suministrar un tenant

- **WHEN** los argumentos incluyen `tenant_id` o `user_id`
- **THEN** la validacion estricta rechaza los campos adicionales

### Requirement: Resultado comun trazable

Cada herramienta SHALL devolver estado, correlation ID, fuente, fecha del dato,
resultado, evidence IDs, supuestos y limitaciones mediante un envelope comun.

#### Scenario: Consulta completada

- **WHEN** `query_costs` obtiene filas validas
- **THEN** devuelve `ok`, moneda, periodo, filtros, cobertura y un evidence ID reproducible

#### Scenario: Datos validos pero inexistentes

- **WHEN** una consulta valida no encuentra registros
- **THEN** devuelve `no_data` con lista vacia y no inventa un total

### Requirement: Discovery restringido al dataset autorizado

`get_finops_capabilities` SHALL describir cobertura, dimensiones, tags, metricas
y disponibilidad; `list_dimension_values` SHALL enumerar solo valores visibles
para el tenant y dimension autorizados.

#### Scenario: Dimension no soportada

- **WHEN** el modelo intenta enumerar `owner`
- **THEN** la herramienta devuelve `unsupported` y declara que el dataset no contiene ese campo

#### Scenario: Limite excesivo

- **WHEN** `list_dimension_values` recibe un limite superior al maximo contractual
- **THEN** los argumentos se rechazan antes de consultar datos

### Requirement: Consulta de coste alineada con el contrato Azure simulado

`query_costs` SHALL soportar coste real, scope de suscripcion, periodos
`[from, to)`, granularidad `daily` o `none`, hasta dos agrupaciones y filtros
`in` sobre dimensiones y tags aprobados.

#### Scenario: Consulta por servicio y proyecto

- **WHEN** se consulta un periodo valido agrupado por `ServiceName` y tag `Project`
- **THEN** los resultados mantienen coste, moneda, orden de columnas, cobertura y procedencia

#### Scenario: Scope o operador fuera del MVP

- **WHEN** se solicita un management group, coste amortizado o un operador distinto de `in`
- **THEN** la herramienta devuelve `unsupported` sin ampliar silenciosamente el contrato

#### Scenario: Ajustes y creditos

- **WHEN** las filas contienen importes negativos o cero
- **THEN** se conservan en las agregaciones y en la evidencia

### Requirement: Comparaciones y KPIs deterministas

`compare_cost_periods`, `calculate_finops_kpis` y `analyze_tag_coverage` SHALL
calcular en codigo sus operandos, formulas, porcentajes y ordenacion; el LLM
SHALL limitarse a explicar el resultado.

#### Scenario: Comparacion con baseline

- **WHEN** dos periodos comparables tienen datos
- **THEN** la herramienta devuelve costes, diferencia absoluta, diferencia relativa, moneda y contribuidores

#### Scenario: Division por cero

- **WHEN** el denominador de una metrica es cero
- **THEN** el resultado marca la metrica como no calculable sin devolver infinito ni un valor inventado

#### Scenario: Allocation incompleta

- **WHEN** se solicita unallocated cost basado en owner y `owner` no existe
- **THEN** se devuelve `unsupported` y puede ofrecerse cobertura de tags como analisis alternativo

### Requirement: Proyeccion declarada como run rate

`project_period_end_cost` SHALL usar un metodo determinista de run rate,
identificar dias observados y dias del periodo y SHALL evitar denominar el
resultado forecast estadistico.

#### Scenario: Periodo parcial suficiente

- **WHEN** existen dias observados contiguos dentro de un mes
- **THEN** devuelve proyeccion, formula, cobertura y advertencia metodologica

#### Scenario: Cobertura insuficiente

- **WHEN** no se alcanza el minimo configurado de dias con datos
- **THEN** devuelve `insufficient_data` sin proyectar el cierre

### Requirement: Anomalias siempre candidatas y evidenciadas

`detect_cost_anomaly_candidates` SHALL aplicar umbrales versionados a series
deterministas y SHALL devolver candidatos, no causas raiz confirmadas.

#### Scenario: Doble umbral superado

- **WHEN** la diferencia relativa supera 20 por ciento y la absoluta supera 100 EUR por dia
- **THEN** se genera un candidato con scope, baseline, observado, severidad, evidencia y limitaciones

#### Scenario: Variacion esperada desconocida

- **WHEN** no hay datos de despliegues, trafico o utilizacion
- **THEN** el agente no atribuye una causa y propone investigacion

### Requirement: Recuperacion documental con citas

`search_finops_knowledge` SHALL buscar solo en el corpus permitido para el
tenant y SHALL devolver documento, chunk, seccion, fragmento y score.

#### Scenario: Respuesta conceptual con contexto

- **WHEN** el agente explica la diferencia entre budget y forecast
- **THEN** conserva las citas de los chunks utilizados en la respuesta

#### Scenario: Sin contexto relevante

- **WHEN** retrieval no supera el umbral de relevancia
- **THEN** devuelve `no_data` y el agente reconoce que no dispone de una fuente suficiente

### Requirement: Recomendaciones limitadas por la evidencia disponible

El sistema SHALL distinguir recomendaciones sustentadas, candidatos de
investigacion y acciones no evaluables con los datos actuales.

#### Scenario: Solicitud de rightsizing sin utilizacion

- **WHEN** solo existen datos de coste y facturacion
- **THEN** el agente no recomienda un nuevo tamaño y declara que faltan CPU, memoria, I/O, picos y SLA

#### Scenario: Recomendacion de tagging

- **WHEN** `analyze_tag_coverage` identifica coste sin un tag requerido disponible
- **THEN** puede generar un candidato con evidencia, impacto, riesgo y confianza sin modificar recursos

### Requirement: Superficie peligrosa prohibida

El registro SHALL excluir SQL arbitrario, HTTP arbitrario, shell, ejecucion de
codigo, busqueda web general, secretos y mutaciones de recursos Azure.

#### Scenario: Prompt solicita ejecutar SQL

- **WHEN** el usuario pide al agente una consulta SQL directa
- **THEN** el agente usa una herramienta FinOps permitida o rechaza la solicitud

#### Scenario: Prompt solicita apagar un recurso

- **WHEN** el usuario pide aplicar automaticamente una recomendacion
- **THEN** el agente explica que el MVP no dispone de mutaciones Azure y no ejecuta ninguna accion

### Requirement: Escrituras futuras con confirmacion explicita

Las herramientas futuras que cambien registros internos SHALL exigir rol
autorizado, confirmacion explicita, token de un solo uso e idempotency key.

#### Scenario: Borrador sin confirmacion

- **WHEN** el modelo solicita crear o actualizar una recomendacion sin confirmacion valida
- **THEN** la operacion no escribe y devuelve `confirmation_required`

#### Scenario: Repeticion de una escritura confirmada

- **WHEN** se repite la misma idempotency key
- **THEN** el sistema devuelve el resultado previo sin duplicar el registro

### Requirement: Orquestacion portable y acotada

El agente SHALL utilizar schemas identicos, llamadas secuenciales y un maximo
de cinco rondas con GLM-5.2 y DeepSeek; SHALL validar todos los argumentos antes
de ejecutar una herramienta.

#### Scenario: JSON invalido del modelo

- **WHEN** una llamada no cumple el schema de la herramienta
- **THEN** el orquestador devuelve un error controlado y no ejecuta la implementacion

#### Scenario: Limite de rondas alcanzado

- **WHEN** el modelo intenta superar cinco rondas
- **THEN** el orquestador detiene nuevas llamadas y responde con una limitacion trazable

### Requirement: Observabilidad sin contenido sensible

Cada ejecucion SHALL medir herramienta logica, estado, latencia y correlation
ID; prompts, respuestas, secretos y filas completas SHALL permanecer fuera de logs.

#### Scenario: Fallo de una herramienta

- **WHEN** una consulta agota su timeout
- **THEN** el log contiene herramienta, estado, latencia y correlation ID sin argumentos sensibles ni credenciales
