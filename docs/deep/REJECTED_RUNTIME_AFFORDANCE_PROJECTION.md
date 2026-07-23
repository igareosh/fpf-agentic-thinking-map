# Rejected: Runtime Affordance Projection

**Status**: Rejected — will not be added to this package.
**Date**: 2026-07-23
**Decision by**: igareosh (prichindel.com)
**Source**: an external draft submitted for review, proposing runtime
orientation additions to this package. Its pending-external-input /
`AWAIT` proposal was adopted — see
[`ADOPTED_PENDING_INPUT_AWAIT.md`](ADOPTED_PENDING_INPUT_AWAIT.md). Its
tool/capability-availability proposal, covered here, was not.

## What was proposed

A `RuntimeAffordance` primitive (`affordance_id`, `label`, `kind`,
`available`, opaque `metadata`) attached to `RuntimeBinding`, plus a
`TransitionPrimitive.relevant_affordance_ids` declaration naming which
affordances a map author considers relevant to a given move. `slice()`
would gain an `affordances` block splitting into `available` /
`relevant_to_move` / `relevant_but_unavailable`, purely as orientation —
explicitly, by the proposal's own invariants, never entering
`missing_evidence_for()`, gate evaluation, guard denial, `can_fire`, or
`transition_to()`.

## Why it is rejected

This repo's own contribution rule settles it before any implementation
detail matters. `CONTRIBUTING.md` lists, under **Out of scope**:

> Additions that enrich the semantic model without changing per-move agent
> behavior [...] Runtime payload growth (more fields in the LLM prompt
> state, wider slices, ambient scanning).

and states the **Design rule** plainly:

> Only add structure when a missing relation changes what the agent does
> on a single move.

The proposal fails that test by its own admission, not by a stretch of
interpretation: it states directly that `can_fire` stays the same whether
a relevant affordance is present or absent. Nothing about what the model
is legally allowed to do changes. That makes it enrichment of the
semantic model without a behavioral relation behind it — the precise
shape `CONTRIBUTING.md` already rules out, not a judgment call specific to
this proposal.

Compare it to `safe_alternatives`, the nearest real precedent
(`ADOPTED_IGNITION_LOCK.md`): that field changes what the model can act on
next — it's folded directly into the `ESCALATE` outcome as concrete,
fireable alternative transitions. A relevant-but-unavailable affordance
folds into nothing. It is map-author-declared metadata, echoed back
verbatim, with no computed relation to any decision the engine makes —
closer to a comment than a primitive.

There's a second, more concrete problem underneath the scope argument: in
every real deployment shape this package targets, the host's own
function-calling/tool-use API already tells the model what tools are
available, natively, as part of the same turn. Routing an equivalent list
through the map adds a second primitive, a second wire format, and a
second place that can drift out of sync with the host's actual tool
inventory — for information the model already has. The proposal's own
fallback (project unstructured `available_tools` strings as affordances
when the structured list is empty) underlines this: it treats the
pre-existing plain-string field as sufficient in the common case, which is
a tell that the structured version isn't earning its keep.

This is the same shape of rejection as
[`REJECTED_C32_CANDIDATE_SYNTHESIS.md`](REJECTED_C32_CANDIDATE_SYNTHESIS.md)
and [`REJECTED_F17_UNIFIED_TERM_SHEET.md`](REJECTED_F17_UNIFIED_TERM_SHEET.md):
structure proposed for orientation's sake, not because a missing relation
changes what the agent does on a single move.

## What was adopted instead

The same external draft's pending-external-input proposal — a declared
dependency plus an `AWAIT` outcome distinct from `IDLE` — does change
per-move behavior: it adds a real outcome the model acts differently on
(wait vs. stop). That part passes the same design rule this section fails,
and was kept. See
[`ADOPTED_PENDING_INPUT_AWAIT.md`](ADOPTED_PENDING_INPUT_AWAIT.md).

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
