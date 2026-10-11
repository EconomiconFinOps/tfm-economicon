# JUP-035: server-owned response period

Local correction, 2026-10-11. Approved direction: server manages scope.period;
the provider does not generate it. This isolated implementation is not merged,
published, or an independent human review/acceptance of JUP-035.

## Changes

- Processor projects the chat provider schema without scope.period and rejects
  unsolicited provider periods. Full public FinOpsResponse 1.0 is unchanged.
- Backend derives response_period from successful billing verification records:
  one distinct valid UTC interval, otherwise null. Multiple intervals are not
  combined. Invalid verified intervals fail closed.
- Processor fills period from the authenticated, frozen backend context before
  full validation; backend verifies equality before completing the operation.
- Resource manifest fingerprints the provider schema and server-period policy;
  both services use the actual provider schema for token-budget accounting.
- Existing ingestion providers, financial query filters, endpoints and stored
  histories are unchanged. New images must carry the matching resource bundle.

## Verification

Commands use existing Docker test images, the isolated checkout mounted at
/workspace, networking disabled and PYTHONDONTWRITEBYTECODE=1.

Processor image: economicon-jup035-processor-final-dev59:20261010.

```text
python -m pytest -p no:cacheprovider tests/test_chat_server_period_jup035.py
# Red: 3 failed, including actual gateway rejection of a periodless response.

python -m pytest -p no:cacheprovider tests/test_chat_server_period_jup035.py tests/test_chat_gateway_jup035.py tests/test_chat_resources_jup035.py tests/test_chat_context_budget_jup035.py tests/test_chat_private_jup035.py -q --tb=short
# Green: 82 passed.
```

Backend image: economicon-jup035-mock-backend-packaged-tests:20261010.

```text
python -m pytest -p no:cacheprovider tests/test_chat_server_period_jup035.py tests/test_chat_context_assembly_jup035.py tests/test_chat_operations_jup035.py tests/test_chat_history_final_jup035.py -q --tb=short
# Green: 55 passed; inherited SQLite datetime deprecation warnings remain.
```

Five new tests; existing fixtures were adapted to the provider's periodless
response while preserving assertions about complete public responses. Initial
regression had 12 failures from old provider fixtures still including period;
these are not product failures silently ignored. After stronger assertions,
targeted processor tests passed 4/4 and backend/context tests 15/15; these overlap
the 137 tests above and are not additional unique tests.

Two isolated mutations were detected: replacing the trusted period with null
failed two processor assertions; disabling backend period comparison failed its
rejection test. Original product files were not changed by mutation overlays.

OpenSpec strict validation and JUP traceability passed. This correction does not
claim independent review, production deployment, or real database persistence.

## Real E5 replay

Same frozen synthetic E5 messages and model configuration; actual corrected
processor gateway invoked LiteLLM/OpenRouter with the new provider schema.
One initial request returned HTTP429; a bounded subsequent request succeeded.
Response: stop, status ok, one evidence entry, server period null; unchanged
backend validation functions accepted the assembled response in memory.
Duration 13.539 seconds; 3791 input + 430 output = 4221 tokens;
reported cost 0.0029064375 USD. Full response content was not retained.

Safe result is in the local investigation artifact e5-real-period-fixed7/
real-result.json. The successful replay does not exercise backend HTTP or a real
database write. Those paths were covered here with existing local test fixtures,
not claimed as real-service acceptance. Shared budget reconciliation must retain
the separate HTTP429 uncertainty and asynchronous key-meter settlement.

The independent unauthorized-evidence finding remains out of scope; this fix
does not make arbitrary model output acceptable. No PR, merge or archive done.
