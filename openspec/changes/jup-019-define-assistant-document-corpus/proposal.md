## Why

Economicon needs a curated, versioned assistant corpus before building the rest of the RAG pipeline. Without an explicit corpus contract, JUP-020 chunking and embeddings, JUP-022 semantic retrieval, JUP-024 prompt guardrails, and JUP-025 source citations can drift or rely on inconsistent document inputs.

JUP-019 defines the MVP knowledge base for the Azure-focused simulated environment only. The change keeps the work repo-local and avoids depending on cloud decisions, real Azure access, LiteLLM/OpenRouter credentials, or UI changes.

## What Changes

- Add a repo-versioned assistant corpus for the MVP.
- Define the folder structure for FinOps documentation, business rules, glossary entries, and customer-safe product architecture/context notes.
- Define a document manifest contract with metadata needed by future indexing, retrieval, and citation work.
- Include tenant/scope metadata so the corpus can distinguish global, dataset-scoped, and future tenant-specific knowledge.
- Add usage documentation explaining how future JUPs should consume the corpus.
- Add basic validation for corpus integrity, including manifest structure, required metadata, existing paths, allowed categories, and non-empty documents.

### Scope Boundary

JUP-019 stops at defining and validating the repo-local corpus contract. It may create corpus documentation, a manifest, metadata rules, and validation for those files, but it must not implement runtime indexing, model calls, retrieval behavior, source rendering, cloud integration, or UI behavior.

### Out of Scope

- Connecting to real cloud infrastructure.
- Consuming real Azure APIs.
- Implementing real embeddings.
- Implementing semantic retrieval.
- Integrating LiteLLM or OpenRouter.
- Changing the frontend or assistant UI.
- Implementing final source-citation rendering.

## Capabilities

### New Capabilities

- `assistant-document-corpus`: Defines the curated MVP document corpus, manifest metadata contract, validation rules, and usage expectations for future assistant indexing and retrieval.

### Modified Capabilities

- None.

## Impact

- Product area: documentation, IA/RAG planning, corpus validation.
- Frontend: no direct impact.
- Backend: no direct endpoint or runtime behavior change in this HU.
- Processor: no direct worker, chunking, embedding, or pgvector behavior change in this HU.
- Infra/DB: no cloud, database, queue, pgvector, or migration change in this HU.
- AI/cost: prepares the local knowledge contract for later RAG work without invoking paid model or embedding providers.
- Multi-tenant: defines metadata for `scope`, `tenant_id`, and `dataset_id` so later retrieval work can preserve tenant isolation and support global or dataset-scoped documents.
- Dependencies: downstream JUP-020, JUP-022, JUP-024, and JUP-025 should consume or respect this corpus contract.
- Delivery notes: carril `standard`; pre-code approval and `pnpm hu:check:pre-code -- --change jup-019-define-assistant-document-corpus` are required before creating corpus files or validation scripts.

## Human Approval

- Change: jup-019-define-assistant-document-corpus
- Approval type: pre-code
- Decision: approved
- Approver: Paris Arcos Martin
- Date: 2026-08-12
- Carril: standard
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Main risks: scope creep into retrieval/model/cloud/UI work; tenant and dataset scope ambiguity; metadata insufficient for future citations
- Required changes before execution: none
- Notes: JUP-019 is limited to repo-local corpus definition, manifest metadata, documentation, and structural validation.
