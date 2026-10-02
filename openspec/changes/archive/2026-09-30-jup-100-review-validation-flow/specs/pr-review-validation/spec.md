## Purpose

Define what each rotating role does and how a pull request is reviewed, validated and merged, so that everyone knows what is expected of them and what has actually been checked. Make the rules reach every contributor and their local tooling through an enforced check and repository instructions.

## ADDED Requirements

### Requirement: The four rotating roles are defined
`CONTRIBUTING.md` SHALL define each of the four rotating roles (leadership, pairing/co-authorship, PR review, and validation/tests/documentation). For every role it SHALL state what the role does, at which step of the flow, what it delivers as a result, and what does not belong to it. It SHALL state that when a role is reassigned, the PR description (Participacion section) and the Trello card are updated.

#### Scenario: Each role is fully described
- **WHEN** a contributor reads the roles section of `CONTRIBUTING.md`
- **THEN** each of the four roles lists what it does, when, what it delivers and what it does not do

#### Scenario: A role changes hands
- **WHEN** a person other than the one assigned in Trello takes over a role
- **THEN** `CONTRIBUTING.md` tells them to update the PR description and the Trello card

### Requirement: Review and validation are two separate titled reviews
Review and validation SHALL be published as two separate GitHub reviews on the pull request. The review body SHALL start with `Revision JUP-XXX` for the review and `Validacion JUP-XXX` for the validation, where `JUP-XXX` is the PR's identifier. Title matching SHALL ignore letter case and accept both the unaccented and the accented forms (`Revision`/`Revisión`, `Validacion`/`Validación`).

#### Scenario: Both reviews present
- **WHEN** a PR for JUP-100 has a review starting with `Revision JUP-100` and another starting with `Validacion JUP-100`
- **THEN** both the review and the validation are considered published

#### Scenario: Accented or lowercase titles
- **WHEN** the reviews start with `Revisión JUP-100` and `validación jup-100`
- **THEN** they are recognised as the review and the validation

#### Scenario: Title for another card
- **WHEN** a PR for JUP-100 has a review starting with `Validacion JUP-026`
- **THEN** it does not count as the validation of that PR

### Requirement: Review states follow the target branch
Towards `develop`, the first of the two reviews to be published SHALL be a Comment when it finds no problem, and the second SHALL be an Approve only when both are satisfied and nothing blocking remains. Towards `main`, which requires two approvals, both reviews SHALL be Approve when satisfied. Any problem SHALL be published as Request changes, and a Request changes review SHALL include what is still pending from the other review, so that reading only the latest review is enough. A Comment SHALL NOT lift a Request changes: once the changes are addressed, whoever requested them approves, or the request is dismissed with a reason.

#### Scenario: First review towards develop
- **WHEN** the validation is published first on a PR towards `develop` and finds no problem
- **THEN** it is a Comment that states the review is still missing

#### Scenario: Problem found by the second review
- **WHEN** the second review finds a problem and the first one had pending requests
- **THEN** it is a Request changes that lists its own requests and the pending ones from the first

#### Scenario: Release pull request
- **WHEN** both reviews are satisfied on a PR from `develop` to `main`
- **THEN** both are Approve

### Requirement: Distinct people with declared exceptions
Review and validation SHALL be done by the people assigned in Trello, who are different people. If exceptionally the same person does both, the PR description SHALL declare it explicitly, and that person SHALL still publish two separate reviews. Neither review SHALL come from the PR author.

#### Scenario: Same person without declaration
- **WHEN** the same person publishes both reviews and the PR description does not declare the exception
- **THEN** the flow is not satisfied

#### Scenario: Same person with declaration
- **WHEN** the same person publishes both reviews and the PR description declares the exception
- **THEN** the flow is satisfied

#### Scenario: Participation reflects the same person in both roles
- **WHEN** the PR description names the same person for PR review and validation, declares the exception, and names two other different people for leadership and pairing
- **THEN** the role traceability check (`JUP policy`) accepts it, and without the declaration it still requires four different people

#### Scenario: Exception declared with different names
- **WHEN** the exception line is present but the PR description names different people for PR review and validation
- **THEN** the role traceability check rejects the pull request as incoherent

#### Scenario: Exception line not shown as plain text
- **WHEN** the exception line only appears inside an HTML comment (closed or not), a fenced or indented code block
- **THEN** it does not count as a declaration

#### Scenario: The exception never covers leadership or pairing
- **WHEN** the person who reviews and validates is also the leader or the pairing, even with the exception declared
- **THEN** the role traceability check rejects the pull request

#### Scenario: Review by the author
- **WHEN** the PR author publishes a review titled `Revision JUP-XXX`
- **THEN** it does not count as the review

