# technical-architecture-deliverable Specification

## Purpose
Provide a dated, traceable technical architecture of Economicon, separating
implemented flows, optional configuration, historical evidence and documentary
AWS/Terraform references without claiming unverified runtime capabilities.
## Requirements
### Requirement: Traceable architecture views

The technical architecture SHALL provide component, data, deployment and sequence
views tied to a dated integrated code baseline and source references.

#### Scenario: Reader follows a user interaction

- **WHEN** the reader follows the assistant, document ingestion or Azure ingestion
- **THEN** the view distinguishes synchronous retrieval, queued document processing
  and CLI cost ingestion, with their actual data owners and dependency boundaries

### Requirement: Implemented and proposed capabilities remain distinct

The architecture SHALL distinguish implemented code, optional runtime configuration,
historical execution evidence and proposed integrations or cloud deployment.

#### Scenario: A gateway exists but chat generation is not integrated

- **WHEN** the architecture depicts tools, RAG and LLM in the user vertical
- **THEN** deterministic chat and implemented modules are identified separately
  from pending orchestration, without claiming end-to-end generative acceptance

#### Scenario: A reviewer reads the AWS proposal

- **WHEN** the proposal is linked from the deployment view
- **THEN** AWS is identified as a documentary reference without deployment,
  and account, budget or runtime migration are not prerequisites for accepting
  the documentation; historical EC2 execution steps are marked superseded

#### Scenario: A reviewer inspects the Terraform reference

- **WHEN** the requested Terraform template is included with the architecture
- **THEN** source, provider lockfile, examples and mock validation evidence are
  available in the repository, application adaptations are explicit, and neither
  mock tests nor disabled workloads imply deployed resources or a cost-free apply

### Requirement: Security and operations evidence boundaries

The architecture SHALL describe authentication, tenant authority, secret boundaries,
observability, CI/CD status and dataset limits, linking canonical decisions
without changing their acceptance state.

#### Scenario: A private deployment is claimed

- **WHEN** a reader assesses the local Compose topology
- **THEN** host port exposure, insecure local database exception, persistence
  limits and the absence of current host verification are visible

### Requirement: Canonical memory and attributable acceptance

The deliverable SHALL preserve the shared memory as its editable source and record
coverage of the official guide, human participation and criterion evidence.

#### Scenario: Technical reference is ready before human acceptance

- **WHEN** the repository contribution is delivered
- **THEN** pending memory incorporation, review and validation remain pending,
  without copying the complete memory or treating agent checks as human approval

### Requirement: La vista de arquitectura coincide con el stack integrado en su corte

La arquitectura técnica SHALL declarar la SHA de develop contra la que se verificó y, en esa SHA, SHALL
describir cada servicio, red, secreto y volumen de la topología local, así como cada capacidad integrada, sin
afirmaciones que el código contradiga. Las capacidades integradas pero desactivadas por defecto SHALL
describirse como tales, sin presentarlas como activas ni como pendientes. Las que el código prepara para un
entorno sin desplegar SHALL distinguirse de un despliegue realizado.

#### Scenario: Un servicio de Compose aparece en la topología

- **WHEN** un revisor lista los servicios, redes y volúmenes de Compose en la SHA del corte, con los perfiles y
  el overlay de IA
- **THEN** cada uno aparece en la vista de despliegue o tiene una justificación explícita de su ausencia
- **AND** los recuentos de servicios y volúmenes del documento coinciden con esa lista

#### Scenario: Una capacidad integrada está desactivada por defecto

- **WHEN** el documento describe una capacidad cuyo código está integrado pero cuya activación depende de
  configuración, como el chat generativo o la recuperación contextual e híbrida
- **THEN** indica qué la activa y su valor por defecto
- **AND** mantiene rotulado como objetivo lo que no está integrado, como las tools deterministas conectadas al
  agente

#### Scenario: El código admite un entorno cloud que no está desplegado

- **WHEN** el documento menciona modos de aplicación o pipelines para un proveedor cloud
- **THEN** separa lo que el código admite de lo que se ha desplegado a fecha del corte
- **AND** remite el estado operativo a la documentación de ese despliegue en lugar de copiarlo

#### Scenario: El corte declara la SHA verificada

- **WHEN** un lector abre la cabecera del documento
- **THEN** encuentra la fecha y la SHA de develop contra la que se contrastó el contenido
- **AND** el documento no presenta como estado actual un hecho posterior a ese corte

