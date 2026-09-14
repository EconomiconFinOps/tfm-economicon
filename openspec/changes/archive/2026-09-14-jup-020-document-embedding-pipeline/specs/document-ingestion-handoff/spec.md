## ADDED Requirements

### Requirement: Adapt the backend ingestion envelope

The processor SHALL adapt a backend ingestion job envelope to graph input
with `job_id` from envelope `id`, identity and source fields from the envelope,
and text and metadata from its nested `payload`.

#### Scenario: Ordinary API job completes

- **WHEN** a valid job produced by `Database.create_job` reaches `IngestTask`
- **THEN** the graph receives the original document text and metadata
- **AND** the job reaches completed with chunks and embeddings associated
  with its envelope job identifier and tenant.

#### Scenario: Payload cannot replace envelope identity

- **WHEN** nested payload or metadata contains identity or graph control fields
- **THEN** only the documented document fields are copied into graph input
- **AND** the envelope's job identifier and tenant remain authoritative.

#### Scenario: Optional document fields are omitted

- **WHEN** a valid envelope contains text but omits metadata or artifact URI
- **THEN** graph metadata is empty and the artifact URI is null.

### Requirement: Preserve failure handling and request correlation

The adapter SHALL leave the queue message unchanged and preserve existing
job failure handling and worker request correlation.

#### Scenario: Processing succeeds

- **WHEN** the adapted graph finishes successfully
- **THEN** the task records completion and the worker acknowledges the message
- **AND** processing logs keep the HTTP request identifier.

#### Scenario: Invalid envelope or downstream processing failure

- **WHEN** adaptation or graph execution raises an exception
- **THEN** the task records the safe `ingestion_failed` status reason
- **AND** the worker retains the exception cause for redacted diagnostics
- **AND** retry processing retains the original envelope and request identifier.
