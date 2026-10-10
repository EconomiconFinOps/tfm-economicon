JUP: JUP-027
Trello: https://trello.com/c/W6gAiOWt

## Why

Direction needs to attribute observed Azure spend to teams, projects and applications. The normalized ledger already supplies costs and canonical tags, but no exact organizational attribution report exists in develop.

## What Changes

- Add authenticated GET /billing/showback with owner, project, application or cost_center and a UTC period.
- Attribute each selected record in full to one unit or an explicit missing/invalid bucket, preserving signed costs and currencies.
- Return exact decimal strings, record counts and reconciliation per currency; reject overlapping completed cost sources.
- Reuse the minimum syntax contract of JUP-015 through an explicitly provisional adapter. Corporate catalog membership and owner-to-organization mappings remain unavailable.
- Add service, API and real CockroachDB acceptance tests and reproduction instructions.

No shared-cost redistribution, chargeback, new UI, ingestion change or JUP-028 implementation is included. This endpoint is the functional showback delivery; human participation and independent validation remain required before closure.

## Impact

New backend modules and a router registration; no schema migration or billing summary contract change. Assigned roles remain Paris leadership, Victor pairing, Alejandro review and Lucia validation. Assignments do not certify participation.
