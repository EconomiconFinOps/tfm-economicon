# JUP-015 design

The [taxonomy](../../../../docs/architecture/tagging-taxonomy.md) is canonical prose;
[JSON](../../../../docs/finops/tagging-taxonomy.json) holds machine-readable syntax.
[ADR-0018](../../../../docs/adr/ADR-0018-tagging-taxonomy.md) records the separation
of format compliance, catalog membership and owner-to-unit mapping.

The reference tool consumes canonical normalized tags, tenant, usage date and
one explicit optional catalog snapshot. It emits per-key defects, minimum-v1
compliance, catalog applicability/membership and a provenance-labeled mapping.
It does not select versions, authenticate approvals, ingest Azure data, calculate
monetary totals or modify consumers. Those are explicit adoption boundaries.

Synthetic catalogs cannot yield organizational approval. Missing/inapplicable
catalogs retain unknown membership rather than silently accepting or rejecting
real-world ownership. Exact identifiers retain case; environment has only the
eight existing allowed spellings. No cross-dimension inference is introduced.

Validation covers boundary values, tenant/date separation, catalog structure,
missing/invalid data, mapping integrity and independent expected examples.
