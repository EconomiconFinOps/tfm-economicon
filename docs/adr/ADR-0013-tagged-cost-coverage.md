# ADR-0013: Coverage weighted by positive cost and a versioned tag policy

- Status: Proposed
- Date: 2026-10-03
- Related JUP/OpenSpec: JUP-017 / jup-017-tagged-cost-coverage
- Trello: https://trello.com/c/3wiy5PJS
- Supersedes: none
- Superseded by: none

## Context

Signed net cost can produce undefined or out-of-range coverage when adjustments
cancel spend. The public dataset uses CostCenter/Project/env/org predominantly
and contains no row with all five proposed required dimensions.

## Decision

Require owner, environment, application, cost_center and project under a
versioned explicit validation policy. Weight compliance by positive observed
pretax cost separately per currency; retain signed adjustments and net
reconciliation. Zero positive cost means N/D. Never infer semantic aliases.
The MVP validates identifier syntax and a defined environment vocabulary, not
membership of unavailable corporate catalogs; disclose this limitation.
Future JUP-015 catalogs can supersede this policy with an explicit new version.

## Consequences

Coverage remains bounded and intelligible even at zero or negative net spend.
It measures observed metadata compliance, not verified accounting attribution.
Source aggregation must preserve all five tags. Public fixtures stay intact;
new synthetic controls verify conforming and nonconforming cases.

## Alternatives Considered

- Divide by signed net cost: distorted percentages and zero denominators.
- Count any tag or tagged rows: technical tags and cheap rows mask costly gaps.
- Treat organization as owner and project as application: unsupported semantics.

## Evidence And Follow-up

User approval is recorded in the OpenSpec proposal; no approval is attributed to
Paris. [FinOps allocation guide](https://www.finops.org/wg/cloud-cost-allocation/)
motivates organization-specific metadata compliance. Operational evidence and
catalog follow-up are in [JUP-017 evidence](../evidence/JUP-017-validation.md).
