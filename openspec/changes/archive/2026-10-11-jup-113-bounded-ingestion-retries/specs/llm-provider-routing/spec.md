## MODIFIED Requirements

### Requirement: Fallos reales terminales sin alterar otros errores

El sistema SHALL convertir el fallo de salida de `parse_and_validate_response`
solo en ruta LiteLLM a ProviderError saneado. IngestTask SHALL conservar ese tipo
al registrar `failed`/`ingestion_failed`; worker SHALL ejecutar nack con
`requeue=False`. Los errores que no son ProviderError, incluidos los de los
proveedores mock, SHALL seguir la politica de fallo permanente de entrada y de
reintento acotado de `document-ingestion-handoff`; este requisito no les da otro
tratamiento.

#### Scenario: JSON incompatible despues de invoke
- **WHEN** el contenido LiteLLM llega al runtime pero incumple schema o guardrails
- **THEN** falla como ProviderError sin retry ni requeue, sin relajar guardrails
  ni incluir la respuesta en logs o excepciones

#### Scenario: Error tipado atraviesa ingestion
- **WHEN** chat o embeddings falla con ProviderError, incluido agotamiento transitorio
- **THEN** ingestion registra failed sin perder el tipo y el worker rechaza sin reencolar

#### Scenario: Exito y errores ajenos
- **WHEN** se procesa un exito, un InvalidJobMessage o un error ajeno a proveedores reales
- **THEN** el exito mantiene el ack y el InvalidJobMessage el rechazo existente
- **AND** el error ajeno sigue la politica de `document-ingestion-handoff`: se
  reintenta una vez como maximo y despues se descarta con el trabajo en `failed`
