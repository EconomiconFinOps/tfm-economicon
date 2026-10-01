# local-runtime-operations Specification

## Purpose
TBD - created by archiving change jup-050-reproducible-local-runtime. Update Purpose after archive.
## Requirements
### Requirement: Preflight diagnostic of the local environment

The repository SHALL provide a diagnostic command (`corepack pnpm local:doctor`)
that runs before the stack starts and reports every problem it finds, not only
the first one. It SHALL check:

- that `.env` exists, and if not, point to the README instead of creating it;
- that every variable the Compose file requires without default (`${VAR:?...}`)
  is present and not empty, reading the list from the Compose file itself; today
  `AUTH_SECRET_KEY`, `RABBITMQ_DEFAULT_USER`, `RABBITMQ_DEFAULT_PASS`,
  `RABBITMQ_ERLANG_COOKIE`, `RABBITMQ_URL`, `POSTGRES_PASSWORD`,
  `VECTOR_DATABASE_URL`, `DATABASE_URL` and `GRAFANA_ADMIN_PASSWORD`;
- that dependent values agree: the user and password in `RABBITMQ_URL` match
  `RABBITMQ_DEFAULT_USER` and `RABBITMQ_DEFAULT_PASS` after URL decoding; the
  password in `VECTOR_DATABASE_URL` matches `POSTGRES_PASSWORD` after URL
  decoding; `AUTH_SECRET_KEY` has at least 32 characters; the local insecure
  CockroachDB requires `RUNTIME_ENVIRONMENT` set to `development` or `test` and
  `ALLOW_INSECURE_LOCAL_DATABASE=true`;
- that the values satisfy the startup rules that backend and processor enforce
  in `app/core/runtime_secrets.py` and the backend settings: service schemes,
  host, port and database of each DSN, allowed query options, the insecure
  `DATABASE_URL` only towards a local host, non-empty credentials, no known
  placeholder or default credential (`guest`/`guest`, `postgres`) outside
  `RUNTIME_ENVIRONMENT=test`, single-line `AUTH_SECRET_KEY` of at least 32
  characters counted as code points, and a valid `DEMO_PASSWORD` whenever the
  demo seed is enabled; a test SHALL fail if the rule lists of backend or
  processor change without the diagnostic;
- that each host port the Compose file publishes, read from the Compose file
  with its default when the variable is unset (today `API_HOST_PORT`,
  `PROCESSOR_HOST_PORT`, `FRONTEND_HOST_PORT`, `AZURE_COST_API_HOST_PORT`,
  `COCKROACH_SQL_PORT`, `COCKROACH_HTTP_PORT`, `RABBITMQ_PORT`,
  `RABBITMQ_MANAGEMENT_PORT`, `PGVECTOR_PORT`, `PROMETHEUS_PORT` and
  `GRAFANA_PORT`), is a valid port number and is free on the address Compose
  binds it to, or held by this Compose project;
- which named volumes of the project already exist, stating whether this is a
  new or an existing installation.

Values SHALL be resolved with the same precedence as Compose: a variable set in
the process environment wins over `.env`. The command SHALL exit with a non-zero
status when any blocking problem exists and zero otherwise. It SHALL NOT create,
modify or generate `.env` or any secret.

#### Scenario: Clean clone with the example copied

- **WHEN** `.env` is a plain copy of `.env.example`
- **THEN** the diagnostic lists every required secret as missing and the
  insecure-database opt-in as not enabled, and exits non-zero

#### Scenario: Missing `.env`

- **WHEN** no `.env` exists
- **THEN** the diagnostic says so, points to the README section, exits non-zero
  and no `.env` is created

#### Scenario: Credentials that do not agree

- **WHEN** `RABBITMQ_URL` carries a password different from
  `RABBITMQ_DEFAULT_PASS`, or `VECTOR_DATABASE_URL` one different from
  `POSTGRES_PASSWORD`
- **THEN** the diagnostic names the two variables that disagree, without
  printing either value

#### Scenario: Values the backend would reject

- **WHEN** `.env` uses `guest`/`guest` for RabbitMQ, a placeholder such as
  `changeme` in any case, a `DATABASE_URL` with a PostgreSQL scheme, or an
  `AUTH_SECRET_KEY` of 16 emoji
- **THEN** the diagnostic names the variable and exits non-zero, instead of
  reporting `[OK]` and leaving the backend to fail at startup

#### Scenario: Values that Compose interpolates

- **WHEN** `.env` builds `RABBITMQ_URL` from `${RABBITMQ_DEFAULT_USER}` and
  `${RABBITMQ_DEFAULT_PASS}`, or contains `$` in an unquoted value
- **THEN** the diagnostic checks the value Compose will pass after
  interpolation, as `docker compose config` resolves it

