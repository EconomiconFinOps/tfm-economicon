JUP: JUP-066

## Context

The official brief sets 10–20 minutes and active participation by every member.
The existing JUP-065 package budgets seven minutes and still requires an
integrated rehearsal. Shared memory remains outside Git under its own governance.

## Decisions

- Use an 18-minute main schedule and a 15-minute shortened schedule. Both
  preserve the demo and all four speakers; actual duration remains unmeasured.
- Keep the script and its documentary checks in `docs/presentation/JUP-066/`
  and `docs/evidence/`, with references rather than copies of the memory or brief.
- Pin PR63 at `48ee74250714c6fe50946906824b80dc9ffd59fa`. Reference its seven-minute
  flow without importing another card's branch or altering its generated data.
- Use explicit offline/live/recorded modes. A missing rehearsal defaults to an
  honest offline walkthrough, never to presumed successful product execution.
- Preserve the known deterministic response implementation in base `c2995a1`:
  a configured embeddings gateway is not evidence of generative chat.
- Leave personal contributions and human approvals pending. The separate
  contributor branch is handed to leadership, not presented as their authored PR.

## Risks and validation

Memory, demo and evaluation can change while the script is reviewed. The sources
file fixes versions and lists divergences, including pending memory sections,
historical provisional mock results and unconfirmed dates. Before final use,
refresh affected claims with their owners and execute the rehearsal sheet.
Document checks cover links, arithmetic, provenance and governance; they do
not replace timing, audience comprehension, individual participation or runtime.
