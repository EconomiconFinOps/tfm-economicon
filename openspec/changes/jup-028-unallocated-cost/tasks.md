JUP: JUP-028

## 1. Scope And Contract

- [x] 1.1 Read JUP-028 and the available JUP-015/JUP-017/JUP-027 contracts, recording metadata-versus-assignment limits.
- [x] 1.2 Define candidate detection, policy version, disjoint groups, explicit period and protected source scope.
- [x] 1.3 Record the older corpus taxonomy conflict without rewriting that separate source.

## 2. Backend Implementation

- [x] 2.1 Reuse the JUP-017 minimum-tag predicate without integrating unrelated PR functionality.
- [x] 2.2 Add aggregate candidate detection with exclusive signatures and overlapping-source rejection.
- [x] 2.3 Add the authenticated endpoint, response schema and database facade.
- [x] 2.4 Return separate positive charges, signed adjustments and net amounts per currency with decimal precision.
- [x] 2.5 Confirm the final response uses candidate/complete-metadata names and declares financial allocation unevaluated.

## 3. Verification

- [x] 3.1 Verify valid/missing/invalid tags, several defects in one record and diagnostic reasons.
- [x] 3.2 Verify tenant, completed-run and explicit-period isolation using compatible real SQL, recording any test doubles or skips.
- [x] 3.3 Verify overlapping completed sources fail with 409 and no amounts.
- [x] 3.4 Verify credits, zero costs, empty/partial data, multiple currencies, large amounts and display-rounding boundaries.
- [x] 3.5 Verify denied access and invalid/missing dates do not query costs.
- [x] 3.6 Run applicable backend regression, OpenSpec validation and repository governance checks.

## 4. Reviewable Delivery

- [x] 4.1 Record evidence by card criterion, commands, versions and untested limits.
- [x] 4.2 Update continuity and link the implementation and evidence from its pull request.
- [x] 4.3 Record the actual state of pairing, independent review and validation without attributing unverified participation.
