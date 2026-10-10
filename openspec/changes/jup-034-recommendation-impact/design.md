# Design — JUP-034

Use a pure Decimal calculator behind POST /recommendations/impact/evaluate and
the established get_active_tenant dependency. No body tenant selector and no
provider/database cost access. Caller-supplied provenance is visible in every
report; evidence IDs are references, not server-verified source records.

Monthly baseline minus target is floored at zero; annual repeats the unrounded
monthly difference 12 times. Bounds on decimal text and batch size allow a local
40-digit context independent of ambient precision. Missing pairs stay null.
Observed savings cannot enter the model and are always null in the response.

Greedy descending raw savings with stable ID tie-break chooses disjoint atomic
cost scopes; report every excluded ID and winning alternative. Separate currencies
and reject an overlap represented in two currencies. This algorithm is feasible
under declared scopes, not an optimal portfolio solver. Caller must enumerate
the same atomic keys in every alternative; the server cannot infer overlaps
from natural language or incompatible levels of hierarchy.

See [contract](../../../docs/contracts/recommendation-impact.md) for JUP-033 mapping,
rounding, complete-month assumptions and limitations. Do not reinterpret the
existing period-free processor estimated_savings scalar or demo dashboard.
