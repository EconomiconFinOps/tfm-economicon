JUP: JUP-030

## Implementation

- [x] Define strict period, currency, grouping and configurable detection rules.
- [x] Implement deterministic evaluation with decimal arithmetic and honest baseline states.
- [x] Expose the authenticated endpoint using existing billing source protections.
- [x] Return reusable assessments, alert/evidence IDs and explicit quality limitations.
- [x] Document request/response reproduction and the JUP-038/JUP-084 boundaries.

## Verification and delivery

- [x] Run focused unit/API tests, including edge cases and tenant/source failures (150 passed).
- [x] Run applicable integration and repository checks; record versions, results and limitations (997 backend passed, 21 external skips; OpenSpec 56/56).
- [x] Link acceptance evidence, contribution branch and PR #91 from project continuity and Trello.
- [x] Obtain assigned human participation, independent PR review and functional validation. Not pursued: under the temporary exception of 2026-10-11 no human review or validation is requested from other people on GitHub. It is replaced by an independent adversarial review (`review.md`), validation evidence (`docs/evidence/JUP-030-validation.md`) and Lucia's `Human Approval`; it does not certify anyone's participation.
