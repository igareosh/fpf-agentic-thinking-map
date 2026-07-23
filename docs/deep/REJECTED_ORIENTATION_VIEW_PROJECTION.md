# Rejected: Mandatory Orientation Projection in Every View

**Status**: Rejected — will not be added to this package.
**Date**: 2026-07-23
**Decision by**: igareosh (prichindel.com)
**Source**: an external draft submitted for review, proposing checkpoint/
restore and traversal-orientation additions. Its checkpoint/restore
portion is accepted — see
[`DESIGN_TRAVERSAL_CHECKPOINT.md`](DESIGN_TRAVERSAL_CHECKPOINT.md). This
document covers only the part of it that isn't: the requirement that
`map_revision`, `binding_revision`, and `computed_at_step` appear in
*every* `slice()` and `to_llm_prompt_state()` call, not just in a
checkpoint.

## What was proposed

Every full state and focused slice would gain:

```json
{
  "orientation": {
    "map_revision": "sha256:...",
    "binding_revision": 12,
    "computed_at_step": 7
  }
}
```

on every single `step()`, alongside an explicit admission that this data
never changes what the engine decides: "This is orientation, not
enforcement" and "Orientation revision informs the model but does not
authorize or deny moves."

## Why it is rejected

That admission is the whole argument, and this repo already ruled on the
identical shape once this week. `CONTRIBUTING.md`'s **Out of scope**
list:

> Additions that enrich the semantic model without changing per-move agent
> behavior [...] Runtime payload growth (more fields in the LLM prompt
> state, wider slices, ambient scanning).

and its **Design rule**:

> Only add structure when a missing relation changes what the agent does
> on a single move.

`REJECTED_RUNTIME_AFFORDANCE_PROJECTION.md` rejected a different
proposal for exactly this reason days earlier — that one also stated
outright that `can_fire` never changes because of it. Accepting this one
anyway, on the grounds that it's about traversal identity instead of tool
availability, would apply the rule selectively. The test in
`CONTRIBUTING.md` doesn't ask what the metadata is about; it asks whether
it changes a computed decision. Neither proposal's own field-list does.

What's actually load-bearing survives this rejection intact:
`map_fingerprint` equality and `orientation.binding_revision` are real,
necessary parts of `from_checkpoint()`'s own validation — that's core to
`DESIGN_TRAVERSAL_CHECKPOINT.md` and stays. The rejected part is narrower
than the whole idea: forcing that same data into every `slice()` /
`to_llm_prompt_state()` call regardless of whether anything is being
checkpointed. `ActiveState.map_revision` / `binding_revision` remain real
fields for that reason — they're just not projected into every view.

## What this means for a host that wants to show the model staleness

Nothing stops it — the host already holds whatever checkpoint it last
took, and can read `orientation.binding_revision` straight off that
without the core manufacturing a slice field for it. Same argument as
`REJECTED_RUNTIME_AFFORDANCE_PROJECTION.md`'s tool-availability case: the
data already exists somewhere the host controls; duplicating it into
every prompt-facing view isn't the only way to make it visible, and it's
the one CONTRIBUTING.md's rule rules out.

## What would change this

If a host integration finds a model actually needs revision awareness
*inline*, in the same turn as a move decision — not "the host chooses to
show it," but a demonstrated case where the model reasons wrong without
it in the slice itself — that's a concrete, testable trigger to revisit,
not a hypothetical one. Absent that, `checkpoint()`'s own `orientation`
block already carries this data to wherever it's needed.

---

prichindel.com | 2026-07-23 | pre-v1.9.0 (design stage, no release yet)
