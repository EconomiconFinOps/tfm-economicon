## 1. Source Selection And Audit

- [x] 1.1 Select the official Microsoft FinOps Toolkit v14 public Azure dataset and record its MIT license, release URL, archive size and SHA-256 checksum.
- [x] 1.2 Audit all 11 CSV entries, 1,295,308 records, schemas, date ranges, malformed rows, currencies, negative costs and zero-cost records.
- [x] 1.3 Document the canonical actual-cost dataset, alternative exports and downstream Azure fake API constraints.

## 2. Versioned Reproducible Fixtures

- [x] 2.1 Implement deterministic streaming audit and sampling without extracting or committing the large source archive.
- [x] 2.2 Version 11 CSV fixtures capped at 50 rows, their source manifest and Microsoft's MIT copyright notice.
- [x] 2.3 Preserve all selected public Microsoft values without anonymization, pseudonymization or other transformations.
- [x] 2.4 Keep negative, zero and positive amounts in the canonical `EA-Cost-Actual.sample.csv` fixture.

## 3. Validation And Delivery

- [x] 3.1 Add automated tests covering source provenance, deterministic sampling, malformed rows, unsafe archive paths, fixture inventory and the Microsoft license.
- [x] 3.2 Validate all OpenSpec changes strictly and verify the JUP-072 Trello/OpenSpec link.
- [x] 3.3 Publish `docs/JUP-072-audit-azure-dataset` as a pull request targeting `develop`.
