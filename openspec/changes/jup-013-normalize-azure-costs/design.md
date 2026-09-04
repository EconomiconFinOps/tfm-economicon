JUP: JUP-013

## Context

Azure Cost Query returns aggregated columns selected by each request. JUP-077
validates those dynamic columns and persists non-core values in JSON. The public
dataset includes EA and FOCUS names for the same concepts, and explicitly warns
that casing and serialized tags vary. A useful common record must normalize
names while preserving source values and optionality.

## Decisions

### Extend the existing record instead of creating another pipeline

`NormalizedCostRecord` remains the single boundary between the client and
CockroachDB. Known aliases are promoted; unrecognized values remain in
`dimensions`. This keeps JUP-076/077 idempotency and failure semantics intact.

### Model aggregation sparsity explicitly

Azure returns only requested groupings. Billing account, subscription name,
resource group, service, project and consumption are therefore nullable. The
scope subscription remains a required repository column supplied by the path,
not copied from an optional response grouping.

### Normalize aliases, not source spelling

EA, FOCUS and Query aliases map to one field. Text is trimmed but its spelling
and case are preserved. Tag keys become stable snake-case names; values remain
source values. The canonical hash uses promoted fields, so equivalent alias
names with equivalent values produce the same hash.

### Require a complete consumption pair

Quantity and unit are both optional, but one without the other is rejected.
Finite zero and negative quantities are retained because adjustments are valid
in the public fixture, just as zero and negative costs are retained.

### Evolve storage in place

Migration 003 adds nullable typed columns and a non-null JSON tag object,
backfills fields available in old `dimensions`, and creates indexes for scope,
resource group and service. The original JSON remains for unknown dimensions.

## Risks and mitigations

- A query omits a dimension: keep the field null and never infer it.
- Provider schemas use different aliases: normalize the audited EA/FOCUS set
  and reject conflicting aliases in one row.
- Legacy tag serialization is malformed: parse valid key/value pairs
  tolerantly and preserve recognized content.
- Migration loses prior demo rows: use additive columns and backfill only nulls.

## Rollback

The code can stop reading the new columns while the additive database columns
remain harmless. No destructive down migration is provided because removing
columns would discard evidence and violates the project's migration policy.
