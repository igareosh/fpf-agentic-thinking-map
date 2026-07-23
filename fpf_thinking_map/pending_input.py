"""Pending external inputs — traversal waiting on something the map doesn't produce.

`IDLE` today means two different things at once: "done, nothing left to do"
and "nothing to do *right now*, but something outside the map is still owed."
Those call for different agent behavior — stop, versus come back later — and
collapsing them loses the distinction the same way a single `current_state`
string once lost track of a still-unanswered human ask (see
`ActiveState.pending_authorizations`, closed for that reason).

A PendingInput names one such external dependency: a worker result, a human
reply, an event from a process the map does not run. The map never polls,
schedules, or resolves it — it only carries the fact that it's outstanding,
and the wake conditions that would resolve it, so the model (and the host
loop around it) can tell "nothing to do, ever" from "nothing to do, yet."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PendingInputStatus(Enum):
    EXPECTED = "expected"
    PENDING = "pending"
    RECEIVED = "received"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PendingInput:
    """One declared external dependency the map is waiting on.

    source_ref is opaque to the core — it may name a worker, a human
    request, an external service, anything the host owns the lifecycle of.
    The core never reads it; it exists so the host/adapter can find its way
    back to whatever it refers to.

    unresolved is EXPECTED or PENDING — the two states that still block.
    RECEIVED/FAILED/CANCELLED are resolutions; the host sets them, the core
    never does.
    """
    input_id: str
    label: str = ""
    status: PendingInputStatus = PendingInputStatus.EXPECTED
    expected_evidence_ids: list[str] = field(default_factory=list)
    source_ref: str = ""
    wake_conditions: list[str] = field(default_factory=list)
    context_id: str | None = None

    @property
    def unresolved(self) -> bool:
        return self.status in (PendingInputStatus.EXPECTED, PendingInputStatus.PENDING)
