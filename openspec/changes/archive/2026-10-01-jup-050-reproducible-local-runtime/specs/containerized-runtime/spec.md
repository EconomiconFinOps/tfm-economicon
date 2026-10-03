## MODIFIED Requirements

### Requirement: Complete MVP topology

The repository SHALL declare buildable images for backend, frontend, processor
and the simulated Azure Cost API, and SHALL declare CockroachDB, RabbitMQ and
Postgres/pgvector as their base infrastructure dependencies. It SHALL preserve
the Prometheus and Grafana services inherited from JUP-043 and SHALL declare the
five named volumes `cockroach-data`, `pgvector-data`, `rabbitmq-data`,
`prometheus-data` and `grafana-data`. Every stateful infrastructure service
(CockroachDB, Postgres/pgvector and RabbitMQ) SHALL mount its data directory on
its named volume, never on an anonymous volume.

#### Scenario: Contributor validates the topology

- **WHEN** the versioned Docker topology test parses the root Compose file
- **THEN** it finds exactly nine services: four applications, three base
  infrastructure services and the two inherited monitoring services
- **AND** it finds the five named volumes for the two databases, the broker and
  monitoring

#### Scenario: RabbitMQ state on an anonymous volume

- **WHEN** the RabbitMQ service does not mount `rabbitmq-data` on
  `/var/lib/rabbitmq`
- **THEN** the topology validation fails

## ADDED Requirements

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
