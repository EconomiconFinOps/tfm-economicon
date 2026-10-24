## MODIFIED Requirements

### Requirement: Explicit illustrative journey and accessible interaction

The landing SHALL distinguish the real approved video, application destination and illustrative product perspectives. It SHALL preserve academic and simulation labels without claiming anonymous access to the application. Exactly one application entry SHALL appear in the header, usable on desktop and mobile. Navigation and tabs SHALL support named controls, keyboard operation, visible focus, and Escape with focus restoration for the mobile menu. The composition SHALL provide selectable light/dark themes and pausable decorative motion.

#### Scenario: Demo journey
- **WHEN** the visitor selects Costes, Anomalías or Fuentes
- **THEN** the corresponding illustrative panel is shown with truthful simulation labels

#### Scenario: Tabs by keyboard
- **WHEN** the visitor presses arrow keys, Home or End on a perspective tab
- **THEN** focus, selection and the visible panel remain consistent

#### Scenario: One application entry and prominent inline video
- **WHEN** valid public destinations are configured
- **THEN** exactly one Abrir aplicación entry is present in the header, including on mobile
- **AND** the video appears alongside the presentation on desktop and after its text on mobile, before illustrative perspectives
- **AND** no video modal or repeated application/video calls are added

#### Scenario: Light and dark presentation
- **WHEN** the visitor changes the accessible theme control by pointer or keyboard
- **THEN** the page, navigation, cards and video container use the selected legible theme
- **AND** the control exposes its state and preserves the explicit selection locally
- **AND** changing theme does not resume a voluntarily paused video

#### Scenario: Motion and mobile menu
- **WHEN** the visitor pauses decorative motion or closes the mobile menu with Escape
- **THEN** motion remains paused or the menu closes with focus returned to its trigger respectively
- **AND** reduced-motion CSS remains supported without treating a waived interactive test as passed

#### Scenario: Useful public copy
- **WHEN** configuration is valid
- **THEN** technical configuration-success messages are absent
- **AND** the global academic notice does not classify real video and app destinations as simulations

### Requirement: Closed public artifact boundary

The build SHALL emit only explicitly allowed public files and generated metadata with a SHA256 manifest, rejecting symlink inputs. A failed build SHALL retain the preceding valid output. Runtime SHALL verify the static artifact and expose only its resources, closed public configuration, a factual generated llms description, minimal health and the selected separately verified public media snapshot. It SHALL NOT expose sources, hidden files, manifests, listings, private APIs, arbitrary filesystem paths or process environment. Unknown paths SHALL return a branded HTTP404. Media SHALL remain outside the repository, static build and image.

#### Scenario: Attempt to include private material
- **WHEN** unrelated files or environment values exist beside approved inputs
- **THEN** they are absent from the artifact and public configuration
- **AND** the media manifest and unselected media are not publicly served

#### Scenario: Symbolic input or invalid origin
- **WHEN** a required static input is a symlink or SITE_ORIGIN is invalid
- **THEN** the build fails without replacing the preceding valid artifact

#### Scenario: Unknown path or unsupported method
- **WHEN** a request targets an unknown/private path or unsupported method
- **THEN** it returns404 or405 without exposing repository material

## ADDED Requirements

### Requirement: Two public runtime destinations

LANDING_VIDEO_URL and LANDING_APP_URL SHALL govern their destinations at startup without operational URLs baked into static assets. Runtime SHALL disclose only normalized videoUrl/appUrl or null, using safe serialization, a closed schema and non-cacheable same-origin delivery without ETag304. HTTPS validation SHALL reject executable schemes, credentials and invalid public destinations. Only the video value MAY additionally use the closed form /media/name.mp4, with a safe single filename and no queries, fragments, encoded separators or traversal. Missing or invalid values SHALL disable only their destination truthfully.

#### Scenario: Configured public destinations
- **WHEN** valid video and app values are supplied
- **THEN** their public actions use only their corresponding configured value
- **AND** unrelated environment and secrets are not disclosed

#### Scenario: One destination missing or unsafe
- **WHEN** one value is absent or invalid
- **THEN** its action is unavailable without a misleading destination
- **AND** the other valid action and illustrative perspectives remain usable

#### Scenario: New configuration after recreation
- **WHEN** the same image is recreated with changed runtime values
- **THEN** configuration reflects them after reload without stale304

### Requirement: Approved local media with controlled automatic inline playback

The approved local video SHALL play in the prominent responsive native video panel with controls, initial muted autoplay and playsinline. Sound SHALL require explicit visitor action. A rejected play promise SHALL leave a usable manual Play alternative and truthful status; fallback alone SHALL NOT establish inline playback. Theme, scrolling or loading events SHALL NOT resume a voluntary pause. External HTTPS viewer URLs SHALL remain secondary links without automatic third-party media loading. Existing CSP boundaries SHALL NOT be weakened or expanded for this local supply.

#### Scenario: Proven initial playback
- **WHEN** the local media snapshot is configured and the browser allows muted autoplay
- **THEN** actual currentTime advancement, paused=false and prepared media are observed without pressing Play
- **AND** the video begins muted, inline and controllable on desktop and mobile

#### Scenario: Browser blocks automatic playback
- **WHEN** the initial play promise rejects
- **THEN** a visible manual playback control and useful status remain
- **AND** no automatic success is asserted

