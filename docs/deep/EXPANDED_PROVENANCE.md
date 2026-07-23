# Expansion — Provenance (v1.7.0–1.9.1, 2026-07-23)

This document is the humble version of the release notes, same job
`ADOPTED_IGNITION_LOCK.md` does for v1.6.0: what shipped, why, how it was
tested, and no claim about what it becomes next. Three separate
mechanisms shipped across four version bumps in one day; this is the
throughline connecting them, not a fourth mechanism of its own.

## The throughline

Ignition Lock (v1.6.0) answered one question: *is this caller allowed to
fire this move.* Everything in this release answers a different, older
question underneath it: *can the map actually account for what happened,
to what, and when* — three gaps that all turned out to be the same shape
of problem wearing different clothes.

- An approval that doesn't name *which exact state* it was given for
  isn't really an approval — it's a rumor that a human said yes to
  something, once, at some point.
- A transition that doesn't name *which concrete proposal* fired it
  can't tell "publish report-v3 to the public" apart from "publish
  report-v4 to a regulator" — both are just `"publish"`.
- A clock that only ticks when someone happens to look isn't a clock —
  it's a snapshot that gets mistaken for one.

Three fixes, one word for what they have in common: **provenance** —
being able to say, after the fact, exactly what was approved, exactly
what was proposed, and exactly when, instead of a good-faith account
that happens to usually be right.

## Why now — this is a correctness property of the runtime, not a trend follow

The reason for each mechanism is internal to the logic and traversal
layer, not external to it. Before this release, the runtime itself could
not represent three distinctions that its own state actually contains:
which exact state an approval was checked against, which concrete move
fired versus which type of move it was, and whether the traversal is
finished versus merely blocked on something outside it. Those are gaps
in what the runtime can *say about itself* — a soundness question, the
same category as a wrong gate decision or a guard that doesn't enforce.
Closing them makes the traversal layer more trustworthy and reliable on
its own terms, independent of which model or which surrounding tooling
is driving it.

- **Clearance** closes a replay/TOCTOU hole in the runtime's own state
  representation: `authorized=True` recorded that *a* human said yes, not
  *to what*. That's a logic defect — an ambiguity the traversal itself
  couldn't resolve — before it's anything about any particular caller.
- **Tail Number** closes an identity gap: the runtime could name a
  transition *type* but not the concrete move firing it, so two
  materially different moves were indistinguishable in the trace and in
  stagnation detection. That's a loss of information the runtime itself
  was responsible for, not a model behavior question.
- **Holding Pattern** closes a state-space gap: `IDLE` had to mean both
  "finished" and "blocked on something outside the map," which is two
  different facts compressed into one value. A runtime that can't
  distinguish those two isn't fully describing its own state.

None of this depends on what any particular LLM or harness happens to
do with the extra structure. A model that ignores a receipt, invents a
`move_id` inconsistently, or never reads `AWAIT` gets exactly the outcome
it would have gotten before this release — the fix is in what the
runtime can express, not a bet on model behavior. That a well-built
caller *can* now supply and consume this structure correctly is a
welcome side effect, not the reason it exists: the reason is that the
logic layer is more precise and more honest about its own state than it
was a day earlier, for any LLM reading it.

## What shipped

| Working name | Mechanism | Version |
|---|---|---|
| **Clearance** | `AuthorizationReceipt` — an approval scoped to one transition and a hash of the exact state it was issued against, not an ambient `authorized=True` boolean | v1.7.0 |
| **Holding Pattern** | `PendingInput` / `OutcomeKind.AWAIT` — waiting on a declared external dependency, distinct from `IDLE`'s "done, nothing to do" | v1.8.0 |
| **Tail Number** | `MoveIntent` / `inspect_move()` — a concrete proposed move's own identity and parameters, distinct from its reusable `TransitionPrimitive` type | v1.9.0 |
| — | `AuthorizationReceipt` expiry rebound to a dedicated clock after an adversarial find | v1.9.1 |

