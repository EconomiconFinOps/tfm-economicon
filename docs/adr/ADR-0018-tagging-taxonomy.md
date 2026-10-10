# ADR-0018: Separate tag syntax, catalog membership and organizational mapping

- Status: Proposed
- Date: 2026-10-10
- Related JUP/OpenSpec: JUP-015 / jup-015-tagging-taxonomy
- Trello: https://trello.com/c/UDIyjTyl
- Supersedes: none
- Superseded by: none

## Context

JUP-015 requires five dimensions. JUP-017 already implements minimum-v1 syntax
in PR66 without corporate catalogs. Showback, unassigned spend and ownership
queries must distinguish teams, applications and organizational units. No
approved tenant catalogs were provided or found in the task source.

## Decision

Publish the [canonical dictionary](../architecture/tagging-taxonomy.md) and
machine-readable minimum-v1 contract. Define catalog-v1 as a separate, explicit
tenant/date/version-bound snapshot, with an optional owner-to-unit relationship.
Ship an offline reference verifier and labeled synthetic examples. Leave runtime
adoption to the consuming changes, preserving minimum-v1 results.

Membership requires exact IDs; missing catalog means unverified, not valid or
invalid ownership. An example catalog never certifies corporate assignment.
Approval references are claims to be checked by humans, not trusted authorization.

## Consequences

Consumers can share semantic rules without inventing project/application or
organization/owner aliases. Reproducible examples verify the design independently
of deployment. The project still needs real catalogs, approval and integration
tests. This decision remains Proposed until explicit acceptance is recorded.

## Alternatives considered

- Treat syntax as ownership proof: conflates format with organizational reality.
- Infer entities from project/org names: introduces unsupported equivalences.
- Replace minimum-v1 in PR66: changes an independently owned metric without a
  policy migration or its validation.

## Evidence and follow-up

[JUP-015 evidence](../evidence/JUP-015-validation.md) records the precise checks
and pending human roles. JUP-017's draft ADR-0013 about coverage is a separate
document from the integrated ADR-0013 about pgvector; neither is overwritten.
