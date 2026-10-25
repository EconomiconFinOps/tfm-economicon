## Purpose

Define el formato estructurado y los guardrails que controlan la entrada, el
prompt y la salida del agente FinOps de Economicon.

## ADDED Requirements

### Requirement: Respuesta FinOps versionada y estricta

El agente SHALL devolver `FinOpsResponse` version `1.0` con status, answer,
scope, evidence, metrics, recommendations, assumptions, limitations y
next_actions; todos los objetos SHALL rechazar campos adicionales.

#### Scenario: Provider devuelve el contrato completo

- **WHEN** la respuesta contiene todos los campos requeridos y enums validos
- **THEN** el runtime devuelve un objeto estructurado serializable

#### Scenario: Provider agrega un campo no definido

- **WHEN** el JSON contiene cualquier propiedad adicional
- **THEN** la respuesta se rechaza antes de llegar al pipeline

### Requirement: JSON Schema estricto para providers compatibles

El runtime SHALL pasar `response_format.type=json_schema`, schema name estable y
`strict=true` a cada invocacion; SHALL volver a validar localmente la respuesta.

#### Scenario: Invocacion de provider

- **WHEN** el runtime solicita una respuesta
- **THEN** el provider recibe el JSON Schema derivado de `FinOpsResponse`

#### Scenario: Salida que el endpoint no hizo cumplir

- **WHEN** el provider devuelve JSON que no satisface el schema
- **THEN** Pydantic lo rechaza sin confiar en la declaracion del endpoint

### Requirement: Estados controlan contenido accionable

Las respuestas `ok` y `partial` SHALL incluir evidencia; `no_data`,
`insufficient_data`, `unsupported`, `refused` y `error` SHALL excluir metricas
y recomendaciones.

#### Scenario: Datos insuficientes

- **WHEN** no existe evidencia para calcular o recomendar
- **THEN** la respuesta usa `insufficient_data` sin metricas ni recomendaciones

#### Scenario: Respuesta completa sin evidencia

- **WHEN** el provider usa `ok` con evidence vacio
- **THEN** la validacion rechaza la respuesta

### Requirement: Toda metrica y recomendacion referencia evidencia existente

El contrato SHALL exigir evidence IDs no vacios en metricas y recomendaciones,
y SHALL comprobar que cada ID existe una sola vez en la coleccion evidence.

#### Scenario: Referencia desconocida

- **WHEN** una metrica cita un evidence ID no incluido
- **THEN** la respuesta completa se rechaza

#### Scenario: Evidence ID duplicado

- **WHEN** dos fuentes usan el mismo ID
- **THEN** la respuesta completa se rechaza

### Requirement: Recomendaciones permanecen propuestas humanas

Cada recomendacion SHALL incluir categoria, accion, rationale, confianza,
riesgo, evidencia y `requires_human_approval=true`; savings y currency SHALL
aparecer juntos o ambos ser null.

#### Scenario: Recomendacion valida sin ahorro calculable

- **WHEN** existe evidencia pero no un ahorro determinista
- **THEN** savings y currency son null y la accion sigue requiriendo aprobacion

#### Scenario: Provider afirma ejecucion autonoma

- **WHEN** omite o cambia la aprobacion humana a false
- **THEN** el schema rechaza la recomendacion

### Requirement: Claims numericos requieren evidencia

El runtime SHALL rechazar claims monetarios o porcentuales en `answer` cuando
la respuesta no contiene evidencia estructurada.

#### Scenario: Coste inventado en insufficient data

- **WHEN** answer afirma una cifra en EUR, USD, euros o porcentaje sin evidence
- **THEN** la postvalidacion rechaza la respuesta

#### Scenario: Metrica respaldada

- **WHEN** una respuesta `ok` contiene metrica y evidence ID valido
- **THEN** el valor se acepta como dato estructurado pendiente de renderizado

### Requirement: Scope limitado a Azure simulado

El schema SHALL fijar cloud `azure` y data_environment `simulated`; el preflight
SHALL evitar invocar el provider para una fuente cloud no soportada.

#### Scenario: Fuente AWS heredada

- **WHEN** el job declara `aws-cur`
- **THEN** el runtime devuelve `unsupported` sin invocar el modelo

#### Scenario: Fuente Azure admitida

- **WHEN** el job declara un alias Azure Cost Management permitido
- **THEN** puede continuar a la invocacion del provider

### Requirement: Contexto tenant mediado por la aplicacion

El preflight SHALL exigir tenant valido para autorizacion y SHALL omitir su
identificador del prompt enviado al modelo.

#### Scenario: Tenant ausente

- **WHEN** el job no contiene tenant no vacio
- **THEN** el runtime falla antes del provider

#### Scenario: Tenant presente

- **WHEN** el job contiene tenant y source validos
- **THEN** el prompt no contiene el identificador del tenant

### Requirement: Metadata se trata como datos no confiables

El runtime SHALL exigir metadata objeto, acotarla, serializarla de forma
determinista y delimitarla como `UNTRUSTED_DATA`; SHALL redactar valores de
claves asociadas a credenciales.

#### Scenario: Metadata contiene prompt injection

- **WHEN** un valor ordena ignorar instrucciones o revelar el system prompt
- **THEN** permanece dentro del bloque de datos no confiables y no altera la jerarquia

#### Scenario: Metadata contiene API token

- **WHEN** una clave coincide con token, secret, password, credential, authorization o API key
- **THEN** su valor se sustituye por `[REDACTED]` antes del provider

#### Scenario: Dataset publico contiene valores FinOps

- **WHEN** metadata contiene region, resource group, servicio o tag publico
- **THEN** sus valores funcionales se conservan dentro de los limites de longitud

### Requirement: Prompt fija limites FinOps y de agencia

El system prompt SHALL prohibir inventar datos y citas, afirmar Azure real,
revelar secretos, ejecutar recomendaciones y hacer rightsizing sin telemetria;
SHALL exigir JSON sin Markdown.

#### Scenario: Solicitud de apagar un recurso

- **WHEN** el usuario intenta convertir una recomendacion en mutacion Azure
- **THEN** el agente usa `refused` o `unsupported` y no afirma haber actuado

#### Scenario: Solicitud de causa raiz sin contexto operativo

- **WHEN** solo existen datos de coste
- **THEN** el agente presenta una hipotesis o limitacion, no una causa confirmada

### Requirement: Errores no filtran la salida del modelo

Un error de parseo o validacion SHALL usar un mensaje controlado y SHALL evitar
incluir el JSON completo del provider en excepciones o logs.

#### Scenario: Provider devuelve contenido malicioso e invalido

- **WHEN** la respuesta no es JSON valido
- **THEN** se genera `AgentResponseError` generico sin copiar el contenido

### Requirement: Mock seguro y verificable

El provider mock SHALL devolver un `FinOpsResponse` valido con
`insufficient_data` y SHALL evitar recomendaciones o cifras simuladas.

#### Scenario: Desarrollo sin credenciales LLM

- **WHEN** el processor usa `llm_provider=mock`
- **THEN** recibe una respuesta estructurada valida sin consumo externo
