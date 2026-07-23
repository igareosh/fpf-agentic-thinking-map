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

## Why now — this tracks what capable models already do, not the other way around

None of this release asks a model to do something new. Each mechanism
gives the map a place to receive structure a sufficiently capable model
and agent harness already produce natively — the gap being closed is in
the map, not in the model.

- **Tail Number.** Every modern tool-calling API — the ones behind
  Claude, and every serious agent harness built on top of one — already
  gives each tool invocation its own call ID and its own distinct
  arguments, separate from the tool's name. A model reasoning well
  already tells "publish this artifact to this audience" apart from
  "publish that one to a different one" when it makes the call; the map
  used to throw that distinction away the instant it arrived, keeping
  only the bare `transition_id`. `MoveIntent` is the map catching up to
  structure the model side already had.
- **Clearance.** Scoped, single-use authorization — a token good for one
  specific action under one specific condition, not an ambient "yes" —
  is exactly the shape human-in-the-loop gates take in every serious
  agent framework already: an approval object issued by something
  outside the model's own reasoning loop, checked against, not asserted
  by, the model. A capable agent doesn't need to be told what a receipt
  is; it already expects to be handed one and to present it, not
  fabricate one. `authorized=True` asked the model (or whatever calls on
  its behalf) to just say so instead.
- **Holding Pattern.** Tool results that come back "still running, check
  again" instead of "done" are already an ordinary shape in async/
  long-running tool-use — background jobs, queued approvals, anything
  that doesn't resolve inside one turn. A model built for that world
  already knows the difference between "nothing left to do" and "not
  done yet, waiting on something." `IDLE` collapsing both into one value
  was the map failing to represent a distinction the calling side was
  already prepared to make.

The honest boundary, same one every mechanism in this library draws:
none of this makes a weak model behave well. A model that ignores the
receipt it was handed, invents a `move_id` inconsistently across turns,
or never checks `AWAIT` before assuming it's stuck gets exactly the same
outcome it would have gotten before this release — these are affordances
a capable model and a well-built harness can use correctly, not
enforcement that makes an incapable one do so. What changes is that the
map no longer discards the structure a good agent already has to offer
it. That's the sense in which this release is about compliance with
where LLM tool-use and agentic design already are, not a bet on where
they're going.

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
