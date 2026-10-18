# verified-contextual-retrieval Specification

## Purpose
TBD - created by archiving change jup-127-contextual-hybrid-retrieval. Update Purpose after archive.
## Requirements
### Requirement: Identity of verified embedding spaces
The system SHALL identify a verified space by provider, resolved model, dimension, cosine distance, mapping fingerprint, tokenizer and preparation recipe, and SHALL reject inconsistent provider identity before cache or publication.

#### Scenario: Consistent accredited mapping
- **WHEN** a verified response matches the accredited small1536 model, mapping and deployment
- **THEN** the complete vector response is accepted for that exact space

#### Scenario: Alias or dimension alone is insufficient
- **WHEN** a response supplies only an unbound alias or a contradictory deployment
- **THEN** verification rejects it and does not retrospectively label legacy vectors

### Requirement: Deterministic contextual input
The system SHALL prepare contextual embedding text separately from content without an LLM, preserving JUP-125 content and metadata and recording context truncation warnings.

#### Scenario: Bounded D context
- **WHEN** a D chunk has accredited title and common section metadata
- **THEN** only deterministic context is prepended within128 context tokens and1024 input tokens/16384bytes, while content and positions remain unchanged

#### Scenario: Unknown structure
- **WHEN** headings are unknown or mixed
- **THEN** preparation does not invent a shared heading or include operational tenant metadata

### Requirement: Bounded batches and isolated cache
The system SHALL validate complete bounded batches and cache canonical vectors by tenant, space and exact UTF8 text hash, reusing only compatible entries.

#### Scenario: Complete batch
- **WHEN** all indices/model/dimensions/finite nonzero canonical vectors are valid
- **THEN** the batch is stored atomically as complete

#### Scenario: Concurrent cache and tenant boundary
- **WHEN** two consumers race or another tenant requests identical text
- **THEN** the canonical winner is returned without crossing tenant or space boundaries

### Requirement: Exact dense and hybrid retrieval
The system SHALL support exact cosine dense retrieval and FTS/GIN/RRF hybrid retrieval with explicit generation parameters and literal eligibility, without interpreting financial formulae.

#### Scenario: D ranking
- **WHEN** a D generation receives a question
- **THEN** dense uses inclusive0.6, FTS simple/GIN and each lane≤20; RRF60 produces pool≤20 with ID tie break and four chat seeds plus authorized neighbors

#### Scenario: Unsupported or malformed comparison
- **WHEN** a question contains unsupported comparison syntax or repeated numeric separators
- **THEN** another identifier does not rescue it lexically; supported EUR and percent punctuation retain full units

#### Scenario: Lane failure
- **WHEN** one hybrid lane fails
- **THEN** the operation does not silently claim successful degraded hybrid retrieval

#### Scenario: Positional neighbors and policy sections after base integration
- **WHEN** an authorized immediate neighbor or complete policy section is outside the dense threshold or initial candidate set
- **THEN** bounded expansion uses only the captured tenant, generation and embedding space, preserves policy ambiguity and source-position limits, keeps the final pool at most twenty and never rescues results from mutable legacy rows

#### Scenario: Expanded retrieval reaches the offline metrics consumer
- **WHEN** a captured neighbor or policy fragment has a distance beyond the semantic threshold
- **THEN** producer and metrics projection preserve its explicit positional or policy admission, real distance and paired generation/space identity (both unknown for legacy); the validator checks identity against the declared run without labelling it lexical or relaxing ordinary dense admission

#### Scenario: Literal normalization and lane-specific eligibility
- **WHEN** equivalent NFC/NFD text or case variants occur in a complete literal anchor
- **THEN** literal comparison uses NFC and casefold, preserving full token boundaries, signs and units
- **WHEN** an incidental query anchor such as y/o or a differently formatted date does not occur in a dense candidate
- **THEN** it does not remove that candidate within the inclusive cosine bound0.6; anchor eligibility gates only lexical rescue outside the dense set
- **WHEN** a comparison is unsupported or malformed
- **THEN** another identifier still cannot rescue it lexically; dense eligibility is independent of lexical rescue


### Requirement: Complete immutable generations and fencing
The system SHALL build coherent snapshots, publish and activate complete generations by CAS, resume captured state and fence obsolete build executions.

