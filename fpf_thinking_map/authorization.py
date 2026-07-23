"""Authorization receipts — a human's yes, scoped to the exact state it was given for.

`attempt_transition(state, "publish", authorized=True)` is an ambient boolean:
it says a human said yes, but not *to what*. That gap is a TOCTOU hole —
inspect state A, get a human's approval, let the model take other moves that
carry the traversal to state B, then spend the same `authorized=True` there.
The human approved A. Nobody approved B.

An AuthorizationReceipt closes that gap by naming the transition and hashing
the exact state it was issued against. verify_authorization() (called from
both ActiveState.transition_to() and ThinkingMapTraversal.attempt_transition(),
same defense-in-depth split as the authorized= boolean) rejects a receipt
whose transition, state, or freshness doesn't match *right now* — not
whatever was true when it was issued.

authorized=True still works, unmigrated. Prefer this eventually.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fpf_thinking_map.state import ActiveState


@dataclass(frozen=True)
class AuthorizationReceipt:
    """One human decision, scoped to one transition and one inspected state.

    Not reusable against a different transition (transition_id is checked),
    not reusable once the state has moved (state_fingerprint is checked),
    not reusable twice (request_id is checked against
    ActiveState.consumed_authorizations), and not valid forever
    (expires_at_step bounds how many step()s may pass before it goes stale
    even if the fingerprint would otherwise still match).
    """
    transition_id: str
    state_fingerprint: str
    request_id: str
    issued_at_step: int
    expires_at_step: int


def compute_state_fingerprint(state: "ActiveState") -> str:
    """Hash of exactly what a human inspects before approving a move.

    Context + current_state + the evidence set in view — the parts of
    ActiveState an approval is actually conditioned on. Anything that
    changes one of these invalidates every receipt issued against the old
    value, by construction: the hash won't match.
    """
    payload = {
        "context": state.binding.active_context_id,
        "current_state": state.current_state,
        "evidence": sorted(state.available_evidence_ids),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def issue_authorization_receipt(
    state: "ActiveState",
    transition_id: str,
    request_id: str,
    ttl_steps: int = 1,
) -> AuthorizationReceipt:
    """Stamp a receipt against the state as it exists right now.

    Call this at the moment a human actually approves — not earlier, not
    from a cached inspection. ttl_steps bounds how many step()s may pass
    before the receipt goes EXPIRED even if the fingerprint would otherwise
    still match (e.g. the traversal loops back through the same state).
    """
    return AuthorizationReceipt(
        transition_id=transition_id,
        state_fingerprint=compute_state_fingerprint(state),
        request_id=request_id,
        issued_at_step=state.step_count,
        expires_at_step=state.step_count + ttl_steps,
    )
