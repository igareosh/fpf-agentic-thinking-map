# Adopted — MoveIntent and Move Inspection (2026-07-23)

**Status**: Adopted, unreleased (built on local `main`, not yet pushed or
pinned — see `governance/SPEC-ETHAN-FPF-THINKING-MAP-MOVE-INTENT.md` in
the brain repo for the ratification record and current release state).
**Decision by**: igareosh (prichindel.com)
**Source**: an external draft submitted for review, arguing
`TransitionPrimitive` identifies a reusable move *type* ("publish") while
every concrete attempt ("publish report-v3 to public" vs. "publish
report-v4 to regulator Y") collapses onto the same `transition_id` with no
distinguishing structure. Its concrete-move-identity proposal shipped
here, reduced. Its two-stage externally-enacted commit model stays
design-only, by its own original scoping. Its reject/adapter items were
already correct and are unchanged.

## Why this is in scope

Checked the central claim against the actual code rather than taking it
on faith: grepped the whole package for `parameters` and any per-attempt
identity concept before building anything — none existed.
`attempt_transition(state, transition_id, authorized=...,
authorization=...)` and `TransitionPrimitive` really did reduce "publish X
to Y" and "publish X to Z" to the identical bare string `"publish"`.
`WorkPrimitive` already has `inputs`/`outputs: dict[str, Any]` fields that
could record exactly this kind of concrete detail, but it's a
`SemanticMap`-registered static primitive, pre-declared by the map author
like every other primitive on the board — it can't represent an LLM
improvising a novel parameter combination at runtime. The gap was real.

More importantly, it wasn't only decorative — `register_visit()`'s
stagnation counter keys on `f"{context_id}:{current_state}"` (`state.py`)
and resets only when the *evidence snapshot* changes. Two genuinely
distinct concrete moves sharing a `transition_id` and an evidence snapshot
read as the *same stagnant retry*, and `is_stagnant`/`visits_remaining`
are already-computed values the model acts on. That's a real "runtime
produces a wrong outcome" case (`CONTRIBUTING.md`'s **Review focus**), not
the same shape as `RuntimeAffordance` or the mandatory orientation
projection, both of which admitted outright that nothing computed changes
because of them.

One objection checked and rejected: Claude Code's own tool-invocation
system (invocation ID, concrete input, progress, result) might seem to
already cover this, the same way a host's native tool-calling API already
made `RuntimeAffordance` redundant. It doesn't transfer. An invocation ID
identifies a call to some external function; a `MoveIntent` identifies a
proposed transition in *this library's* graph — from_state, to_state,
gate, evidence — which nothing outside the library knows about. A single
`MoveIntent` might correspond to zero, one, or several actual tool calls,
or none at all for a purely internal reasoning transition. No existing
channel already gave the map this identity; nothing was being duplicated.

## What shipped

### 1. `fpf_thinking_map/move_intent.py` (new module)

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
`PendingInput.source_ref` — the core never interprets it, only carries
it.

### 2. `ThinkingMapTraversal.inspect_move(state, intent)`

A thin wrapper, not new machinery: delegates to `step(state,
transition_id=intent.transition_id)`, the no-mutation evaluation path
that already existed, then attaches `intent` to the returned
`Outcome.llm_prompt_state["move_intent"]` as `{"move_id", "transition_id",
"parameters"}` — the same pattern the `BRIDGE` outcome already uses for
`bridge_options`. Calling it repeatedly while the model revises
`parameters` before deciding is always safe; it never mutates state.

### 3. `MoveTrace.move_id` / `MoveTrace.parent_move_id`

Two new optional fields (`str | None = None`). Stamped by
`transition_to()` (and forwarded through `attempt_transition()`) from
`intent.move_id`/`intent.parent_move_id` on a successful fire — giving
the trace a stable reference across the traversal, and something concrete
for `checkpoint()`'s `trace` block (`DESIGN_TRAVERSAL_CHECKPOINT.md`) to
carry forward once that ships.

### 4. Mismatched-intent handling (found during implementation, not in the source draft)

`transition_to(transition_id, intent=...)` only stamps `move_id`/
`parent_move_id` when `intent.transition_id == transition_id`. An intent
naming a different transition than the one that actually fired is
treated as if no intent were given — not stamped, and not blocking the
fire either, since intent carries no legality weight either way. Without
this check, a caller mistakenly passing the wrong `MoveIntent` object
would silently corrupt `trace` with an unrelated move's identity; the
source draft didn't specify this because it didn't consider the
mismatched-object case. Checked directly with `state.transition_to()`,
not just through the engine wrapper — same defense-in-depth split every
other intent-shaped check in this engine already uses.

## What did not ship as part of this

**Folding `parameters` into the stagnation visit-key.** The gap that
justified building `MoveIntent` (two distinct proposals reading as one
stagnant retry) is not, on its own, authorization to make
`register_visit()` compare opaque `parameters` dicts for equality. That
would be a separate interpretive policy decision, and it opens the same
gaming vector `register_visit()`'s own docstring already documents for
evidence ("a harness that adds a new evidence_id on every attempt...
resets the counter every time, no matter how unproductive the loop
actually is"). `check_move_intent` tests this directly — two different
`MoveIntent`s inspected at the same state with the same evidence still
produce `visit_count == 2`, asserting the current, documented boundary
rather than silently changing it.

## Explicitly not built

- **Two-stage commit** (`commit_move`/`record_move_failure` for
  externally-enacted transitions) — the source draft already marks this
  design-only, gated on a `TransitionPrimitive` classification that
  doesn't exist yet. `attempt_transition()`/`transition_to()` remain the
  only firing path; nothing here forks it.
- **Storing arbitrary tool progress, executing or supervising a move** —
  not a new rejection; consistent with every boundary already drawn this
  week (`PendingInput.source_ref` opaque, `dev_mcp` keeping execution
  outside core, `ADV-08`'s no-persistence-surface stance).
- **Multi-agent branch management** — adapter-owned, same as the
  continuation capsule in `DESIGN_TRAVERSAL_CHECKPOINT.md`. An adapter
  building a branch tree out of `parent_move_id` chains today already
  can.

## Regression guarantee

A caller that never constructs a `MoveIntent` sees zero behavioral
change: `attempt_transition()`/`transition_to()` keep working with a bare
`transition_id` exactly as before, `MoveTrace.move_id`/`parent_move_id`
default to `None`, and `inspect_move()` is a new method, not a
replacement for anything existing. 26/26 verify checks pass (was 25/25);
`dev_mcp`'s 38/38 are unaffected — no change to `attempt_bridge()` and
`attempt_transition()`'s existing parameters, only an additional optional
one.
