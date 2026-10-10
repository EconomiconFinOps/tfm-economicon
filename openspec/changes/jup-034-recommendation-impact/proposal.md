JUP: JUP-034
Trello: https://trello.com/c/Hdwz4SXw

## Why

Direction needs reproducible monthly and annual potential savings per
recommendation to prioritize actions without treating estimates as realised
benefits or adding competing actions on the same cost twice.

## What Changes

- Add an authenticated, stateless scenario evaluation endpoint with explicit
  baseline month, monthly baseline/target costs, assumptions and evidence refs.
- Calculate per-recommendation potential and disjoint-scope totals by currency.
- Preserve unknown estimates and unmeasured observed savings as null.
- Document a versioned input contract for JUP-033 and synthetic executable examples.

## Capabilities

### New Capabilities

- `recommendation-impact`: deterministic monthly/annual potential with provenance
  and overlap-aware aggregation.

## Impact

Backend schemas, service, route, tests and documentation only. No cloud mutation,
pricing API, recommendation generation, observed-savings ledger or frontend wiring.
JUP-033 producer interoperability remains pending until its contract is available.
Trello roles remain Lucia leadership, Paris pairing, Victor review and Alejandro
validation; assignment does not prove participation or independent acceptance.
