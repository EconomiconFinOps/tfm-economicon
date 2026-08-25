# Assistant Corpus

This directory contains the repo-versioned document corpus for the Economicon assistant MVP.

JUP-019 defines the corpus contract only. This README is operational handoff documentation for contributors; it is not an indexable corpus document unless it is explicitly added to `manifest.yaml`.

## Structure

```text
docs/assistant-corpus/
|-- README.md
|-- manifest.yaml
|-- finops/
|-- business-rules/
|-- glossary/
`-- product-architecture/
```

## Categories

- `finops`: FinOps guidance for the Azure-focused simulated MVP.
- `business-rules`: Economicon MVP rules, thresholds, KPIs, and interpretation rules.
- `glossary`: Short definitions for FinOps, Azure, data, and product terms.
- `product-architecture`: Indexable product architecture context for the assistant.

## Manifest

`manifest.yaml` is the source of truth for documents intended for future indexing. Downstream work must use it instead of scanning this directory implicitly.

Every indexable document entry must include:

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

Run the structural validation before relying on the corpus:

```bash
pnpm assistant-corpus:validate
```

## Scope

The MVP uses repo-local corpus documents and simulated Azure context.

Scope metadata must be interpreted as follows:

- `scope: global`: shared corpus knowledge. `tenant_id` and `dataset_id` must be `null`.
- `scope: dataset`: knowledge tied to the MVP simulated dataset or contract. `tenant_id` must be `null` and `dataset_id` must be a non-empty string.
- `scope: tenant`: reserved for future tenant-specific knowledge. JUP-019 does not create tenant-specific corpus documents.

The current provisional dataset ID is `economicon-mvp-azure-simulated`. At the end of JUP-019 only `business-rules.economicon-mvp` is dataset-scoped. If JUP-072 or JUP-073 names the Azure sample dataset differently, update the manifest deliberately in that later change.

## Downstream Handoff

JUP-020, chunking and embeddings:

- Read only documents declared in `manifest.yaml`.
- Preserve document metadata on each chunk, including `id`, `title`, `path`, `category`, `version`, `scope`, `tenant_id`, `dataset_id`, and `updated_at`.
- Do not infer indexable documents from directory scans.

JUP-022, semantic retrieval:

- Filter or rank context using `scope`, `tenant_id`, and `dataset_id`.
- Decide the final strategy for combining global, dataset-scoped, and future tenant-specific documents.
- Keep tenant-specific behavior out of JUP-019.

JUP-024, prompts and guardrails:

- Treat the corpus as allowed product and FinOps context.
- Do not let prompts claim capabilities that are absent from the corpus or outside the MVP.
- Keep model-provider and runtime prompt integration outside JUP-019.

JUP-025, citations:

- Use manifest metadata as the citation base.
- At minimum, future citations should be able to reference `id`, `title`, `path`, `version`, and `updated_at`.
- Final rendering of citations is not implemented in JUP-019.

## JUP-019 Exclusions

JUP-019 does not implement:

- real cloud access;
- real Azure API consumption;
- real embeddings;
- semantic retrieval;
- LiteLLM/OpenRouter integration;
- frontend or assistant UI changes;
- final citation rendering;
- backend, processor, database, queue, pgvector, model-provider, or deployment behavior changes.
