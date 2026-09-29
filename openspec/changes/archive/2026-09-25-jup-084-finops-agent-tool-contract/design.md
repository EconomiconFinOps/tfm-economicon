JUP: JUP-084
Trello: https://trello.com/c/m1i7iXBm
ADRs: docs/adr/ADR-0001-azure-cost-api-simulation.md, docs/adr/ADR-0002-litellm-openrouter.md

## Context

El processor solo expone actualmente un proveedor mock con una respuesta
generica. El backend recupera fragmentos vectoriales y conserva IDs de citas,
pero no existe un registro de herramientas ni un bucle de ejecucion. Al mismo
tiempo, el corpus ya define reglas de negocio y el simulador Azure soporta un
subconjunto determinista de Cost Management Query.

JUP-084 fija la frontera antes de implementar el agente real. La decision
principal es que el modelo orquesta y redacta; los servicios de Economicon
autorizan, consultan, calculan y producen evidencia.

## Goals

- Proporcionar una taxonomia unica de funciones de usuario y herramientas.
- Evitar calculos financieros realizados a partir de texto por el LLM.
- Hacer explicitos autorizacion, procedencia, cobertura y limitaciones.
- Mantener schemas compatibles con ambos modelos aprobados.
- Permitir evolucion por historias sin exponer primitivas arbitrarias.

## Non-Goals

- Implementar herramientas en esta tarjeta.
- Convertir el agente en un administrador autonomo de Azure.
- Habilitar datos o servicios que no existen en el MVP.
- Resolver mediante prompt una regla que deba vivir en codigo versionado.

## Boundary

```text
usuario
  -> backend autenticado
  -> orquestador del agente
  -> registro de herramientas permitido
  -> servicios deterministas / RAG
  -> resultado estructurado con evidencia
  -> LLM redacta la respuesta
```

El LLM recibe schemas JSON y puede proponer una llamada. El orquestador valida
nombre y argumentos, incorpora `tenant_id`, `user_id`, roles y correlation ID,
ejecuta la implementacion registrada y devuelve el resultado como mensaje de
herramienta. El modelo nunca recibe credenciales ni una conexion de base de
datos.

## Capability Classes

El registro distingue dos conceptos:

- `lifecycle`: `contracted`, `conditional`, `future` o `prohibited`;
- `availability`: `enabled`, `experimental` o `disabled` en un despliegue.

`contracted` significa que los datos actuales permiten una implementacion
fiable. No significa que el codigo ya exista. Una herramienta `conditional`
solo se ejecuta si sus precondiciones de datos se cumplen. `future` no se
presenta al modelo. `prohibited` documenta una frontera que no puede registrarse.

## Tool Families

### Discovery and cost analysis

- `get_finops_capabilities`
- `list_dimension_values`
- `query_costs`
- `compare_cost_periods`
- `calculate_finops_kpis`
- `analyze_tag_coverage`

### Conditional analysis

- `project_period_end_cost`
- `detect_cost_anomaly_candidates`

### Knowledge

- `search_finops_knowledge`

### Future workflow

- `evaluate_budget`
- `get_rate_optimization_candidates`
- `estimate_recommendation_impact`
- `create_recommendation_draft`
- `update_recommendation_status`
- `record_anomaly_outcome`

Los contratos detallados y ejemplos viven en
`docs/architecture/finops-agent-tools.md`.

## Deterministic Calculations

Costes, diferencias, porcentajes, KPIs, cobertura temporal, umbrales y
ordenacion se calculan con codigo y tipos numericos adecuados. El modelo no
suma filas ni infiere un porcentaje a partir de snippets. La respuesta de una
herramienta incluye formula o metodo, operandos y moneda cuando proceda.

Periodos usan limites `[from, to)`. Los importes negativos y cero se conservan.
Una division por cero produce estado `unsupported` o una metrica sin valor,
nunca infinito ni un porcentaje inventado.

## Authorization

`tenant_id`, `user_id`, roles y correlation ID pertenecen a
`ToolExecutionContext` y no forman parte de los argumentos que puede generar
el modelo. Si una herramienta acepta `subscription_id`, el backend comprueba
que pertenece al tenant autenticado antes de consultar datos.