#### Scenario: Voluntary pause or explicit audio action
- **WHEN** the visitor pauses video or explicitly changes its audio control
- **THEN** the pause persists through theme changes and sound changes only in response to visitor action

#### Scenario: Missing media or external viewer
- **WHEN** the configured local file cannot be verified/loaded or only an external viewer URL is supplied
- **THEN** a truthful error or secondary external link remains as applicable
- **AND** the app and page remain available without weakening protections

### Requirement: Bounded verified public media snapshot

Runtime SHALL read a dedicated read-only public directory, with a closed manifest of safe filenames, video/mp4 MIME, byte lengths and SHA256. It SHALL verify only the selected file, reject symlink directory/manifest/media, invalid schemas, wrong MIME/hash/size and files over50MiB, and retain verified bytes in memory for the process lifetime. Only the selected exact /media/name.mp4 route SHALL be served. GET/HEAD and single byte ranges SHALL preserve exact bytes, lengths,206 and416 semantics. Manifest failure SHALL disable media without disabling health, public config or app. Host read-only mounts alone SHALL NOT be described as immutable.

#### Scenario: Host changes after startup
- **WHEN** approved host media or manifest bytes change after snapshot creation
- **THEN** running responses retain the verified snapshot until landing is recreated

#### Scenario: Range or private path request
- **WHEN** a valid single byte range, an unsatisfiable range or an unselected/private/encoded media path is requested
- **THEN** the server returns exact206 bytes,416 with total length or404 respectively
- **AND** HEAD ignores Range, while unknown range units or unsupported multipart requests may be ignored with200

### Requirement: General Compose service and immutable image configuration change

The landing SHALL have a reproducible pinned Node22-or-later image and a general Compose service without an optional profile or separate manual server. Runtime SHALL use a non-root user, read-only static artifact, disabled privilege escalation, local health and a dedicated read-only media directory mounted from outside the checkout. It SHALL have no product credentials or private app dependencies. Changing approved media or either destination SHALL recreate only landing with the same image and unchanged static build, without rebuilding or writing Git. The initial build of modified code or the existing SITE_ORIGIN SHALL be distinguished from later media/link substitutions. General Compose SHALL pass SITE_ORIGIN only as its existing initial-build argument, never as a third public runtime destination.

#### Scenario: General stack startup
- **WHEN** the documented general Compose flow starts an isolated project with the approved public directory supplied
- **THEN** landing starts with local health while existing service declarations remain preserved
- **AND** health alone does not assert playback, application access or external deployment

#### Scenario: A to B to A with identical image
- **WHEN** the operator changes destinations and recreates only landing with no build or pull
- **THEN** container identity changes while imageID, static manifest and assets remain identical
- **AND** destinations reflect A, B and A without PR or recreation of other services

#### Scenario: Media handoff and recovery
- **WHEN** an operator receives the approved image/reference and external public media directory
- **THEN** documented exact paths, read-only mount, hashes, startup values, HTTP checks and recovery steps allow local rehearsal without rebuilding the image
- **AND** unpublished image distribution and external deployment remain explicit pending stages

#### Scenario: Restart without new environment
- **WHEN** an existing container is only restarted
- **THEN** that action is not reported as applying changed environment values


### Requirement: Factual discoverable description from verified public inputs

The landing SHALL include a versioned llms.txt Markdown description as an explicit verified build input, discoverable through same-origin rel=describedby metadata without visual changes. Its GET/HEAD text/plain UTF-8 response SHALL describe the academic Azure FinOps MVP factually, public/synthetic data, candidate anomaly signals and documentary sources, with real limitations and useful public links. It SHALL NOT contain agent identities, secrets, misleading instructions or invented measured benefits. It SHALL append only the normalized public application destination from the same startup snapshot as runtime configuration, omitting missing or unsafe values without fetching them. The generated response SHALL use no-store, no ETag/304 and a closed exact route; static template bytes and the build manifest SHALL remain unchanged.

#### Scenario: Description and coherent application destination
- **WHEN** a valid app destination is configured and the client requests llms.txt
- **THEN** GET returns the factual Markdown and that same validated public app link, with a warning that access may need authorization
- **AND** HEAD reports the same UTF-8 byte length without a body and no unrelated environment or video URL is exposed

#### Scenario: Missing, unsafe or stale application destination
- **WHEN** the app value is absent, unsafe or changed only outside an existing startup snapshot
- **THEN** the description omits an invalid app link or retains the original startup destination respectively
- **AND** recreating A to B to A with one image changes runtime/llms links coherently while compiled files remain identical

#### Scenario: Description boundary and integrity
- **WHEN** the template is altered, omitted, or an alias/query/private route is requested
- **THEN** startup integrity validation fails or the route is rejected as applicable, without exposing sources, manifests or secrets

#### Scenario: Explicit build origin and conservative local discovery
- **WHEN** general Compose builds with an explicitly supplied valid SITE_ORIGIN for the landing
- **THEN** its existing Dockerfile build argument receives that origin and canonical/sitemap use the landing origin rather than the runtime app destination
- **AND** an empty origin retains local noindex/nofollow, robots Disallow and a URL-free sitemap, including a noindex header for the generated description
- **AND** later app/video substitutions still require no rebuild and no indexing or remote availability is promised
