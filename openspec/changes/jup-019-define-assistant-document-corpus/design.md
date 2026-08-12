## Context

JUP-019 starts the IA/RAG block by defining what knowledge the assistant is allowed to index for the MVP. The Trello scope constrains the MVP to Azure-oriented simulated data, with no real cloud integration required for this story.

The repository already contains a minimal backend/processor architecture for ingestion and retrieval, but this change does not alter that runtime path. It defines the document inputs and metadata contract that later stories can consume when implementing chunking, embeddings, retrieval, prompts, and citations.

Stakeholders:

- Paris Arcos Martin: JUP-019 lead.
- Victor Mendez: pairing/coauthoring.
- Alejandro Aguado: PR review.
- Lucia Mateo: validation, tests, and documentation.

## Goals / Non-Goals

**Goals:**

- Define a repo-versioned assistant corpus for the MVP.
- Group documents into the four JUP-019 categories: FinOps documentation, business rules, glossary, and customer-safe product architecture/context.
- Define a manifest contract with metadata required for indexing, filtering, and future citations.
- Include scope metadata for global, dataset-scoped, and future tenant-specific documents.
- Add a lightweight validation path that makes the corpus objectively checkable.
- Document how downstream JUPs should consume the corpus.

**Non-Goals:**

- Connect to real cloud infrastructure.
- Consume real Azure APIs.
- Implement real embeddings or choose embedding providers.
- Implement semantic retrieval or modify pgvector queries.
- Integrate LiteLLM, OpenRouter, or model gateways.
- Change frontend screens or assistant UI behavior.
- Render final citations in assistant answers.

Scope guardrail: JUP-019 may only change OpenSpec artifacts before pre-code approval. After approval, implementation remains limited to repo-local corpus files, manifest metadata, documentation, and validation. Backend, processor, frontend, infrastructure, cloud provider, and model-provider changes remain out of scope.

## Decisions

### Decision: Store the corpus under `docs/assistant-corpus/`

The corpus SHALL live in a dedicated documentation subtree:

```text
docs/assistant-corpus/
|-- README.md
|-- manifest.yaml
|-- finops/
|-- business-rules/
|-- glossary/
`-- product-architecture/
```

Rationale: keeping the corpus in Git makes the MVP reproducible, reviewable, and independent of cloud storage decisions. It also keeps JUP-019 repo-local.

Alternative considered: reuse scattered existing docs directly. That was rejected because downstream indexing would need ad hoc discovery rules and would make future citation metadata inconsistent.

### Decision: Use `manifest.yaml` as the corpus source of truth

The manifest SHALL enumerate every document intended for indexing. Each entry SHALL include:

- `id`
- `title`
- `path`
- `category`
- `tags`
- `language`
- `version`
- `scope`
- `tenant_id`
- `dataset_id`
- `source_type`
- `updated_at`

Allowed categories SHALL be `finops`, `business-rules`, `glossary`, and `product-architecture`.

Rationale: JUP-020, JUP-022, and JUP-025 need a stable list of documents and metadata. A manifest avoids implicit filesystem behavior and prepares future citations without implementing them in this HU.

Alternative considered: infer metadata from Markdown front matter only. That remains possible later, but the MVP needs one simple, central contract that can be validated without parsing every document format.

### Decision: Model scope explicitly, but start with global and dataset-scoped documents

The manifest SHALL support:

- `scope: global` for shared FinOps or product knowledge.
- `scope: dataset` for knowledge tied to the MVP Azure sample dataset or simulated Azure contract.
- `scope: tenant` for future tenant-specific knowledge.

For JUP-019, tenant-specific documents are not required because the MVP has no real tenant. `tenant_id` remains part of the contract so later tenant isolation work does not need to redesign the corpus metadata.

Rationale: the current backend retrieval path is tenant-aware, while project scope says the MVP has no real tenant. Capturing both constraints now avoids a later mismatch between global knowledge and tenant-filtered retrieval.

Alternative considered: make `tenant_id` mandatory on all documents. That was rejected because glossary, FinOps, and customer-safe product context documents are shared knowledge, not tenant-owned records.

### Decision: Add validation before indexing exists

The validation SHALL check at least:

- manifest exists and parses;
- document IDs are unique;
- required metadata fields exist;
- categories and scopes use allowed values;
- referenced document paths exist under `docs/assistant-corpus/`;
- referenced documents are non-empty.

Rationale: the Trello DoD requires a verifiable result. Validation gives JUP-019 an objective pass/fail outcome without needing real embeddings or retrieval.

Alternative considered: manual review only. That was rejected because corpus drift would be easy and downstream JUPs would inherit hidden errors.

## Risks / Trade-offs

- Scope creep into retrieval implementation -> Keep JUP-019 limited to corpus files, metadata, documentation, and validation.
- Metadata too weak for future citations -> Include `id`, `title`, `path`, `category`, `tags`, `version`, and scope fields from the start.
- Tenant/global ambiguity -> Require explicit `scope`, `tenant_id`, and `dataset_id` fields and validate their consistency.
- Corpus becomes stale as Azure dataset work evolves -> Mark dataset-dependent documents with `dataset_id` so later Azure-data JUPs can update them deliberately.
- Manifest contract becomes a durable RAG architecture decision -> Treat this design as sufficient for JUP-019; reassess ADR need if a later JUP turns the manifest into a runtime service contract.

## Migration Plan

1. Complete and approve OpenSpec planning artifacts for JUP-019.
2. Run the pre-code HU gate before creating corpus files or validation scripts.
3. Add the corpus directory, manifest, seed documents, usage documentation, and validation.
4. Run focused validation plus repository checks accepted for the selected carril.
5. Record review, findings, and post-review approval before archive.

Rollback is file-based: revert the JUP-019 corpus files, validation script, and related package script if the corpus contract is rejected before archive.

## Open Questions

- Which final `dataset_id` should be used if JUP-072 names the Azure sample dataset differently?
- Should later tenant-aware retrieval search both tenant-specific and global corpus documents in the same query, or should global documents be replicated per tenant? This belongs to JUP-022 unless it becomes necessary during JUP-019 validation.
