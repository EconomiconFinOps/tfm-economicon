JUP: JUP-025
Trello: https://trello.com/c/qzRy4RQc

## Why

The current assistant stores opaque chunk IDs and cites all retrieved records,
although its answer quotes only three. Operators cannot inspect evidence when
reopening a conversation. The August description was reconciled against develop
`2efef1a` and the current Trello card on 2026-09-30.

## What Changes

- Keep the existing ordered `metadata.citations` IDs and add resolved
  `metadata.source_citations`, with document, title, source, stable reference,
  optional section/page and the exact excerpt used by the answer.
- Resolve references only from the active tenant's retrieved records; reject
  missing, duplicate and foreign references before persisting an assistant reply.
- Link numbered answer excerpts to expandable evidence, also after reopening.
- Preserve the JUP-024 FinOpsResponse 1.0 schema and evidence identities.

## Capabilities

### New Capabilities
- `answer-citations`: verifiable document citations for assistant conversations.

## Impact

Backend retrieval, assistant response metadata and conversation UI. No database
migration, dependency change or PR #53 dependency: that PR concerns pgvector
dimensions, deployment and recovery, not these existing query tables.

The current chat returns retrieved excerpts, not the processor's structured
FinOpsResponse. This change does not connect that separate generation pipeline
or invent cost-query evidence. JUP-024 remains its unchanged validation boundary.
The current ingestion has no page metadata; page stays null. Section is recovered
from original Markdown only when its normalized chunk can be uniquely located.
