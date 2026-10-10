JUP: JUP-039
Trello: https://trello.com/c/ojFr6fCU

## Why

FinOps stakeholders need a shareable executive summary of potential savings,
with sources and assumptions, without confusing candidates or hypothetical
scenarios with realized savings.

## What Changes

- Add deterministic executive summaries and an internal provider contract for
  JUP-033 recommendations and JUP-034 impact reports.
- Expose explicit selection through assistant messages and the existing chat
  command `/ahorro YYYY-MM-DD YYYY-MM-DD`.
- Preserve full evidence, separate currencies, bound presentation, retain
  unavailable estimates and avoid summing potentially overlapping benefits.
- Fail explicitly when the upstream provider has not been installed.

## Impact

Backend schemas, service, assistant branch, tests and documentation only.
No LLM calls, infrastructure, migrations, optimization execution or realized
savings measurement. JUP-033/034 are not yet integrated in the baseline. Their
server adapter remains a deployment integration dependency. Four assigned roles
remain Paris leadership, Victor pairing, Alejandro review and Lucia validation;
assignment does not imply participation or acceptance already performed.
