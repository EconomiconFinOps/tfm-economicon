# JUP-023: technical review history

- Date: 2026-10-02.
- Branch: `feat/JUP-023-litellm-openrouter`.
- HEAD/base: `5a54ce2ed9001dfb9d4b9d8e06eae84cffe91124`, plus uncommitted changes.
- Current scope: complete uncommitted JUP-023 implementation, tests and evidence.
- Reviewer: automated internal technical review, not Alejandro's human review.
- Current result: **REVIEW_PASS and local QA_PASS**, combining full-change review,
  affected re-review and final local QA. F1/F2 closed; human gates pending.
  Earlier focused results below are historical, not current full-change approval.

## Evidence and finding

See [validation evidence](../../../docs/evidence/JUP-023-validation.md) for
commands, Red/Green, mutations, preserved records, actual counts and limits.
The processor regression remains 433 passed / 57 skipped; gateway/governance
checks passed 31 tests. Those are overlapping suite results, not new tests.

One low-severity observation concerned the README assertion that both privacy
controls were independently necessary. The implementation owner clarified
source inspection, the surviving HTTP flag-removal mutant, and detection by
the direct logging helper at ERROR. The read-only documentation recheck passed
on 2026-10-02 with no new findings; this observation is addressed.
No code or test change followed the focused review.

Known limits: callback failures in runtime are fail-open; initializer probes
are not HTTP startup tests; direct known-cost preservation is not real billing
or DB cost recovery. The Windows relay does not validate the published port.
The simulated gateway does not validate OpenRouter or processor persistence
with real embeddings. No production fallback or failure-row deletion is enabled.

## Process and recovery

Current CONTRIBUTING has no Process version; the user-adopted local workflow
is `2026-09-30 (JUP-100)`, not evidence of remote rule activation. Export roles:
Paris leads, Victor pairs, Alejandro reviews and Lucia validates. Actual
participation remains to be confirmed; automated results are not participation.
Both `Revision JUP-023` and `Validacion JUP-023` are pending. No PR exists for
this work and no remote checks or approvals are claimed.

Implementation, tester and focused read-only review boundary checks passed.
The later README-only clarification lacked a dedicated pre-edit snapshot.
Comparison against the existing earlier snapshot showed only that README
changed, with product and tests unchanged. Paris explicitly authorized using
that comparison on 2026-10-02 to complete documentation and QA. This records
the exception; it does not claim a retroactive snapshot or final QA approval.
Operational recovery details remain outside the repository.

## Validation and approval

- Focused documentation recheck: passed, with no file changes by the reviewer.
- Focused QA: passed with the approved documentation-recovery exception on
  2026-10-02; read-only boundary check passed. OpenSpec 37, traceability 9,
  hygiene 727 files and 16 local links checked. No blocking findings.
- QA's nonblocking Python-attribution note is corrected in the evidence:
  the earlier host executions used 3.10.11. A subsequent isolated run on
  CPython 3.12.13 passed 433 tests, skipped 57, without repository changes.
  Additional temporary gateway checks demonstrated budget/revocation/expiry
  denial and privacy; these new preflight results are not a final QA verdict.
- Full JUP-023 validation: pending a successful mandatory real smoke with
  pgvector. Paris attested team agreement and effective limits/prices were
  checked; the first real-provider request returned HTTP 400, as recorded below.
- Final human approval: pending; no approver or approval timestamp recorded.
- No real spend, PR, commit, push, merge, archive or tracker update authorized
  by this documentation recovery. Keep the no-PR-before-real-smoke condition.

## Subsequent real-smoke diagnosis

On 2026-10-02 a separate read-only internal reviewer inspected the failed real
smoke and temporary runner. This is neither final full-change review nor human
validation. It established no concrete cause for HTTP 400; temporary routing
restrictions remain an unproven candidate. No model calls or file changes by
the diagnostic reviewer; its role guard passed.

Low-severity diagnostic observation: the temporary runner asserted success
before exporting SpendLogs, so cleanup removed the disposable failure metadata.
Owner: smoke-runner owner. Addressed in the expressly authorized single-call
diagnostic replay: one failure row's allowlisted metadata was retained before
cleanup, with classification before unconditional sanitization. Do not infer a product retention defect or enable raw
logging. The unsuccessful real smoke remains a delivery blocker independently
of this diagnostic observation. No final QA or publication approval is implied.

