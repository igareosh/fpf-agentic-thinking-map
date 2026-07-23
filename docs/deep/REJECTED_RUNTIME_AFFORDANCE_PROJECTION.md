# Rejected: Runtime Affordance Projection (ADOPT-1)

**Status**: Rejected — will not be added to this package.
**Date**: 2026-07-23
**Decision by**: igareosh (prichindel.com)
**Source**: "FPF Runtime Orientation Alignment Specification" (GPT-authored
external draft, submitted for review), section 5 (`ADOPT-1`). Sections 6–7
of the same draft (pending external inputs, `AWAIT`) were adopted — see
[`ADOPTED_PENDING_INPUT_AWAIT.md`](ADOPTED_PENDING_INPUT_AWAIT.md).

## What ADOPT-1 proposed

A `RuntimeAffordance` primitive (`affordance_id`, `label`, `kind`,
`available`, opaque `metadata`) attached to `RuntimeBinding`, plus
`TransitionPrimitive.relevant_affordance_ids` declaring which affordances
a map author considers relevant to a given move. `slice()` would gain an
`affordances` block splitting into `available` / `relevant_to_move` /
`relevant_but_unavailable`, purely as orientation — explicitly, by the
draft's own §5.3 and §9.1, never entering `missing_evidence_for()`, gate
evaluation, guard denial, `can_fire`, or `transition_to()`.

## Why it is rejected

The draft's own invariants are the argument against it. §9.1 states
plainly that `can_fire` stays `true` regardless of what affordances are
present or absent — meaning the entire feature computes nothing the engine
acts on. That is exactly the case `CONTRIBUTING.md`'s design rule rejects:

> Only add structure when a missing relation changes what the agent does
> on a single move.

and the matching out-of-scope entry:

> Additions that enrich the semantic model without changing per-move agent
> behavior [...] Runtime payload growth (more fields in the LLM prompt
> state, wider slices, ambient scanning).

Compare it to `safe_alternatives`, the nearest real precedent
(`ADOPTED_IGNITION_LOCK.md`): that field changes what the model can act on
next — it's folded directly into the `ESCALATE` outcome as concrete,
fireable alternative transitions. `relevant_affordance_ids` folds into
nothing. It is map-author-declared metadata, echoed back verbatim, with no
computed relation to any decision the engine makes — closer to a comment
than a primitive.

There's a second, more concrete problem underneath the abstract one: in
every real deployment shape this package targets, the host's own
function-calling/tool-use API already tells the model what tools are
available, natively, as part of the same turn. Routing an equivalent list
through the map adds a second primitive, a second wire format, and a
second place that can drift out of sync with the host's actual tool
inventory — for information the model already has. §5.5's `available_tools`
compatibility fallback underlines this: the feature's own design treats
the pre-existing plain-string list as sufficient in the common case,
which is a tell that the structured version isn't earning its keep.

This is the same shape of rejection as
[`REJECTED_C32_CANDIDATE_SYNTHESIS.md`](REJECTED_C32_CANDIDATE_SYNTHESIS.md)
and [`REJECTED_F17_UNIFIED_TERM_SHEET.md`](REJECTED_F17_UNIFIED_TERM_SHEET.md):
structure proposed for orientation's sake, not because a missing relation
changes what the agent does on a single move.

## What was adopted instead

The same draft's `ADOPT-2`/`ADOPT-3` (pending external inputs, `AWAIT`
distinct from `IDLE`) do change per-move behavior — they add a real
outcome the model can act differently on (wait vs. stop) — and were kept.
See [`ADOPTED_PENDING_INPUT_AWAIT.md`](ADOPTED_PENDING_INPUT_AWAIT.md).

## What would change this

If a concrete failure mode surfaces where a model fires a `CONTINUE`-legal
transition specifically *because* it couldn't tell a tool it needed was
unavailable — not a hypothetical, an actual observed traversal going
wrong for that reason — that's the trigger to revisit, the same
"deferred, not rejected outright" treatment given to other patterns in
this file's siblings. Absent that, the host's native tool-availability
signal already covers this, and the map should not duplicate it.

---

prichindel.com | 2026-07-23 | v1.8.0
