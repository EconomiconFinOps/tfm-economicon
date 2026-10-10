JUP: JUP-035
Trello: https://trello.com/c/BJfABykd

## Why

The web chat retrieves documents but answers with a template. The processor's
JUP-024 generation does not serve interactive conversations. The 08/10 card
expansion assigns the missing retrieval → model → cited reply to this task.

## What Changes

- Add an opt-in backend chat provider using the existing LiteLLM/OpenRouter
  gateway, its backend virtual key and the approved logical model alias.
- Adapt JUP-024 system policy to interactive answers; require individual
  supported statements with literal evidence, validate source membership and
  numeric tokens, abstain without evidence and fail closed on provider errors.
- Preserve JUP-025 document citations and JUP-037's tenant-scoped cost tool;
  use the latter's immutable result as evidence for generated cost prose.
- Persist claim/evidence metadata, distinguish mock mode, improve accessible
  loading/empty/error states and responsive layout, and bound user input.
- Exercise JUP-069 and record outcomes with model/mocks clearly distinguished.

## Capabilities

### New Capabilities
- `conversational-generation`: evidence-grounded interactive answers.

## Impact

Backend configuration, chat service/routes, frontend conversation components,
Compose, tests and operator documentation. No dependencies, auth scheme,
tenant boundaries, CI policy or processor runtime changes. JUP-036 is not
integrated in the starting develop: no copied branch implementation or invented
subscription/service tool. JUP-037's explicit selection remains its adapter.

User authorization 10/10: implement the leadership functions while preserving
Paris's Trello role. Technical work is performed under this request; no pairing,
review or validation by the named team members is inferred. Roles remain
Paris/Victor/Alejandro/Lucia. Independent review of this contribution remains
necessary; its author cannot review it independently.
