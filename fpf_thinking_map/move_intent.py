"""MoveIntent — a concrete proposed move, distinct from its transition type.

`TransitionPrimitive` names a reusable move *type* ("publish"). Every
concrete attempt at firing it — publish report-v3 to the public site,
publish report-v4 to a regulator — collapses onto that same bare
`transition_id` today, with nothing distinguishing one proposal from
another. That's not just a labeling gap: `ActiveState.register_visit()`'s
stagnation counter keys on `context:current_state` and only resets on a
changed evidence snapshot, so two genuinely different concrete moves that
happen to share a transition_id and evidence set read as the same stuck
retry.

MoveIntent gives one concrete proposal a stable identity (`move_id`),
optional lineage (`parent_move_id`), and a place for its specific
parameters to live — opaque to the core, same discipline as
`PendingInput.source_ref`: the map carries this, it never interprets it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MoveIntent:
    """One concrete proposed move against a `TransitionPrimitive`.

    parameters is opaque to the core — never read by gates, guards, or
    can_fire. Carrying it (and move_id/parent_move_id) into
    ActiveState.trace is the whole extent of what the engine does with it.
    """
    move_id: str
    transition_id: str
    parameters: dict[str, Any] = field(default_factory=dict)
    requested_by: str = ""
    binding_revision: int = 0
    parent_move_id: str | None = None
