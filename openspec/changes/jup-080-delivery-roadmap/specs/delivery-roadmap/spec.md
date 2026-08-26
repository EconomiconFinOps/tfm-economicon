## Purpose

Define a complete, testable delivery plan from the current backlog through the
Jupiter documentary delivery and final defense.

## ADDED Requirements

### Requirement: Complete P0 coverage
The roadmap SHALL assign every current P0 Trello card to exactly one milestone
without treating existing implementation as absent.

#### Scenario: Existing capability overlaps a backlog card
- **WHEN** current code and evidence satisfy all acceptance criteria
- **THEN** the team reviews and closes the card instead of reimplementing it

### Requirement: Protected delivery dates
The roadmap SHALL reserve October 9 for code freeze, October 16 for memory and
evaluation freeze, October 23 for documentary delivery and October 29 for the
defense.

#### Scenario: Product work slips after code freeze
- **WHEN** optional or P1 scope threatens a protected freeze
- **THEN** optional scope is removed before evaluation, observability or documentation

### Requirement: Jupiter brief traceability
The roadmap SHALL include explicit gates for a functional GenAI MVP, vector
storage and retrieval, model API, CI/CD, Docker, observability, architecture,
business value, evaluation, individual contributions, memory and defense.

#### Scenario: Milestone appears complete without an official deliverable
- **WHEN** a required Jupiter deliverable lacks reproducible evidence
- **THEN** the milestone remains open even if its implementation cards are merged

### Requirement: Bounded work in progress
The team SHALL keep no more than two implementation P0 cards and one
documentation/evaluation card in progress simultaneously.

#### Scenario: A fourth card is proposed
- **WHEN** the WIP limit is full
- **THEN** the team finishes, blocks or returns an active card before starting another

### Requirement: Controlled calendar activation
The project SHALL distinguish team working dates from institutional confirmation
and SHALL NOT apply bulk Trello due dates before roadmap approval.

#### Scenario: Draft roadmap passes automated tests
- **WHEN** technical validation completes but team approval is absent
- **THEN** JUP-080 may enter review while all other card dates remain unchanged
