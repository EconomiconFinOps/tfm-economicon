## ADDED Requirements

### Requirement: Único modelo generativo activo
The system SHALL offer economicon-chat as the only active generative alias,
mapping it to openrouter/deepseek/deepseek-v4.1-flash through deepinfra/fp8 normal.
It SHALL retain strict output validation, ZDR, data_collection deny, disabled
fallbacks/reasoning and existing permissions, budgets and retry/deadline limits.
Historical reports SHALL retain their original model identity.

#### Scenario: Active model selection
- **WHEN** the current gateway configuration is loaded
- **THEN** only the Flash generative mapping and unchanged embedding mapping exist
- **AND** retired GLM/Pro aliases cannot select another generative route

#### Scenario: Coordinated consumers
- **WHEN** chat, summary or an authorized provider diagnostic builds a request
- **THEN** it selects the stable alias and approved FP8 route without FP4/fallback

### Requirement: Tokenizer versioned without destructive history changes
New generations SHALL count with an immutable official Flash tokenizer installed
and verified at build time. Historical summary contracts SHALL select their exact
original reader and tokenizer. Limits and embedding tokenization SHALL not change.

#### Scenario: Historical summary read
- **WHEN** a stored summary has an authorized historical contract
- **THEN** its original reader validates it without rewriting its bytes or hashes

#### Scenario: New resource or incompatible tokenizer
- **WHEN** active resources are loaded or an incompatible contract is supplied
- **THEN** Flash resources use their pinned tokenizer and mismatches fail closed
- **AND** no asset is downloaded during runtime

## MODIFIED Requirements

### Requirement: Endpoint explicito del principal sin cambiar contrato

Para la configuración vigente, `economicon-chat` SHALL usar DeepSeek V4.1 Flash mediante
OpenRouter con `provider.only: [deepinfra/fp8]` y `require_parameters: true`.
SHALL conservar schema estricto completo, ZDR, `data_collection: deny`,
`allow_fallbacks: false`, `reasoning.enabled: false`, 30 s y maximo 800 tokens.
El alias secundario SHALL retirarse y embeddings SHALL permanecer sin cambios.

#### Scenario: Ruta principal compatible
- **WHEN** se prepara la solicitud del principal para la prueba aprobada
- **THEN** se transmite el schema completo intacto con la restriccion al unico
  endpoint y los parametros anteriores, sin conectar directamente a DeepInfra

#### Scenario: Endpoint incompatible o sin margen contable
- **WHEN** la ruta no satisface el contrato o no se han conciliado reservas y
  acreditado margen bajo los caps vigentes
- **THEN** no se repite una llamada real ni se cambia modelo, schema, privacidad,
  endpoint o caps para continuar; el uso observado cero no libera reservas
