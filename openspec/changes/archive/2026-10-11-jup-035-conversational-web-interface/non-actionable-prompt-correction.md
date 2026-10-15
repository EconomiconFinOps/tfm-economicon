# Non-actionable chat response clarification

Paris approved correction of the isolated full-path failure on 2026-10-11.
The second real response declared no_data but violated the existing prohibition
on metrics or recommendations for non-actionable responses. An external observer
reproduced the backend validation error; this does not establish that the live
backend, rather than the processor validator, was the first rejecting component.

Scope: clarify the versioned chat system prompt for no_data, insufficient_data,
unsupported, refused and error. Require empty metrics and recommendations and
place nonfinancial data-gathering suggestions in next_actions. Update the prompt
fingerprint. Public schema, validation, transport, retries and storage do not change.

Verification: one resource regression first fails on the old prompt, passes on
the corrected bundle, and fails on a valid old-bundle mutation. Reuse existing
invalid-response and period tests. Restart only the isolated service pair so both
load the new fingerprint. Repeat the same browser question as a new request;
retain failed operations and all prior call counters. A successful real response
must finish and persist through the application, not only pass an offline parser.
This remains local developer verification, not independent human validation.
