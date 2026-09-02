## 1. Implement The Normal Query Service

- [x] 1.1 Add the standalone FastAPI workspace, settings, health endpoint and contractual OpenAPI endpoint.
- [x] 1.2 Load and validate all 50 rows from the canonical public actual-cost fixture and JUP-073 mapping.
- [x] 1.3 Implement supported subscription, date, aggregation, grouping, dimension/tag filtering and deterministic output behavior.
- [x] 1.4 Return Azure-shaped validation/scope errors and explicitly reserve pagination/authentication failure modes for JUP-075.

## 2. Package And Document The Service

- [x] 2.1 Add Docker/Compose execution, healthchecks, configurable host port and an unprivileged read-only container.
- [x] 2.2 Document local/Docker usage, service boundaries, architecture and downstream JUP-075/JUP-076 responsibilities.
- [x] 2.3 Link the implementation to the accepted ADR-0001, JUP-072 dataset and JUP-073 OpenAPI/cases.

## 3. Verify And Deliver

- [x] 3.1 Add API, repository, strict request, relative-clock, exact aggregate and contract-drift tests.
- [x] 3.2 Validate service tests, shared dataset/contract tests, strict OpenSpec, workspace build/tests and Docker smoke behavior.
- [x] 3.3 Publish `feat/JUP-074-azure-cost-api` as a pull request targeting `develop`.
