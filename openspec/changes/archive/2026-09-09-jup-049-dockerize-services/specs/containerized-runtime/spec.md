## Purpose

Define the reproducible and least-privilege Docker application baseline required
by JUP-049 without claiming the later JUP-050 local-environment or JUP-052
deployment outcomes.

## ADDED Requirements

### Requirement: Complete MVP topology

The repository SHALL declare buildable images for backend, frontend, processor
and the simulated Azure Cost API, and SHALL declare CockroachDB, RabbitMQ and
Postgres/pgvector as their base infrastructure dependencies. It SHALL preserve
the Prometheus and Grafana services inherited from JUP-043 and the four named
volumes `cockroach-data`, `pgvector-data`, `prometheus-data` and `grafana-data`.

#### Scenario: Contributor validates the topology

- **WHEN** the versioned Docker topology test parses the root Compose file
- **THEN** it finds exactly nine services: four applications, three base
  infrastructure services and the two inherited monitoring services
- **AND** it finds the four named volumes for the two databases and monitoring

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
only dependency process creation. Prometheus SHALL wait for healthy backend
and processor, and Grafana SHALL wait for healthy Prometheus, preserving the
JUP-043 dependency gates.

#### Scenario: Dependency has started but is not ready

- **WHEN** a required database, broker, API or backend container has not passed
  its healthcheck
- **THEN** Compose does not start the dependent application as ready

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
