JUP: JUP-028
Trello: https://trello.com/c/RG9O2Ltx

## Why

FinOps users need to identify observed costs whose ownership or classification
metadata is incomplete, without counting the same cost once for every missing
tag. The card requests detection of costs without an owner or classification.
There is no integrated allocation-rule registry or organizational catalog that
can establish final financial assignment from the current billing records.

This increment therefore detects candidates for investigation using the five
minimum tags named by JUP-015 and the versioned predicate implemented in
JUP-017. A candidate is not a finding that the cost is financially unallocated;
complete metadata is not proof that the cost is financially allocated.

## What Changes

- Add authenticated `GET /billing/unallocated-cost` with an explicit UTC date
  interval for the active tenant.
- Return `detection_basis=observed_required_tags`,
  `allocation_status=not_evaluated`, policy version and required canonical tags.
- Partition observed cost records by their exact set of missing or invalid
  tags. Return disjoint candidate groups, their reasons and record counts.
- Report positive costs, signed negative adjustments and net reconciliation
  separately for each currency, preserving decimal arithmetic until display.
- Reject ambiguous overlapping completed ingestion sources using the existing
  billing policy and expose excluded undated records.
- Add backend acceptance tests and evidence for the scope and its limitations.

## Capabilities

### New Capabilities

- `unallocated-cost`: detection of incomplete-metadata cost candidates with
  disjoint diagnostic groups and monetary reconciliation.

### Modified Capabilities

- None. Existing billing summary, processor schema and ingestion remain intact.

## Dependencies And Boundaries

The five dimensions are `owner`, `environment`, `application`, `cost_center`
and `project`, as specified by [JUP-015](https://trello.com/c/UDIyjTyl). Its
organizational catalog is not available in the integrated baseline. The older
assistant corpus lists `businessunit` instead of `project`; that historical
proposal does not supersede the card's dimensions. This change does not edit
the corpus or claim that the inconsistency is resolved there.

The policy module is reused byte-for-byte from
[JUP-017 PR #66](https://github.com/EconomiconFinOps/tfm-economicon/pull/66).
This reuse does not integrate its endpoint, frontend or entire PR, and does
not establish completion of JUP-017's review process.

[JUP-027](https://trello.com/c/W6gAiOWt) has no integrated showback contract in
the inspected baseline. Future consumers must distinguish these candidates
from missing values in a selected showback dimension. Costs grouped separately
by owner, project and application cannot be summed across those dimensions.

## Out Of Scope

- Authoritative `allocated`, `shared`, `unallocated` or `excluded` decisions,
  rule persistence, organizational catalogs, manual assignment or reallocation.
- Resource-level findings, raw tag values, frontend panels, alerts or agent tools.
- Resolving ingestion overlap, choosing a preferred source or modifying data.
- Currency conversion, invoice completeness, chargeback or realized savings.
- Treating absent source metadata as proof of absence on the original resource.

## Impact And Delivery Status

The change adds a backend schema, service, database facade, billing route and
tests. SQL aggregates at most 32 defect signatures per currency; raw billing
rows are not returned. The initial baseline is `origin/develop` at `c2995a1`.
Implementation was authorized by the user's 2026-10-10 dispatch of this card;
no separate historical pre-code restriction is treated as current scope.

Trello roles remain Victor Mendez (leadership), Alejandro Aguado
(pairing/co-authorship), Lucia Mateo (PR review) and Paris Arcos Martin
(validation, tests and documentation). These assignments do not prove human
participation. Pairing, independent review and acceptance remain unverified;
the implementation and its own test evidence do not replace those steps.