The subsequent read-only diagnostic recheck confirmed that the emitted
`request_parameter` category also matches generic `invalid_request_error`;
the particular marker and parameter remain unknown. It must not be reported
as a confirmed parameter defect or proof of upstream contact. The second call
also returned HTTP 400. Privacy checks passed within the checked scope, cleanup
completed, and the review guard reported no edits. No further calls were made
by that reviewer. Final QA, successful real validation and human reviews remain
pending; see the updated validation record for counts and accounting limits.

## Authorized technical-message diagnostic review

Targeted read-only review on 2026-10-02, checkpoint `technical-message-review`,
guard PASS with no changed paths. The fourth run captured `ExportLimitError`:
GLM grammar export exceeded 262144 intermediate states. The offending field is
unknown; this does not prove the JSON Schema invalid. Earlier generic errors
must not be retroactively assigned this cause without evidence.

Medium in-scope acceptance blocker: the submitted schema is rejected by the
real provider. Owner: Paris/implementation. A simpler provider-facing schema
is a proposed remedy, not a demonstrated fix. Enumerate constraints moved to
local enforcement and obtain agreement before changing the transmitted schema;
preserve FinOpsResponse 1.0, full local validation, models and privacy. Do not
disable structured output or add fallback merely to obtain a successful call.

Receipt privacy checks, failure-row retention, revocation and cleanup passed
within their checked scope. Official observed usage zero is not final billing
proof; USD 0.40 reservations remain held. No model calls by reviewer, no human
approval, no full-change QA or publication. See the validation record.

## Approved DeepInfra amendment review

2026-10-02, working tree on feat/JUP-023-litellm-openrouter, HEAD/base 5a54ce2.
Internal targeted reviewer: REVIEW_PASS for endpoint amendment only, no blocking
config/test-change findings. Only primary chat selects deepinfra/fp4 and requires
parameter support; full schema, privacy, models and other aliases unchanged.
Reused Node 7 passed, Docker 19 checks/10 rows, two detected routing mutants.
Reviewer guard deepinfra-evaluation-review PASS with zero changed paths; no
tests/model calls by reviewer. Not a human review or full-change approval.

Acceptance remains incomplete: one real chat passed full local validation but
a prior invalid_response is unexplained. Embedding HTTP 200 did not establish
vector validity, persistence or job completion: absent cost fields stopped the
temporary runner. Official usage USD 0.001992921; the later USD 0.000000240
embedding attribution is inferred. Earlier 8/10 SpendLogs observation remains
unresolved, not claimed fixed. No final QA, publication or closure.

Focused documentation QA on the same working tree: QA_PASS, no blocking
inconsistency between review, evidence and pending tasks. Reused current strict
OpenSpec 37 passed and traceability PASS; hygiene 727 files, whitespace check
and 10 local links passed. Guard deepinfra-evaluation-qa PASS, zero changes.
No paid calls, Docker or new tests by QA. Full acceptance remains BLOCKED on
verifiable real vector dimensions/persistence and completion of affected
validation plus full review/QA. No final human approval or publication.

## Real-smoke continuation ready for full review

