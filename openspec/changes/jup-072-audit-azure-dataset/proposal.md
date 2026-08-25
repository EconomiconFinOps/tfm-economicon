JUP: JUP-072
Trello: https://trello.com/c/gfhukWIZ

## Why

Economicon needs an official, reproducible Azure cost dataset to develop and test its simulated Azure Cost Management API without connecting to a real Azure tenant. Team members need the same documented provenance, schema inventory, licensing information and small versioned fixtures before downstream API and ingestion stories can proceed.

## What Changes

- Document Microsoft FinOps Toolkit v14 as the official public dataset source, including its download URL, MIT license, archive checksum and complete CSV inventory.
- Version an auditable report covering 11 CSV exports, 1,295,308 records, schemas, date ranges, currencies, malformed rows and negative/zero costs.
- Add a deterministic streaming auditor and 11 reproducible CSV fixtures capped at 50 rows each.
- Preserve Microsoft's published public values exactly, without anonymization, pseudonymization or other data transformations.
- Identify `EA-Cost-Actual.sample.csv` as the canonical input for the future Azure fake API and keep the 109 MB source archive outside Git.
- Add automated checks for provenance, fixture integrity, reproducible sampling, malformed entries, archive safety, negative/zero amounts and the Microsoft MIT notice.

## Capabilities

### New Capabilities

- `azure-public-cost-dataset`: The repository supplies a reproducible, licensed and validated public Azure cost dataset for local development and tests.

### Modified Capabilities

- None. Existing frontend, backend, processor and infrastructure runtime behavior remain unchanged.

## Impact

- Affected areas: `docs/data/`, `fixtures/azure-cost/`, `scripts/audit_azure_dataset.py`, dataset unit tests and repository ignore rules.
- Downstream consumers: the simulated Azure Cost Management API, its ingestion client and end-to-end cost tests.
- No Azure tenant, cloud credentials, external runtime dependency or production customer data is required.