### Requirement: Validation leaves evidence per criterion
The validation SHALL check each acceptance criterion of the Trello card against the running PR branch and SHALL record, per criterion, what was done and what was observed. It SHALL list what was not validated and the limitations of the evidence, and SHALL NOT mark as validated anything that was not tested.

#### Scenario: Criterion that could not be tested
- **WHEN** a criterion cannot be checked in the available environment
- **THEN** the validation lists it as not validated with the reason, instead of marking it as met

### Requirement: Reviewers do not push to the branch
Neither the review nor the validation SHALL push commits to the PR branch, because a push dismisses existing approvals. Findings outside the PR scope SHALL be requested from the leader in the review text.

#### Scenario: Out-of-scope finding during review
- **WHEN** the reviewer finds a pre-existing defect outside the PR scope
- **THEN** the review asks the leader to register it, and the reviewer does not commit it

### Requirement: Every source of feedback is read
Whoever addresses requested changes or decides to merge SHALL read all reviews, the PR conversation comments and the inline comments on the diff, not only the latest review.

#### Scenario: Blocking request in an inline comment
- **WHEN** a request for changes was left only as an inline comment on the diff
- **THEN** it is treated as pending until resolved

### Requirement: Merge only when reviewed and validated
Any team member MAY merge a pull request, but only when it has both titled reviews and nothing pending. When "Update branch" brings changes from the base branch that touch the same files or areas as the PR, a revalidation of what is affected SHALL be requested before merging.

#### Scenario: Merge with only one review
- **WHEN** a PR has the review but not the validation
- **THEN** it is not merged

#### Scenario: Base changes overlap the PR
- **WHEN** "Update branch" brings changes to files the PR also modifies
- **THEN** a revalidation of the affected criteria is requested before merging

### Requirement: The flow is enforced by a required check
A required CI check named `JUP reviews` SHALL run on pull requests towards `develop` and `main` whenever the PR is opened, updated or edited and whenever a review is submitted, edited or dismissed. It SHALL read the current reviews from GitHub rather than from the triggering event. It SHALL pass only when:
- a review titled `Revision JUP-XXX` and a review titled `Validacion JUP-XXX` exist for the PR's identifier, neither from the PR author (reviews on earlier commits and dismissed reviews still count as published);
- no reviewer's latest decisive review (Approve, Request changes or a dismissal of their review) is a Request changes; a dismissed review leaves that reviewer without a current decision, so an older request does not come back;
- if the same person published both, the PR description declares the exception.
When it fails, its message SHALL say what is missing and link to the flow in `CONTRIBUTING.md`. If the reviews cannot be read, the check SHALL fail rather than pass.

#### Scenario: Validation missing
- **WHEN** a PR has only the titled review
- **THEN** the check fails with a message naming the missing `Validacion JUP-XXX` review and linking to CONTRIBUTING

#### Scenario: Pending request for changes
- **WHEN** both titled reviews exist and one reviewer's latest decisive review is a Request changes
- **THEN** the check fails and says changes are pending

#### Scenario: Request changes later approved
- **WHEN** a reviewer who requested changes later approves
- **THEN** that request no longer blocks the check

#### Scenario: Approval dismissed by a push after a request for changes
- **WHEN** a reviewer requested changes, later approved, and that approval was dismissed by a push
- **THEN** the older request for changes does not block the check

#### Scenario: Exception line hidden in an HTML comment
- **WHEN** the exception line only appears inside an HTML comment of the PR description
- **THEN** it does not count as a declaration

#### Scenario: Reviews from an earlier commit
- **WHEN** both titled reviews were published before the latest push
- **THEN** the check still counts them, and GitHub's own dismissal of stale approvals decides whether a new approval is needed

#### Scenario: Reviews cannot be read
- **WHEN** the GitHub API call fails
- **THEN** the check fails with an explanatory message

### Requirement: The rules reach local tooling
`AGENTS.md` SHALL state, without naming any specific assistant, the flow rules that the check cannot verify (evidence per criterion and what was not validated, no pushes by reviewers, first review as Comment towards `develop`, reading every feedback source, revalidation after overlapping base changes, merge only with both reviews) and SHALL ask anyone using local tooling to review, validate or merge to align it with `CONTRIBUTING.md`. `AGENTS.md` and `CONTRIBUTING.md` SHALL contain the same `Process version` line, and a governance test SHALL fail if they differ. The pull request template SHALL include a checklist of the flow and SHALL state that its Validacion section holds the leader's evidence, not the validation role's review.

#### Scenario: Process version drift
- **WHEN** the `Process version` line in `AGENTS.md` differs from the one in `CONTRIBUTING.md`
- **THEN** the governance test fails

#### Scenario: New pull request
- **WHEN** a contributor opens a pull request from the template
- **THEN** the description contains the flow checklist and the clarification about its Validacion section
