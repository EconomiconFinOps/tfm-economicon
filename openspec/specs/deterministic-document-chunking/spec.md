# deterministic-document-chunking Specification

## Purpose
TBD - created by archiving change jup-125-deterministic-document-chunking. Update Purpose after archive.
## Requirements
### Requirement: Consume durable normalized documents without re-extraction
The system SHALL chunk the versioned normalized text and available blocks from
ingestion for MD, TXT, DOCX, DOC and digital, scanned or mixed PDF. It SHALL use
explicit deterministic fallback for unavailable structure without inventing
hierarchy, positions or a need to recover the deleted original.

#### Scenario: Original is no longer available
- **WHEN** a valid normalized checkpoint or manual-text document is supplied
- **THEN** chunking consumes that text and its available annotations without extraction/OCR
- **AND** unknown structure and positions remain explicit.

### Requirement: Enforce effective token budgets and bounded overlap
The system SHALL use a pinned versioned tokenizer with configurable target of 600,
maximum of 800 and overlap of 0.1 of the target by default. Effective overlap SHALL follow
natural boundaries and be recorded; maximum includes all repeated content.

#### Scenario: Repetition competes with primary content
- **WHEN** a chunk needs overlap or table/header context
- **THEN** the complete effective content remains within the configured maximum
- **AND** independent sections have no cross-section overlap.

### Requirement: Preserve structural units before fallback splitting
The system SHALL keep headings/subsections and small tables together when they
fit the maximum; split larger tables by rows with declared context/provenance,
lists with available parent-child relationships and code by lines before token
fallback. Excessive units SHALL retain all characters without broken Unicode.

#### Scenario: Fitting subsection belongs to a large parent
- **WHEN** an H3-H6 subsection fits the maximum of 800 but its parent exceeds the budget
- **THEN** recursive partitioning preserves that subsection before block fallback
- **AND** emitted slices retain their actual hierarchy and text.

#### Scenario: Single row or code line exceeds maximum
- **WHEN** a structural unit cannot fit whole
- **THEN** bounded fragments preserve source order, unit identity and all text
- **AND** repeated context is explicit and included in the maximum.

### Requirement: Retain related conditions and exceptions structurally
The system SHALL retain conditions, thresholds and exceptions together when
they form a structural unit within the maximum, without hardcoded business
phrases, a semantic model or an embedding call to decide the cut.

#### Scenario: Strict business threshold rule fits
- **WHEN** relative_delta >20% AND absolute_delta >100 EUR/day and the strict-limit clarification form a fitting structural unit
- **THEN** rule and clarification remain together
- **AND** an unrelated rule with the same structural shape follows the same algorithm.

### Requirement: Preserve stable chunk identity and honest provenance
Chunks SHALL retain document_id, chunk_id, chunk_index, content/content_type,
token_count and chunk_hash, plus available hierarchy and source_spans pointing
to actual blocks/pages/lines/ranges under an explicit coordinate contract.

#### Scenario: Parser line domains differ
- **WHEN** Markdown contains Unicode separators inside CommonMark CR/LF/CRLF lines
- **THEN** headings, section paths and spans refer to their actual canonical text
- **AND** an old misaligned checkpoint block produces a warning and unknown block reference rather than false attribution.

### Requirement: Record persisted fragments and deliberate repetition
Chunk metadata SHALL record split reason, fragment group/order/count, overlap
and repeated context, algorithm/configuration/tokenizer versions. Document-level
metadata SHALL remain associated with the parent without indiscriminate copying.
Fragment indices/count SHALL describe records actually persisted after omissions.

#### Scenario: Interior whitespace yields omitted pieces
- **WHEN** splitting a valid document omits whitespace-only groups from embeddings
- **THEN** retained fragments have consecutive indices and their actual count
- **AND** omitted whitespace remains exactly recoverable from metadata, without empty embedding chunks or relaxed completeness checks.

### Requirement: Make boundaries and derived metadata reproducible
The same normalized document, document identity, configuration and versions
SHALL produce identical boundaries, content, order, derived metadata, hashes and
IDs. LLMs, embeddings, randomness and operational timestamps SHALL NOT decide cuts.

#### Scenario: Repeat the same input
- **WHEN** chunking runs again with identical contractual inputs
- **THEN** the complete derived result is identical apart from explicitly separate operational measurements.

### Requirement: Publish compatible generations atomically
The pipeline SHALL persist enriched chunks and metadata in PostgreSQL/pgvector
with additive compatibility, idempotence and atomic replacement. A failed new
generation SHALL leave the previous one queryable; stale operations SHALL NOT
overwrite a newer publication or mix active generations.

#### Scenario: Replacement fails after deletion inside transaction
- **WHEN** provider or SQL publication fails before successful commit
- **THEN** the previous parent/chunks/vectors remain coherent and queryable.

#### Scenario: Late result attempts publication
- **WHEN** the expected publication differs from the active publication
- **THEN** the stale operation is rejected without replacing the current generation.

