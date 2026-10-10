JUP: JUP-015
Trello: https://trello.com/c/UDIyjTyl

## Why

Five required tags exist in the card and the JUP-017 syntax policy, but consumers
lack a common dictionary and a distinction between syntax, catalog membership
and organizational mapping. Inferring application from project or team from
organization would create unsupported ownership claims.

## What Changes

- Publish a canonical taxonomy, minimum-v1 JSON contract and catalog-v1 format.
- Deliver an offline reference verifier, synthetic examples and negative tests.
- Document adoption contracts for JUP-017/027/028/037 and current ingestion limits.
- Record an ADR, evidence and continuity without claiming corporate approval.

## Capabilities

### New Capabilities

- tagging-taxonomy: versioned tag and organizational catalog design contract.

### Modified Capabilities

- None.

## Impact

Documentation and standalone tooling only; no SQL/API/normalizer/UI changes.
No new dependencies or alterations to public fixtures. Actual tenant catalogs,
deployment, pairing, independent reviews and organizational acceptance remain
explicitly pending. User dispatch authorizes implementation of this P1 card.

## Assigned participation

Paris Arcos Martin leads; Victor Mendez pairing; Alejandro Aguado PR review;
Lucia Mateo validation/tests/documentation. Assignment does not assert work done.
