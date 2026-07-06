## Why

The backend already has a basic local authentication flow, but the behavior needs to be hardened so it can be used as a reliable baseline for future product work.

The current capability should provide predictable validation, token handling, and error responses for the demo operator login without expanding into a full identity platform.

## What Changes

- Make `POST /auth/login` behavior explicit for valid and invalid credentials.
- Make `GET /me` behavior explicit for valid, missing, expired, or invalid tokens.
- Ensure token expiration is enforced consistently using the configured TTL.
- Add focused backend tests for login and profile access.
- Keep the existing demo operator account and local password behavior.

## Capabilities

### New Capabilities

- `basic-auth-hardening`: Defines the expected behavior for the local login and current-user profile flow.

### Modified Capabilities

- None.

## Architectural Impact

- Frontend: yes; the login flow may need to handle clearer auth errors and token expiration, but this HU does not require a new screen.
- Backend: yes; `POST /auth/login`, `GET /me`, token validation, and auth/security tests are the main implementation surface.
- Processor: no; user authentication remains at the backend boundary and should not be pushed into the worker.
- Infra/DB: limited; uses existing user/auth seed and token secret behavior unless design finds a gap.

## Impact

- Backend auth route behavior and tests.
- Frontend login may rely on clearer error responses, but no new frontend screen is required.
- No OAuth, password reset, user administration, or role management.
- No new production identity provider.

## Risks / Unknowns

- Token expiration tests may need time control or focused token utility tests.
- Existing clients may rely on current error message shapes; keep HTTP status semantics stable unless design confirms otherwise.
- This HU touches auth, so review should check security-sensitive behavior carefully.
