## MODIFIED Requirements

### Requirement: Complete MVP topology

The repository SHALL declare buildable images for backend, frontend, processor
and the simulated Azure Cost API, and SHALL declare CockroachDB, RabbitMQ and
Postgres/pgvector as their base infrastructure dependencies. It SHALL preserve
the Prometheus and Grafana services inherited from JUP-043 and SHALL declare
the five base named volumes `cockroach-data`, `pgvector-data`, `rabbitmq-data`,
`prometheus-data` and `grafana-data`. Every stateful infrastructure service
(CockroachDB, Postgres/pgvector and RabbitMQ) SHALL mount its data directory on
its named volume, never on an anonymous volume. An optional `ai` profile SHALL
add LiteLLM and its dedicated PostgreSQL with a distinct persistent named
volume without adding them to the default nine-service runtime.

#### Scenario: Contributor validates the topology

- **WHEN** the versioned Docker topology test parses the root Compose file
  without enabling optional profiles
- **THEN** it finds the nine base services: four applications, three base
  infrastructure services and two monitoring services
- **AND** it finds the five base named volumes
- **AND** neither LiteLLM nor its dedicated PostgreSQL starts

#### Scenario: RabbitMQ state on an anonymous volume

- **WHEN** the RabbitMQ service does not mount `rabbitmq-data` on
  `/var/lib/rabbitmq`
- **THEN** the topology validation fails

#### Scenario: Contributor enables real AI

- **WHEN** the `ai` profile is enabled from the principal Compose file
- **THEN** LiteLLM and its dedicated PostgreSQL are added to the same Compose
  project without removing any base service
- **AND** PostgreSQL data uses a separate named volume

## ADDED Requirements

### Requirement: Optional, reproducible gateway startup

The principal Compose SHALL provide one documented command to start the full
application with the `ai` profile and one to start the mock baseline.
The real-mode command SHALL also apply `infra/litellm/compose.ai.yml`, which
makes gateway health a required dependency for both consumers.
Default mock startup and configuration validation SHALL NOT require OpenRouter or
gateway administration credentials. Enabling `ai` SHALL reject absent required
gateway secrets rather than start an unauthenticated gateway. The one-time
creation of independent virtual keys SHALL use the same root Compose project,
without manually connecting a second project; after this bootstrap, the
documented full-stack command SHALL use those keys.

#### Scenario: Mock startup without gateway credentials

- **WHEN** a contributor selects mock providers and has no OpenRouter or
  gateway keys configured
- **THEN** Compose validates and starts the baseline without the gateway

#### Scenario: Real profile with missing secret

- **WHEN** the `ai` profile is started without an upstream key, master key or
  gateway database password
- **THEN** the gateway is not healthy and consumers do not use it
- **AND** no usable fallback credential is supplied

### Requirement: Internal gateway access and readiness

Backend and processor SHALL resolve and reach LiteLLM by its Compose service
name when `ai` is enabled. They SHALL wait for gateway health in real mode and
retain their existing base dependencies in mock mode. Backend and processor
SHALL receive different virtual keys; neither SHALL receive the upstream or
master key. The backend key SHALL only authorize `economicon-embedding`.
Gateway administration SHALL bind only to loopback, and its PostgreSQL SHALL
have no published host port. The healthcheck SHALL NOT call a model.

#### Scenario: Authorized and unauthorized gateway requests

- **WHEN** backend and processor use their respective virtual keys
- **THEN** each permitted request reaches the gateway and is authorized
- **AND** a request with an invalid key is rejected
- **AND** the backend key cannot call a chat alias

#### Scenario: Gateway is not ready

- **WHEN** the documented real-mode command enables `ai` and its required
  dependency override but LiteLLM has not passed its
  healthcheck
- **THEN** neither backend nor processor starts

### Requirement: Reused pinned gateway and durable state

The principal and isolated Compose runtimes SHALL reuse the same pinned
LiteLLM/PostgreSQL images, model aliases, privacy/logging configuration and
health behavior without divergent copies. Gateway virtual keys and spend
metadata SHALL reside in a dedicated named PostgreSQL volume separate from
application databases. Documentation SHALL explain two independent virtual
keys, safe start/stop and preservation of that volume.

#### Scenario: Containers are recreated

- **WHEN** gateway and PostgreSQL containers are recreated while their named
  volume is retained
- **THEN** previously created virtual keys remain valid and their persisted
  metadata remains available

#### Scenario: Isolated gateway regression

- **WHEN** the existing isolated LiteLLM test project runs after the change
- **THEN** it uses the canonical gateway configuration and preserves its
  synthetic authentication, privacy and logging checks
