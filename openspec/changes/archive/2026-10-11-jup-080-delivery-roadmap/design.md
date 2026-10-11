JUP: JUP-080

## Context

The initial August 26 capture contained 47 P0 cards: 33 Backlog, one Prepared,
four In Review and nine Done. The August 28 reconciliation contains 50 P0 cards
after adding JUP-085, JUP-086 and JUP-087. The repository already covers parts
of old backlog cards, so treating the backlog as greenfield work would create
false load. Eight weeks remain before the working delivery date.

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
maps every P0 in its dated snapshot exactly once. Weekly checkpoints compare
that snapshot with Trello to expose scope drift. The September 2 check found
52 P0 cards: JUP-090 and JUP-091 are outside the August 28 snapshot and have no
milestone or due date recorded on their cards. JUP-080 must reconcile their
assignment before claiming full current-board coverage; this documentation
update preserves the historical 50-card snapshot and does not invent dates.

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

- The historical 33-card P0 backlog exceeded capacity: reconcile overlap in M1 and
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

## Reconciliation on 2026-10-11

The dated DockerServer integration snapshot contains 65 P0 cards (54 Done,
11 open). Preserve the historical 50-card snapshot in the JSON and extend
the unique milestone mapping: 084 to M3, the eleven frontend cards
090/091/092/093/094/095/098/099/103/104/105 to M4, and 109/110/111 to M6.
This is scope reconciliation, not a claim that past gates were met on time.

Keep an explicit recovery plan for open P0 only. Product integration precedes
testing and robustness, which precede evaluation conclusions and the submission
candidate. Due-date writes must compare the live card with the expected prior
state and produce a readback receipt. Completed cards retain historical dates.

The user's specific authorization replaces the JUP-080 human roles with
independent subagents; record their actual verdicts without impersonating team
members. It does not confirm campus dates or waive academic participation.
Institutional confirmation and operational activation remain explicit pending
conditions until a documented decision resolves them.

## Calendar activation completed — 2026-10-11

The user confirmed delivery23/10 and defense29/10 in this chat. This is
user-supplied confirmation, not independent access to the campus. All eleven
recovery dates were applied through the deployed DockerServer integration and
read back; other fields and92 other cards were preserved. Receipt:
`docs/evidence/JUP-080-calendar-activation.json`. This resolves the pending
conditions above without claiming that future product milestones are achieved.
