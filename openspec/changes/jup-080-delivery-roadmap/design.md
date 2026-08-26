JUP: JUP-080

## Context

As of August 26, Trello contains 47 P0 cards: 33 Backlog, one Prepared, four In
Review and nine Done. The repository already covers parts of old backlog cards,
so treating all 33 as greenfield work would create false load. Eight weeks
remain before the working delivery date.

The Jupiter brief prioritizes not just implementation but business value,
architecture, DevOps, monitoring, evaluation, team contribution and defense.
Documentation and evaluation therefore run in parallel instead of becoming a
final-week phase.

## Decisions

### Reconcile before implementing

M1 compares old P0 acceptance criteria against current code and evidence. A
covered card closes; a partial card receives a narrow residual scope. This is
not permission to close cards without verifiable evidence.

### Use milestone gates rather than optimistic start dates

Every milestone has a latest completion date and observable exit gate. The JSON
maps every current P0 exactly once so the plan cannot silently omit a mandatory
card. Weekly checkpoints expose drift early.

### Freeze features two weeks before delivery

Functional scope freezes October 9. Memory and evaluation freeze October 16.
The final week is reserved for reproducibility, packaging, demo and corrections.
P1 and P2 cannot displace mandatory evaluation, observability or documentation.

### Distinguish team baseline from institutional confirmation

Discord records October 23 and October 29 as team dates, but the four-page
official brief contains no calendar. The roadmap uses the dates conservatively
and requires confirmation through the campus or tutor before final bulk Trello
updates.

### Keep communications controlled

JUP-080 updates its own Trello evidence as part of the requested work. It does
not send Discord messages or modify due dates on other cards without explicit
authorization and team approval.

## Risks and mitigations

- Thirty-three apparent P0 cards exceed capacity: reconcile overlap in M1 and
  enforce a two-implementation WIP limit.
- A real RAG vertical may reveal provider or retrieval gaps: complete it by M3,
  before UI and release work.
- Memory can exceed 20 pages: maintain it weekly and freeze on October 16.
- Individual grading may lack evidence: update the contribution matrix at each
  weekly checkpoint.
- Dates may change institutionally: rebaseline the JSON once and propagate only
  after approval.

## Rollback

If official dates differ, update the machine-readable dates, milestone table and
Trello proposal in one reviewed JUP-080 commit. Do not silently move individual
cards or weaken required Jupiter deliverables.