Las herramientas son de solo lectura en la primera fase. Las escrituras futuras
solo afectan a registros internos de Economicon y exigen rol, confirmacion
explicita, token de confirmacion de un solo uso e idempotency key. No se definen
mutaciones de recursos Azure.

## Dataset Constraints

El fixture canonico cubre 19 dias de junio de 2024 y soporta coste real a nivel
de suscripcion. Por eso:

- la proyeccion solo puede ser run rate, no forecast estacional;
- las anomalias son candidatas segun reglas declaradas, no deteccion robusta;
- no se permite rightsizing sin CPU, memoria, I/O, SLA y utilizacion;
- un resultado sin cobertura suficiente debe indicarlo de forma explicita.

El contrato Azure expone `CostCenter`, `Project`, `env` y `org`. El vocabulario
funcional usa `costcenter`, `application`, `environment` y `businessunit` como
aliases documentados. `owner` no esta disponible. En consecuencia, la primera
version puede medir cobertura de tags, pero no afirmar allocation completa ni
unallocated cost basado en owner.

## Knowledge and Citations

`search_finops_knowledge` devuelve identificador de documento, chunk, seccion,
fragmento y score. Las respuestas factuales basadas en documentos conservan
citas. Los numeros procedentes de consultas citan un `evidence_id` de consulta
con filtros, periodo y fecha del dato. Una cita no convierte una inferencia en
un hecho: el resultado separa `data`, `assumptions` y `limitations`.

## Portable Tool Calling

La linea base utiliza schemas compatibles con JSON Schema, llamadas
secuenciales y un maximo de cinco rondas. No depende de llamadas paralelas
porque su soporte puede variar entre modelos. Cada nombre de herramienta,
enum y campo requerido es identico para GLM-5.2 y DeepSeek.

La implementacion futura comprobara soporte de function calling al arrancar,
validara cada JSON recibido y ejecutara solo funciones presentes en un registro
local. Un error de argumentos se devuelve como resultado controlado; nunca se
evalua codigo generado.

## Limits and Observability

- maximo de cinco rondas por respuesta;
- maximo de dos consultas de coste normales por respuesta;
- `top_n` y `limit` acotados;
- timeout y cancelacion por herramienta;
- payloads y resultados truncados antes de enviarse al modelo;
- metricas de nombre logico, estado, latencia y correlation ID;
- prompts, respuestas, secretos y filas completas fuera de logs.

## Alternatives Considered

### Exponer una unica herramienta generica de SQL

Rechazado porque amplia el acceso, dificulta autorizacion por tenant y permite
consultas costosas o no reproducibles.

### Dar al modelo el endpoint Azure completo

Rechazado porque el modelo podria inventar versiones, dimensiones o scopes. Un
adaptador interno conserva el contrato aprobado y la autorizacion.

### Calcular KPIs en el prompt

Rechazado porque no ofrece precision numerica, trazabilidad ni pruebas
deterministas.

### Activar busqueda web del proveedor

Rechazado para el MVP. El corpus versionado es la fuente documental permitida;
la web introduciria fuentes no aprobadas, coste y comportamiento variable.

## Rollout

1. Aprobar JUP-084 y sus schemas.
2. Implementar el bucle portable y el registro en JUP-023/JUP-024.
3. Implementar discovery, consulta y calculos en JUP-026.
4. Conectar RAG y citas en JUP-022/JUP-025.
5. Habilitar herramientas condicionadas solo con pruebas de cobertura.
6. Incorporar workflows de escritura en tarjetas separadas.

## Risks

- Un catalogo demasiado amplio aumenta errores de seleccion; el runtime solo
  anuncia herramientas habilitadas y relevantes para el usuario.
- Las dimensiones del dataset pueden divergir del vocabulario de negocio; los
  aliases quedan versionados y las ausencias son visibles.
- Un modelo puede repetir una llamada; se aplican limites, cache por request e
  idempotencia para futuras escrituras.
- Proyecciones y anomalias pueden parecer mas precisas de lo que son; metodo,
  cobertura y limitaciones son obligatorios en el resultado.
