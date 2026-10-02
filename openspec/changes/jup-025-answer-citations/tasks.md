## 1. Contract and implementation
- [x] 1.1 Reconcile JUP-025 with develop, JUP-024 and PR #53.
- [x] 1.2 Resolve used IDs to tenant-scoped document citations without a migration.
- [x] 1.3 Persist citations and render expandable evidence with local passage links.
- [x] 1.4 Preserve old ID metadata and distinguish unavailable historical evidence.

## 2. Verification and delivery
- [x] 2.1 Test missing, duplicate and foreign references and authorized reopening.
- [x] 2.2 Verify real pgvector retrieval and browser interaction.
- [x] 2.3 Run regression suites, typecheck, build and OpenSpec checks.
- [x] 2.4 Record evidence, publish a PR against develop and link Trello (PR #55).
- [x] 2.5 Record the assigned review and hand off remaining human approval and functional validation to Trello; do not count them as completed technical implementation.

## 3. Review corrections (2026-10-01)
- [x] 3.1 Handle empty/CRLF headings and preserve C# titles; API regression.
- [x] 3.2 Index each document once; fetch text once per document with a consistent tenant-scoped snapshot; performance and real database tests.
- [x] 3.3 Ignore fenced/indented code and initial YAML front matter as heading sources.
- [x] 3.4 Normalize display source consistently and register retry finding RF-025-001.

Pending human approval and functional validation remain in [JUP-025](https://trello.com/c/qzRy4RQc). This checklist does not authorize merge, claim approval, or close the card.


## 4. Validation corrections (2026-10-02)
- [x] 4.1 Cancel default fragment navigation and verify focus remains on the source summary.
- [x] 4.2 Cover excerpts longer than 140 characters and require exact agreement with the quoted passage.
- [x] 4.3 Use immutable contract links in evidence, architecture and continuity documentation so archiving does not break them.
- [x] 4.4 Separate the continuity convention into JUP-101 / draft PR #64 and preserve its summaries outside this functional PR.

Lucía approved the implementation and Víctor completed functional validation;
acceptance of these corrections remains tracked in Trello and PR #55.
