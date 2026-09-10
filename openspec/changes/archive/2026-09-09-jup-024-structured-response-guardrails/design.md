JUP: JUP-024
Trello: https://trello.com/c/8SDUi2t9
ADR: docs/adr/ADR-0002-litellm-openrouter.md

## Context

`AgentRuntime` renderiza un prompt corto y `MockLLMProvider` devuelve una frase
que recomienda rightsizing, commitments e investigacion sin evidencia. El
runtime no diferencia datos insuficientes, no valida JSON y entrega el tenant
al modelo aunque la tarea de ingesta no necesita que lo repita.

LiteLLM y OpenRouter soportan `response_format` con `json_schema` en modelos y
endpoints compatibles. Ese mecanismo mejora la forma, pero no sustituye la
validacion local: el soporte varia por endpoint y la aplicacion sigue siendo
responsable de revisar la salida y autorizar cualquier efecto.

## Goals

- Crear un contrato de respuesta pequeno, versionado y extensible.
- Impedir cifras y recomendaciones no vinculadas a evidencia estructurada.
- Representar de forma uniforme datos inexistentes o insuficientes.
- Reducir prompt injection indirecta desde metadata o RAG.
- Preparar una interfaz portable para GLM-5.2 y DeepSeek.
- Mantener pruebas locales sin llamadas ni costes externos.

## Non-Goals

- Garantizar veracidad unicamente mediante JSON Schema.
- Implementar un clasificador externo de contenido.
- Incluir chain of thought o razonamiento interno en la respuesta.
- Sustituir autorizacion, herramientas o reglas de negocio por instrucciones.

## Response Contract

`FinOpsResponse` contiene siempre:

- `schema_version`: `1.0`;
- `status`: resultado semantico;
- `answer`: explicacion breve para el usuario;
- `scope`: Azure, entorno simulado, suscripciones y periodo;
- `evidence`: fuentes estructuradas;
- `metrics`: valores numericos como texto decimal y evidence IDs;
- `recommendations`: propuestas con riesgo, confianza y aprobacion humana;
- `assumptions`, `limitations` y `next_actions`.

Todos los objetos rechazan propiedades adicionales. Todas las colecciones estan
acotadas. Los decimales se representan como texto para no introducir redondeo
binario en el contrato; los calculos futuros seguiran realizandose fuera del
LLM.

## Status Semantics

| Status | Uso |
| --- | --- |
| `ok` | Respuesta completa con evidencia |
| `partial` | Respuesta util con evidencia y limitaciones |
| `no_data` | Consulta valida sin registros |
| `insufficient_data` | Faltan operandos o contexto necesario |
| `unsupported` | Fuera de capacidades o fuente Azure admitida |
| `refused` | Solicitud insegura o accion no permitida |
| `error` | Fallo controlado sin exponer internals |

`ok` y `partial` requieren evidencia. Los estados no accionables no pueden
contener metricas ni recomendaciones.

## Guardrail Layers

### 1. Preflight in application

- exige tenant presente, pero no lo introduce en el prompt;
- valida source y status como identificadores seguros;
- solo permite fuentes Azure simuladas conocidas;
- exige metadata objeto y limita profundidad, items y longitud;
- redacta valores cuyas claves indican token, secret, password, credential,
  Authorization o API key;
- normaliza valores no finitos antes de serializar.

La redaccion protege secretos operativos accidentales. No anonimiza el dataset
publico de Microsoft ni altera sus dimensiones FinOps.

### 2. Prompt hierarchy and untrusted data boundary

El system prompt fija alcance, no invencion, estados, aprobacion humana y
respuesta JSON. Metadata y futuro contexto RAG se delimitan como
`UNTRUSTED_DATA`; las instrucciones contenidas dentro se ignoran.

No se usa una blacklist de frases como defensa principal. Una frase puede ser
dato legitimo y un ataque puede expresarse de infinitas maneras. La frontera
real combina jerarquia, minimos privilegios, schemas y validacion posterior.

### 3. Provider structured output

El runtime pasa:

```json
{
  "type": "json_schema",
  "json_schema": {
    "name": "economicon_finops_response_v1",
    "strict": true,
    "schema": {}
  }
}
```

