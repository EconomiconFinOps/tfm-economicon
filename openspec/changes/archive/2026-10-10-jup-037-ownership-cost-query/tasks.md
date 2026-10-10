## 1. Implementation

- [x] 1.1 Contrast card/roles, previous refinement and JUP-036/JUP-015 contracts.
- [x] 1.2 Add bounded schema and deterministic ownership service on billing v2.
- [x] 1.3 Add optional provenance in the same SQL snapshot, preserving defaults.
- [x] 1.4 Integrate authorized conversation persistence and error handling.
- [x] 1.5 Complete chat form and independent evidence presentation.

## 2. Verification and delivery

- [x] 2.1 Execute meaningful schema/service/API and real SQL tests (209 pass).
- [x] 2.2 Execute frontend regressions (35 pass), lint, typecheck and build.
- [x] 2.3 Record per-criterion evidence, limitations and continuity.
- [x] 2.4 Publish draft PR against develop and link Trello evidence (PR100; Trello comment 6ac9ede7d532f7533a85b38d).

Human pairing Lucia, Revision Paris and Validacion Victor remain external gates;
automated checks do not satisfy them. Deployed application/owner data and combined
JUP-036 integration are explicitly unverified, not implementation claims.
