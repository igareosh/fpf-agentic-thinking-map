# Architecture

Current visual index for the thinking-map runtime and its public demos.

## Quick links

- [Repo architecture doc](../ARCHITECTURE.md)
- [Live demos](./demos/)
- [v1.9.1 — Three live traces](./demos/three-runs.html)
- [Core step() cascade — Single Trace](./demos/single-trace.html)

## Module chain

- `primitives.py` — 10 primitives + 5 floors
- `authorization.py` — state-bound, expiring, single-use approval receipts
- `pending_input.py` — declared external dependencies and wake conditions
- `move_intent.py` — concrete move identity and lineage
- `state.py` — binding + active state + slice
- `guards.py` — 9 hard constraints
- `logic.py` — 6 operators + rules
- `traversal.py` — step engine + 11 declared outcomes
- `examples.py` — 8 shipped scenarios
- `verify.py` — 26 deterministic checks

## Runtime contract

`step()` inspects the active state and returns a compact, bounded outcome:

- where the agent is
- what can fire
- what is blocked
- what evidence is missing or stale
- whether the runtime should act, bridge, wait, or rest

`inspect_move()` evaluates one concrete `MoveIntent` without mutation.
`attempt_transition()` is the explicit write path: it rechecks evidence,
gates, guards, and any required `AuthorizationReceipt` before changing state.

`PendingInput` keeps unresolved external work distinct from completion:
`AWAIT` means the host still owes the runtime something; `IDLE` means nothing
actionable or unresolved remains.

The model stays free to generate and compare. The runtime keeps movement
legality, authorization, waiting, and trace identity explicit.
