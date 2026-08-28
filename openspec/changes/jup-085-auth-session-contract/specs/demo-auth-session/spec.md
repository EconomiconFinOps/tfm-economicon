## ADDED Requirements

### Requirement: Demo login exposes a deterministic minimal contract

The MVP SHALL authenticate the seeded demo user through `POST /auth/login` and
SHALL return a bearer access token plus the canonical user profile without
revealing whether a submitted email exists.

#### Scenario: Valid demo credentials create a session

- **WHEN** a caller submits the configured demo email and matching password
- **THEN** the service returns `200`, `token_type: bearer`, an access token and
  a profile containing `id`, `email`, `full_name` and `role`.

#### Scenario: Credentials are invalid

- **WHEN** the email is unknown or the password does not match
- **THEN** the service returns the same generic `401` response in both cases.

### Requirement: Access tokens expire and resolve a current user

The demo access token SHALL be signed with a runtime-only secret, SHALL contain
`sub`, `iat` and `exp`, and SHALL use the configured TTL. `/me` SHALL return the
current persisted user only while that token remains valid.

#### Scenario: Bearer is absent or malformed

- **WHEN** `/me` receives no bearer token or an invalid authorization scheme
- **THEN** it returns `401` without exposing token parsing details.

#### Scenario: Token is invalid or expired

- **WHEN** signature verification fails or the current time is after `exp`
- **THEN** `/me` returns `401` and no profile data.

#### Scenario: Token references a removed user

- **WHEN** a valid token subject no longer resolves to a persisted user
- **THEN** `/me` returns `401` rather than accepting stale identity state.

### Requirement: Frontend session lifecycle is cleared consistently

The frontend SHALL treat the access token and user profile as one demo session
and SHALL remove that session, the active tenant and cached tenant data on
logout or confirmed session invalidation.

#### Scenario: User logs out

- **WHEN** the user activates logout
- **THEN** `finops.session`, `finops.activeTenant` and the query cache are cleared
  before the login view is shown.

#### Scenario: Restored session is no longer authorized

- **WHEN** a persisted session receives `401` while restoring profile or tenants
- **THEN** the frontend clears local auth and tenant state and requests login.

### Requirement: Demo credentials and runtime secrets remain separated

The project SHALL document demo credentials as non-production fixtures and SHALL
NOT version a deployment signing secret or expose it through the frontend bundle.

#### Scenario: Production-like configuration is prepared

- **WHEN** a non-local runtime is configured
- **THEN** its signing secret is injected outside Git and no `VITE_*` value
  contains the signing key or a privileged credential.
