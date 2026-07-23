# Adopted — PendingInput / AWAIT (2026-07-23)

**Status**: Adopted, v1.8.0
**Decision by**: igareosh (prichindel.com)
**Source**: split from an external draft submitted for review, proposing
runtime orientation additions to this package. The pending-external-input
/ `AWAIT` portion is adopted here. Its tool/capability-availability
portion is rejected — see
[`REJECTED_RUNTIME_AFFORDANCE_PROJECTION.md`](REJECTED_RUNTIME_AFFORDANCE_PROJECTION.md).

## Why it is in scope

`CONTRIBUTING.md`'s **Review focus** names exactly this kind of change as
welcome:

> Bug fixes where the runtime produces a wrong outcome [...] New guards or
> logic rules that change what the agent does on a single move.

`IDLE` producing a wrong outcome is precisely what this closes. It
conflated two different things: "done, nothing left to do" and "nothing
to do *right now*, but something outside the map is still owed." Those
call for different agent behavior — stop, versus come back later — and
`OutcomeKind.AWAIT` is a new outcome that changes exactly what the agent
does on that single move: wait with named wake conditions, instead of
reading "at rest" and treating a live dependency as closed.

This isn't a novel category for the package, either — `ADV-08` (closed,
2026-07-20) forced the same fix once already, on a different axis:
`requires_human_authorization` created "a pending-decision state that had
nowhere to live" until `pending_authorizations` gave it one.
`PendingInput`/`AWAIT` is that same design applied a second time, to a
genuinely different kind of waiting (an external producer, not a human
decision) — extending an already-adopted pattern, not introducing a new
one.

## What shipped

- `fpf_thinking_map.pending_input.PendingInput` / `PendingInputStatus` — a
  declared external dependency (`EXPECTED`/`PENDING`/`RECEIVED`/`FAILED`/`CANCELLED`),
  with `expected_evidence_ids`, `wake_conditions`, and an opaque `source_ref`
  the core never reads.
- `RuntimeBinding.pending_inputs: list[PendingInput]`, empty by default.
- `ActiveState.unresolved_pending_inputs` — the `EXPECTED`/`PENDING` subset;
  `RECEIVED`/`FAILED`/`CANCELLED` entries stay in the binding as a record
  but drop out of this view.
- `OutcomeKind.AWAIT`, plus `Outcome.pending_input_ids` /
  `Outcome.wake_conditions` (omitted from `to_dict()` when empty).
- `to_llm_prompt_state()["pending_inputs"]` — unresolved entries only, in
  the compact shape the model reasons over: `id`, `label`, `status`,
  `expected_evidence`, `wake_conditions`. No `source_ref`, no resolved
  history — that's an adapter/host concern, not the model's.
- `step()` appends a "pending input unresolved" warning for every
  unresolved entry on every call, regardless of which move is under
  evaluation — same treatment as the existing `pending_authorizations`
  warning, and for the same reason: a still-open dependency elsewhere must
  not be silently buried just because the current move went fine.

## Where the boundary sits

The core:

- exposes pending inputs and lets them shape `AWAIT` vs. `IDLE`;
- does **not** poll, schedule, resolve, or update their status;
- does **not** convert `expected_evidence_ids` into `current_evidence`
  automatically, on any status transition, including `RECEIVED`;
- does **not** infer anything about the producer named by `source_ref`.

All of that stays the adapter's job — the same "computes and surfaces
facts, does not decide policy or run the workflow" line every other
feature in this package draws (`safe_alternatives`, `bridge_options`,
`ADV-*` advisories). A host loop calling `PendingInput.status = ...` after
its own worker/human-reply/webhook resolves is exactly the intended use;
the map does not know or care what triggered that assignment. Keeping the
core this narrow is also why the rejected half of the same proposal
(tool/capability availability) doesn't belong here — see
`REJECTED_RUNTIME_AFFORDANCE_PROJECTION.md` for why that one doesn't clear
the same bar.

## Evaluation order

`AWAIT` sits after `CONTINUE` (candidate actions) and `BRIDGE` in the
no-transition branch, before `IDLE`:

```
no transitions
  → candidate_actions?        → CONTINUE
  → bridge_options?           → BRIDGE
  → unresolved_pending_inputs? → AWAIT
  → else                      → IDLE
```

This order is deliberate and tested (`check_pending_input_await`): a
pending external input must never hide a move or a bridge the model could
take right now instead of waiting.

## Regression guarantee

A map that never populates `RuntimeBinding.pending_inputs` sees zero
behavioral change — `unresolved_pending_inputs` is always empty, the
`AWAIT` branch never triggers, and `IDLE`'s reason string is the only
visible diff (updated to name pending input as a fourth thing it checked
for, not just three). 25/25 verify checks pass; `dev_mcp`'s 38/38 are
unaffected since `attempt_transition`/`attempt_bridge` signatures didn't
change.

See [main README](../../README.md#await--waiting-on-something-outside-the-map-distinct-from-being-done)
for the runtime-facing summary.
