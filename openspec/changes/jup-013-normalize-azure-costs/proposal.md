JUP: JUP-013
Trello: https://trello.com/c/vw0xIKRN

## Why

JUP-077 established a reliable Azure Cost ingestion but stores every grouping
other than cost, currency and date in a generic `dimensions` object. Business
queries would therefore need provider-specific field names and JSON extraction
for resource group, service, project and tags. JUP-013 must turn that foundation
into a stable FinOps record without duplicating the API client or ingestion.

## What Changes

- Promote known EA, FOCUS and Azure Query aliases to explicit FinOps fields.
- Normalize resource group, service, project, tags and optional consumption.
- Preserve cost zero/credits, source spelling and unknown dimensions.
- Make equivalent provider aliases produce the same canonical record and hash.
- Add a CockroachDB migration that preserves and backfills existing records.
- Persist and return the explicit columns from the processor repository.
- Use resource group and service as the default demonstrable cost slice.

## Capabilities

### New Capabilities

- azure-cost-normalization: provider-independent normalized FinOps cost records.

### Modified Capabilities

- None.

## Out of Scope

- Building the hierarchy required by JUP-014.
- Calculating business KPIs owned by JUP-026.
- Expanding the fake Azure API beyond its approved Query contract.
- Fabricating dimensions that were not requested from Azure Cost Management.
- Applying roadmap due dates before JUP-080 is approved.

## Impact

The processor normalization model, persistence migration, repository SQL,
default ingestion definition, tests and architecture documentation change. The
existing client and run identity remain compatible.
