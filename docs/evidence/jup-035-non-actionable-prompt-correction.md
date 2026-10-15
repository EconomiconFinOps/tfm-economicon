# JUP-035: non-actionable response prompt correction

Date: 2026-10-11. Paris approved the correction after two isolated browser
attempts failed. Developer verification, not independent review or acceptance.
No publication, merge or archive is included.

## Defect and scope

The second real attempt declared no_data but contained metrics or recommendations.
An external observer reproduced `Invalid non-actionable response.` using the
unchanged backend validator. Both operations failed without a partial final answer
in dialogue history. The observer does not establish which live validator rejected
first: the processor also enforces this rule.

The chat system prompt now requires empty metrics and recommendations for
no_data, insufficient_data, unsupported, refused and error. Data-gathering
suggestions belong in next_actions. Only system.md and its manifest fingerprint
change at runtime. Public schema, validators, retries, transport and storage
remain unchanged. The earlier server-owned period correction remains in place.

- System SHA256: `f92dc4213b18abbd310fdd15237d0c943a100f2766f3bbb0be87566fed0039d5`.
- Resource version: `jup-035.chat.v2:cc21eb6fd1d9192a5a062330888cc757a79bb78696f94d45e0b40e6cedb969c4`.

## Automated verification

- Red: the new packaged-resource regression failed on the absent instruction.
- Green: 83 processor tests and 55 backend tests passed. One new case; the rest
  reuse existing suites. Backend reported 1236 SQLite datetime deprecation warnings.
- Mutation: selecting the original valid bundle made the new regression fail.
- OpenSpec strict validation, JUP traceability, hygiene and diff whitespace passed.

Commands run in existing cached test images, without network, with a read-only
checkout, PYTHONDONTWRITEBYTECODE=1 and the service PYTHONPATH:

```text
python -B -m pytest -p no:cacheprovider tests/test_chat_resources_jup035.py tests/test_chat_gateway_jup035.py tests/test_chat_server_period_jup035.py tests/test_chat_context_budget_jup035.py tests/test_chat_private_jup035.py -q
python -B -m pytest -p no:cacheprovider tests/test_chat_server_period_jup035.py tests/test_chat_context_assembly_jup035.py tests/test_chat_operations_jup035.py tests/test_chat_history_final_jup035.py -q
openspec validate jup-035-conversational-web-interface --strict --no-interactive
node tools/jup-check.mjs --change jup-035-conversational-web-interface
node tools/jup-cleanup-check.mjs
```

The new regression guards the prompt and bundle integrity, not model obedience.
The real experiment below supplies behavioral evidence for the observed case.

## Real browser experiment

After restarting only the isolated backend and processor, the same synthetic
question was submitted in a new conversation. Existing failures and call counters
were retained. Browser -> backend -> private processor -> LiteLLM -> OpenRouter
completed, and the browser displayed `Respuesta completada`. The shared gateway
configuration was unchanged. Retrieval used an empty disposable pgvector database
and mock embeddings; chat inference was real.

- Conversation: `91d03e01-f36b-4a35-bd10-38bbdf987094`.
- Operation: `69ddf1a1-c39d-409e-90f2-73b2ee817427`, completed, one attempt.
- Result: `619328d1-4fda-4d48-9e0a-b446ca276448`.
- HTTP 200, finish_reason stop, relay duration 11.457 seconds.
- Stored response: no_data, zero metrics, zero recommendations, four next_actions,
  period null and the new prompt version above.
- CockroachDB contains exactly two messages: user and assistant. The earlier
  failed conversation still contains no dialogue messages.
- New call: 1774 input + 475 output = 2249 tokens, reported USD 0.001618635.
- Three calls including both failures: 6710 tokens, reported USD 0.00470646.
  Conservative EUR reservations do not claim a currency conversion. Zero summary
  inference calls occurred.

Local receipts: calls.json, prompt-fix-real-sql.json, original source snapshot,
and browser captures in the separate validation evidence directory. Secrets and
raw provider responses were not added to Git.

## Limits

This verifies the observed empty-screen case, not every future model output.
Invalid responses still fail closed. The source is an uncommitted snapshot based
on ceb6520 with corrected backend/processor and runtime58 frontend; it is not a
claim about another checkout. Recovery after restart and real compression/reuse
remain separate sequential checks, not completed by this evidence.

## Subsequent phase: restart persistence, 2026-10-11

After the separate user instruction to continue, backend and processor were
stopped, the isolated CockroachDB container restarted, SQL readiness checked and
both application services started again. Before/after SQL snapshots match for
all conversation data and all three operation records. Both failed operations
remain failed; the completed operation retains its result and exactly two
messages without duplication. Successful-history SHA256 remains
`c424edc22613bf3d5b316de793ba2044261edf401588ae6ab6015ba51ae1e649`.

The browser was reloaded and the completed saved request selected from history.
It recovered the original question and full answer. The upstream receipt file
is byte-identical to the pre-restart reference: zero new model calls or spend.
Local receipts: persistence-before.json, persistence-after.json,
persistence-calls-before.json, persistence-result.json and persistence-browser.png.

This checks restart of existing containers, not recreation or backup restoration:
the disposable CockroachDB uses its container writable layer, with no mounted
data volume. No product code was changed. Compression remains untested here.
