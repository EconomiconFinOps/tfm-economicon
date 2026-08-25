# Architecture Decision Records

This directory contains the project decision log for durable architecture choices. OpenSpec `design.md` captures the technical design of an individual Trello task; ADRs explain decisions that remain relevant across tasks, modules or project phases.

## Naming And Status

- Store records as `docs/adr/ADR-0001-short-slug.md` and increment numbers sequentially.
- Use `Proposed`, `Accepted`, `Superseded` or `Deprecated` as the record status.
- Link the related Trello card, `JUP-XXX` identifier and OpenSpec change.
- Link replacement records whenever an existing ADR is superseded.

## When An ADR Is Required

Create or update an ADR for durable decisions affecting:

- service or application boundaries;
- persistence, queues, vector stores or synchronization;
- authentication, security, identity, permissions or tenancy;
- critical external providers and integration ownership;
- LLM, RAG, agent or FinOps cost architecture; or
- shared patterns affecting several modules or future tasks.

Local implementation details, small refactors and documentation-only changes without architectural impact do not require an ADR. Record `ADR: not applicable` in the OpenSpec change when appropriate.

## Workflow

1. Decide during OpenSpec proposal/design whether the Trello task requires an ADR.
2. Start from `docs/templates/adr.md` and link the relevant `JUP-XXX` card.
3. Link the ADR from the OpenSpec `design.md` and keep its status `Proposed` during review.
4. Once accepted, preserve the decision in Git-tracked documentation and update `docs/architecture.md` if the current architecture changes.
