## MODIFIED Requirements

### Requirement: Demo operator credential references stay consistent
The project SHALL keep seed data, frontend email default and active documentation aligned on the same validator-safe demo operator email. The password SHALL be supplied externally for explicit demo seeding and entered manually in the frontend; it MUST NOT be prefilled or bundled. Seeding MUST NOT overwrite an existing account password, identity or role. Existing-account rotation SHALL be an explicit operator action, without migrations or changes to login/session/tenant contracts.

#### Scenario: Contributor follows demo login documentation
- **GIVEN** explicit demo seeding and an externally supplied non-default password
- **WHEN** a new demo account is created and the contributor opens login
- **THEN** seed, documentation and frontend agree on operator@example.com, the password field is empty, and manually entering the configured password authenticates under the existing contract.

#### Scenario: Existing account retains its rotated password
- **GIVEN** an existing demo account whose hash was explicitly rotated
- **WHEN** the service restarts with seeding enabled and a different DEMO_PASSWORD
- **THEN** the stored hash and identity remain unchanged; changing env does not rotate it, and a detected legacy default password outside test instead blocks startup with a safe rotation instruction.
