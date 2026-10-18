## ADDED Requirements

### Requirement: PR135-only human-authorized pairing and review allocation
For the explicit human authorization of 2026-10-18 only, the checks SHALL allow
Lucia Mateo to pair and review PR135/JUP-126, with Alejandro Aguado as leader and
Paris Arcos Martin as validator. Activation SHALL require authoritative number
135, repository EconomiconFinOps/tfm-economicon, author Iber1to, base develop,
head fix/JUP-126-dismissed-review-titles, matching JUP-126 title/body, exact roles
declared once and this unique visible plain Markdown declaration:

```
- Excepcion puntual PR135: pairing y revision por Lucia Mateo; validacion por Paris Arcos Martin; autorizada por Alejandro Aguado el 2026-10-18
```

The checks SHALL reject use of this declaration for any other PR, repository,
author, branch, base, card or role allocation. A declaration or role inside HTML,
comments, fenced/indented code or multiline code spans SHALL NOT activate it.
For this allocation only, the latest eligible Revision of lmatsan and Validacion
of ParisArcos SHALL supply the required titles. Other historical role titles
SHALL remain published without supplying these allocated roles. The complete
published history SHALL still resolve all requests for changes, including those
from other participants. Author and draft titles SHALL NOT count. A dismissed
latest title SHALL NOT revive an older one, and Comment SHALL NOT lift changes.
The exception SHALL NOT replace either verdict, content acceptance, revalidation
or merge authorization, and SHALL NOT alter rulesets, workflows or permissions.

#### Scenario: Authorized allocation with both verdicts
- **WHEN** the exact PR135 context, roles and visible declaration are present with eligible titled reviews from lmatsan and ParisArcos
- **THEN** both checks accept the authorized allocation without dismissing historical reviews

#### Scenario: Other PR or allocation
- **WHEN** the declaration is copied to another PR or its required identity or roles differ
- **THEN** it does not authorize an exception and the checks reject the declaration

#### Scenario: Hidden authorization
- **WHEN** the declaration exists only inside HTML, a comment or code, including a multiline code span
- **THEN** it cannot activate the exception

#### Scenario: Missing or ineligible assigned title
- **WHEN** either assigned title is absent, pending, dismissed, from the PR author, or replaced by a different participant or card
- **THEN** the review check still fails and names the missing title

#### Scenario: Complementary request for changes
- **WHEN** both assigned titles exist but any participant has a pending decisive Request changes followed only by Comment
- **THEN** the check still fails until that request is properly resolved