2026-10-02: authorized temporary accounting repair passed 8/8 offline probes;
the next bounded real smoke passed (exit 0). Original FinOpsResponse validation,
finite 1536-dimensional embedding, actual pgvector persistence and completed
SQLite job were observed. Tester guard `embedding-accounting-smoke` passed,
no repository changes. This supersedes the missing real-smoke gate, not previous
review history or unresolved limitations. See the [updated evidence](../../../docs/evidence/JUP-023-validation.md#successful-real-smoke-and-accounting).

Official aggregate cost is USD 0.002591308 under the unchanged USD 0.40 upstream
cap. The embedding's positive usage delta matches tokens/pricing; attribution is
inferred, not an individual invoice. SpendLogs recorded zero for that embedding,
so virtual-key cost coverage is not established. Full technical review must
assess that discrepancy and all approved implementation paths. Full QA, final
human approval and human reviews remain pending; no publication authorization.

## Full-change review after real smoke

2026-10-02, same HEAD/base and uncommitted working tree. Internal reviewer returned
REVIEW_FAIL; guard `full-change-post-smoke-review` passed with zero changed paths.
Reviewed stdlib transport, factories, configuration/limits/retries, strict output
and vector validation, typed ingestion/worker failures, callback, Compose,
routing, changed tests and evidence. No tests, model calls, code edits, commits
or publication by the reviewer. Reused the recorded Python 3.12 433 passed / 57
skipped, simulated integration, Node 7, governance 24 and mutation results.

1. **F1, medium, in scope, blocking QA:** real embedding SpendLogs recorded zero
   for 12 tokens despite positive official usage USD 0.000000240. No post-call
   virtual-counter evidence demonstrates accounting/enforcement; seeded exhausted
   budget tests do not establish accrual. This conflicts with the inherited
   [virtual-budget requirement](../jup-078-llm-provider-adr/specs/llm-provider-routing/spec.md).
   Owner: Paris/implementation. The upstream cap and official reconciliation
   bounded the smoke; no overspend is alleged. Fix or explicit exception required.
2. **F2, low, in scope:** current-status wording in README/design still described
   compatibility as wholly unproven. Addressed by marking historical design and
   linking the limited successful smoke, without claiming reliability or hiding
   F1. Spec-planner guard `budget-accounting-proposal` and coder README-only guard
   `smoke-status-readme` passed. This does not resolve F1.

No additional blocking code defects were found. Accepted runtime callback
fail-open behavior, initializer-only startup proof, prior unexplained invalid
chat and the unreproduced 8/10-row observation remain explicit limitations.

Read-only diagnosis in the pinned image reproduced missing embedding pricing:
the exact OpenRouter embedding model is absent from the included price map;
12 tokens calculate zero without pricing and USD 0.000000240 with supported
explicit `model_info` rates. This proves local calculation, not DB counter or
denial enforcement. Guard `budget-accounting-diagnosis` passed without edits.
The narrow [correction proposal](proposal.md#pending-embedding-budget-correction-approval)
is **PENDING HUMAN APPROVAL**. No tariff/max-price setting or tests were changed.

Proposal checks: strict OpenSpec 37/37, traceability and whitespace passed.
No final QA PASS is issued while F1 is unresolved. Final human approval,
Alejandro's review, Lucia's validation, publication and integration remain
pending and distinct from these internal checks.

## Approved F1 correction ready for re-review

Paris approved the exact embedding rates and price ceiling on 2026-10-02,
without changing the upstream cap. Configuration and README updated; existing
Node/Docker tests extended with zero new permanent cases. RED reproduced zero
spend and unintended third-call admission. GREEN Node 7/7; Docker 25/25 checks,
actual counter accrual and structured budget denial without upstream contact.
The test's message-based classifier was corrected to require the preserved
`error.type`; the privacy callback is unchanged. Two configuration mutants caught.

Exactly one authorized real embedding (no chat/retries) then passed original
finite1536 validation; SpendLogs, actual key counter and official usage increment
all equal USD 0.000000240. Accumulated official usage USD 0.002591548; no cap change.
See [full correction evidence](../../../docs/evidence/JUP-023-validation.md#embedding-budget-correction).
Tester/coder guards passed, cleanup complete. Accounting is asynchronous;
denial after accrual is not a guarantee against last/in-flight-request overshoot.
Earlier unsuccessful tests and TEMP preparation failure are retained in evidence.
This evidence does not itself change the review verdict or establish human QA.

## Final technical re-review

2026-10-02, same HEAD/base and uncommitted branch. Internal reviewer returned
REVIEW_PASS based on the prior full-change review plus the budget correction.
Guard `embedding-budget-final-review` passed with zero changes/violations.
F1 closed: correct units, actual virtual-counter accrual, structured budget
denial with no upstream increment, and real cost/counter/official-use agreement.
F2 closed: current status distinguished from historical plans. Tests, model calls,
commits and publication were not performed by the reviewer.

F3 low, nonblocking, evidence wording: "No new paid calls ... in this correction"
contradicted the recorded authorized embedding. Orchestrator clarified that no
additional calls occurred beyond that one replay; no test/result changed.

Remaining limits: asynchronous accounting can overshoot a cap on last/in-flight
requests; derived prices are not invoices; prior SQLite/pgvector evidence is not
Cockroach/RabbitMQ E2E or reliability proof. Accepted callback and historical
observation limits remain. QA may proceed. Final human approval, required human
reviews and publication are separate and still pending.

## Final local QA and post-QA gate

2026-10-02: internal QA returned QA_PASS; `embedding-budget-final-qa` guard PASS,
zero changed paths/violations. Acceptance/evidence, approval history, cost totals,
skips and residual limits checked. Strict OpenSpec 37, traceability 9 changes,
hygiene 727 files, whitespace and 26 local links passed; `dod -Stage qa` PASS.
No new behavioral suite, paid call, Docker or unrelated build was run by QA.

F1/F2 are closed and F3's wording is corrected. Durable status updates after
this verdict do not change tested product/configuration/tests. Internal QA does
not replace Alejandro's review, Lucia's validation or recorded real participation.

Post-QA human decision: **PENDING**. No final approver or approval timestamp
recorded. The approval of the pricing correction was pre-code, not post-QA.
No commit, push, PR, merge, archive or Trello update was authorized or performed.

## Develop reconciliation review

2026-10-02: user-authorized local update from `5a54ce2` to `11d63ea` (JUP-100,
PR #56) completed by fast-forward. HEAD, develop and origin/develop agree;
29 pending local files retained identical hashes, with no conflict. The incoming
21-file governance delta does not alter product behavior or overlap JUP-023.

Internal incremental reviewer: REVIEW_PASS, no new findings; read-only guard
`develop-reconciliation-review` PASS. Prior behavioral and mutation evidence
remains applicable, with its recorded limits. No new implementation, tests,
Docker, model requests or human reviews occurred during reconciliation.
The next gate only repeats affected policy/CI/governance, OpenSpec, traceability,
hygiene and documentation checks; it does not repeat unrelated accepted work.

Process source is now merged CONTRIBUTING.md/AGENTS.md at `11d63ea`, version
`2026-09-30 (JUP-100)`. Earlier references to PR #56 as open describe history.
Paris leads, Victor pairs, Alejandro reviews and Lucia validates; actual human
participation and separate reviews remain pending, as does final human approval.
The known archive-order clarification remains for a future authorized archive,
not this local reconciliation. No publication, delivery merge, tracker update
or archive is authorized. See [reconciliation evidence](../../../docs/evidence/JUP-023-validation.md#develop-reconciliation).

Incremental QA completed on 2026-10-02: QA_PASS, policy 57 / CI 10 / governance
13 tests passed; strict OpenSpec 38, traceability 9 changes, hygiene 736 files,
whitespace and 16 local links passed. The evidence records exact commands and
resolved sandbox EPERM limitations. QA-stage DoD and read-only guard
`develop-reconciliation-qa` passed. No new behavioral run, Docker or model call;
prior functional results retain their original scope. Final human approval and
human review/validation remain pending. This note records, not extends, QA.

## PR publication authorization

2026-10-02: Paris requests "publica PR" after the reconciliation QA result.
This authorizes committing the prepared JUP-023 change, pushing its task branch
and opening a non-draft pull request against develop for review and validation.
It does not authorize delivery merge, OpenSpec archive, Trello updates or further
paid calls. The real-smoke requirement before publication has been met within
the documented scope. Remote CI, actual human participation, Alejandro's
`Revision JUP-023` and Lucia's `Validacion JUP-023` remain pending. Publication
authorization is not recorded as final human acceptance or either human review.

## PR 65 HTTP Timeout Correction

2026-10-02, HEAD `9fe836e` plus local correction. All live PR feedback
was read. Alejandro's Revision and Lucia's Validacion both request changes on
the attempt timeout; neither request is resolved by this internal review. See
[correction evidence](../../../docs/evidence/JUP-023-validation.md#pr-65-http-timeout-correction).

Paris approved the local correction/tests and explicitly limited the work to
the PR requests, excluding an added DNS cancellation mechanism. Internal
incremental reviewer: REVIEW_PASS, no actionable in-scope findings. Reviewed
client blob `4175f2edfaad90e327c3c69c6b117fac565b19fc` and test blob
`84a1e7bf3f25ea22fa00276c44475b420d82274a`. Review covers socket/TLS/header/body
deadline, cleanup including proxy tunnels, error classification and retries.
Independent slow CONNECT/TLS probes pass; read-only guard passes with no edits.
Red: 4 fail/1 pass. Green: 5 focused tests pass, full processor 438 pass/57 skip;
3/3 targeted mutants killed. OpenSpec 38, traceability 9, hygiene 736 and Node
7+80 checks pass. Evidence maps commands, results and skipped checks.
System DNS remains non-cancelable, without a full DNS-inclusive time guarantee
or inferred human acceptance. No real-provider/Docker validation repeated.
Incremental QA: QA_PASS; strict OpenSpec, traceability, hygiene, whitespace,
relevant links, unchanged product/test blobs, read-only guard and QA-stage DoD
passed. No blocking local findings. Post-QA human gate: PENDING; approver and
approval timestamp not yet recorded. Publication authorization remains separate.

Process remains CONTRIBUTING 2026-09-30 (JUP-100): Paris leadership, Victor
pairing, Alejandro review, Lucia validation. Their affected human reviews and
post-QA approval remain pending, as does separate authorization to publish the
fix. No commit, push, merge, archive, tracker update or paid call in this phase.

## Authorized Real Revalidation Of Timeout Correction

2026-10-03: Paris authorized exactly one real primary chat and one embedding,
zero retries, unchanged budgets/privacy and current corrected client. See
[real revalidation](../../../docs/evidence/JUP-023-validation.md#real-revalidation-after-timeout-correction).
Chat HTTP 200 passed strict FinOpsResponse guardrails in 4.672 s. Embedding
HTTP 200 took approximately 1 s, but the temporary accounting helper stopped
before vector validation with `cost_mismatch`. Two requests, 793 reported tokens;
new official aggregate delta 0.000738787 USD at cleanup, with embedding billing
unresolved. Do not call this a complete real-validation PASS or a proven product
regression. No additional paid attempt; no product/test changes. Cleanup and
tester read-only guard passed. Prior internal code review remains applicable;
human Requests changes and post-QA approval remain pending.

Read-only accounting follow-up at 23:52:38 UTC reconciled the embedding delta
0.000000240 USD and total new aggregate spend 0.000739027 USD, with no additional
model call. The temporary helper stopped on an intermediate aggregate mismatch;
its exact observation was not retained. Vector validation still did not run and
cannot be recovered from the receipt, so the two-operation result remains partial.

2026-10-03 authorized follow-up: the temporary checker was corrected and passed
10 offline checks; one additional embedding, no chat/retries, passed actual
adapter validation (1536 finite values, 0.516 s, 12 tokens). SpendLogs, virtual
counter and official aggregate delta matched 0.000000240 USD after 173.641 s.
Cleanup/privacy and tester guard passed with no repository edits. See
[single embedding recheck](../../../docs/evidence/JUP-023-validation.md#authorized-single-embedding-recheck).
This completes the missing real-provider check alongside the earlier successful
chat without rewriting the partial run. Existing product review remains valid;
human review/validation, publication and post-QA approval remain separate gates.

### Correction Publication Authorization

2026-10-03: incremental evidence QA returned QA_PASS, no findings; reviewed
product/test hashes, links, whitespace, read-only guard and local QA-stage DoD
passed. Paris then requests "publica los cambios", authorizing a commit and
push of these eight prepared files to the existing PR #65. No additional code,
paid call, human review, merge, archive or tracker action is authorized.
The existing human Requests changes still require their authors' revalidation
and approval; publication is not their acceptance or delivery closure.
Remote refs were refreshed before publication: the task branch remains at
`9fe836e`, while develop has JUP-050/JUP-021 at `d6fc408`. Base reconciliation
and its affected checks remain pending before integration; this publication
preserves exactly the reviewed and live-tested product/test blobs.

### Local Develop Reconciliation

2026-10-03: Paris authorized incorporating current develop. Automatic merge of
`d6fc408` into `59fcea2` imports JUP-050 and JUP-021 without conflicts or edits
to the incoming files. JUP-023 product/test blobs, including the timeout fix,
remain unchanged. Existing processor suite: 448 passed, 57 skipped; affected
Node suites: 135 passed. OpenSpec 40, traceability 9, hygiene 763 and whitespace
passed. No new product code, tests, Docker execution or paid calls.

Internal incremental REVIEW_PASS: no blocking compatibility findings; tester
and reviewer read-only guards passed. See the commands and limitations in
[reconciliation evidence](../../../docs/evidence/JUP-023-validation.md#develop-reconciliation-2026-10-03).
Process and human assignments remain unchanged. Both human Requests changes
on PR #65 still require reassessment by Alejandro and Lucia. Publication,
PR merge, archive and tracker updates are not part of this local reconciliation.
