JUP: JUP-062
Trello: https://trello.com/c/5sBSKurr

## Why

The official Jupiter brief requires a complete technical and business memory of
at most 20 pages. The business case represents 10% of the deliverables score
and must justify opportunity, market, impact, viability and differentiation.

The current Google Docs draft is a useful six-page baseline: it covers the
problem, intended audience and central value proposition, but it does not yet
substantiate business viability, expected impact, costs or risks. Several
market assertions also need a primary source or must be presented as
hypotheses instead of facts.

## What Changes

- Define the linked Google Doc as the editable source of truth for the memory.
- Store dated PDF and Markdown snapshots in `materiales/06-entregables/` for
  reproducible review.
- Set a four-page working budget for the introduction and business case while
  preserving the official 20-page hard limit for the complete memory.
- Require explicit coverage of opportunity, users, market evidence, value
  proposition, differentiation, viability, impact, costs and risks.
- Require traceable sources for external claims and distinguish evidence,
  assumptions and hypotheses.
- Record content review, technical coherence and real contribution by the four
  team members before the card leaves review.

## Capabilities

### New Capabilities

- business-memory: governed, reviewable business section for the Jupiter
  project memory.

### Modified Capabilities

- None.

## Out of Scope

- Writing the architecture, AI, DevOps, evaluation or contribution sections
  owned by JUP-060, JUP-061, JUP-063, JUP-064 and JUP-067 through JUP-071.
- Claiming customer validation, measured impact or production economics before
  those results exist.
- Setting a commercial price or committing to a production hosting provider.
- Replacing the collaborative Google Docs editing workflow with a second
  canonical copy in Git.

## Impact

Adds a versioned content contract, a dated baseline audit and explicit review
gates. The memory itself remains collaborative in Google Docs; immutable
exports remain outside Git with the other final deliverables.
