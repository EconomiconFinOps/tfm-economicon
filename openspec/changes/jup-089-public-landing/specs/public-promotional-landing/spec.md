## ADDED Requirements

### Requirement: Public site is independent of private application
The system SHALL build a static public landing from explicitly selected public files without publishing credentials, private configuration, application sessions or backend connectivity.

#### Scenario: Building the preview
- **WHEN** a contributor builds the landing without publication configuration
- **THEN** the output contains only landing pages and selected assets, disallows indexing and does not call private APIs

#### Scenario: Requesting an unknown page
- **WHEN** a visitor requests an unknown path from the preview server
- **THEN** the response is HTTP 404 with a branded recovery link, without serving the application shell or filesystem files outside the output

### Requirement: Content distinguishes evidence from concepts
The landing SHALL explain audience, FinOps value, capabilities, architecture, resources and team while labelling simulated imagery and future functionality explicitly.

#### Scenario: Visitor inspects product imagery
- **WHEN** the visitor reads a historical screenshot or brand mockup
- **THEN** its provenance and simulated nature are visible and it does not claim validated savings or finished generative functionality

### Requirement: Accessible responsive presentation
The landing SHALL provide semantic headings, meaningful links, alternative image text, keyboard navigation and visible focus across desktop and narrow mobile widths.

#### Scenario: Keyboard and mobile visit
- **WHEN** a visitor navigates at a 320 CSS pixel width or using only a keyboard
- **THEN** the page has no horizontal overflow, essential links remain usable and a skip link reaches the main content

### Requirement: Publication configuration is explicit
The build SHALL accept only public HTTPS publication URLs and SHALL produce canonical, Open Graph and crawler metadata appropriate to the selected preview or publication mode.

#### Scenario: Invalid publication origin
- **WHEN** a configured origin contains credentials, an internal hostname, an insecure scheme or unsupported path
- **THEN** the build fails with a clear error before publishing output

#### Scenario: No approved video URL
- **WHEN** a public video location has not been configured
- **THEN** the page explains that the concept material is pending publication instead of linking to a fake or private destination

### Requirement: Publication and rollback are documented
The delivery SHALL record reproducible commands, checks, known limitations and pending domain, renewal ownership, HTTPS, M4 and M5 decisions.

#### Scenario: Maintainer prepares release
- **WHEN** the maintainer reads the deployment runbook
- **THEN** they can build the static artifact and understand promotion and rollback without exposing the application environment or treating local checks as production validation
