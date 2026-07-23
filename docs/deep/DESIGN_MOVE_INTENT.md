# Design (accepted, not yet built) — MoveIntent and Move Inspection

**Status**: Accepted for implementation — no code exists yet. This document
is the implementation reference; nothing here should be read as shipped.
**Decision by**: igareosh (prichindel.com)
**Date**: 2026-07-23
**Source**: an external draft submitted for review, arguing
`TransitionPrimitive` identifies a reusable move *type* ("publish") while
every concrete attempt ("publish report-v3 to public" vs. "publish
report-v4 to regulator Y") collapses onto the same `transition_id` with no
distinguishing structure. Its concrete-move-identity proposal is accepted,
reduced. Its two-stage externally-enacted commit model stays design-only,
by its own original scoping. Its reject/adapter items were already
correct and are unchanged.

## Why this is in scope

Checked the central claim against the actual code rather than taking it
on faith: grepped the whole package for `parameters` and any per-attempt
identity concept — none exists. `attempt_transition(state, transition_id,
authorized=..., authorization=...)` and `TransitionPrimitive` really do
reduce "publish X to Y" and "publish X to Z" to the identical bare string
`"publish"`. `WorkPrimitive` already has `inputs`/`outputs: dict[str,
Any]` fields that could record exactly this kind of concrete detail, but
it's a `SemanticMap`-registered static primitive, pre-declared by the map
author like every other primitive on the board — it can't represent an
LLM improvising a novel parameter combination at runtime. The gap is
real.

More importantly, it isn't only decorative — `register_visit()`'s
stagnation counter keys on `f"{context_id}:{current_state}"`
(`state.py`) and resets only when the *evidence snapshot* changes. Two
genuinely distinct concrete moves sharing a `transition_id` and an
evidence snapshot read as the *same stagnant retry* today, and
`is_stagnant`/`visits_remaining` are already-computed values the model
acts on. That's a real "runtime produces a wrong outcome" case
(`CONTRIBUTING.md`'s **Review focus**), not the same shape as
`RuntimeAffordance` or the mandatory orientation projection, both of
which admitted outright that nothing computed changes because of them.

One objection checked and rejected: Claude Code's own tool-invocation
system (invocation ID, concrete input, progress, result) might seem to
already cover this, the same way a host's native tool-calling API already
made `RuntimeAffordance` redundant. It doesn't transfer. An invocation ID
identifies a call to some external function; a `MoveIntent` identifies a
proposed transition in *this library's* graph — from_state, to_state,
gate, evidence — which nothing outside the library knows about. A single
`MoveIntent` might correspond to zero, one, or several actual tool calls,
or none at all for a purely internal reasoning transition. No existing
channel already gives the map this identity; nothing is being duplicated.

## What ships

### 1. `fpf_thinking_map/move_intent.py` (new module)

Same pattern as `authorization.py` / `pending_input.py` — a focused,
transient value object gets its own module, not a growth of `state.py`.

```python
@dataclass(frozen=True)
class MoveIntent:
    move_id: str
    transition_id: str
    parameters: dict[str, Any] = field(default_factory=dict)
    requested_by: str = ""
    binding_revision: int = 0
    parent_move_id: str | None = None
```

`parameters` stays opaque to the core, same discipline as
`PendingInput.source_ref` and `RuntimeAffordance.metadata` in the
rejected proposal — the core never interprets it, only carries it.

### 2. `ThinkingMapTraversal.inspect_move(state, intent)`

A thin wrapper, not new machinery: `step(state,
transition_id=intent.transition_id)` already evaluates gate, evidence,
and guards for one transition without mutating `current_state` — that
no-mutation path exists today. `inspect_move()` calls it and attaches
`intent` to the returned `Outcome.llm_prompt_state["move_intent"]`, the
same way the `BRIDGE` outcome already attaches `bridge_options` to its
prompt dict. No new evaluation logic; a name and a slice attachment.

### 3. `MoveTrace.move_id` / `MoveTrace.parent_move_id`

Two new optional fields (`str | None = None`) on the existing `MoveTrace`
dataclass. Populated when `attempt_transition()`/`transition_to()` is
called with an `intent` argument — `move_id` from `intent.move_id`,
`parent_move_id` from `intent.parent_move_id`. Gives the trace a stable
reference across the traversal, and something concrete for
`checkpoint()`'s `trace` block (`DESIGN_TRAVERSAL_CHECKPOINT.md`) to carry
forward — that document's own "why this matters" list names "which exact
move should appear in a checkpoint or continuation capsule" as something
FPF currently can't express; this is what closes it.

## What does not ship as part of this

**Folding `parameters` into the stagnation visit-key is not automatic.**
The gap identified above (two distinct `MoveIntent`s reading as one
stagnant retry) is the justification for building `MoveIntent` at all —
it is not, on its own, authorization to make `register_visit()` compare
opaque `parameters` dicts for equality. That would be an interpretive
policy decision this proposal never made, and it opens the same gaming
vector `register_visit()`'s own docstring already documents for evidence
("a harness that adds a new evidence_id on every attempt... resets the
counter every time, no matter how unproductive the loop actually is").
If a caller wants distinct `MoveIntent`s to reset stagnation, that is a
separate, explicit follow-up decision — with the same tradeoff writeup
evidence-triggered reset already carries — not a side effect of adopting
identity/lineage.

## Explicitly not built now

- **Two-stage commit** (`engine.inspect_move()` → act externally →
  `engine.commit_move(state, intent, work_record=...)` /
  `engine.record_move_failure(state, intent, evidence=[...])`) — the
  source draft already marks this design-only, gated on a
  `TransitionPrimitive` classification (which transitions "claim some
  external occurrence changed reality") that doesn't exist yet. Correct
  call, unchanged here. `attempt_transition()`/`transition_to()` remain
  the only firing path; nothing about this document forks it.
- **Storing arbitrary tool progress, executing or supervising a move** —
  not a new rejection; consistent with every boundary already drawn this
  week (`PendingInput.source_ref` opaque, `dev_mcp` keeping execution
  outside core, `ADV-08`'s no-persistence-surface stance). No separate
  write-up needed; nothing here loosens it.
- **Multi-agent branch management** — adapter-owned, same as the
  continuation capsule in `DESIGN_TRAVERSAL_CHECKPOINT.md`. An adapter
  building a branch tree out of `parent_move_id` chains today already
  can; the core doesn't need to model the tree itself.

## Regression guarantee

A caller that never constructs a `MoveIntent` sees zero behavioral
change: `attempt_transition()`/`transition_to()` keep working with a bare
`transition_id` exactly as before, `MoveTrace.move_id`/`parent_move_id`
default to `None`, and `inspect_move()` is a new method, not a
replacement for anything existing.