The working names aren't a fourth primitive and don't appear in the
runtime's own vocabulary — `AuthorizationReceipt`, `PendingInput`,
`MoveIntent` are the real names, the ones in the code and the ones a map
author actually writes. The names above exist for the same reason
"Ignition Lock" does: so the shape of the idea sticks before the field
list does.

**Clearance** is the right word for what `AuthorizationReceipt` actually
is — not a signature, a *clearance to do one specific thing under one
specific set of conditions*, revoked the instant those conditions
change, by construction, not by policy. **Holding Pattern** because
`AWAIT` is exactly that: not stuck, not done, circling on a declared
condition until it resolves. **Tail Number** because a transition_id is
the aircraft *model* — every `"publish"` looks the same on the manifest —
and a `MoveIntent` is the specific one that actually flew, with its own
identity and its own parameters, however many identical-looking
transitions of that type ever fire.

## Where this sits in the general map

None of the three needed a new kind of primitive to exist. `Clearance`
extends the exact pattern `pending_authorizations`/`denied_authorizations`
already used — visible, persisted bookkeeping instead of a silent void —
to a second question (not just *was this asked*, but *what, exactly, was
approved*). `Holding Pattern` extends the same pattern `ADV-08` already
forced once, to a second kind of waiting (an external producer, not a
human decision). `Tail Number` corrects a conflation the library already
had a name for elsewhere — `WorkPlanPrimitive` vs. `WorkPrimitive`, plan
is not occurrence — and applies the same distinction to the transition
API itself, which had never gotten it.

Two related proposals were reviewed alongside this batch and rejected,
on the same grounds each time: runtime-affordance/tool-availability
projection and mandatory orientation-revision metadata, both admitted
outright that they never change `can_fire` or any computed outcome —
`CONTRIBUTING.md`'s own design rule rules that out directly, independent
of what the metadata happens to be about. See
[`REJECTED_RUNTIME_AFFORDANCE_PROJECTION.md`](REJECTED_RUNTIME_AFFORDANCE_PROJECTION.md)
and [`REJECTED_ORIENTATION_VIEW_PROJECTION.md`](REJECTED_ORIENTATION_VIEW_PROJECTION.md).

## How it was tested, and how you can too

Verify() coverage locally (26/26) proves the code does what the tests
say. What actually found the sharpest bug in this batch was the same
thing that found the one real bug in Ignition Lock: deliberately
adversarial testing against the live engine through `dev_mcp`, not
design review.

The find: `AuthorizationReceipt.expires_at_step` was checked against
`step_count`, which only advances on `step()`. Issue two receipts against
the same state, fire one, fire an unrelated transition back to a
fingerprint-identical state purely through `attempt_transition()` calls —
zero `step()` calls anywhere — and the second, never-consumed receipt
still validated. The state had genuinely round-tripped back to the exact
fingerprint it was issued against; nothing had advanced to say otherwise.
Confirmed live via `run_scenario`, fixed the same session with a
dedicated `_authorization_clock` that ticks on every fire, not just every
look — v1.9.1, same day.

`run_scenario(code, scope="core", compliance_mode=True)` runs arbitrary
Python scenario code with the package's classes pre-imported. If a claim
in this document doesn't hold up against your own adversarial scenario,
that's the tool to confirm or deny it with — not a request to trust this
write-up.

## Conclusion

Ignition Lock answered *who's allowed to fire this*. Provenance answers
the three questions underneath that one: approved under what conditions,
proposed as what specifically, and when — precisely, not approximately.
None of the three mechanisms here claim to close every gap in that
space; `AuthorizationReceipt` still doesn't defend the channel that
mints receipts in the first place, `MoveIntent` still doesn't fold its
own parameters into stagnation detection, and none of this replaces a
map author's judgment about what a move actually means. What each one
does is stop the map from silently pretending it knows something it
doesn't — the same job every mechanism in this library has had since
`safe_alternatives` and `pending_authorizations` first drew that line.

See [`CHANGELOG.md`](../../CHANGELOG.md) for the version-by-version
account, and each mechanism's own `EXPANDED_*.md` for the full detail
this document deliberately leaves out.
