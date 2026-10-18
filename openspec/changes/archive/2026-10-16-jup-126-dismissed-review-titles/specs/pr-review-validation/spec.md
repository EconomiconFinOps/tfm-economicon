## MODIFIED Requirements

### Requirement: The flow is enforced by a required check
A required CI check named `JUP reviews` SHALL run on pull requests towards `develop` and `main` whenever the PR is opened, updated or edited and whenever a review is submitted, edited or dismissed. It SHALL read the current reviews from GitHub rather than from the triggering event. It SHALL pass only when:
- a review titled `Revision JUP-XXX` and a review titled `Validacion JUP-XXX` count for the PR's identifier, neither from the PR author; for each person and review kind only the latest published title SHALL count, and a dismissed latest title SHALL supply no role and SHALL NOT revive an older title;
- no reviewer's latest decisive review (Approve, Request changes or a dismissal of their review) is a Request changes; a dismissed review leaves that reviewer without a current decision, so an older request does not come back;
- if the same person supplies both counting titles, the PR description declares the exception. Dismissed titles SHALL NOT create an overlap.
When it fails, its message SHALL say what is missing and link to the flow in `CONTRIBUTING.md`, and in GitHub Actions it SHALL also show each error as an annotation in the checks panel. If the reviews cannot be read, the check SHALL fail rather than pass.

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
- **WHEN** both latest titles were published before the latest push and neither is dismissed
- **THEN** the check still counts them, without proving current-SHA acceptance or replacing the assigned roles and required revalidation


#### Scenario: Dismissed validation and complementary review
- **WHEN** one person has a dismissed validation title and a non-dismissed review title, while other people supply the required titles
- **THEN** that dismissed validation does not create a same-person overlap

#### Scenario: Latest title dismissed
- **WHEN** a person's latest title of a kind is dismissed after an earlier title of the same kind
- **THEN** neither title supplies that role and the check reports it missing unless another eligible person supplies it

#### Scenario: Fresh title after dismissal
- **WHEN** a person publishes a new non-dismissed title after a dismissed title of the same kind
- **THEN** the new title can supply that role, while pending requests for changes still block

#### Scenario: Reviews cannot be read
- **WHEN** the GitHub API call fails
- **THEN** the check fails with an explanatory message
