## ADDED Requirements

### Requirement: Session expiry is communicated to the operator

When the frontend ends the current session because the server rejected its
bearer with `401`, the login screen SHALL tell the operator that the session
expired, in a notice that is distinguishable from login credential errors and
from backend or network failures. The notice SHALL NOT appear when the session
ended for any other reason. It SHALL describe the session that just ended, not
persist as state: it SHALL NOT survive a reload of the login screen and SHALL
disappear once a new sign-in attempt starts. It SHALL NOT include token values,
response bodies or other server diagnostics. Cleanup, generation isolation and
the strict `/me` logout policy defined by the existing requirements remain
unchanged.

#### Scenario: An in-flight authenticated operation is rejected with 401

- **GIVEN** a current session is showing a tenant-scoped screen, such as the legacy overview, or has an ingestion or conversation mutation in flight
- **WHEN** that operation receives `401`, including with a non-JSON body
- **THEN** the existing cleanup runs and the login screen shows the session-expired notice.

#### Scenario: Startup revalidation finds the stored token rejected

- **GIVEN** a structurally valid session is persisted from an earlier visit
- **WHEN** the current `/me` revalidation fails with `401`
- **THEN** the existing logout runs and the login screen shows the session-expired notice.

#### Scenario: Profile revalidation fails for a reason other than 401

- **WHEN** the current `/me` revalidation fails with `403`, `422`, `5xx`, a network failure or an invalid response contract
- **THEN** the existing strict logout still runs, and the login screen does not show the session-expired notice.

#### Scenario: The session ends without server rejection

- **WHEN** the operator logs out manually, or startup discards an absent or structurally invalid stored session
- **THEN** the login screen does not show the session-expired notice.

#### Scenario: Failures that keep the session never show the notice

- **WHEN** an authenticated request other than `/me` fails with `403`, `422`, `5xx` or a network failure, or a public login or health request receives `401`
- **THEN** the session is retained as already specified, and no session-expired notice is shown anywhere.

#### Scenario: The notice is distinguishable from a credential error

- **GIVEN** the login screen shows the session-expired notice
- **WHEN** the operator starts a new sign-in attempt
- **THEN** the notice is no longer shown, and a failed attempt shows only its own login error.

#### Scenario: The notice is not persisted

- **GIVEN** the login screen shows the session-expired notice
- **WHEN** the operator reloads or navigates directly to the login screen
- **THEN** the notice is not shown and no expiry marker remains in browser storage.

#### Scenario: Abandoned work cannot raise the notice for a later session

- **GIVEN** a request from an abandoned session generation is still pending and a new session has been accepted
- **WHEN** that abandoned request later receives `401`
- **THEN** the new session is not ended and no session-expired notice is shown.
