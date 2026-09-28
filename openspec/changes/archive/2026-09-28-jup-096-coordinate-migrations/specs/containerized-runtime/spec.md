## MODIFIED Requirements

### Requirement: Healthy dependency gates

Backend, processor and frontend SHALL wait for dependency health rather than
only dependency process creation. The processor SHALL also wait for a healthy
backend, so that the backend-owned schema exists before the processor uses it.
Prometheus SHALL wait for healthy backend and processor, and Grafana SHALL wait
for healthy Prometheus, preserving the JUP-043 dependency gates.

#### Scenario: Dependency has started but is not ready

- **WHEN** a required database, broker, API or backend container has not passed
  its healthcheck
- **THEN** Compose does not start the dependent application as ready

#### Scenario: Processor waits for the backend on a cold start

- **WHEN** the complete stack starts with empty volumes
- **THEN** the processor container is created only after the backend reports
  healthy, and both backend and processor end healthy

#### Scenario: Backend never becomes healthy

- **WHEN** the backend container fails or does not pass its healthcheck
- **THEN** Compose does not start the processor and reports the unmet backend
  dependency instead of starting a processor without the backend schema
