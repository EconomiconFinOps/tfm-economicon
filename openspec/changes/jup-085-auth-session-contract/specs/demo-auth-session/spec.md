## Reconciliation Scope

Status synchronized on 2026-09-23: the worktree now consumes HEAD `3a08d60`,
including JUP-097/PR #42. Paris's literal approval is recorded in proposal.md
at 13:05:53 UTC; ADR-0007 is Accepted. The approved session residual and backend
CORS are implemented; current results reported by the orchestrator are recorded
in tasks.md. Code is REVIEW_PASS after the local RF-085-001 fix. RF-085-002 is
Open: temporary mitigation did not sustain synchronization. The [current review](../../review.md)
records QA_BLOCKED_ENV. The user excludes Windows/WSL/Docker/DB clock changes
and authorizes only native PyJWT leeway of five seconds. Incremental implementation,
Red/Green, mutation, review and QA audit are complete, with QA_PASS scoped to
this increment. Global QA_BLOCKED_ENV and pending post-QA human approval remain,
with no environment fix or exception. Parallel profile/tenant queries and logout on any current `/me` query
error, including transient errors, retain their existing retry/refetch behavior.

The five-second addendum in proposal.md updates only token time validation and
its logout validity window below; other requirements remain unchanged. The prior
zero-leeway rule `0 <= iat <= now < exp` is historical, not the current rule or an
inferred specific human choice. BE1 was reevaluated and KILLED in this increment;
its former equivalence remains historical. Current evidence and the reviewer's
8/8 browser pass are recorded in [incremental evidence](../../../../../docs/evidence/JUP-085-validation.md#incremento-actual-tolerancia-jwt-de-5-s),
not inferred from prior results. Native leeway does not resolve RF-085-002 or close CORS
findings. No product tests run in this documentation update; proxy stays unselected.

## ADDED Requirements

### Requirement: Demo login exposes a deterministic minimal contract

The MVP SHALL authenticate the seeded demo user through `POST /auth/login` and
SHALL return a bearer access token plus the canonical user profile without
revealing whether a submitted email exists.

#### Scenario: Valid demo credentials create a session

- **WHEN** a caller submits the configured demo email and matching password
- **THEN** the service returns `200`, `token_type: bearer`, `access_token` and
  `user` containing `id`, `email`, `full_name` and `role`.

#### Scenario: Credentials are invalid

- **WHEN** a syntactically valid email is unknown or a nonempty password does not match
- **THEN** both cases return `401` with `{"detail":"Invalid email or password."}`, no token/profile and no echo of submitted credentials.

#### Scenario: Login input is invalid

- **WHEN** email or password is missing, null or the wrong type, the email is invalid, or the password is the empty string
- **THEN** login returns the existing sanitized `422` validation response without input or context values, and creates no session.
- **AND** a nonempty password is compared literally without trimming or other normalization.

### Requirement: Access tokens expire and resolve a current user

The demo access token SHALL use HS256 with the runtime-only signing secret and
SHALL require a nonempty string `sub` and integer UTC-second `iat` and `exp`.
The configured TTL SHALL be a positive integer in minutes, defaulting to 480;
issuance SHALL use one instant and `exp = iat + TTL * 60`. Validation SHALL
use native PyJWT `leeway=5` seconds and require `0 <= iat <= now + 5`,
`exp > now - 5` and independently `exp > iat`, without coercion of boolean,
string or fractional iat/exp claims or acceptance of negative iat/exp. Signature,
required claims and current-user lookup SHALL remain enforced. Optional `nbf`
SHALL retain native PyJWT validation with the same leeway; it is not newly issued
or required. `/me` SHALL return the current persisted user only while the token
passes all these checks. Emission and configured TTL SHALL NOT be extended.

#### Scenario: Issuance uses the configured TTL

- **GIVEN** an isolated fixed clock and a positive configured TTL different from the default
- **WHEN** valid login issues a token
- **THEN** verification with the runtime key and HS256 succeeds, sub equals the persisted user id, iat equals the fixed UTC second and exp minus iat equals TTL times 60.

#### Scenario: TTL configuration is not usable

- **WHEN** configuration supplies zero, a negative number or a non-integer TTL
- **THEN** startup configuration rejects it through the existing safe diagnostic path before tokens are issued, without exposing runtime secrets.

#### Scenario: Valid token resolves a profile

- **GIVEN** the persisted user's profile has changed since login
- **WHEN** `/me` receives a valid bearer for that user, without X-Tenant-Id
- **THEN** it returns `200` and the profile fields `id`, `email`, `full_name`
  and `role` from current persistence directly, without the login response's
  `user` wrapper, password or password_hash.

#### Scenario: Bearer is absent or malformed

- **WHEN** `/me` receives no Authorization header, duplicate headers, a wrong scheme, an empty bearer or extra token segments
- **THEN** it returns `401` with `{"detail":"Missing or invalid bearer token."}`, without parsing details or a user lookup.
- **AND** a single well-formed bearer with a case variant of the Bearer scheme remains usable.

#### Scenario: Token is invalid or expired

- **WHEN** the JWT is corrupt, unsigned, signed with a wrong key/algorithm, or the clock reaches or exceeds exp plus five seconds
- **THEN** `/me` returns `401` with `{"detail":"Invalid access token."}`, no profile and no user lookup.

#### Scenario: Signed token has missing or malformed claims

- **GIVEN** a token signed with the correct isolated test key
- **WHEN** sub, iat or exp is absent/null, sub is empty or not a string, a time is boolean/string/fractional, iat is negative or more than five seconds in the future, exp is negative, or exp is not after iat
- **THEN** `/me` returns the generic invalid-access-token `401`, never a claim-induced `500`, and does not query the user store.

#### Scenario: Issued-at tolerance includes exactly five seconds

- **GIVEN** a fixed current second, valid signature, existing user and otherwise valid strict claims with exp after iat
- **WHEN** iat equals now+5
- **THEN** `/me` returns `200`; iat later than now+5 (including now+6) returns the generic invalid-token `401` before user lookup.

#### Scenario: Expiration tolerance excludes exactly five elapsed seconds

- **GIVEN** a fixed current second and otherwise valid strict claims with iat earlier than exp
- **WHEN** exp equals now or now-4, or another valid integer greater than now-5
- **THEN** `/me` returns `200` for the existing user without changing the issued TTL.
- **WHEN** exp equals now-5 or is earlier
- **THEN** `/me` returns the generic invalid-token `401` before user lookup.

#### Scenario: Time ordering remains independent within the tolerance window

- **GIVEN** valid signature and integer claims iat=now+4 and exp=now-4 at a fixed current second
- **WHEN** both claims individually fall inside the five-second clock limits
- **THEN** `/me` still rejects the token with generic `401` before user lookup because exp is not after iat.
- **AND** exp equal to iat is also rejected; negative or wrongly typed iat/exp remain invalid even if a clock check alone would pass.

#### Scenario: Optional not-before uses native tolerance

- **GIVEN** otherwise valid claims, valid signature, existing user and a fixed current second, using integer nbf values for these boundary cases
- **WHEN** nbf is absent or at or before now+5
- **THEN** it adds no temporal rejection and `/me` returns `200`.
- **WHEN** nbf is later than now+5 (including now+6)
- **THEN** native PyJWT validation rejects it and `/me` returns generic `401` before user lookup, without disabling verification or requiring nbf on other tokens.

#### Scenario: Legacy demo token lacks iat

- **WHEN** `/me` receives a correctly signed previously issued token with sub and future exp but no iat
- **THEN** it returns the generic invalid-access-token `401` and a new login is required; no compatibility bypass or token migration is performed.

#### Scenario: Token references a removed user

- **WHEN** a valid token subject no longer resolves to a persisted user
- **THEN** `/me` returns the generic invalid-access-token `401`, without disclosing that the referenced user was removed.

#### Scenario: User store fails for a valid identity

- **WHEN** a valid token passes verification but user lookup raises a service error
- **THEN** the existing sanitized server-error response is preserved and the failure is not misclassified as invalid credentials.

### Requirement: Session revalidation preserves the parallel bootstrap

The frontend SHALL validate persisted session structure and SHALL start the
direct `/me` profile query and `/tenants` bootstrap in parallel for a usable
session. It SHALL expose server-confirmed identity and SHALL keep protected
content hidden during initial profile/tenant loading. Every error state of
the current session's `/me` revalidation query SHALL invoke logout regardless
of cause, including transient failures, preserving JUP-097. Structured errors
or global `401` handling SHALL NOT weaken this policy. Existing query
retry/refetch timing is not changed by this requirement.

#### Scenario: Stored session cannot represent a session

- **GIVEN** finops.session contains invalid JSON, null, a primitive, an array, an empty/non-string accessToken or an incomplete/wrongly typed user profile
- **WHEN** the application starts
- **THEN** it clears session, active tenant and cache, displays login without crashing and makes no authenticated request.
- **AND** the same cleanup applies when session is absent but a stale tenant/cache remains.

#### Scenario: Valid stored session is restored from the server

- **GIVEN** a nonempty token and a profile with nonempty string id/email/role and string full_name are persisted
- **WHEN** startup begins and `/me` is still pending
- **THEN** `/me` and `/tenants` start without waiting for one another, using that bearer without X-Tenant-Id; persisted identity and protected tenant data remain hidden and billing/jobs/assistant requests wait.
- **WHEN** `/me` returns a valid direct profile for the same id and tenant bootstrap succeeds for the current session
- **THEN** the server profile is exposed through the protected context, the proposed residual updates the stored profile, and normal tenant selection resumes.

#### Scenario: Parallel bootstrap results arrive in either order

- **WHEN** `/tenants` resolves while the initial `/me` query is pending
- **THEN** internal tenant selection/cache may advance, but protected content and product requests remain blocked; tenants success does not confirm identity.
- **WHEN** `/me` succeeds first but tenants is pending or fails
- **THEN** protected product content waits for usable tenant bootstrap and its failure is reported instead of presented as empty data; errors outside `/me` follow their separate policy below.

#### Scenario: Server identity differs from the stored profile

- **GIVEN** profile and tenant requests started in parallel for a stored session
- **WHEN** a valid direct `/me` profile has a different id from the stored profile
- **THEN** the proposed residual reconciles the current identity, discards selection/cache tied to the previous identity including concurrent tenant results, and repeats tenant bootstrap before exposing protected data.
- **AND** obsolete callbacks cannot reapply those discarded results; this exceptional recovery does not serialize normal startup.

#### Scenario: Restoration returns an invalid response contract

- **WHEN** `/me` returns `200` with missing/wrongly typed required fields or a login-style user wrapper
- **THEN** the proposed runtime guard treats it as a revalidation error and follows the strict logout path, clearing local session, tenant and cache and requesting login.
- **AND** already started or resolved parallel tenant work cannot restore local state or start protected product requests.

#### Scenario: Any current profile query error ends the session

- **GIVEN** initial `/me` revalidation or a later query revalidation for the current session
- **WHEN** the query enters its error state because of `401`, `403`, `422`, `5xx`, network or response parsing failure
- **THEN** `handleLogout` clears session, active tenant and query cache and returns to login; protected content stays blocked between the error state and the logout effect.
- **AND** an earlier successful profile does not exempt the failure; the session is not retained with a recoverable-error retry screen.
- **AND** this uses the existing query error-state trigger without redefining retries before that state; backend service errors remain service errors rather than being relabeled invalid credentials.

#### Scenario: Profile failure abandons parallel tenant work

- **GIVEN** `/tenants` is pending or has populated local bootstrap state for the current session
- **WHEN** the parallel `/me` query enters an error state and invokes logout
- **THEN** the proposed cleanup/isolation clears existing tenant effects and ignores subsequent results and callbacks, leaving session, tenant and cache empty.

#### Scenario: Fresh login validates its wrapper

- **WHEN** login returns a nonempty access_token, token_type bearer and a valid user profile
- **THEN** the frontend persists accessToken and user and enters SessionGate, preserving parallel `/me` and `/tenants` bootstrap rather than skipping profile revalidation.
- **AND** the proposed validation rejects an invalid login response without creating a session or starting either bootstrap request; credential rejection remains a login error.

### Requirement: Frontend session lifecycle is cleared consistently

The frontend SHALL treat the access token and user profile as one demo session
and SHALL remove that session, the active tenant and cached tenant data on
logout, any current `/me` query error, or current-session `401` invalidation
outside `/me`. The broader cleanup and generation guarantees below are residual
requirements pending approval and verification, not existing JUP-097 guarantees.

#### Scenario: User logs out

- **GIVEN** authenticated queries, mutation results and page state exist
- **WHEN** the user activates logout, including a repeated logout
- **THEN** `finops.session`, `finops.activeTenant` and the query cache are cleared
  together with in-memory identity, tenant, mutation cache and page state before login is shown.
- **AND** logout sends no revocation request; the old JWT can still pass `/me` while now < exp+5 if its user exists and all other checks pass.

#### Scenario: Tenant bootstrap returns unauthorized

- **WHEN** the current session receives `401` from `/tenants`
- **THEN** the frontend performs the same cleanup automatically and requests login without requiring Reset session or retrying that unauthorized request.
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

### Requirement: Backend CORS grants only explicit browser origins

After the pending pre-code gate, the backend SHALL use existing FastAPI/Starlette
CORSMiddleware with `CORS_ALLOWED_ORIGINS` parsed as a JSON list through Settings.
Entries SHALL be exact serialized HTTP(S) origins without paths, credentials,
query, fragment or wildcard; production SHALL require HTTPS, with HTTP allowed
only in development/test. No regex, arbitrary reflection or `null` origin is
permitted. CORS SHALL NOT replace JWT authentication or tenant authorization.

#### Scenario: Valid explicit origins are configured

- **WHEN** Settings receives a JSON list of valid exact origins for its runtime environment
- **THEN** only those origins receive cross-origin read permission; localhost and 127.0.0.1 are distinct, and the origin must match the actual frontend host port.
- **AND** the proposed local examples are `http://localhost:5173` and `http://127.0.0.1:5173` only for development/test; production origins are supplied by the operator.

#### Scenario: Origins are missing or empty

- **WHEN** the variable is absent or is the JSON list `[]`
- **THEN** no origin receives cross-origin permission; same-origin or non-browser requests retain normal server behavior and authentication.

#### Scenario: Configured origins are invalid

- **WHEN** the value is blank, malformed JSON, a non-list, contains non-string entries, `*`, wildcard patterns, regex, `null`, noncanonical origins or HTTP in production
- **THEN** startup fails through the existing generic StartupError without echoing configuration input, secrets or exception causes; it does not silently enable permissive defaults.

#### Scenario: Public and bearer preflights are permitted

- **GIVEN** an allowed Origin and GET or POST with Authorization, Content-Type and/or X-Tenant-Id as required by the actual client
- **WHEN** native OPTIONS preflight is sent to login or a protected endpoint without a JWT
- **THEN** middleware responds with `200` and the exact Allow-Origin, `Vary: Origin`, permitted methods and required headers without user/tenant lookup.
- **AND** normal framework safelisted headers remain allowed; no exclusive three-header assertion is made. Credentials permission is absent, `allow_credentials=false`, `expose_headers=[]`, and frontend fetch does not add `credentials: "include"` or cookie authentication.

#### Scenario: Preflight or request is not granted cross-origin access

- **WHEN** preflight asks for an unlisted Origin, method or nonsafelisted header outside the explicit list
- **THEN** it returns `400` without granting that combination; an unlisted Origin receives no Allow-Origin, while an allowed Origin can still appear on a method/header rejection.
- **WHEN** an actual simple request uses an unlisted Origin, including `null`
- **THEN** it may reach the backend but receives no Allow-Origin; CORS is not a server firewall and does not promise to prevent side effects.

#### Scenario: Allowed origin does not bypass authentication

- **WHEN** a real protected request follows successful preflight with missing or invalid bearer, or fails existing tenant authorization
- **THEN** existing `401` or `403` behavior remains; an explicit Authorization header permits sending a bearer without enabling cookies, and `/me` still needs no X-Tenant-Id.

#### Scenario: Browser can observe the bounded application response matrix

- **WHEN** an actual request has an allowed Origin and returns `200`, auth `401`, existing tenant `403`, sanitized validation `422`, or a route/DB failure converted to sanitized `500` by RequestIdMiddleware before headers start
- **THEN** its response has the exact Allow-Origin and `Vary: Origin`, preserving status/body and normal metrics/tracing; repeat each status with a denied Origin and assert no Allow-Origin.
- **AND** a `500` generated outside the CORS layer by ServerErrorMiddleware is an explicit limit, not guaranteed browser-readable; test that boundary with isolated failure injection. Startup and already-started streaming failures are outside this response guarantee.
- **AND** `app.main.app` remains FastAPI with state, dependency_overrides, router and lifespan; importing it does not require secrets. Native preflight terminates before inner metrics/access logging, as disclosed in design.md.

#### Scenario: Canonical browser flow preserves JUP-097

- **WHEN** future QA exercises real login, `/me`, `/tenants` and logout on the canonical separate-port stack with matching explicit origins, normal browser security and no proxy
- **THEN** login and API responses are observable, profile/tenant queries remain parallel, and any current `/me` query error, including transient/CORS errors, still logs out with retry/refetch behavior unchanged.
- **AND** native frontend tests are reused; mocks or ASGI checks alone do not establish browser success. RF-087-001/RF-095-001 remain Open until implementation and evidence; RF-087-002 and JUP-086 are not inferred fixes.

### Requirement: Demo credentials and runtime secrets remain separated

The project SHALL preserve JUP-053's delivered runtime secret and demo credential
boundaries: opt-in seed with external password, manual password entry and no
overwrite of existing seeded accounts. It SHALL NOT version a deployment signing
secret, include a password prefill or expose privileged credentials in the bundle.

#### Scenario: Production-like configuration is prepared

- **WHEN** a non-local runtime is configured
- **THEN** its signing secret is injected outside Git and no `VITE_*` value
  contains the signing key or a privileged credential.

#### Scenario: Frontend quality work is integrated without credential regression

- **GIVEN** the coordinated JUP-087 baseline has been integrated against JUP-053
- **WHEN** the login page opens and existing demo-seed regression cases run after approval
- **THEN** the email remains operator@example.com, password starts empty, seeding still requires explicit opt-in and restarts do not overwrite an existing password, identity or role.

#### Scenario: Authentication diagnostics contain no credentials

- **WHEN** synthetic passwords, tokens or signing-key sentinels participate in rejected login/token requests or user-store failures
- **THEN** error responses and captured diagnostics contain none of those sentinels, hashes or decoded subjects; successful login exposes only its intended access_token and profile contract.
