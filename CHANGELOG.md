# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Narrative version of this arc, if you want the story instead of the
list: [`docs/deep/EXPANDED_PROVENANCE.md`](docs/deep/EXPANDED_PROVENANCE.md).

## [Unreleased]

### Planned

- Traversal checkpoint and restore — `ActiveState.checkpoint()` /
  `ActiveState.from_checkpoint()`, `SemanticMap.fingerprint()`. Design
  finalized, not yet implemented. See
  [`docs/deep/DESIGN_TRAVERSAL_CHECKPOINT.md`](docs/deep/DESIGN_TRAVERSAL_CHECKPOINT.md).

## [1.9.1] - 2026-07-23

### Fixed

- **`AuthorizationReceipt` expiry** ("the tower's clock"): `expires_at_step`
  was checked against `ActiveState.step_count`, which only advances on
  `step()` — never on `attempt_transition()`/`transition_to()` firing. A
  caller whose workflow only calls `attempt_transition()` got no
  time-based expiry at all: issue two receipts against the same state,
  fire one, fire an unrelated transition back to a fingerprint-identical
  state purely through fires (zero `step()` calls anywhere), and the
  second, never-consumed receipt would still validate. Found via
  adversarial testing against the live engine, not design review.
  Fixed with `ActiveState._authorization_clock`, a counter dedicated to
  receipt freshness that ticks on both `step()` and every successful
  fire — deliberately not merged into `step_count`, which stays scoped to
  evidence TTL decay so this fix doesn't also make evidence go stale
  faster as a side effect.

## [1.9.0] - 2026-07-23

### Added

- **`MoveIntent` / `inspect_move()`** ("Tail Number"): `TransitionPrimitive`
  names a reusable move *type* ("publish"); `MoveIntent` now names one
  concrete proposed move (`move_id`, `transition_id`, `parameters`,
  `requested_by`, `binding_revision`, `parent_move_id`), distinct from
  it — the type/instance conflation `WorkPrimitive`'s own docstring
  already warns against elsewhere in this package.
  `ThinkingMapTraversal.inspect_move(state, intent)` evaluates one
  without firing anything, a thin wrapper over the no-mutation `step()`
  path that already existed. `MoveTrace.move_id`/`parent_move_id` are
  stamped on a successful fire.
- Found during implementation, not in the original design: an intent
  naming a transition other than the one that actually fired is not
  stamped into `trace` (would corrupt lineage with an unrelated move's
  identity) — and `attempt_transition()` surfaces this as a `warnings`
  entry rather than absorbing it silently.
- Deliberately not shipped: `MoveIntent.parameters` does not reset the
  stagnation visit-key. Asserted directly in `check_move_intent`, not
  left as an accident of omission.

See [`docs/deep/EXPANDED_MOVE_INTENT.md`](docs/deep/EXPANDED_MOVE_INTENT.md).

## [1.8.0] - 2026-07-23

### Added

- **`PendingInput` / `OutcomeKind.AWAIT`** ("Holding Pattern"): `IDLE`
  used to mean two different things — "done, nothing left to do" and
  "nothing to do *right now*, but something outside the map is still
  owed." `PendingInput`/`PendingInputStatus` declare an external
  dependency with `wake_conditions`; `AWAIT` fires when nothing else is
  actionable and one is still unresolved. A candidate action or a bridge
  elsewhere still wins over `AWAIT` — waiting never hides an available
  move. The core never polls, schedules, or resolves the dependency;
  status is host/adapter-owned.
- Same design pattern `ADV-08` already forced for
  `pending_authorizations`, applied a second time to a different kind of
  waiting (an external producer, not a human decision).

See [`docs/deep/EXPANDED_PENDING_INPUT_AWAIT.md`](docs/deep/EXPANDED_PENDING_INPUT_AWAIT.md).

### Rejected (reviewed alongside this release, not shipped)

- Runtime affordance/tool-availability projection into every `slice()` —
  by its own design it never changes `can_fire` or any computed outcome.
  See [`docs/deep/REJECTED_RUNTIME_AFFORDANCE_PROJECTION.md`](docs/deep/REJECTED_RUNTIME_AFFORDANCE_PROJECTION.md).
- Mandatory orientation-revision metadata in every `slice()`/
  `to_llm_prompt_state()` call — same reasoning, same rejection. See
  [`docs/deep/REJECTED_ORIENTATION_VIEW_PROJECTION.md`](docs/deep/REJECTED_ORIENTATION_VIEW_PROJECTION.md).

## [1.7.0] - 2026-07-23

### Added

- **`AuthorizationReceipt`** ("Clearance"): `authorized=True` proved *a*
  human said yes, not that they said yes *to this state* — a TOCTOU gap
  named but explicitly left untested in the Ignition Lock wind-tunnel
  writeup. `AuthorizationReceipt` binds an approval to one `transition_id`
  and a hash of the exact state (context, current_state, evidence) it was
  issued against. `attempt_transition()`/`transition_to()` independently
  re-verify transition identity, state fingerprint, expiry, and prior
  consumption before spending one — rejected outright, with a specific
  reason, on any mismatch. `authorized=True` still works for callers who
  haven't migrated.

See [`docs/deep/IGNITION_LOCK_WIND_TUNNEL.md`](docs/deep/IGNITION_LOCK_WIND_TUNNEL.md#2026-07-23-update)
for how this closes (and doesn't close) that document's own stated gaps.

## [1.6.0] and earlier

See [GitHub Releases](https://github.com/igareosh/fpf-agentic-thinking-map/releases)
and [`docs/deep/ADOPTED_IGNITION_LOCK.md`](docs/deep/ADOPTED_IGNITION_LOCK.md).
