JUP: JUP-025

## Decisions

1. Use an additive presentation contract beside the existing evidence ID list.
   `evidence_id` preserves the corpus ID and `kind=corpus` matches JUP-024's
   vocabulary. Do not widen or copy FinOpsResponse 1.0. Metrics and recommendations
   in that separate processor response retain their existing evidence_ids and
   validators; this chat does not generate either.
2. Retrieve document identity, ownership, index and original text in the existing
   tenant-filtered query. Check ownership before calling the assistant. Resolve
   only IDs from that retrieval set, without a second unscoped lookup. Unknown,
   duplicate or foreign references produce the same sanitized 502 and no assistant
   message. The submitted user message remains, consistent with other send failures.
3. Cite exactly the first three excerpts used by the existing deterministic chat.
   The ordered IDs map to numbered passage links and source panels. Each stored
   citation contains the exact 140-character excerpt, title and source snapshot.
   Historical replies remain readable without a live lookup, even after reingestion.
4. Use the original document's first Markdown heading as title, or its source if
   no heading exists. Whitespace-normalized chunks are matched to original text;
   the nearest preceding Markdown heading supplies section only for unique matches.
   Missing or ambiguous locations remain null. Pages are supported in the contract
   but are not inferred from plain text. No claim of PDF pagination support.
5. The stable reference is `document:<id>/chunk:<index>`. It identifies the stored
   record but is not a public download URL. Render the historical excerpt locally;
   do not expose artifact URIs, signed URLs or create an unscoped evidence endpoint.
6. Treat persisted metadata as untrusted in React. Require a complete, unique,
   ordered mapping to the ID list, escape text, and create only local fragment
   links. Activating a citation opens the details and focuses its summary. Old
   messages with only IDs show evidence unavailable rather than fabricated titles.

## Verification and rollout

Exercise missing/duplicate/foreign IDs, unused fourth retrieval result, optional
locations, exact excerpts, persistence and conversation authorization. Keep
JUP-024 regression tests unchanged. Validate the real pgvector query independently
of PR #53, UI interaction, typecheck, build and OpenSpec. Backend can deploy before
frontend because old IDs remain. Frontend tolerates the older backend. Rollback
does not require a schema migration or metadata deletion.
