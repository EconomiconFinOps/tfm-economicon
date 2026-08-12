## 1. Corpus Structure

- [x] 1.1 Create `docs/assistant-corpus/` with `README.md`, `manifest.yaml`, and category folders for `finops`, `business-rules`, `glossary`, and `product-architecture`.
- [x] 1.2 Add at least one MVP document for each required corpus category.
- [x] 1.3 Keep corpus content limited to the Azure-focused simulated MVP and repo-local product knowledge.

## 2. Manifest Contract

- [x] 2.1 Populate `manifest.yaml` with one entry for every indexable corpus document.
- [x] 2.2 Include required metadata for each entry: `id`, `title`, `path`, `category`, `tags`, `language`, `version`, `scope`, `tenant_id`, `dataset_id`, `source_type`, and `updated_at`.
- [x] 2.3 Enforce explicit scope semantics for `global`, `dataset`, and future `tenant` documents.

## 3. Corpus Validation

- [x] 3.1 Add a repo-local validation command for the assistant corpus manifest and referenced documents.
- [x] 3.2 Validate unique IDs, allowed categories, allowed scopes, required metadata, repository-local paths, existing files, and non-empty documents.
- [x] 3.3 Add focused tests or fixtures that prove validation fails for representative invalid corpus states.

## 4. Documentation And Handoff

- [x] 4.1 Document how downstream JUP-020, JUP-022, JUP-024, and JUP-025 should consume the corpus contract.
- [x] 4.2 Document JUP-019 exclusions: real cloud access, real Azure consumption, embeddings, semantic retrieval, LiteLLM/OpenRouter integration, UI changes, and final citation rendering.
- [x] 4.3 Record any dataset naming assumptions so JUP-072/JUP-073 can update them deliberately if needed.

## 5. Verification

- [ ] 5.1 Run `pnpm openspec:validate` and the JUP-019 corpus validation command.
- [ ] 5.2 Run focused tests/checks for changed files and document exact commands and results in `review.md`.
- [ ] 5.3 Confirm ADR applicability in review, recording `ADR not applicable` unless the manifest becomes a durable runtime RAG contract during implementation.
