# Compression deadline correction - 2026-10-11

Paris authorized this focused correction and separate Red, Green and mutation
phases after the independent Compose validation. Real repetition belongs to the
independent validator under the remaining authorized budget; no paid call here.

## Observed cause and limits of evidence

The backend scheduler starts a 30-second absolute deadline. Backend submit and
processor envelope admission independently reject deadlines beyond 30 seconds.
The compression ownership lease is 45 seconds. These windows were not updated
when summary output capacity became 10000 tokens. The independent spend receipt
records one summary request lasting 146.203 seconds, consuming 10000 completion
tokens and USD 0.0261016875, while local compression failed and preserved all 14
messages. The receipt cannot prove socket lifetime, provider cancellation, exact
gateway internal timeout behavior or the validity/finish reason of the output.

## Minimal correction

Add SUMMARY_TIMEOUT_SECONDS to the existing settings in both applications:
integer 30..300, default 180 seconds. The complete lot (preparation, private HTTP,
generation, validation and installation) shares one absolute deadline. Backend
submit and processor admission use their configured ceiling; Compose mirrors it.
The compression lease lasts the configured timeout plus 15 seconds, retaining
existing CAS, ownership and uncertain-outcome rules. Expiry remains no proof of
remote settlement. No migration or public/private envelope shape change.

Summary gateway reserves five seconds inside that deadline for downstream
validation/installation. The request's timeout and owned monotonic socket deadline
use the same remaining generation budget. The existing connection/DNS cap stays
five seconds. Chat deadlines, LLM_TIMEOUT_SECONDS, token/byte limits, model,
credentials, retry/fallback policy, quotas and gateway configuration stay intact.
Invalid configuration fails startup through the existing settings validation.

180 seconds accommodates the observed 146-second call with finite local headroom;
it is not a promise of successful or valid model output. Finishing at length,
invalid JSON or unsupported citations still fails existing validators. Local
timeout/cancellation cannot guarantee upstream generation or billing stops.

## Evidence plan

Focal tests check default/bounds, scheduler-to-envelope deadline, matching lease,
authenticated transport/admission above 30 seconds, gateway timeout/headroom,
expiration/cancellation without retry and unchanged chat timeout. Use scripted
loopback responses and controlled time rather than waiting minutes or paying.
Mutations exercise a retained 30-second boundary and missing generation reserve.
Rebuild only backend and processor after review; retain isolated database and
gateway. Validator repeats only compression and compares original messages.

Official references consulted:
- https://docs.litellm.ai/docs/proxy/timeout (per-request timeout)
- https://docs.python.org/3.12/library/urllib.request.html (blocking timeout;
  does not by itself establish an absolute multi-operation deadline)
