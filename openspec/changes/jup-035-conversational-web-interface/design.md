# JUP-035 design

Gateway and provider choice follow ADR-0002 and the JUP-023/JUP-108 deployment.
`CHAT_PROVIDER` is independent of the processor's `LLM_PROVIDER`; mock preserves
development fixtures and is explicitly labelled in the UI. `litellm` uses the
backend key (never upstream OpenRouter/master keys), one bounded attempt and
the configured logical model. The existing retrieval transport's deadline,
response-size and redirect/proxy protections are reused. DNS resolution has the
same non-cancelable system limitation as JUP-022. No automatic retry of paid
generation is added; retry remains explicit in the interface.

The system role carries an interactive adaptation of JUP-024, not its
processing-event prompt or FinOpsResponse envelope. Inputs are JSON data with
no history or tool execution instructions. Each generated statement must supply
one or more source IDs and literal supporting quotes. The backend rejects extra
fields, unknown/duplicate references, nonexistent quotes, newly invented numeric
tokens and fabricated citation markers. It renders citation indices itself.
This verifies provenance, not semantic entailment or truth; JUP-070 human
evaluation remains required. No arbitrary SQL, write tools or model-selected
tenant can execute. Existing JUP-037 selection queries SQL first and supplies
the resulting text as a cost source while retaining the full cost snapshot.

No-context and refused responses use fixed truthful notices. Provider failure
returns a sanitized 503 and never appends an assistant response. The existing
document route persists the user question before retrieval; failed attempts
remain visible in history and retry is a new attempt. No implicit idempotency
or atomic exchange guarantee is introduced. Structured cost failure occurs
before either message is persisted.

RF-087-002's string-versus-JSONB normalization already exists in develop.
Exercise it with real CockroachDB instead of duplicating that correction.
The frontend preserves React/Vite/TSX, routing/auth and data-query ownership
from JUP-095/097/105; no migration or visual framework replacement is needed.

Context limits: 4,000 characters per source, at most 20 sources, 4,000-character
question, 32,000-character model JSON, eight statements, 1,600 output tokens by
default (max 4,096). Truncated context cannot be cited beyond its supplied text.
Replies are escaped React text, with local evidence disclosure links only.
