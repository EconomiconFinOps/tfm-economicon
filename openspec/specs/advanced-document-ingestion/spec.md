# advanced-document-ingestion Specification

## Purpose
Define the authenticated, tenant-isolated ingestion of supported document files using temporary private object storage, bounded local extraction and durable normalized content, while preserving the existing text-ingestion and retrieval contracts.
## Requirements
### Requirement: Extract supported document formats locally
The system SHALL extract MD, UTF-8 TXT, DOCX, legacy DOC and digital, scanned or
mixed PDF locally into versioned text/blocks/origin/metadata with available
positions, method and warnings. Conversion/OCR SHALL be bounded and isolated,
without inherited secrets, Internet access or arbitrary host files.

#### Scenario: Supported document is processed
- **WHEN** an authorized supported file is within configured limits
- **THEN** normalization preserves extracted text and available structure
- **AND** scanned or eligible mixed PDF pages use local OCR without promising perfect layout reconstruction.

#### Scenario: Extraction exceeds its boundary
- **WHEN** conversion/OCR exceeds limits or its sandbox is unavailable
- **THEN** extraction fails safely without unrestricted fallback or completed partial output.

### Requirement: Bound uploads and reserve by user
The system SHALL admit one file per selection/send, at most 20,000,000 actual
bytes, and one active transfer per authenticated user across sessions/tenants,
while allowing different users to transfer to the same tenant concurrently.

#### Scenario: User already has an active transfer
- **WHEN** the same user requests another transfer from another session
- **THEN** admission rejects the second reservation without replacing the first.

#### Scenario: Boundary and multi-user behavior
- **WHEN** distinct authorized users upload to the same tenant
- **THEN** their reservations are independent
- **AND** exactly 20,000,000 bytes is eligible while a larger or empty file is rejected.

### Requirement: Authenticate admission and verify actual content
Backend and worker SHALL enforce persisted identity and tenant membership.
The backend SHALL verify actual size, SHA256 and allowed format/content before
creating a processable job; malformed containers SHALL fail controlled admission.

#### Scenario: Foreign or invalid upload
- **WHEN** an upload is foreign or its verified content is invalid
- **THEN** it is not exposed or processed as an authorized document
- **AND** unsupported or corrupt content is rejected without a valid job or leaked credentials.

#### Scenario: Corrupt compressed DOCX
- **WHEN** confirmation encounters corrupt DEFLATE, BZip2 or LZMA container data
- **THEN** it returns the controlled 422 format error, not an uncaught decompression error
- **AND** no job is created/published; existing cancel/expiry behavior remains available.

### Requirement: Keep private storage in the general stack
MinIO SHALL run separately in general Compose with a dedicated private bucket,
bounded staging PUT authorization and explicit browser origins. Administrator
credentials SHALL stay outside frontend/backend/processor.

#### Scenario: Browser uploads an authorized original
- **WHEN** the backend issues a temporary PUT for a server-selected staging key
- **THEN** transfer uses no application Bearer/cookies/tenant header
- **AND** anonymous clients or foreign browser origins do not gain bucket access.

### Requirement: Preserve asynchronous identity and recovery
The system SHALL expose transfer/job states, distinguish queued from completed,
keep repeated confirmation idempotent and deduplicate content within a tenant.
Queue/retries SHALL use durable references/checkpoints under the existing policy,
without re-extracting a published normalized checkpoint.

#### Scenario: Confirmation or delivery is repeated
- **WHEN** confirmation, uncertain publication or a worker delivery is retried
- **THEN** identity and durable recovery prevent accidental duplicate accepted work
- **AND** completion publication remains fenced by the current worker reservation.

#### Scenario: Failed attempt remains recoverable
- **WHEN** a job is failed with retry_pending true
- **THEN** UI and smoke wait for recovery or a terminal result
- **AND** a transient polling notice disappears after successful status recovery.

### Requirement: Clean originals only after durable success
The system SHALL preserve originals needed by queued/running/recoverable work.
Cleanup SHALL follow durable success or existing terminal/cancelled/expired
retention conditions and SHALL recover failed deletion without undoing completion
or deleting the normalized document.

#### Scenario: Cleanup initially fails
- **WHEN** checkpoint, vectors and completed are durable but deletion fails
- **THEN** maintenance retries deletion without reprocessing or revoking completed
- **AND** the normalized document remains available after original removal.

#### Scenario: Staging authorization is still live
- **WHEN** a client can recreate staging before PUT expiry
- **THEN** cleanup continues until authorization expires and deletion is confirmed
- **AND** staging expiration does not delete confirmed active originals.

### Requirement: Preserve the existing RAG and manual text contract
The system SHALL deliver normalized text to existing chunking/embeddings without
changing models, dimensions, retrieval/citations or tenant isolation. Manual
text input SHALL remain supported.

#### Scenario: Retrieval follows cleanup or restart
- **WHEN** the original is removed or services restart after persistence
- **THEN** authorized documents and stored vectors remain recoverable
- **AND** retrieval/citations retain their tenant boundary.

### Requirement: Reuse ingestion interface conventions
File input SHALL preserve style tokens, light/dark themes and responsive layout,
present transfer/processing/errors, omit a forced-reprocessing checkbox and
coexist with the manual text field.

#### Scenario: Multiple selection or pending work
- **WHEN** the user drops multiple files or observes an accepted queued file
- **THEN** selection requests a single file and queued is not displayed as completed
- **AND** retry/cancel controls follow existing transfer/terminal-state semantics.

### Requirement: Keep schema and deployment preparation compatible
The system SHALL use additive migration/configuration and documented local
operation. CD SHALL fill only missing document secrets without rotation and
derive distinct S3 ports/endpoints/origins per slot.

#### Scenario: New and legacy CD roots prepare both slots
- **WHEN** init/prepare handles a new or legacy root for slots A and B
- **THEN** current Compose has required settings and previous credentials/HMAC remain intact
- **AND** slots have distinct MinIO ports, matching public endpoints/CORS and separate volumes.

### Requirement: Keep diagnostics and fixtures aligned with Compose
local:doctor SHALL retain detection of missing/empty configuration, conflicting
or occupied ports and secret-safe messages. Its fixtures SHALL represent current
MinIO/S3/CORS requirements without weakening negative checks.

#### Scenario: Configured origins and absent credentials
- **WHEN** the example has configured CORS origins but lacks required secrets
- **THEN** diagnostics name missing values, not already configured origins
- **AND** absent, empty or environment-emptied document variables remain errors.

#### Scenario: Invalid or occupied S3 port
- **WHEN** MINIO_HOST_PORT is invalid, duplicated or occupied
- **THEN** diagnostics reject it by variable/port without exposing secrets.
