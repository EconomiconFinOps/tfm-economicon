# Findings Backlog

This folder tracks review findings that need follow-up after a HU review.

The HU `review.md` remains the audit record for what was found during a specific change. `openspec/findings/backlog.md` is the operational backlog for findings that are open, planned, in progress, fixed, accepted as risk, or explicitly not fixed.

## When to Add a Finding

Add a row to `backlog.md` when a review finding is:

- out of scope for the current HU,
- unresolved at HiTL final,
- deferred to a later HU,
- accepted as risk,
- useful to track until a later decision.

In-scope findings that are fixed before HU closure can remain only in the HU `review.md`, unless the reviewer or approver wants central tracking.

## ID Convention

Use:

```txt
RF-<hu-number>-<sequence>
```

Examples:

```txt
RF-004-001
RF-004-002
RF-005-001
```

The ID is based on the HU where the finding was discovered. It does not change when the finding is planned, fixed, or closed.

## Status Values

- `Open`: accepted into the backlog, not yet planned.
- `Planned`: expected to be handled by a future HU/change.
- `In progress`: currently being fixed.
- `Fixed`: resolved and verified.
- `Accepted risk`: consciously accepted by a human approver.
- `Won't fix`: explicitly closed without fixing.

## Closure Rules

- Do not delete closed findings.
- Fill `Change/Fix` when a finding is handled by a HU/OpenSpec change.
- A finding outside HU scope does not block closure if it is documented in the review, added to the backlog, has an action, and the human approver accepts deferring it.
