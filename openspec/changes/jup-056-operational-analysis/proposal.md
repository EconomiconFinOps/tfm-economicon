JUP: JUP-056
Trello: https://trello.com/c/4AbHqWKW

## Why

The operational cost page still displays static demonstration data. Analysts cannot investigate stored Azure expenditure using the account, service, project and tag filters requested by the card. Existing billing v2 supports grouping, which cannot substitute for combined filtering.

## What Changes

- Replace the operational demonstration with a scoped, accessible analysis of stored Azure costs.
- Add optional, conjunctive billing filters for subscription ID, service, project and tag key/value before aggregation; preserve existing unfiltered clients.
- Reuse the authenticated frontend API, tenant/session isolation, billing response and design tokens.
- Show exact amounts by currency, grouped detail, current-result export and explicit loading, invalid, empty, partial and error states.
- Record reproducible tests, evidence and limitations without attributing agent work to human pairing or acceptance.

## Impact

Affected: operational frontend, additive billing filter contract/query, focused tests and documentation. No new dependencies, provider ingestion, recommendations, brand redesign or change to executive dashboard semantics. Account means Azure subscription in the existing cost model. Production deployment, human review/validation and merge remain separate.

## Participation

Source checked 2026-10-10 using DockerServer `/home/danteadmin/economicon-collaboration`: Victor Mendez leads, Alejandro Aguado pairs, Lucia Mateo reviews, Paris Arcos Martin validates. This implementation is an authorized technical contribution; no role reassignment or human participation is inferred.