### Requirement: Retrieve legacy and new data without mandatory reindexing
The system SHALL retrieve old documents/chunks/vectors together with new chunks,
with compatible citations and tenant isolation. Structural reprocessing SHALL
require an explicit authorized owner/tenant request and a valid normalized
checkpoint; no automatic mass reindexing or re-extraction is introduced.

#### Scenario: Legacy and structured documents coexist
- **WHEN** current retrieval queries pre-migration data and newly ingested data
- **THEN** SQL returns the correct document/content/reference under the caller tenant
- **AND** old IDs/text/metadata/vectors remain unchanged without reprocessing.

#### Scenario: Reprocess lacks checkpoint or authority
- **WHEN** completed data has no valid checkpoint or the caller lacks owner/tenant authority
- **THEN** reprocessing fails explicitly and existing lookup remains available.

### Requirement: Demonstrate all formats with identified real extraction
Validation SHALL use normalized documents originating from identified real
extraction of supported formats, checking coverage, structure, limits and
provenance while reusing valid frozen extraction/OCR instead of repeating it
routinely. A manually labelled JSON SHALL NOT establish extraction of a format.

#### Scenario: Format fixture is used for acceptance
- **WHEN** a frozen normalized fixture is passed to the actual chunker
- **THEN** its source and extracted identity are demonstrable
- **AND** available table/list/code and location data are contrasted, without inventing missing structure.

### Requirement: Reconstruct exact normalized text from chunks alone
The system SHALL reconstruct normalized text using only chunks and their
metadata, excluding overlap/repeated headers and preserving Unicode and omitted
whitespace. It SHALL fail clearly for incomplete or incoherent sets, without
using the parent/oracle to fill gaps. Binary bytes or original layout are not required.

#### Scenario: Complete shuffled set is reconstructed
- **WHEN** all coherent chunks are supplied out of order
- **THEN** their recorded order/ranges/repetition and omission metadata recover the exact normalized text
- **AND** the frozen original is used only to compare the finished reconstruction.

#### Scenario: Valid long interior separator is generated
- **WHEN** TXT contains Before., 200000 spaces and After. within document limits
- **THEN** its generated chunk set reconstructs exactly rather than failing its own fragment completeness validation.

#### Scenario: Record is missing or duplicated
- **WHEN** a chunk or persisted fragment is absent, duplicated or incoherent
- **THEN** reconstruction rejects the set explicitly, including when intentional whitespace omissions are present.

### Requirement: Contrast retrieved text and citations with their source
Recovered chunks/citations SHALL lead to the actual declared document and
available block/section/page/line/range, with textual correspondence checked for
Unicode, multiple sections/pages, overlap and table/list fragments. Unknown
locations SHALL remain explicit and legacy citations SHALL remain compatible.

#### Scenario: Chunk spans several locations
- **WHEN** retrieval returns a chunk with multiple source locations
- **THEN** spans identify their real substrings and available origins
- **AND** no false single page, section or hierarchy is manufactured.

### Requirement: Validate integrity before persistence
The system SHALL validate size, coverage, order, references, hierarchy and
unexpected duplication before publishing new chunks, distinguishing explicit
warnings for unavailable structure from corruption and deliberate repetition.

#### Scenario: Metadata or content is corrupt
- **WHEN** IDs, hashes, ranges, repetitions or fragment completeness are incoherent
- **THEN** validation fails before publishing the new generation
- **AND** declared unknown structure alone is not misreported as verified provenance.

### Requirement: Compare against a frozen real-vector baseline honestly
Evaluation SHALL compare old/new with frozen corpus/questions/reference evidence
and the same embedding model, measuring integrity, structure, traceability,
sizes, fragmentation, latency and real-vector retrieval. It SHALL NOT claim
Recall improvement without measurement or generalize a small exploratory sample.

#### Scenario: Existing cache still represents the candidate
- **WHEN** complete comparison inputs/chunks/metadata remain equivalent
- **THEN** existing real vectors may be reused without paying for identical inference
- **AND** reported metrics retain their sample, configuration and limitations.

### Requirement: Preserve retrieval contracts and offline preparation
The system SHALL preserve provider/model/dimensions/distance, ranking and prompts.
The pinned tokenizer resource SHALL be downloaded/verified in preparation/build,
kept outside Git and available offline at runtime. Configuration, contracts,
compatibility and limits SHALL have proportionate tests and independent review
and validation of the final candidate.

#### Scenario: Runtime tokenizer is absent or altered
- **WHEN** the external pinned tokenizer resource is missing, linked or has a wrong hash
- **THEN** loading fails closed without runtime download or silent equivalent-tokenizer fallback.

#### Scenario: Documentation formalizes an existing implementation
- **WHEN** JUP-125 is recorded after experimental implementation and corrections
- **THEN** documentation identifies its retrospective nature, evidence/base and actual human roles
- **AND** local agent PASS does not establish human participation, CI success, archive or publication authorization.
