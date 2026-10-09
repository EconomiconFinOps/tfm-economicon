JUP: JUP-062

## Context

See proposal.md for the motivation. The memory is edited by several people in one shared document, outside Git. `AGENTS.md` already fixes who owns what (Trello for scope and assignments, OpenSpec for requirements, GitHub for code and documentation) and asks for repository instructions that do not depend on a specific tool. The open change `jup-062-business-memory` already declares the document as the source of truth for the business section; this change generalises that declaration to the whole memory and adds the handling rules.

## Goals / Non-Goals

**Goals:**
- One versioned place where any contributor or tool learns where the memory lives and how to treat it.
- Rules that can be checked by reading the document, with no new tooling.

**Non-Goals:**
- No automation: nothing in CI inspects the shared document, and no check is added for exports.
- No copy of the document's content in the repository.

## Decisions

- **A documentation file plus one pointer line, not a new section of CONTRIBUTING.** `docs/memoria/README.md` holds the rules and `AGENTS.md` gets one bullet under the source-of-truth rules. CONTRIBUTING is about the pull request flow and the memory is not a pull request; `AGENTS.md` is what tools read. Alternative considered: putting everything in `AGENTS.md`, rejected because it would grow a file meant to stay short.
- **A new capability instead of extending `business-memory`.** `business-memory` governs the content of one section and still lives inside an active change. Governing the whole memory's location and handling is a different contract with a different lifecycle. Alternative considered: adding requirements to that change, rejected because it would couple two unrelated closures.
- **No document URL and no assignee names in the repository.** The link lives on the Trello card, which controls who can reach it; assignments change with the rotation and Trello owns them. The map therefore only joins sections to cards.
- **Neutral wording for tools.** The rules speak of "tools and assistants" without naming any, as `AGENTS.md` requires.
- **Authorization is separate for reading and modifying, and per section.** Read access is cheaper to grant than write access, and the memory is a graded deliverable edited by several people.
- **ADR assessment:** no new ADR. This is process documentation, not a durable architecture decision; the source-of-truth choice for the business section is already recorded in `jup-062-business-memory`.

## Risks / Trade-offs

- [The rules drift from the shared document's own style guide] → The document refers to the guide by name instead of copying its text, so the guide stays authoritative.
- [A merge conflict with the open draft that also edits `AGENTS.md` (JUP-101)] → The line is additive and sits in a different section; resolve by keeping both.
- [The section map becomes stale when the team reassigns a section] → It lists cards, not people, so a reassignment does not change it; only a new or merged card does.
