## ADDED Requirements

### Requirement: Checklist reflects pilot friction

The HU workflow documentation SHALL capture concrete lessons learned from HU-001 before being used for product HUs.

#### Scenario: HU-001 friction is documented

- **WHEN** a contributor reads the HU adaptation plan
- **THEN** the plan explains how doc-only changes, archive behavior, anti-harness checks, and post-archive validation should be interpreted.

### Requirement: Anti-harness checks separate structure from text

The HU workflow documentation SHALL distinguish structural regressions from intentional documentation references.

#### Scenario: Documentation mentions old harness guardrails

- **WHEN** `rg` finds `sdd-harness`, `.sdd`, `SPEC`, or similar terms only in documentation
- **THEN** the result is treated as informational unless structural path checks or tracked files show old harness content.

### Requirement: Doc-only changes use doc-only archive

The HU workflow documentation SHALL instruct contributors to archive process/documentation-only OpenSpec changes with `--skip-specs`.

#### Scenario: Process-only change is complete

- **WHEN** a process-only OpenSpec change has completed proposal, design, specs, tasks, review, and HiTL
- **THEN** it is archived with `pnpm openspec archive <change> --skip-specs`.
