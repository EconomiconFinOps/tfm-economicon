# Assistant Corpus

This directory contains the repo-versioned document corpus for the Economicon assistant MVP.

JUP-019 defines the corpus contract only. It does not implement runtime indexing, embeddings, semantic retrieval, LiteLLM/OpenRouter integration, real Azure access, cloud infrastructure, UI changes, or final citation rendering.

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

`manifest.yaml` is the source of truth for documents intended for future indexing. Downstream JUPs must use it instead of scanning this directory implicitly.

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

## Scope

The MVP uses repo-local corpus documents and simulated Azure context. Real cloud access, real Azure API consumption, embeddings, retrieval, model gateway integration, and UI behavior belong to downstream JUPs.
