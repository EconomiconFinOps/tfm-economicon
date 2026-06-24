## ADDED Requirements

### Requirement: HU templates are available

The project SHALL provide lightweight Markdown templates for recurring HU workflow artifacts.

#### Scenario: Contributor starts a new HU

- **WHEN** a contributor starts a new HU
- **THEN** they can copy templates for pre-code approval, review, post-review approval, hotfix justification, and the HU checklist from `docs/templates/hu/`.

### Requirement: Templates remain documentation-only

The project SHALL keep HU templates as documentation, not executable harness logic.

#### Scenario: Template is used in a change

- **WHEN** a template is copied into an OpenSpec change
- **THEN** it guides documentation and review without adding skills, agents, hooks, or CI enforcement.

### Requirement: HU plan links canonical templates

The HU adaptation plan SHALL point contributors to the canonical template location.

#### Scenario: Contributor reads the HU plan

- **WHEN** a contributor reads `docs/openspec-hu-adaptation-plan.md`
- **THEN** they can find the reusable HU templates without reconstructing snippets from prose.
