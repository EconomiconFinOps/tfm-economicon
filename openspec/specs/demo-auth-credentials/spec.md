# demo-auth-credentials Specification

## Purpose

Define the validity and consistency requirements for demo auth credentials used by local seed data, tests, UI defaults, and active documentation.

## Requirements
### Requirement: Demo operator email is validator-safe

The project SHALL use a demo operator email address that is accepted by the backend auth request schema and the installed email validation rules.

#### Scenario: Backend auth schema accepts demo operator email

- **WHEN** a backend auth schema test creates a login request with the demo operator email
- **THEN** the request validates successfully.

### Requirement: Demo operator credential references stay consistent

The project SHALL keep active seed data, frontend login defaults, and active documentation aligned on the same demo operator email.

#### Scenario: Contributor follows demo login documentation

- **WHEN** a contributor uses the documented demo operator email and password
- **THEN** those credentials match the seeded demo account and the frontend login defaults.
