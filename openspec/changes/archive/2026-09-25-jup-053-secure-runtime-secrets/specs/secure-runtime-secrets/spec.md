## ADDED Requirements

### Requirement: External configuration rejects insecure runtime defaults
Backend and processor SHALL require explicit external secrets, reject known insecure defaults outside explicit test configuration and never infer test mode from the test runner or AI execution mode.

#### Scenario: Missing or unsafe required credentials
- **GIVEN** a non-test runtime with a missing/blank required secret, replace-me-auth-secret, a short JWT key, guest/guest RabbitMQ or default pgvector password
- **WHEN** startup validates configuration
- **THEN** it fails before clients, workers or database initialization, without emitting the supplied values.

#### Scenario: Valid external configuration and precedence
- **GIVEN** valid external credentials and an explicitly selected dotenv file with a conflicting value
- **WHEN** settings load and clients are constructed
- **THEN** environment wins, secrets remain masked in settings representations, and clients receive the correct values; no implicit .env is read.

#### Scenario: Controlled test fixtures do not weaken other modes
- **GIVEN** tests inject synthetic credentials, explicit test mode and isolated dependencies
- **WHEN** configuration and negative non-test cases execute
- **THEN** fixtures need no real credentials, missing values still fail, and AI_EXECUTION_MODE=test alone does not bypass runtime protections.

### Requirement: Configuration validation respects existing provider boundaries
Processor SHALL preserve its conditional AI validators and SecretStr handling; gateway upstream/master credentials MUST NOT enter application configuration, browser bundles or image build inputs.

#### Scenario: Conditional gateway credentials
- **GIVEN** mock providers without a gateway key, or litellm selected with an absent, malformed or upstream key
- **WHEN** settings validate with otherwise valid runtime configuration
- **THEN** mock configuration remains possible, unsafe litellm configuration fails, and existing alias/dimension/evaluation rules remain enforced without deploying a provider.

### Requirement: Startup and import errors do not expose secrets
Services SHALL defer resource construction until controlled startup and SHALL sanitize errors before emitting diagnostics, including failures before logging configuration completes.

#### Scenario: Import without configured secrets
- **GIVEN** an isolated environment without runtime credentials
- **WHEN** app.main is imported
- **THEN** no DB/broker/vector connection or worker starts, while actual startup still requires valid configuration.

#### Scenario: Every entrypoint fails safely
- **GIVEN** invalid settings or a dependency exception containing synthetic credentials
- **WHEN** backend run or processor API, worker, combined or ingestion entrypoint starts
- **THEN** readiness is not reached and failure reports only safe diagnostics on stdout/stderr, including chained exceptions, with no worker left running after initialization failure.

### Requirement: Local insecure database use requires an approved exception
The local exception and full pre-code gate are APPROVED as recorded in proposal.md. The exception SHALL require development/test, explicit opt-in defaulting to false, an allowed local target and operator-confirmed disposable isolation; production/shared use MUST remain prohibited.

#### Scenario: Exception is absent or used outside its boundary
- **GIVEN** a credential-free CockroachDB DSN with no opt-in, production/shared use or a nonlocal target
- **WHEN** startup is attempted
- **THEN** it is rejected despite the approval; TLS/provisioning remains separate scope requiring approval.

#### Scenario: Approved disposable local operation
- **GIVEN** the recorded local exception approval, development/test mode, explicit opt-in and an operator-confirmed disposable isolated local stack with loopback published ports
- **WHEN** the local exception is exercised after the full pre-code gate
- **THEN** only that local DB connection is permitted; JWT, broker and vector password protections remain active, and approval never enables opt-in automatically.

### Requirement: Diagnostics redact bounded sensitive data
Services SHALL redact sensitive named fields and configured secret values, including URL-encoded forms, after interpolation/exception formatting and before rendering. This SHALL cover nested structures, standard logging and structlog, without claiming detection of unknown secrets or arbitrary encodings.

#### Scenario: Logs and exception chains contain sentinels
- **GIVEN** synthetic active secrets in positional messages, nested fields and chained exceptions
- **WHEN** application or standard-library logs are rendered
- **THEN** sentinels and credential-bearing URLs/headers are absent while valid JSON, service, level, logger, timestamp, request_id where available and safe exception metadata remain.

#### Scenario: Request and job failures remain safe
- **GIVEN** sensitive request inputs or an internal failure containing a sentinel
- **WHEN** validation returns 422, an internal error returns 500, or ingestion persists failure
- **THEN** responses and stored error fields omit raw input/context/exception secrets and use safe diagnostics; bodies and authorization are not logged, and the legitimate login access_token contract remains unchanged.

### Requirement: Examples and image inputs exclude real credentials
The project SHALL inventory credential sources and distinguish synthetic simulator/test fixtures from actual credentials. Examples SHALL contain no usable real secrets, and all application build contexts/layers and frontend output MUST exclude runtime secret material.

#### Scenario: Compose and examples use external inputs
- **GIVEN** the proposed configuration with required secret fields left empty
- **WHEN** Compose/runtime validation is attempted
- **THEN** required credentials cannot fall back to defaults; conditional gateway values remain optional for mocks and simulator fixtures remain explicitly classified as synthetic.

#### Scenario: Build boundaries exclude sentinel files
- **GIVEN** synthetic .env and variant files at root and nested application locations
- **WHEN** each declared Docker context, resulting application image layers and frontend bundle are checked
- **THEN** neither sentinel files nor their values appear, and no runtime secret is supplied through ARG, image ENV or VITE_*.

#### Scenario: Repository inspection reports bounded evidence
- **GIVEN** versioned sources/examples and synthetic positive controls
- **WHEN** known-pattern and sentinel inspection runs without reading real credential stores
- **THEN** it identifies positive controls, classifies synthetic matches, reports paths/categories and coverage limitations without values, and does not claim universal secret detection.

### Requirement: Credential rotation is documented without implicit data changes
Documentation SHALL explain startup prerequisites, independent credential ownership and explicit rotation for new and existing installations, without treating environment replacement as a database or account password update.

#### Scenario: Existing installation rotates credentials
- **GIVEN** an existing demo user, persistent DB volumes and running credential consumers; Grafana relocation is excluded from this rotation scenario
- **WHEN** an operator follows the documented rotation procedure
- **THEN** server/account credentials are explicitly updated before coordinated consumer restart, JWT rotation invalidates prior tokens, and no volume deletion, silent hash overwrite or insecure-default rollback is required.

### Requirement: Approved Grafana externalization preserves the existing password
Grafana scope and the full pre-code gate are APPROVED as recorded in proposal.md. The existing password SHALL move to GRAFANA_ADMIN_PASSWORD in an ignored local .env excluded from Git, build contexts and browser bundles; .env.example SHALL leave it empty and Compose SHALL use required interpolation without a committed default, preserving existing environment precedence. The move MUST NOT erase, generate, rotate or reset the current password, account or volume, or disable authentication. Moving a weak value does not strengthen it; no broader hardening or scan result is implied.

#### Scenario: Grafana password source moves without changing the credential
- **GIVEN** an existing Grafana password, authentication and account/volume state represented by synthetic fixtures
- **WHEN** its source moves to GRAFANA_ADMIN_PASSWORD in the ignored local .env and the versioned fallback is removed
- **THEN** Compose rejects an absent/empty value and otherwise supplies the unchanged credential, preserving authentication and account/volume state; no secret enters examples, Git, build contexts or bundles and no password generation, rotation or reset occurs.
