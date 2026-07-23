# Design (accepted, not yet built) — Traversal Checkpoint and Restore

**Status**: Accepted for implementation — no code exists yet. This document
is the implementation reference; nothing here should be read as shipped.
**Decision by**: igareosh (prichindel.com)
**Date**: 2026-07-23
**Source**: split from an external draft submitted for review, proposing
checkpoint/restore and traversal-orientation additions to this package.
The checkpoint/restore portion is accepted here, in reduced form. Its
requirement to project revision metadata into every `slice()` and
`to_llm_prompt_state()` call is rejected — see
[`REJECTED_ORIENTATION_VIEW_PROJECTION.md`](REJECTED_ORIENTATION_VIEW_PROJECTION.md).
Its rebind design and continuation-capsule sketch are untouched: both were
already correctly non-normative/adapter-only in the source draft and stay
that way — tracked below, not scheduled.

## Why this is in scope

`CONTRIBUTING.md`'s **Review focus** covers this directly:

> Bug fixes where the runtime produces a wrong outcome (wrong gate
> decision, wrong guard verdict, evidence check that doesn't enforce)

Three fields on `ActiveState` are declared `init=False`:

```python
_evidence_added_at: dict[str, int] = field(default_factory=dict, init=False, repr=False)
_state_visits: dict[str, int] = field(default_factory=dict, init=False, repr=False)
_state_visit_evidence: dict[str, frozenset[str]] = field(default_factory=dict, init=False, repr=False)
```

There is no supported way to hand a paused `ActiveState` back to the
constructor today. Any host that needs to survive a process boundary —
which is most of what this library's own downstream integrations look
like — has to hand-roll a reconstruction, and it will silently corrupt
TTL decay and stagnation counting the moment it does, because those three
fields are the ones no constructor accepts. That's a real "runtime
produces a wrong outcome" bug class sitting one layer above the library,
not a hypothetical one.

This is also not a new kind of scope for the package — it finishes a job
`ADOPTED_IGNITION_LOCK.md` started. `pending_authorizations` /
`denied_authorizations` (and this week's `consumed_authorizations`, see
`ADOPTED_PENDING_INPUT_AWAIT.md`'s sibling work) were pulled out to real
constructor fields for exactly this reason — "a harness restoring from
persistence can pass it straight back in," in their own docstrings. The
three private counters are what got left behind. This closes that.

## What ships

### 1. `fpf_thinking_map/checkpoint.py` (new module)

Same pattern as `authorization.py` and `pending_input.py` — a focused,
new, cross-cutting concern gets its own module rather than growing
`state.py` further.

```python
class CheckpointError(ValueError): ...
class UnsupportedCheckpointVersion(CheckpointError): ...
class MapFingerprintMismatch(CheckpointError): ...
class InvalidCheckpointState(CheckpointError): ...

SCHEMA_VERSION = "1"

def build_checkpoint(state: "ActiveState") -> dict: ...
def restore_from_checkpoint(
    semantic_map: "SemanticMap", checkpoint: dict, *, strict: bool = True,
) -> "ActiveState": ...
```

`ActiveState.checkpoint()` and `ActiveState.from_checkpoint(semantic_map,
checkpoint)` (the public API, matching the source draft's §4.1 exactly)
are thin wrappers that delegate to these two functions — same split
`authorization.py`'s `issue_authorization_receipt()` already uses.

Checkpoint schema (JSON-compatible only, matches the source draft's §4.2,
verified field-for-field against the real dataclasses):

```json
{
  "schema_version": "1",
  "map_fingerprint": "sha256:...",
  "orientation": {
    "map_revision": "sha256:...",
    "binding_revision": 0,
    "computed_at_step": 7
  },
  "binding": { "task": "...", "goal": "...", "...": "... every RuntimeBinding field ..." },
  "active": {
    "current_state": "candidate",
    "step_count": 7,
    "stagnation_threshold": 3,
    "pending_authorizations": [],
    "denied_authorizations": {},
    "consumed_authorizations": [],
    "evidence_added_at": {"test_results": 4},
    "state_visits": {"deployment:candidate": 2},
    "state_visit_evidence": {"deployment:candidate": ["test_results"]},
    "trace": {
      "previous_state": "prepared", "last_transition_id": "prepare_candidate",
      "bridge_target": null, "blockers": [], "evidence_delta": ["test_results"]
    }
  }
}
```

Two additions the source draft's schema doesn't have, because they didn't
exist when it was written: `consumed_authorizations` (this week's
`AuthorizationReceipt` replay guard — must round-trip or a restored state
would accept an already-spent receipt again) and whatever
`RuntimeBinding.pending_inputs` carries (this week's `PendingInput` —
JSON-compatible already, just needs `status` serialized via `.value`).

### 2. `SemanticMap.fingerprint()`

Canonical SHA-256 over sorted, JSON-serialized primitive data —
`contexts`, `roles`, `role_assignments`, `work_records`, `work_plans`,
`speech_acts`, `commitments`, `gates`, `evidence`, `transitions`,
`publications` — every dict already on `SemanticMap`. Checked: none of
these primitive dataclasses hold a `Callable` field (confirmed by grep —
`GuardEngine` and `LogicLayer` are constructed separately and passed into
`ThinkingMapTraversal`, never registered on `SemanticMap`), so this is
plain-data serialization, not object introspection.

Implementation note the source draft didn't have to consider (it doesn't
know this file's caching pattern): cache the result the same way
`_ctx_transition_idx` already is —

```python
_fingerprint: str | None = field(default=None, init=False, repr=False)
```

— invalidated on every `register_*` call, not just `register_transition`
(today only `register_transition` resets `_ctx_transition_idx`; the
fingerprint cache needs the same reset added to all ten `register_*`
methods, since any of them changes what the map hashes to).

### 3. `ActiveState.map_revision` / `ActiveState.binding_revision`

Real constructor fields (`map_revision: str = ""`, `binding_revision: int
= 0`), populated because checkpoint validation needs them
(`map_fingerprint` equality, the checkpoint's own `orientation` block) —
not projected into `slice()` or `to_llm_prompt_state()`. See the rejected
doc for why that projection doesn't happen.

`ActiveState.mark_binding_changed()` — increments `binding_revision` by
one, no other side effect. Cheap, single-purpose, kept because the
checkpoint's own `orientation.binding_revision` field needs a caller-owned
way to advance — an adapter that wants to expose staleness to the model
can read it straight off a checkpoint it already holds, without the core
manufacturing a slice field for it.

### 4. Restore validation, in order (source draft §4.6, mapped onto real code)

1. `schema_version` is `"1"` (only supported value right now) → else `UnsupportedCheckpointVersion`
2. required top-level keys present, correct value types → else `InvalidCheckpointState`
3. `map_fingerprint == semantic_map.fingerprint()` → else `MapFingerprintMismatch`
4. `active_context_id` exists in `semantic_map.contexts`
5. `current_state` is a known state for that context — derived by
   scanning `{t.from_state, t.to_state} for t in semantic_map.transitions.values() if t.context_id == ctx_id}`,
   since there is no separate state-primitive/registry today; this scan
   is new code, not an existing lookup
6. bound evidence IDs are known, when `strict=True` (the default)
7. every `evidence_added_at` value `<= step_count`
8. `state_visits` values are non-negative
9. `state_visit_evidence` values decode to valid evidence-id collections
10. `pending_authorizations` / `denied_authorizations` / `consumed_authorizations`
    keys/transition-ids resolve to known transitions
11. `trace.last_transition_id` / `trace.bridge_target`, when present,
    reference a real transition / context

Any failure raises immediately — `from_checkpoint()` never partially
restores or silently repairs.

### 5. No side effects

Neither `checkpoint()` nor `from_checkpoint()` may call `step_count += 1`,
`register_visit()`, `add_evidence()`, or fire a transition. Observational
only, same as the source draft's §4.8 — this is a straightforward
constraint to hold, not an open design question.

## Fidelity requirement

For an unchanged map: `state.to_llm_prompt_state()` before checkpointing
must equal `ActiveState.from_checkpoint(semantic_map,
state.checkpoint()).to_llm_prompt_state()` after restoring, and the next
`traversal.step()` call must produce the same outcome kind/reason on both
— same test shape as `check_authorization_receipt` and
`check_pending_input_await`, extended to cover TTL freshness, stagnation
state, and both authorization dicts plus the new `consumed_authorizations`
set.

## Explicitly not built now

- **Rebind** (`state.rebind(new_binding, mode=...)`, `RebindMode.ENRICH` /
  `REORIENT` / `SUPERSEDE`) — the source draft already gates this behind
  checkpoint/fingerprint stability and leaves evidence/authorization
  carry-forward rules unspecified. That gate is correct as written; this
  document doesn't loosen it. Tracked, not scheduled.
- **Continuation capsule** (`{checkpoint, current_slice, pending_inputs,
  orientation_revision, host_continuation_notes}`) — already correctly
  adapter-owned in the source draft (conversation summaries, worker
  state, transport are explicitly not core concerns). Nothing to
  implement here; an adapter composing this from `checkpoint()` +
  `slice()` output today already can.

## Regression guarantee

A caller that never calls `checkpoint()`/`from_checkpoint()` sees zero
behavioral change: `map_revision`/`binding_revision` are new fields with
inert defaults, `mark_binding_changed()` is never called unless the host
calls it, and no existing method's return shape changes.
