JUP: JUP-062
Trello: https://trello.com/c/5sBSKurr

## Why

The project memory is written in a shared Google Doc outside Git, and five Trello cards contribute sections to it. Nothing in the repository says where it lives, who may edit which section, how its review is recorded or how tools that read the repository must treat it. The only declaration is inside the open `jup-062-business-memory` change, and it covers the business section only.

With the memory freeze on the planning calendar close, teammates will start editing their sections and their tooling will read the repository for guidance. The rules need to be versioned before that, not discovered in the document afterwards.

## What Changes

- Declare the memory's editable source (a shared document outside Git), the policy for immutable exports (outside Git, with a SHA-256 manifest) and the prohibition of a second canonical copy in the repository.
- Map each memory section to the Trello card that owns it, without copying assignees or dates, which Trello owns.
- State the editing rules: the document's own style guide, one author per section, suggestions or comments for other people's sections, and traceable sources for every figure.
- State how the review and validation of the deliverable are recorded, given that it has no diff and no GitHub review.
- State the rules for tools and assistants that read the repository, so that the memory is never searched for, regenerated or edited from it without authorization.
- Add `docs/memoria/README.md` as the human-readable version and one line in `AGENTS.md` that points to it.

## Capabilities

### New Capabilities

- `project-memory-governance`: where the final project memory lives, who edits which section, how its review is recorded and how tools must treat it.

### Modified Capabilities

None. The `business-memory` capability, still inside the active `jup-062-business-memory` change, governs the content of the business section; this change governs the whole memory's location and handling and does not alter that content contract.

## Out of Scope

- Writing any section of the memory or changing the Google Doc.
- Reassigning sections once their cards exist; that is a team decision recorded in Trello.
- Moving, deleting or regenerating the dated exports already stored outside Git.
- Changing the `JUP reviews` check or any CI workflow.

## Impact

Adds a new spec and one documentation file, and one bullet in `AGENTS.md` under the source-of-truth rules. No application code, configuration or CI changes. The `AGENTS.md` line is additive and may need a trivial merge with the open draft that also edits that file (JUP-101).
