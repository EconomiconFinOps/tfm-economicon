## MODIFIED Requirements

### Requirement: Expected values verified independently

Every figure in the route (monthly totals per currency, the month with no data, the recorded zero, the credit, the comparisons between months and the grouped totals) SHALL be listed in a machine-readable file and SHALL equal an exact decimal computation over the records of the synthetic dataset. No expected value SHALL be produced by the loader's own aggregation code or by the application. The route SHALL NOT show an excluded undated record, because the demo dataset contains none; that case is covered by an automated test.

#### Scenario: Values match an exact computation
- **WHEN** the expected values are compared with the sums computed from the dataset records using exact decimal arithmetic
- **THEN** every expected value equals the computed value
- **AND** a changed amount, month or currency in the dataset makes the comparison fail

#### Scenario: Comparisons follow the documented rule
- **WHEN** the comparison for a currency is computed from its first and last months with a non-zero cost inside the period
- **THEN** the difference and the percentage equal the figures in the file and in the guide of JUP-106
- **AND** a month with a recorded zero is not used as an endpoint

#### Scenario: A drifted guide is detected
- **WHEN** a figure in the expected-values file is altered
- **THEN** the verification fails and names the figure

### Requirement: Preparation and return to the initial state

The preparation guide SHALL start from an isolated stack with its own volumes where the demo tenants have no cost data, SHALL load the cost and anomaly datasets with the single entry point `scripts/demo_data.py`, SHALL state the reference date to set for the route, SHALL confirm the loaded state and the expected summary before the route, SHALL NOT run a detection before the route, and SHALL end with the removal of the datasets and the confirmation that both tenants are empty again, without episodes or detection state. It SHALL NOT use the stack of another task and SHALL state that the JUP-065 demo requires the same tenant to be empty.

#### Scenario: Preparation confirms the loaded state
- **WHEN** the preparation steps are followed on a fresh isolated stack
- **THEN** the entry point reports the datasets present and the billing summary for the main period equals the expected values
- **AND** the anomalies panel of `tenant-core` shows the never-detected state
- **AND** the loading is refused by the entry point, not worked around, if a tenant already has cost data outside the manifest

#### Scenario: Return to the initial state
- **WHEN** the final steps are followed
- **THEN** each removal reports its synthetic rows removed and a second removal reports nothing to remove
- **AND** the billing summaries of both tenants are empty and `tenant-core` has no episodes

### Requirement: No secrets, binaries or interference with other work

The package SHALL NOT contain secrets, credentials, captures, recordings or other binaries, and the browser recipe SHALL run outside the repository, SHALL NOT intercept or fake requests, and SHALL fail on a page error, a cross-origin error or a step that does not hold. The figures of the JUP-065 and JUP-106 demonstrations for the months before September 2026 SHALL stay the same, and the route SHALL state the reference date it assumes.

#### Scenario: Repository hygiene
- **WHEN** the repository hygiene check runs on the change
- **THEN** it passes and the change contains no image, video or executable binary

#### Scenario: Existing work untouched
- **WHEN** the expected values of the route for the periods before September 2026, the original public fixtures and the JUP-065 route are compared with the base
- **THEN** they are identical
- **AND** the only changes to the demo guides are the load commands, the stated reference date, the provenance notice and the removal of the steps that used the fields the demo no longer carries

#### Scenario: Route names its reference date
- **WHEN** the route is read from the top
- **THEN** it states the reference date to set for the route and that the dashboard opens on the month that contains it