#### Scenario: URL-encoded password that agrees

- **WHEN** a password contains characters such as `@`, `:` or `%` and the URL
  carries it URL-encoded
- **THEN** the diagnostic treats the values as matching

#### Scenario: Process environment overrides `.env`

- **WHEN** a required variable is empty in `.env` but set in the process
  environment
- **THEN** the diagnostic does not report it as missing

#### Scenario: Busy host port

- **WHEN** another process listens on the host port configured for a service
- **THEN** the diagnostic names the variable and port, and exits non-zero

#### Scenario: Two services on the same host port

- **WHEN** two port variables resolve to the same number
- **THEN** the diagnostic names both variables and exits non-zero

#### Scenario: Docker is not available

- **WHEN** the Docker daemon does not answer
- **THEN** the diagnostic still reports the `.env` problems, says that Docker
  does not answer, and exits non-zero

#### Scenario: Port held by this project

- **WHEN** the stack of this Compose project is already running
- **THEN** its own published ports are not reported as busy

#### Scenario: Existing installation

- **WHEN** the project's named volumes already exist
- **THEN** the diagnostic reports an existing installation and reminds that the
  credentials the volumes stored at first start (`RABBITMQ_DEFAULT_USER`,
  `RABBITMQ_DEFAULT_PASS`, `POSTGRES_PASSWORD`, `GRAFANA_ADMIN_PASSWORD`) must be
  kept, because changing them in `.env` does not change the service's; the
  environment value of `RABBITMQ_ERLANG_COOKIE` does take precedence

#### Scenario: Secrets never appear in the output

- **WHEN** the diagnostic runs with any combination of present, missing or
  disagreeing secrets
- **THEN** no secret value, nor any password embedded in a URL, appears in its
  standard output or error output

### Requirement: Single smoke of the minimal path

The repository SHALL provide one smoke command (`corepack pnpm local:smoke`) that
runs against the stack already started with `docker compose up --wait` and
checks, in order:

1. every application health endpoint answers successfully;
2. the demo operator logs in through the backend;
3. an Azure cost ingestion from the simulated API completes for the demo
   tenant;
4. the backend cost summary for that tenant returns data;
5. a document ingestion job is accepted by the backend (published to RabbitMQ)
   and the processor marks it as completed.

Each step SHALL have a bounded wait. On failure the command SHALL name the
failed step and exit non-zero; on success it SHALL exit zero. It SHALL read the
demo password from the environment and SHALL NOT print it, tokens or any secret.
It SHALL be safe to run more than once against the same stack.

#### Scenario: Healthy stack

- **WHEN** the smoke runs after `docker compose up --wait` with the demo seed
  enabled
- **THEN** the five steps pass and the command exits zero

#### Scenario: Demo seed disabled

- **WHEN** `DEMO_SEED_ENABLED` is not `true` or `DEMO_PASSWORD` is empty
- **THEN** the smoke stops before calling the backend and says which variable
  to set

#### Scenario: Processor stopped

- **WHEN** the processor is stopped while the rest of the stack is healthy
- **THEN** the smoke fails at the first step that needs the processor, names
  it, and exits non-zero within its bounded wait

#### Scenario: Second run

- **WHEN** the smoke runs twice in a row against the same stack
- **THEN** both runs pass

### Requirement: Stop and restart keep local data

`docker compose down` followed by `docker compose up --wait` SHALL keep the data
of CockroachDB, Postgres/pgvector and RabbitMQ, including durable messages still
queued. Only `docker compose down -v` SHALL remove it. The README SHALL state
what each way of stopping keeps and removes.

#### Scenario: Restart with data

- **WHEN** the smoke has run, the stack is stopped with `down` and started again
- **THEN** the previous cost records, users and document job remain, and the
  smoke passes again

#### Scenario: Queued message survives a restart

- **WHEN** a job is published while the processor is stopped, and the stack is
  then stopped with `down` and started again
- **THEN** the processor consumes and completes that job after the restart

#### Scenario: Full reset

- **WHEN** the stack is stopped with `down -v`
- **THEN** the next start is a new installation and the diagnostic reports it so

### Requirement: Documented path from a clean clone

The README SHALL describe, in order, the path from a clean clone to a verified
stack: copy `.env.example` to `.env` without overwriting an existing one, fill in
the external secrets and the local opt-ins, install the workspace dependencies
with `corepack pnpm install --frozen-lockfile`, run `local:doctor` until it passes,
run `docker compose up --build --wait`, and run `local:smoke`. It SHALL state the
expected duration of the first start.

#### Scenario: Following the README

- **WHEN** a contributor follows the README from a clean clone on a host with
  Docker and Node
- **THEN** each step produces the outcome the README describes, ending with the
  smoke passing

