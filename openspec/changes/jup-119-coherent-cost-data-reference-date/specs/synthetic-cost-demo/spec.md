## MODIFIED Requirements

### Requirement: No secrets, binaries or interference with other work

The package SHALL NOT contain secrets, credentials, captures, recordings or other binaries, and the browser recipe SHALL run outside the repository, SHALL NOT intercept or fake requests, and SHALL fail on a page error, a cross-origin error or a step that does not hold. The figures of the JUP-065 and JUP-106 demonstrations for the months before September 2026 SHALL stay the same, and the route SHALL state the reference date it assumes.

#### Scenario: Repository hygiene
- **WHEN** the repository hygiene check runs on the change
- **THEN** it passes and the change contains no image, video or executable binary

#### Scenario: Existing work untouched
- **WHEN** the expected values of the route for the periods before September 2026, the original public fixtures and the JUP-065 route are compared with the base
- **THEN** they are identical
- **AND** the only changes to the demo guides are the load commands, the stated reference date and the provenance notice

#### Scenario: Route names its reference date
- **WHEN** the route is read from the top
- **THEN** it states the reference date to set for the route and that the dashboard opens on the month that contains it
