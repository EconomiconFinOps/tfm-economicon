# Findings Backlog

This directory records technical review findings that need follow-up. Trello remains the source of truth for task ownership, priority and operational status; this file provides versioned technical context and traceability.

## Identifier Convention

Use `RF-<JUP-number>-<sequence>`, for example `RF-082-001`. The number comes from the Trello task in which the issue was found and remains stable after remediation.

## When To Record A Finding

Add a row when a finding is outside the current task, cannot be resolved before review, requires a later team decision, or represents an accepted risk. Link its resolution to the corresponding `JUP-XXX` task.

## Status Values

- `Open`: identified but not yet scheduled.
- `Planned`: linked to a future Trello task.
- `In progress`: actively being resolved.
- `Fixed`: resolved and verified.
- `Accepted risk`: explicitly accepted by the team.
- `Won't fix`: deliberately closed without remediation.

Keep closed findings visible so the technical decision remains auditable.
