## 1. Reproduce and implement

- [x] 1.1 Confirm the backend envelope and both missing graph fields.
- [x] 1.2 Map the envelope explicitly inside IngestTask's safe failure path.
- [x] 1.3 Add backend/processor contract regression tests and retry checks.

## 2. Validate and document

- [x] 2.1 Run backend and processor tests, strict OpenSpec and JUP traceability.
- [x] 2.2 Reproduce the baseline failure and demonstrate ordinary HTTP ingestion
  reaching completed with persisted chunks/embeddings in an isolated stack.
- [x] 2.3 Record correlation, tenant/identity checks, settings and test limits.
- [x] 2.4 Link a PR and evidence from Trello, preserving assigned roles and
  residual corpus/provider work.
- [x] 2.5 Obtain assigned PR review and functional validation before closure.

Delivery: [PR #34](https://github.com/EconomiconFinOps/tfm-economicon/pull/34),
approved by Lucia Mateo (`lmatsan`) and merged into `develop` on 2026-09-13
as `cfc6668bceb60c38045f72976b9de8e8b8337555`.

Paris Arcos Martin's functional validation is confirmed by the user on
2026-09-14, together with the instruction to close JUP-020. This is the date
of confirmation, not an asserted execution date for Paris. See `review.md`.
The closure covers the delivered ingestion contract correction. Real embedding
providers, full/versioned corpus loading, per-chunk metadata and idempotent
reprocessing remain explicitly unimplemented follow-up work in the Trello
closure record; this checklist does not certify those capabilities.
