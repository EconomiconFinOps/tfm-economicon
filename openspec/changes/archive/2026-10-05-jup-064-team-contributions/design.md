# JUP-064 contribution evidence design

## Context

Trello owns assignments; GitHub owns commits and review history. The deliverable
is evidence for the project memory, not a replacement backlog or merge gate.

## Decisions

1. Use the deployed Economicon TrelloClient through SSH and its Docker container.
   Never call Trello directly from the workstation. GitHub is read with `gh api`.
2. Store a reduced snapshot of public technical identifiers, roles and evidence
   URLs. Exclude credentials, emails, source conversations and review bodies.
3. Keep all four member rows on every open JUP story, including missing actions.
   Join PR by title/branch JUP identifiers, not incidental mentions in the body.
4. Separate recorded actions from structured current-role indicators. Title,
   identity, review state and HEAD checks cannot certify review content or pairing.
5. Keep test/doc artifacts and checks at PR level with no personal attribution.
6. Record source drift and refresh time. A cut is sequential and historical;
   repository and Trello changes during collection may require another refresh.

## Risks and limits

Archived cards, commits outside PR, external docs and Trello pairing comments
are not imported. The manual table holds original links for human contrast.
GitHub author matching excludes unknown identities. Declared coauthors are
recognized by exact normalized team names, and remain declarations. The leader
archives the change in the branch before opening the pull request, as
CONTRIBUTING requires; review, validation and integration follow in Trello.

## Validation

Offline fixtures challenge incorrect story titles, absent actions, stale SHA,
self-review, role drift, declared coauthors and comments after requested changes.
A live capture plus deterministic offline regeneration checks the whole path.