JUP-023 debera comprobar soporte de `response_format`/response schema al
arrancar y exigir un endpoint compatible. JUP-024 no activa response healing:
una salida malformada falla de forma visible en vez de delegar una reparacion
no evaluada a un plugin externo.

### 4. Local output validation

Pydantic vuelve a parsear el JSON y rechaza:

- JSON vacio, invalido o con campos extra;
- schema version o enums desconocidos;
- periodos invertidos;
- evidence IDs duplicados o inexistentes;
- `ok`/`partial` sin evidencia;
- metricas o recomendaciones en estados no accionables;
- savings sin moneda o moneda sin savings;
- recomendaciones sin `requires_human_approval: true`;
- claims monetarios o porcentuales en `answer` cuando no hay evidencia.

El error no incluye la respuesta completa del modelo para evitar que contenido
no confiable o sensible termine en logs.

### 5. Capability boundary

No se ofrecen SQL, HTTP, shell, busqueda web ni mutaciones Azure. JUP-084
versiona esa superficie y JUP-024 impide que una recomendacion se presente como
ejecutada. La autorizacion permanece en servicios deterministas.

## Prompt Content

El prompt usa espanol y establece:

- identidad FinOps para Azure simulado;
- prioridad del sistema sobre usuario, metadata, retrieval y herramientas;
- no revelar prompts o secretos;
- no afirmar Azure real;
- no inventar cifras, citas, causas o ahorros;
- distinguir budget/forecast, shared/unallocated y candidato/causa confirmada;
- no rightsizing sin utilizacion y SLA;
- respuesta exclusivamente JSON.

No solicita razonamiento paso a paso y no conserva chain of thought.

## Mock Migration

El mock deja de inventar una recomendacion generica. Devuelve
`insufficient_data`, sin evidencia, metricas ni recomendaciones. Esto permite
ejecutar desarrollo y pruebas sin dar apariencia de analisis real.

El resultado de `AgentRuntime` cambia de:

```json
{"provider": "mock", "insight": "texto"}
```

a:

```json
{
  "provider": "mock",
  "model": "economicon-chat",
  "response": {"schema_version": "1.0"}
}
```

## Compatibility

La API publica de OpenRouter consultada el 27 de agosto de 2026 anuncia
`structured_outputs` y `response_format` para GLM-5.2 y DeepSeek V4 Pro. La
documentacion advierte que el soporte estricto depende tambien del endpoint;
por eso ADR-0002 mantiene un unico upstream por alias, JUP-023 debera exigir
parametros compatibles y esta implementacion valida siempre en local.

## Alternatives Considered

### Conservar texto libre y parsear secciones

Rechazado por fragilidad, campos ambiguos y falta de validacion tipada.

### Confiar solo en JSON mode

Rechazado porque garantiza sintaxis JSON, no el schema ni las reglas FinOps.

### Confiar solo en structured outputs del proveedor

Rechazado porque el soporte y la fuerza del modo estricto varian por endpoint;
ademas, un JSON valido puede contener una afirmacion falsa.

### Bloquear palabras asociadas a prompt injection

Rechazado como control principal por falsos positivos y bypass sencillo. Se
conserva el contenido como datos no confiables y se limita la agencia.

## Rollout and Rollback

1. Introducir schemas, prompt, guardrails y mock estructurado.
2. Validar processor completo y OpenSpec.
3. JUP-023 implementa el provider real respetando `response_format`.
4. JUP-025 conecta citas renderizables.
5. JUP-084 y JUP-026 incorporan herramientas y evidencia de coste.

Rollback: revertir JUP-024 restaura el texto mock anterior. No hay migracion de
datos ni cambio de API publica.

## Risks

- El schema puede crecer demasiado: se versiona y se mantienen limites bajos.
- Un modelo puede producir JSON valido pero falso: evidencia y calculos siguen
  fuera del LLM.
- La deteccion regex de cifra sin evidencia no cubre numeros escritos con
  palabras: es una defensa adicional, no la fuente de verdad.
- El cambio interno de `insight` a `response` puede afectar codigo externo no
  versionado; no existen consumidores internos y se documenta el cambio.