#### Scenario: Superseded executor
- **WHEN** a new execution resumes and completes or activates a generation
- **THEN** the obsolete executor cannot replace its manifest or change it to failed

#### Scenario: Stale or incomplete activation
- **WHEN** catalog, head version, permissions or membership completeness changed
- **THEN** activation is rejected without replacing the current complete head

### Requirement: Safe D activation and legacy compatibility
The operator SHALL activate D only over complete verified contextual indices while preserving compatible legacy retrieval and SHALL NOT mix or destroy incompatible spaces or vectors.

#### Scenario: Prepare before global flags
- **WHEN** a tenant is missing a compatible ready head
- **THEN** legacy stays selected until every served tenant is prepared; enabling verified mode does not invent a missing-head fallback

#### Scenario: Incompatible legacy dimension
- **WHEN** a legacy store has8 dimensions
- **THEN** the store remains recoverable and the operator prepares a separate authorized1536 store rather than changing its vector column

### Requirement: Concurrency cancellation and isolation
The system SHALL preserve concurrent ingestion, tenant isolation, deadlines and cancellation, and cache maintenance SHALL NOT invalidate a valid recovered vector.

#### Scenario: Busy query cache
- **WHEN** last_used_at is concurrently locked or has a serialization conflict after a verified read
- **THEN** the verified cached vector remains usable within deadline

#### Scenario: Concurrent insert
- **WHEN** cache insertion gets SQL40001 after one inference
- **THEN** only the bounded SQL transaction retries; provider inference is not retried for that conflict

### Requirement: Public chat contracts and excluded calculator
The system SHALL preserve public source, citation and history contracts and SHALL exclude the calculator/private projection additions introduced exclusively for E from this RAG delivery.

#### Scenario: Same document revision
- **WHEN** retrieval expands neighboring evidence
- **THEN** the authorized snapshot/revision remains fixed through citation and history

#### Scenario: Scope separation
- **WHEN** the RAG candidate is prepared
- **THEN** E-only Decimal/expression/private projection delta remains in external custody and is absent from product, with generator/prompts/validators otherwise preserved

### Requirement: Operational consumers and safe return
The delivery SHALL verify PostgreSQL/pgvector and affected Compose/CD/doctor consumers and document preparation, inspection, activation and safe return without new production services.

#### Scenario: Consumer configuration
- **WHEN** the operator renders D using complete accredited private configuration
- **THEN** backend and processor receive the required identity and recipe, doctor checks configuration without claiming SQL readiness, and CD does not implicitly activate D

#### Scenario: Return with retained catalog
- **WHEN** D must be disabled or a prior generation restored
- **THEN** OFF selects preserved compatible legacy; direct rollback requires a compatible catalog and rebuild requires explicit authorization and available budget

### Requirement: Preserved campaign provenance
The delivery SHALL preserve A-D, cancelled E and J5 evidence with distinct recipes, results, source hashes and costs, and SHALL distinguish historical findings from new candidate evidence.

#### Scenario: Historical D limits
- **WHEN** historical D results are reported
- **THEN** 68responses and64assisted acceptances out of68 retain their original provenance and coverage limits without a universal quality claim

#### Scenario: Free saved vector replay
- **WHEN** the candidate reuses stored D vectors and queries
- **THEN** it records provenance and local retrieval observations without claiming new generator outcomes or making provider calls

### Requirement: Independent final candidate evaluation
The delivery SHALL obtain separate technical review and functional validation of an identified final candidate, reusing only applicable evidence and rerunning affected checks.

#### Scenario: Independent controls
- **WHEN** the fixed candidate is dispatched
- **THEN** distinct evaluators receive original PM references before work and return unchanged candidate evidence and complete original reports

#### Scenario: Correction
- **WHEN** an in-scope defect is corrected
- **THEN** original adverse evidence remains preserved and the same evaluators reassess the affected behavior

### Requirement: Traceable delivery and publication boundary
The delivery SHALL maintain JUP-127 traceability through OpenSpec, continuity, evidence and the proposed PR to develop, without treating local agent evaluations as human reviews.

#### Scenario: Prepared PR
- **WHEN** technical work is ready
- **THEN** Paris receives results and the prepared PR message before publication, with human roles and pending actions stated accurately

#### Scenario: Publication permissions
- **WHEN** local reports are favorable
- **THEN** archive, push, remote CI and human reviews still follow their approved process and specific authorizations
