JUP: JUP-072
ADR: not applicable

## Context

The project is limited to Azure but does not have an Azure tenant to query. Microsoft publishes public example Azure cost exports through the FinOps Toolkit repository. JUP-072 establishes the shared dataset contract required by the future fake Azure API, while Trello remains the operational source of truth for scope, ownership and review.

The selected source is the `dataset-examples.zip` asset from Microsoft FinOps Toolkit release `v14`. The original archive is 109,532,323 bytes and has SHA-256 `d7769d9e759b5968a68affcb364235ad938a705168c546ab86cad5bbb27ff607`. Its 11 CSV entries contain 1,295,308 records and approximately 934 MB of uncompressed content.

## Goals / Non-Goals

**Goals:**

- Record the official source URL, exact release, archive checksum, schema inventory, quality findings and Microsoft MIT copyright notice.
- Provide small deterministic fixtures whose headers and selected row values match Microsoft's public exports exactly.
- Define `EA-Cost-Actual.sample.csv` as the default dataset for the Azure Cost Management fake API.
- Preserve valid negative and zero costs required to represent credits, reversals and adjustments.
- Validate every versioned fixture and its manifest without requiring a live Azure tenant or re-downloading the large archive.

**Non-Goals:**

- Implementing the Azure fake API, its HTTP contract, database ingestion or downstream analytics.
- Committing the complete ZIP archive, connecting to Azure or processing real customer exports.
- Anonymizing or pseudonymizing a dataset that Microsoft already publishes publicly.
- Summing actual, amortized and FOCUS views together or treating the limited sample as sufficient for seasonal forecasting.

## Decisions

### Pin an official public Microsoft release by SHA-256

The documentation and machine-readable audit pin the official Microsoft release URL, MIT license and original archive checksum. The ZIP remains outside Git because of its size, while `.gitignore` rejects archive files and raw-data directories. This makes source updates explicit during code review.

### Stream and profile the ZIP without extracting it

The Python auditor reads CSV entries directly from the archive. It inventories columns, row counts, nulls, date ranges, currencies, numeric ranges, identifier columns, malformed rows and unsafe archive paths. Deterministic row scoring uses the source archive checksum, entry name, row number and original row content.

### Version small fixtures with original public values

Each source CSV contributes at most 50 rows, recorded in a manifest containing the source checksum, release, original entry name and sample size. All selected public values are copied without redaction, hashing, anonymization or pseudonymization. The Microsoft MIT notice is stored next to the samples.

### Use actual EA costs as the canonical downstream input

`EA-Cost-Actual.sample.csv` provides the primary dataset for downstream fake Azure API work. The sample intentionally retains negative, zero and positive costs. Amortized, FOCUS, pricing and reservation exports remain separate fixtures to prevent accidental double counting and support future normalization tests.

## Risks / Trade-offs

- [The complete dataset exceeds practical Git size limits] -> Track its exact official URL and SHA-256, version only deterministic fixtures and ignore ZIP archives.
- [A newer Microsoft release changes schemas or values] -> Treat a release or checksum change as an explicit new review and regenerate all audit artifacts together.
- [Developers accidentally discard credits or zero-cost records] -> Validate negative and zero costs in the canonical checked-in fixture and synthetic profiling tests.
- [Public samples are mistaken for private customer exports] -> State explicitly that no anonymization is needed for Microsoft's public example dataset; define any future real-tenant data policy separately.
- [Actual, amortized and FOCUS exports are summed together] -> Document them as alternative views and designate actual EA costs as the single default dataset.
