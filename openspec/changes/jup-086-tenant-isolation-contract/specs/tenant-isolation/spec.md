## ADDED Requirements

### Requirement: Tenant selection is authorized by the authenticated session

Every tenant-aware API operation SHALL derive the user from the bearer session,
require an active tenant selector and verify membership before accessing data.
A tenant identifier supplied in a body SHALL only confirm, never replace, the
authorized header context.

Identity and membership discovery (`/me`, `/tenants`) SHALL authenticate the
user without requiring a selected tenant; discovery SHALL expose only that
user's memberships.

#### Scenario: Authenticated user discovers available tenants

- **WHEN** `GET /tenants` receives a valid bearer without `X-Tenant-Id`
- **THEN** it returns only the authenticated user's memberships so the
  frontend can select an authorized tenant before requesting tenant-owned data.

#### Scenario: Required tenant selector is absent

- **WHEN** an authenticated request reaches a tenant-aware operation without `X-Tenant-Id`
- **THEN** the API returns `400` before reading or writing tenant data.

#### Scenario: User selects an unauthorized tenant

- **WHEN** `X-Tenant-Id` is not present in the current user's `user_tenants`
- **THEN** the API returns a generic `403` without tenant metadata.

#### Scenario: Payload disagrees with authorized tenant

- **WHEN** a body contains `tenant_id` different from the authorized header tenant
- **THEN** the API returns `400` and publishes no job or write.

### Requirement: Tenant context propagates immutably through asynchronous work

The backend SHALL publish the authorized tenant and creator with every
tenant-aware job, and the processor SHALL use that trusted context for every
operational and vector write without accepting a replacement from document
content, user parameters or model output.

#### Scenario: Valid ingestion job is consumed

- **WHEN** the processor handles a schema-valid job emitted after authorization
- **THEN** its execution, normalized cost rows, documents, chunks and embeddings
  are persisted under exactly that job tenant.

#### Scenario: Job tenant context is missing or inconsistent

- **WHEN** a job lacks trusted tenant context or conflicts with its validated envelope
- **THEN** processing fails closed and writes no partial cross-tenant records.

### Requirement: Tenant-owned resources are queried within the authorization predicate

Repositories and vector retrieval SHALL scope costs, jobs, conversations,
messages, documents, chunks and embeddings by authorized tenant during lookup,
not by fetching a global identifier and checking it afterwards.

#### Scenario: Opaque resource ID belongs to another tenant

- **WHEN** an authorized user requests a conversation, job or document ID owned by another tenant
- **THEN** the operation returns `404` and reveals neither existence nor content.

#### Scenario: Vector retrieval runs for a tenant

- **WHEN** the assistant searches for relevant chunks
- **THEN** every candidate and citation belongs to the authorized tenant.

### Requirement: Agent tools cannot choose authorization context

Tenant-aware agent tools SHALL receive tenant and user context from the trusted
runtime and SHALL NOT expose them as freely overridable model arguments.

#### Scenario: Model supplies a different tenant identifier

- **WHEN** model output or a user prompt attempts to select another tenant
- **THEN** the tool ignores or rejects that value and retains the runtime-authorized tenant.

### Requirement: Isolation failures are observable without leaking data

Rejected cross-tenant operations SHALL emit correlation and outcome metadata
without logging tokens, protected payloads or the contents of foreign resources.

#### Scenario: Cross-tenant access is denied

- **WHEN** an isolation check rejects a request or job
- **THEN** logs identify the operation and denial class but contain no foreign business data.
