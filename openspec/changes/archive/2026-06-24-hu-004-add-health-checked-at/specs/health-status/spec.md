## ADDED Requirements

### Requirement: Health response includes evaluation timestamp

The backend `GET /health` response SHALL include a `checked_at` timestamp representing when the server evaluated the health status.

#### Scenario: Successful health evaluation

- **WHEN** a client requests `GET /health`
- **THEN** the response includes `status`, `services`, and `checked_at`.

#### Scenario: Timestamp is UTC aware

- **WHEN** the backend creates a health response
- **THEN** `checked_at` is a timezone-aware UTC timestamp.

### Requirement: Existing health status semantics remain unchanged

The backend `GET /health` response SHALL continue to report `ok` only when all checked services are healthy and `degraded` otherwise.

#### Scenario: All services healthy

- **WHEN** database, queue, and vector store checks return healthy
- **THEN** the response status is `ok`.

#### Scenario: At least one service unhealthy

- **WHEN** any checked service returns unhealthy
- **THEN** the response status is `degraded`.
