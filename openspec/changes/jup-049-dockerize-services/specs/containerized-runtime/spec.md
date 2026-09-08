## Purpose

Define the reproducible and least-privilege Docker application baseline required
by JUP-049 without claiming the later JUP-050 local-environment or JUP-052
deployment outcomes.

## ADDED Requirements

### Requirement: Complete MVP topology

The repository SHALL declare buildable images for backend, frontend, processor
and the simulated Azure Cost API, and SHALL declare CockroachDB, RabbitMQ and
Postgres/pgvector as their infrastructure dependencies.

#### Scenario: Contributor validates the topology

- **WHEN** the versioned Docker topology test parses the root Compose file
- **THEN** it finds exactly the four application services and three
  infrastructure services required by the current MVP

### Requirement: Immutable image inputs

Application base images and external infrastructure images SHALL use immutable
registry digests while retaining readable release tags.

#### Scenario: A floating image tag is introduced

- **WHEN** a Dockerfile base or Compose infrastructure image omits its sha256
  digest
- **THEN** the topology validation fails before the change can be merged

### Requirement: Locked frontend image build

The frontend image SHALL activate pnpm 9.0.0, install the repository lockfile
with frozen semantics and build the frontend before starting its runtime server.

#### Scenario: Clean frontend image build

- **WHEN** Docker builds the frontend without host `node_modules` or a pnpm cache
- **THEN** it installs the locked dependency graph and produces the Vite `dist`
  output without selecting a newer incompatible pnpm release

### Requirement: Least-privilege application containers

Every application SHALL run as a non-root user with an init process, read-only
root filesystem, writable `/tmp`, disabled privilege escalation and an
application-level healthcheck.

#### Scenario: Complete stack becomes ready

- **WHEN** Compose starts the isolated JUP-049 project
- **THEN** all four application containers report healthy while inspection
  confirms non-root users, read-only roots and no-new-privileges

### Requirement: Healthy dependency gates

Backend, processor and frontend SHALL wait for dependency health rather than
only dependency process creation.

#### Scenario: Dependency has started but is not ready

- **WHEN** a required database, broker, API or backend container has not passed
  its healthcheck
- **THEN** Compose does not start the dependent application as ready

### Requirement: Isolated real validation

JUP-049 SHALL retain evidence of a complete build and health smoke using a
unique Compose project on `dockerserver` without modifying unrelated workloads.

#### Scenario: Remote smoke completes

- **WHEN** the seven-service JUP-049 project passes its health and HTTP checks
- **THEN** the project is removed by its exact name and the evidence records the
  branch, commit, commands and observed results
