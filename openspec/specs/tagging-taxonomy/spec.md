# tagging-taxonomy Specification

## Purpose
Define the five required cost tags and distinguish syntax compliance, tenant
catalog membership and explicit organizational mapping for JUP-015 consumers.
## Requirements
### Requirement: Versioned minimum tag dictionary

The project SHALL define owner, environment, application, cost_center and project
as distinct required tags with the existing economicon-minimum-v1 syntax rules.
Additional tags SHALL NOT satisfy missing required keys.

#### Scenario: No semantic substitution
- **WHEN** a row has project and organization but lacks application and owner
- **THEN** both missing dimensions are reported and minimum compliance is false

#### Scenario: Invalid format
- **WHEN** a required value is absent, empty, non-text, a marker or invalid syntax
- **THEN** the reference verifier reports its defect without changing source tags

### Requirement: Tenant and date bound organizational catalogs

The project SHALL define an independently versioned catalog snapshot with exact
tenant, half-open validity dates, distinct entity lists, approval status and
explicit owner-to-organizational-unit relationships.

#### Scenario: Different tenant or historical date
- **WHEN** the supplied catalog does not cover the row's tenant or usage date
- **THEN** membership and organizational validity are unverified and no unit is returned

#### Scenario: Example catalog
- **WHEN** a synthetic example matches a row
- **THEN** matching can be demonstrated but organizational validity remains null

#### Scenario: Unknown entity or missing relationship
- **WHEN** a syntax-valid entity is absent from the applicable catalog
- **THEN** the verifier reports unknown membership without changing syntax compliance
- **AND** an absent owner-to-unit mapping never causes a unit to be inferred

### Requirement: Explicit consumer adoption boundaries

The taxonomy SHALL document JUP-017/027/028/037 adoption without claiming their
runtime integration. It SHALL distinguish compliance from attribution, preserve
historical metadata and require tenant/period/currency isolation for cost consumers.

#### Scenario: Multiple defects on one cost row
- **WHEN** a row lacks owner and application
- **THEN** the contract requires consumers to count the row's cost once while
  retaining both reasons, and forbids adding per-reason totals as disjoint spend

### Requirement: Reproducible reference examples

The project SHALL provide an executable reference verifier and synthetic examples
with explicit expected outputs and tests for format, catalogs, tenant and time.

#### Scenario: Required data unavailable
- **WHEN** no approved catalog is available
- **THEN** documentation identifies the limitation and synthetic results do not
  claim production validation or human acceptance
