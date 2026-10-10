# containerized-runtime Specification

## Purpose

Define the reproducible and least-privilege Docker application baseline required
by JUP-049 without claiming the later JUP-050 local-environment or JUP-052
deployment outcomes.
## Requirements
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

### Requirement: Immutable image inputs

The four application base images and the CockroachDB, RabbitMQ and
Postgres/pgvector images SHALL use immutable registry digests while retaining
readable release tags. This JUP-049 baseline does not extend digest pinning to
the Prometheus/Grafana images inherited from JUP-043.

#### Scenario: A floating image tag is introduced

- **WHEN** one of the four application Dockerfile bases or three base
  infrastructure images omits its sha256 digest
- **THEN** the topology validation fails before the change can be merged

### Requirement: Locked frontend image build

The frontend image SHALL activate pnpm 9.0.0, install the repository lockfile
with frozen semantics and build the frontend before starting its runtime server.

#### Scenario: Clean frontend image build

- **WHEN** Docker builds the frontend without host `node_modules` or a pnpm cache
- **THEN** it installs the locked dependency graph and produces the Vite `dist`
  output without selecting a newer incompatible pnpm release

#### Scenario: Frontend starts with a read-only root

- **WHEN** the built frontend image starts under its non-root runtime user
- **THEN** it copies `vite.config.ts` to writable `/tmp` and starts the installed
  Vite preview binary using that copy, without invoking Corepack or pnpm

### Requirement: Least-privilege application containers

Every application SHALL run as a non-root user with an init process, read-only
root filesystem, writable `/tmp`, disabled privilege escalation and an
application-level healthcheck. This requirement applies to the four MVP
applications; it does not impose that baseline on infrastructure or monitoring.

#### Scenario: Complete stack becomes ready

- **WHEN** Compose starts the isolated JUP-049 project
- **THEN** all four application containers report healthy while inspection
  confirms non-root users, read-only roots and no-new-privileges

### Requirement: Healthy dependency gates

Backend, processor and frontend SHALL wait for dependency health rather than
only dependency process creation. The processor SHALL also wait for a healthy
backend, so that the backend-owned schema exists before the processor uses it.
Prometheus SHALL wait for healthy backend and processor, and Grafana SHALL wait
for healthy Prometheus, preserving the JUP-043 dependency gates.

#### Scenario: Dependency has started but is not ready

- **WHEN** a required database, broker, API or backend container has not passed
  its healthcheck
- **THEN** Compose does not start the dependent application as ready

#### Scenario: Processor waits for the backend on a cold start

- **WHEN** the complete stack starts with empty volumes
- **THEN** the processor container is created only after the backend reports
  healthy, and both backend and processor end healthy

#### Scenario: Backend never becomes healthy

- **WHEN** the backend container fails or does not pass its healthcheck
- **THEN** Compose does not start the processor and reports the unmet backend
  dependency instead of starting a processor without the backend schema

### Requirement: Preserved monitoring integration

The topology SHALL preserve JUP-043's read-only monitoring configuration mounts,
named data volumes and loopback-bound configurable host ports. Prometheus
SHALL retain its container healthcheck. Grafana functional readiness SHALL be
verified through `/api/health` during the isolated smoke; this requirement does
not claim that Grafana declares a Compose healthcheck.

#### Scenario: Contributor validates inherited monitoring

- **WHEN** the versioned topology test validates Prometheus and Grafana
- **THEN** it verifies the configuration paths and read-only mounts, named data
  volumes, loopback ports and healthy dependency gates
- **AND** it checks the Prometheus healthcheck and disabled Grafana anonymous
  access without extending the application privilege or digest baseline

### Requirement: Isolated real validation

JUP-049 SHALL retain evidence of a complete build and health smoke using a
unique Compose project on `dockerserver` without modifying unrelated workloads.

#### Scenario: Remote smoke completes

- **WHEN** the nine-service JUP-049 project passes the configured container
  healthchecks, application HTTP checks, Prometheus readiness and target checks,
  and Grafana `/api/health` check
- **THEN** the project is removed by its exact name and the evidence records the
  branch, commit, commands and observed results

### Requirement: Broker healthcheck does not alter broker state ownership

The RabbitMQ healthcheck SHALL run its diagnostic command as the `rabbitmq`
user, so that a healthcheck executed before the server reads its Erlang cookie
cannot create files in `/var/lib/rabbitmq` owned by root.

#### Scenario: Healthcheck runs before the server is ready

- **WHEN** the healthcheck runs immediately after the RabbitMQ container starts
  on a new volume
- **THEN** the server still starts, and every file under `/var/lib/rabbitmq`,
  including `.erlang.cookie`, is owned by the `rabbitmq` user

#### Scenario: Healthcheck reverts to root

- **WHEN** the RabbitMQ healthcheck command does not switch to the `rabbitmq`
  user
- **THEN** the topology validation fails

### Requirement: Health windows cover the measured cold start

Each application healthcheck SHALL allow, through `start_period` plus
`interval` times `retries`, at least the cold-start time measured on an empty
database with margin. For the processor, whose first start applies CockroachDB
migrations before serving `/health`, `start_period` SHALL be at least 300 seconds.

#### Scenario: First start on empty volumes

- **WHEN** `docker compose up --wait` runs on new volumes
- **THEN** it returns success once every service is healthy, without the
  processor being reported unhealthy while its migrations run

#### Scenario: Processor window is shortened

- **WHEN** the processor `start_period` is below 300 seconds
- **THEN** the topology validation fails

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
