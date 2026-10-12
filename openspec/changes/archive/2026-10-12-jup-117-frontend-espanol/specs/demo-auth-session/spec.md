## MODIFIED Requirements

### Requirement: Frontend session lifecycle is cleared consistently

The frontend SHALL treat the access token and user profile as one demo session
and SHALL remove that session, the active tenant and cached tenant data on
logout, any current `/me` query error, or current-session `401` invalidation
outside `/me`.

#### Scenario: User logs out

- **GIVEN** authenticated queries, mutation results and page state exist
- **WHEN** the user activates logout, including a repeated logout
- **THEN** `finops.session`, `finops.activeTenant` and the query cache are cleared
  together with in-memory identity, tenant, mutation cache and page state before login is shown.
- **AND** logout sends no revocation request; the old JWT can still pass `/me` while now < exp+5 if its user exists and all other checks pass.

#### Scenario: Tenant bootstrap returns unauthorized

- **WHEN** the current session receives `401` from `/tenants`
- **THEN** the frontend performs the same cleanup automatically and requests login without requiring the session-reset button ("Restablecer sesión") or retrying that unauthorized request.
- **AND** a concurrent profile response from the abandoned generation cannot restore session or cache; `/me` errors themselves retain the separate strict query policy above.

#### Scenario: An active authenticated request receives 401

- **WHEN** a current-session billing/conversation query or ingestion/conversation mutation receives `401`, including a non-JSON error body
- **THEN** numeric HTTP status triggers the same cleanup before error-body parsing, without depending on component error rendering or automatic retries.

#### Scenario: Errors outside profile revalidation preserve authentication

- **WHEN** an authenticated request other than `/me` receives `403`, `422`, `5xx` or a network failure, or an unauthenticated login/health request receives `401`
- **THEN** that error alone does not clear the current session; its flow remains able to report the failure, and public failures do not invalidate another active session.
- **AND** this rule never exempts any error state of the current `/me` revalidation query from logout.

#### Scenario: Structured errors preserve the strict profile policy

- **WHEN** a shared HTTP error representation exposes status or distinguishes network/service failures
- **THEN** `/me` failures still propagate to its revalidation query and every current query error invokes logout; the global `401` rule for other endpoints does not replace this path.
- **AND** errors/diagnostics do not acquire bearer credentials; the existing token-bearing profile queryKey is not silently removed or migrated by this requirement.

#### Scenario: Old responses cannot change a new session

- **GIVEN** a query (including `/me` or `/tenants`) or mutation from session A is pending, logout occurs and session B is accepted, including the same user and token value
- **WHEN** A later returns `401`, success, another error or a delayed response body
- **THEN** B's profile, tenant, storage, cache and page state remain unchanged, and A triggers no new query, callback effect or logout in B.
- **AND** a new `/me` query error belonging to B still invokes logout regardless of cause; generation isolation excludes abandoned work, not current transient failures.
- **AND** existing profile/token and tenant/user query keys alone do not demonstrate this guarantee when values repeat.

#### Scenario: Late responses after logout cannot restore data

- **GIVEN** login, restoration, queries or mutations are pending for an earlier session generation
- **WHEN** that generation is abandoned and its responses settle while login is displayed
- **THEN** session/tenant/cache stay empty and no late success or callback restores authenticated UI; client cancellation does not claim to undo server-side work.
