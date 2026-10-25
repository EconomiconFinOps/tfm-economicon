JUP: JUP-062

## Context

The linked `Memoria_Economicon` Google Doc is the team's collaborative draft.
Its August 28 export contains six PDF pages, within the 20-page official limit.
Only the introduction and business case contain substantive prose; later
sections are placeholders owned by other JUP cards.

The business case already states a plausible problem and product direction, but
an evaluator cannot yet verify the segment hypothesis, operating viability,
expected impact, cost envelope or principal risks. The contract must strengthen
those areas without inventing market validation or evaluation results.

## Decisions

### Keep one editable source and immutable review snapshots

Google Docs remains the editable source of truth because it supports the four
authors and preserves the existing layout. At meaningful review checkpoints,
the team exports both PDF and Markdown to `materiales/06-entregables/` using an
ISO date in the filename. PDF proves pagination and layout; Markdown supports
diffable content review. A SHA-256 manifest identifies the exact reviewed
files.

### Allocate pages explicitly

The complete memory has a hard maximum of 20 pages. The introduction plus
business case has a working budget of four pages, including tables and
footnotes. Exceeding the working budget requires a documented trade-off with
another section; exceeding 20 pages is never acceptable.

### Separate facts, hypotheses and future results

External numerical claims cite a named primary source, publication date and
sample size when applicable. The initial target segment and product-market fit
remain hypotheses until user or market validation exists. Expected impact is
written as a measurable objective; it is not reported as achieved before the
evaluation cards produce evidence.

### Use a compact business-case structure

The reviewed section follows this order:

1. Opportunity and problem.
2. Target users and current alternative.
3. Market evidence and bounded segment hypothesis.
4. Value proposition and differentiation.
5. Technical, operational and economic viability.
6. Expected impact and measurement plan.
7. Costs, assumptions and risks.

### Tie business claims to the MVP

The business section describes only the Azure public-dataset MVP currently on
the roadmap. It must not imply live tenant integration, automated savings,
forecasting or production readiness that the technical evidence does not
support.

### Use the card's rotating roles as review gates

- Lucia Mateo leads the business narrative.
- Paris Arcos Martin pairs and coauthors.
- Victor Mendez reviews content and coherence.
- Alejandro Aguado prepares validation, evidence and documentation.

No role is recorded as completed without a review comment, document history,
commit or other attributable evidence.

## Risks and mitigations

- Unsupported market claims weaken the 10% business score: cite primary
  sources or label the statement as a hypothesis.
- The collaborative document can drift from evidence: export dated snapshots
  at each formal review.
- Placeholder sections can inflate pagination late: enforce the page budget at
  weekly checkpoints.
- Business promises can outrun the MVP: reconcile wording against merged code,
  tests and the delivery roadmap.
- Provider and hosting costs can change: report assumptions and dated evidence
  rather than a false fixed total.

## Rollback

If the team chooses a different collaborative editor, update the source link
and snapshot process in one reviewed JUP-062 change. Preserve already-reviewed
exports and their hashes; do not silently replace historical evidence.
