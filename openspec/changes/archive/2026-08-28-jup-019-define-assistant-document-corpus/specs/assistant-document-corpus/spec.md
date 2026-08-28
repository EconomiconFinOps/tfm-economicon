## ADDED Requirements

### Requirement: Corpus contains the required MVP knowledge categories

The assistant document corpus SHALL provide repo-versioned source documents for FinOps documentation, business rules, glossary entries, and customer-safe product architecture/context knowledge.

#### Scenario: Contributor reviews corpus coverage

- **WHEN** a contributor inspects the corpus manifest
- **THEN** it references at least one document in each category: `finops`, `business-rules`, `glossary`, and `product-architecture`.

### Requirement: Manifest identifies every indexable document

The assistant document corpus SHALL use a manifest as the source of truth for documents intended for future assistant indexing.

#### Scenario: Manifest entry contains required metadata

- **WHEN** a manifest entry describes an indexable document
- **THEN** it includes `id`, `title`, `path`, `category`, `tags`, `language`, `version`, `scope`, `tenant_id`, `dataset_id`, `source_type`, and `updated_at`.

#### Scenario: Manifest paths are repository-local

- **WHEN** a manifest entry references a document path
- **THEN** the path resolves under `docs/assistant-corpus/`.

### Requirement: Scope metadata supports global, dataset, and tenant documents

The assistant document corpus SHALL distinguish global documents, dataset-scoped documents, and future tenant-specific documents through explicit metadata.

#### Scenario: Global document metadata is explicit

- **WHEN** a manifest entry uses `scope: global`
- **THEN** `tenant_id` is empty and the document is treated as shared corpus knowledge.

#### Scenario: Dataset document metadata is explicit

- **WHEN** a manifest entry uses `scope: dataset`
- **THEN** `dataset_id` identifies the dataset or simulated contract context the document belongs to.

#### Scenario: Tenant document metadata is explicit

- **WHEN** a manifest entry uses `scope: tenant`
- **THEN** `tenant_id` identifies the tenant context the document belongs to.

### Requirement: Corpus validation detects structural drift

The assistant document corpus SHALL provide a validation path that fails when required metadata or referenced document content is invalid.

#### Scenario: Duplicate document ID is rejected

- **WHEN** two manifest entries use the same `id`
- **THEN** corpus validation fails.

#### Scenario: Missing document path is rejected

- **WHEN** a manifest entry references a path that does not exist
- **THEN** corpus validation fails.

#### Scenario: Empty document is rejected

- **WHEN** a manifest entry references an empty document
- **THEN** corpus validation fails.

### Requirement: Corpus documentation defines downstream usage

The assistant document corpus SHALL document how future RAG stories should consume the manifest and documents.

#### Scenario: Downstream implementer reads corpus documentation

- **WHEN** a contributor works on chunking, embeddings, retrieval, prompts, or citations
- **THEN** the corpus documentation identifies the manifest as the input contract and states that real cloud access, real embeddings, semantic retrieval, LiteLLM/OpenRouter integration, UI changes, and final citation rendering are outside JUP-019.

### Requirement: Corpus scope remains repo-local and non-runtime

JUP-019 SHALL be deliverable without changing runtime backend, processor, frontend, cloud, database, queue, pgvector, model-provider, or UI behavior.

#### Scenario: Contributor reviews implementation scope

- **WHEN** a contributor reviews the JUP-019 implementation
- **THEN** the changed files are limited to OpenSpec artifacts, corpus documentation, manifest metadata, and corpus validation assets.
