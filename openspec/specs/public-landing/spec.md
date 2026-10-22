# public-landing Specification

## Purpose
Presentar Economicon mediante una landing estática independiente, fiel al diseño aprobado, con una demo ilustrativa identificada, interacción accesible, artefacto público cerrado y evidencia que distinga resultados locales de publicación y aceptación públicas.
## Requirements
### Requirement: Presentación pública independiente y fiel al diseño aprobado

The system SHALL deliver a separate static landing application preserving the approved seven-section composition, original Economicon branding and local licensed fonts, without importing private application code or changing authenticated routes. Ordinary contrast, focus and brand semantic fixes SHALL preserve the composition.

#### Scenario: Public first visit
- **WHEN** a visitor opens the static landing without authentication
- **THEN** the approved product, shared audiences, process, project/team and demo presentation is available
- **AND** no private API, tenant data or authentication is requested

#### Scenario: Narrow screen and reduced motion
- **WHEN** the visitor uses a1440,390 or320 CSS-pixel viewport or prefers reduced motion
- **THEN** content and controls remain available without horizontal page overflow
- **AND** motion is disabled under the reduced-motion preference

### Requirement: Explicit illustrative journey and accessible interaction

The landing SHALL identify simulated data/actions, candidate anomalies and illustrative sources. Ver la demo SHALL open only the three-step illustrative journey until a real destination is approved. It SHALL not promise real Azure access, savings, forecasts, clients or a video that does not exist. Navigation, tabs and dialogs SHALL support keyboard, named controls, focus indication, Escape and focus restoration.

#### Scenario: Demo journey
- **WHEN** the visitor activates Ver la demo
- **THEN** three perspectives can be traversed with visible simulation labels
- **AND** closing by button or Escape returns focus to the trigger

#### Scenario: Tabs by keyboard
- **WHEN** the visitor presses arrow keys, Home or End on a perspective tab
- **THEN** focus, selection and the visible panel agree

### Requirement: Closed public artifact boundary

The build SHALL emit only explicitly allowed public files and generated metadata with a SHA256 manifest, rejecting symlink inputs. A failed build SHALL retain the preceding valid output. The local server SHALL expose only the artifact, never source, hidden files, directory listings, private APIs or arbitrary filesystem paths, and SHALL return a branded404 with HTTP404.

#### Scenario: Attempt to include private material
- **WHEN** an unrelated file or environment value exists beside the public inputs
- **THEN** it is absent from the artifact

#### Scenario: Symbolic input or invalid origin
- **WHEN** a required input is a symlink or SITE_ORIGIN is invalid
- **THEN** the build fails without replacing the previous valid artifact

#### Scenario: Unknown path or unsupported method
- **WHEN** a request targets an unknown/private path or an unsupported method
- **THEN** it returns404 or405 without exposing repository material

### Requirement: Honest metadata and publication configuration

The landing SHALL provide Spanish title/description, OG metadata, original favicon and a404 page. An unconfigured build SHALL be non-indexable and omit canonical/public URLs. A production build SHALL require an explicit HTTPS root origin before generating canonical, OG URLs and sitemap. Production hosting SHALL apply documented security headers and HTTPS after human authorization; local HTTP SHALL not count as public HTTPS validation.

#### Scenario: Local build with no domain
- **WHEN** no SITE_ORIGIN is supplied
- **THEN** the build uses noindex and robots Disallow:/ without an invented domain or sitemap URL

#### Scenario: Explicit production origin
- **WHEN** an approved HTTPS root origin is supplied
- **THEN** canonical, OG image/page URLs and sitemap consistently use that origin

### Requirement: Reproducible operation and measured evidence

The project SHALL document build/preview, a concrete proposed deployment and rollback by immutable artifact, and map every official criterion to observed evidence or a truthful pending state. Responsive, basic accessibility, performance and SEO SHALL have identified local measurements; these SHALL not be presented as public field measurements or completed human reviews. Domain/renewal, public HTTPS, deployment and real demo decisions SHALL remain pending until approved and verified.

#### Scenario: Delivery before hosting selection
- **WHEN** local implementation is delivered before domain/hosting approval
- **THEN** evidence separates local results from public criteria and human reviews
- **AND** the deployment alternative and exact remaining decisions are documented
